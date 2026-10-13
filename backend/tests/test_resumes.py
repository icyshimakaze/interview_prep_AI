import asyncio
import subprocess
from collections.abc import AsyncIterator
from types import TracebackType
from urllib.parse import quote
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from pdf_helpers import pdf_bytes
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from test_auth import account_client as account_client
from test_auth import signed_token

from interview_prep.modules.assessments.models import Assessment, AssessmentStatus
from interview_prep.modules.context.models import Resume, ResumeSkillEvidence, ResumeVersion, Skill
from interview_prep.modules.resumes.extraction import extract_evidence
from interview_prep.modules.resumes.upload import MAX_BYTES, PdfParser, run_worker, safe_filename

BASE = "/api/v1/account/resumes"


async def login(client: httpx.AsyncClient, subject: str = "alice") -> None:
    client.headers["Authorization"] = "Bearer " + signed_token(subject)
    assert (await client.post("/api/v1/account/session", json={})).status_code == 200


async def upload(
    client: httpx.AsyncClient,
    data: bytes | None = None,
    filename: str = "candidate.pdf",
    mime: str = "application/pdf",
) -> httpx.Response:
    return await client.post(
        BASE,
        content=data if data is not None else pdf_bytes(),
        headers={
            "Content-Type": mime,
            "X-Resume-Filename": quote(filename, safe=""),
        },
    )


async def test_valid_pdf_extract_review_add_delete_and_private_retention(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await login(account_client)
    response = await upload(
        account_client,
        pdf_bytes(
            "Private contact sentinel: do not retain\nPython FastAPI PostgreSQL Docker\n"
            "Projects\nLibrary catalogue API\nEducation\nBSc Computer Science\n"
            "Experience\nIntern: implemented APIs"
        ),
    )
    assert response.status_code == 201, response.text
    resume = response.json()
    assert resume["page_count"] == 1 and resume["revision"] == 1
    assert {item["category"] for item in resume["evidence"]} == {
        "language",
        "framework",
        "database",
        "tool",
        "project",
        "education",
        "experience",
    }
    assert all(item["review_status"] == "proposed" for item in resume["evidence"])
    assert (
        "Private contact sentinel" not in response.text
        and "Private contact sentinel" not in caplog.text
    )
    assert (await account_client.get(BASE)).json()["items"][0] == resume
    path = f"{BASE}/{resume['id']}"
    evidence = next(item for item in resume["evidence"] if item["claim"] == "Python")
    corrected = await account_client.put(
        f"{path}/evidence/{evidence['id']}",
        json={
            "category": "language",
            "claim": "Python basics; still learning",
            "review_status": "confirmed",
            "expected_revision": 1,
        },
    )
    assert corrected.status_code == 200
    corrected_item = next(
        item for item in corrected.json()["evidence"] if item["id"] == evidence["id"]
    )
    assert (
        corrected_item["claim"] == "Python"
        and corrected_item["source_excerpt"] == evidence["source_excerpt"]
    )
    assert corrected_item["user_correction"] == "Python basics; still learning"
    stale = await account_client.delete(f"{path}?expected_revision=1")
    assert stale.status_code == 409
    added = await account_client.post(
        f"{path}/evidence",
        json={
            "category": "tool",
            "claim": "Supplied niche tool",
            "expected_revision": 2,
        },
    )
    assert added.status_code == 201 and added.json()["revision"] == 3
    supplied = next(item for item in added.json()["evidence"] if item["origin"] == "user")
    assert supplied["source_excerpt"] is None and supplied["source_page"] is None
    assert supplied["review_status"] == "confirmed"
    erased = await account_client.delete(f"{path}/evidence/{supplied['id']}?expected_revision=3")
    assert erased.status_code == 200 and erased.json()["revision"] == 4
    async with async_sessionmaker(database)() as session:
        version = await session.scalar(select(ResumeVersion))
        assert version and version.storage_key is None and version.upload_deleted_at is not None
        assert version.extraction_version == "lexical-sections-v1"
        assert await session.scalar(select(func.count()).select_from(Skill)) == 0
    assert (await account_client.delete(f"{path}?expected_revision=4")).status_code == 204
    assert (await account_client.get(path)).status_code == 404
    assert (await account_client.get(BASE)).json() == {"items": []}
    async with async_sessionmaker(database)() as session:
        for model in (Resume, ResumeVersion, ResumeSkillEvidence):
            assert await session.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.parametrize("mime", ["text/plain", "application/octet-stream", "image/png", ""])
async def test_invalid_mime(account_client: httpx.AsyncClient, mime: str) -> None:
    await login(account_client)
    result = await upload(account_client, mime=mime)
    assert result.status_code == 415 and result.json()["code"] == "pdf_mime"
    assert (await account_client.get(BASE)).json()["items"] == []


@pytest.mark.parametrize(
    "filename",
    [
        "resume.txt",
        "resume.pdf.exe",
        "../resume.pdf",
        "..\\resume.pdf",
        "C:\\private\\resume.pdf",
        ".pdf",
        "secret\x00.pdf",
        "x\u202e.pdf",
    ],
)
async def test_invalid_extension_or_path(account_client: httpx.AsyncClient, filename: str) -> None:
    await login(account_client)
    result = await upload(account_client, filename=filename)
    assert result.status_code == 422 and result.json()["code"] == "pdf_filename"


async def test_oversized_upload_declared_and_chunked(account_client: httpx.AsyncClient) -> None:
    await login(account_client)
    result = await upload(account_client, b"%PDF-1.7\n" + b"x" * MAX_BYTES)
    assert result.status_code == 413

    async def chunks() -> AsyncIterator[bytes]:
        yield b"%PDF-1.7\n"
        for _ in range(6):
            yield b"x" * (1024 * 1024)

    chunked = await account_client.post(
        BASE,
        content=chunks(),
        headers={
            "Content-Type": "application/pdf",
            "X-Resume-Filename": "resume.pdf",
        },
    )
    assert chunked.status_code == 413 and chunked.json()["code"] == "pdf_size"
    assert (await account_client.get(BASE)).json()["items"] == []


@pytest.mark.parametrize(
    "data,code",
    [
        (b"not a PDF", "pdf_corrupt"),
        (b"%PDF-1.7\ncorrupt private sentinel", "pdf_corrupt"),
        (pdf_bytes(encrypted=True), "pdf_encrypted"),
        (pdf_bytes(pages=21), "pdf_page_limit"),
    ],
)
async def test_corrupt_encrypted_and_page_limit(
    account_client: httpx.AsyncClient, data: bytes, code: str, caplog: pytest.LogCaptureFixture
) -> None:
    await login(account_client)
    result = await upload(account_client, data)
    assert result.status_code == 422 and result.json()["code"] == code, result.text
    assert "private sentinel" not in result.text and "private sentinel" not in caplog.text
    assert result.headers["cache-control"] == "no-store"
    assert (await account_client.get(BASE)).json()["items"] == []


async def test_blank_pdf_never_implies_lack_of_knowledge(account_client: httpx.AsyncClient) -> None:
    await login(account_client)
    result = await upload(account_client, pdf_bytes(text=""))
    assert result.status_code == 201
    assert result.json()["evidence"] == [] and result.json()["extraction_note"] == "no_text"
    assert "skill" not in result.json() and "score" not in result.json()


async def test_owner_boundaries_for_every_operation(account_client: httpx.AsyncClient) -> None:
    assert (await upload(account_client)).status_code == 401
    await login(account_client, "alice")
    alice = (await upload(account_client)).json()
    await login(account_client, "bob")
    bob = (await upload(account_client)).json()
    assert [item["id"] for item in (await account_client.get(BASE)).json()["items"]] == [bob["id"]]
    foreign = f"{BASE}/{alice['id']}"
    body = {"category": "tool", "claim": "Forgery", "expected_revision": 1}
    for method, url, payload in [
        ("GET", foreign, None),
        ("DELETE", f"{foreign}?expected_revision=1", None),
        ("POST", f"{foreign}/evidence", body),
        ("PUT", f"{foreign}/evidence/{alice['evidence'][0]['id']}", body),
        ("DELETE", f"{foreign}/evidence/{alice['evidence'][0]['id']}?expected_revision=1", None),
        ("PUT", f"{BASE}/{bob['id']}/evidence/{alice['evidence'][0]['id']}", body),
    ]:
        assert (await account_client.request(method, url, json=payload)).status_code == 404
    forged = await account_client.post(
        f"{BASE}/{bob['id']}/evidence",
        json={
            **body,
            "owner_id": str(uuid4()),
            "source_excerpt": "Invented source",
        },
    )
    assert forged.status_code == 422
    await login(account_client, "alice")
    assert (await account_client.get(foreign)).json() == alice


async def test_resume_quota_and_evidence_validation(account_client: httpx.AsyncClient) -> None:
    await login(account_client)
    for _ in range(5):
        result = await upload(account_client)
        assert result.status_code == 201
    assert (await upload(account_client)).json()["code"] == "resume_limit"
    path = f"{BASE}/{result.json()['id']}/evidence"
    for body in [
        {"category": "tool", "claim": "   ", "expected_revision": 1},
        {"category": "tool", "claim": "x" * 2001, "expected_revision": 1},
        {"category": "invented", "claim": "x", "expected_revision": 1},
        {"category": "tool", "claim": "x", "expected_revision": True},
    ]:
        assert (await account_client.post(path, json=body)).status_code == 422


def test_deterministic_boundaries_source_offsets_and_negative_mentions() -> None:
    page = "Not familiar with Python. Interested in learning React.\nJavaScript, Reacted, GitHub"
    evidence, _ = extract_evidence([page])
    assert {item.claim for item in evidence} == {"Python", "React", "JavaScript", "GitHub"}
    assert "Java" not in {item.claim for item in evidence}
    for item in evidence:
        assert page[item.source_start : item.source_end] == item.source_excerpt
    assert "Not familiar" in evidence[0].source_excerpt
    assert safe_filename("My%20Resume.PDF") == "My Resume.PDF"


def test_worker_rejects_compressed_content_bomb() -> None:
    data = pdf_bytes(text="x" * (3 * 1024 * 1024), compressed=True)
    assert len(data) < MAX_BYTES
    with pytest.raises(HTTPException) as error:
        run_worker(data)
    assert error.value.detail in {"pdf_complex", "pdf_corrupt"}


async def test_parser_concurrency_gate() -> None:
    parser = PdfParser()
    async with parser.slots, parser.slots:
        with pytest.raises(HTTPException) as error:
            await parser.parse(pdf_bytes())
    assert error.value.status_code == 503 and error.value.detail == "pdf_busy"


def test_parser_timeout_kills_worker_and_returns_safe_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TimedOutWorker:
        killed = False
        returncode = 0

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "TimedOutWorker":
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            pass

        def communicate(
            self, input: bytes | None = None, timeout: int | None = None
        ) -> tuple[bytes, None]:
            if timeout is not None:
                raise subprocess.TimeoutExpired("private sentinel", timeout)
            return b"", None

        def kill(self) -> None:
            TimedOutWorker.killed = True

    monkeypatch.setattr(subprocess, "Popen", TimedOutWorker)
    with pytest.raises(HTTPException) as error:
        run_worker(pdf_bytes())
    assert TimedOutWorker.killed and error.value.detail == "pdf_complex"
    assert "private sentinel" not in str(error.value)


def test_excerpt_contains_late_mentions_and_extraction_is_bounded() -> None:
    page = "x " * 600 + "Python"
    evidence, _ = extract_evidence([page])
    assert evidence[0].claim == "Python" and "Python" in evidence[0].source_excerpt
    assert page[evidence[0].source_start : evidence[0].source_end] == evidence[0].source_excerpt
    evidence, note = extract_evidence(
        ["Projects\n" + "\n".join(f"Project {i}" for i in range(150))]
    )
    assert len(evidence) == 100 and note == "evidence_limit"
    evidence, _ = extract_evidence(["Bachelor of Science\nProject: supplied library API"])
    assert {item.category for item in evidence} == {"education", "project"}


async def test_rejection_concurrent_edit_and_history_preserving_deletion(
    account_client: httpx.AsyncClient,
    database: AsyncEngine,
) -> None:
    await login(account_client)
    resume = (await upload(account_client)).json()
    path = f"{BASE}/{resume['id']}"
    first = resume["evidence"][0]
    body = {
        "category": first["category"],
        "claim": first["claim"],
        "review_status": "rejected",
        "expected_revision": 1,
    }
    edits = await asyncio.gather(
        account_client.put(f"{path}/evidence/{first['id']}", json=body),
        account_client.put(f"{path}/evidence/{first['id']}", json=body),
    )
    assert sorted(result.status_code for result in edits) == [200, 409]
    detail = (await account_client.get(path)).json()
    assert detail["revision"] == 2
    async with async_sessionmaker(database)() as session:
        version = await session.scalar(select(ResumeVersion))
        assert version is not None
        session.add(
            Assessment(
                owner_id=version.owner_id,
                resume_version_id=version.id,
                title="Existing history",
                status=AssessmentStatus.DRAFT,
                context_version="test",
                policy_version="test",
            )
        )
        await session.commit()
    result = await account_client.delete(f"{path}?expected_revision=2")
    assert result.status_code == 409 and result.json()["code"] == "resume_in_use"
    for entry in detail["evidence"]:
        result = await account_client.delete(
            f"{path}/evidence/{entry['id']}?expected_revision={detail['revision']}"
        )
        assert result.status_code == 200
        detail = result.json()
    assert detail["evidence"] == []
    async with async_sessionmaker(database)() as session:
        assert await session.scalar(select(func.count()).select_from(Assessment)) == 1
