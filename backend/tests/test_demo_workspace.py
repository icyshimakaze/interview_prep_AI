from httpx import AsyncClient, Cookies
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from interview_prep.modules.demo.router import CSRF_COOKIE_NAME

ORIGIN = {"Origin": "http://localhost:3000"}


async def test_fictional_workspace_content_reuse_and_idempotent_task_completion(
    integration_client: AsyncClient,
) -> None:
    created = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert created.status_code == 200
    dashboard = (await integration_client.get("/api/v1/demo/dashboard")).json()
    assert dashboard["mode"] == "demo" and "Fictional" in dashboard["data_label"]
    assert "fictional" in dashboard["profile"]["display_name"]
    assert len(dashboard["assessments"]) == 2 and len(dashboard["interviews"]) == 1
    assert all(a["result_kind"] == "simulation" for a in dashboard["assessments"])
    assert dashboard["interviews"][0]["result_kind"] == "simulation"
    assert len(dashboard["roadmap_items"]) == 3 and len(dashboard["progress"]) == 4
    headers = {**ORIGIN, "X-CSRF-Token": integration_client.cookies[CSRF_COOKIE_NAME]}
    reused = await integration_client.post("/api/v1/demo/sessions", json={}, headers=headers)
    assert reused.json()["id"] == created.json()["id"]
    task = next(item for item in dashboard["roadmap_items"] if item["status"] == "planned")
    path = f"/api/v1/demo/roadmap-items/{task['id']}/complete"
    assert (await integration_client.patch(path, json={}, headers=ORIGIN)).status_code == 403
    assert (
        await integration_client.patch(path, json={"user_id": "forged"}, headers=headers)
    ).status_code == 422
    for _ in range(2):
        assert (await integration_client.patch(path, json={}, headers=headers)).status_code == 200
    updated = (await integration_client.get("/api/v1/demo/dashboard")).json()
    assert len(updated["progress"]) == 5


async def test_two_demo_visitors_cannot_read_or_mutate_each_others_data(
    integration_client: AsyncClient,
) -> None:
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    first = (await integration_client.get("/api/v1/demo/dashboard")).json()
    integration_client.cookies.clear()
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    second = (await integration_client.get("/api/v1/demo/dashboard")).json()
    assert first["resumes"][0]["id"] != second["resumes"][0]["id"]
    for collection in ["resumes", "targets"]:
        response = await integration_client.get(
            f"/api/v1/demo/{collection}/{first[collection][0]['id']}"
        )
        assert response.status_code == 404
    headers = {**ORIGIN, "X-CSRF-Token": integration_client.cookies[CSRF_COOKIE_NAME]}
    assert (
        await integration_client.patch(
            f"/api/v1/demo/roadmap-items/{first['roadmap_items'][1]['id']}/complete",
            json={},
            headers=headers,
        )
    ).status_code == 404


async def test_exit_erases_demo_principal_and_all_private_data(
    integration_client: AsyncClient, database: AsyncEngine
) -> None:
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    headers = {**ORIGIN, "X-CSRF-Token": integration_client.cookies[CSRF_COOKIE_NAME]}
    response = await integration_client.delete("/api/v1/demo/session", headers=headers)
    assert response.status_code == 204
    assert (await integration_client.get("/api/v1/demo/dashboard")).status_code == 401
    async with database.connect() as connection:
        for table in [
            "principals",
            "candidate_profiles",
            "questions",
            "answer_evaluations",
            "progress_events",
            "demo_sessions",
        ]:
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0


async def test_expired_demo_can_reset_without_erasing_another_visitor(
    integration_client: AsyncClient, database: AsyncEngine
) -> None:
    first = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    first_id = first.json()["id"]
    first_cookies = Cookies(integration_client.cookies)
    integration_client.cookies.clear()
    second = await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    second_id = second.json()["id"]
    async with database.begin() as connection:
        await connection.execute(
            text(
                "UPDATE demo_workspaces SET expires_at=created_at+interval '1 microsecond' "
                "WHERE id=:id"
            ),
            {"id": first_id},
        )
    integration_client.cookies.clear()
    integration_client.cookies.update(first_cookies)
    assert (await integration_client.get("/api/v1/demo/dashboard")).status_code == 401
    assert (await integration_client.post("/api/v1/demo/reset", json={})).status_code == 403
    response = await integration_client.post("/api/v1/demo/reset", json={}, headers=ORIGIN)
    assert response.status_code == 204 and len(integration_client.cookies) == 0
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM candidate_profiles WHERE owner_id=:id"),
                {"id": second_id},
            )
            == 1
        )


async def test_reset_of_live_demo_requires_csrf(integration_client: AsyncClient) -> None:
    await integration_client.post("/api/v1/demo/sessions", json={}, headers=ORIGIN)
    assert (
        await integration_client.post("/api/v1/demo/reset", json={}, headers=ORIGIN)
    ).status_code == 403
    headers = {**ORIGIN, "X-CSRF-Token": integration_client.cookies[CSRF_COOKIE_NAME]}
    assert (
        await integration_client.post("/api/v1/demo/reset", json={}, headers=headers)
    ).status_code == 204
    assert (await integration_client.get("/api/v1/demo/dashboard")).status_code == 401
