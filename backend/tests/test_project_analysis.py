import asyncio
import stat
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import httpx
import pytest
from fastapi import HTTPException

from interview_prep.modules.projects.analyzer import analyze
from interview_prep.modules.projects.archive import MAX_ARCHIVE, UnsafeArchive, read_archive
from interview_prep.modules.projects.example import example_archive
from interview_prep.modules.projects.ingestion import (
    ProjectImporter,
    bounded_get,
    github_archive,
    github_coordinates,
    run_worker,
)
from interview_prep.modules.projects.questions import questions


def zipped(files: dict[str, str]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for path, content in files.items():
            entry = ZipInfo(path)
            entry.filename = path  # Preserve hostile bytes despite Windows ZipInfo normalization.
            archive.writestr(entry, content)
    return output.getvalue()


@pytest.mark.parametrize(
    "path",
    [
        "../outside.py",
        "/etc/passwd",
        "C:/x.py",
        "\\\\host\\x.py",
        "a\\b.py",
        "a/../x.py",
        "a//b.py",
        "a//",
        "a/./b.py",
        "NUL.py",
        "x.py:stream",
        "x. /a.py",
        "a/\x00b.py",
        "a/\u202eb.py",
        "\uff41.py",
    ],
)
def test_project_archive_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(UnsafeArchive):
        read_archive(zipped({path: "print('never executed')"}))


def test_project_archive_duplicate_prefix_links_and_bombs() -> None:
    for files in ({"a.py": "", "A.py": ""}, {"a": "", "a/main.py": ""}):
        with pytest.raises(UnsafeArchive, match="archive_duplicate"):
            read_archive(zipped(files))
    output = BytesIO()
    entry = ZipInfo("link.py")
    entry.create_system = 3
    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
    with ZipFile(output, "w") as archive:
        archive.writestr(entry, "/outside/private")
    with pytest.raises(UnsafeArchive, match="archive_link"):
        read_archive(output.getvalue())
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("bomb.py", "x" * 500000)
    with pytest.raises(UnsafeArchive, match="archive_limits"):
        read_archive(output.getvalue())
    with pytest.raises(UnsafeArchive, match="archive_size"):
        read_archive(b"x" * (MAX_ARCHIVE + 1))
    with pytest.raises(UnsafeArchive, match="archive_corrupt"):
        read_archive(b"not a zip")


def test_project_deterministic_fact_coverage_and_private_content_exclusion() -> None:
    archive = example_archive()
    result = analyze(archive)
    assert result == analyze(archive)
    assert questions(result) == questions(result)
    assert len(questions(result)) == 10
    assert {"Python", "TypeScript"} <= result.summary.languages.keys()
    assert {f.kind for f in result.facts} >= {
        "manifest",
        "dependency",
        "framework",
        "component",
        "database",
        "route",
        "schema",
        "tests",
        "ci",
        "docker",
        "documentation",
        "authentication",
    }
    assert all(f.inferred for f in result.facts if f.kind in {"component", "database", "route"})
    assert all(not f.inferred for f in result.facts if f.kind in {"manifest", "dependency"})
    files = {f.path: f for f in result.files}
    assert all(f.path in files and f.line <= files[f.path].line_count for f in result.facts)
    private = analyze(
        zipped(
            {
                "src/app.py": "raise RuntimeError('UNTRUSTED_BODY')",
                ".env": "PASSWORD=NEVER",
                "private.key": "NEVER",
                "node_modules/evil.py": "NEVER",
                "package.json": '{"scripts":{"postinstall":"UNTRUSTED_BODY"},'
                '"dependencies":{"react":"https://user:password@example.test"}}',
            }
        )
    )
    assert "UNTRUSTED_BODY" not in private.model_dump_json()
    assert "password" not in private.model_dump_json()
    assert {f.path for f in private.files} == {"src/app.py", "package.json"}
    assert private.summary.skipped_files == 3


def test_project_worker_isolated_and_source_not_executed() -> None:
    result = run_worker(zipped({"app.py": "raise SystemExit('never execute')"}))
    assert result.files[0].path == "app.py"
    assert run_worker(example_archive()) == analyze(example_archive())
    with pytest.raises(HTTPException) as error:
        run_worker(zipped({"../private.py": ""}))
    assert error.value.detail == "archive_path"


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/a/b",
        "https://github.com.evil/a/b",
        "https://user:password@github.com/a/b",
        "https://localhost/a/b",
        "https://github.com/a/b/tree/main",
        "https://github.com/a/b?token=x",
        "https://github.com/a/..",
        "https://github.com/a/..git",
        "https://github.com/a/...git",
        "https://github.com/a/%2e%2e",
        "https://github.com/a/b#readme",
        "file:///etc/passwd",
    ],
)
def test_project_github_url_boundary(url: str) -> None:
    with pytest.raises(HTTPException):
        github_coordinates(url)


async def test_project_github_public_commit_fixed_hosts_no_redirects() -> None:
    seen: list[str] = []
    sha = "a" * 40

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        assert "authorization" not in request.headers
        if request.url.path == "/repos/owner/repo":
            return httpx.Response(200, json={"private": False})
        if request.url.host == "api.github.com":
            return httpx.Response(200, json=[{"sha": sha}])
        return httpx.Response(200, content=example_archive())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        data, owner, repo, commit = await github_archive(http, "https://github.com/Owner/Repo.git")
        assert (owner, repo, commit) == ("owner", "repo", sha)
        assert data == example_archive()
    assert seen == [
        "https://api.github.com/repos/owner/repo",
        "https://api.github.com/repos/owner/repo/commits?per_page=1",
        f"https://codeload.github.com/owner/repo/zip/{sha}",
    ]
    for response in [
        httpx.Response(302, headers={"Location": "http://127.0.0.1/private"}),
        httpx.Response(200, json={"private": True}),
        httpx.Response(429, text="UPSTREAM_SECRET"),
    ]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request, response=response: response)
        ) as http:
            with pytest.raises(HTTPException) as error:
                await github_archive(http, "https://github.com/a/b")
            assert error.value.detail == "github_unavailable"


async def test_project_network_bound_and_concurrency_limit() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 20))
    ) as http:
        with pytest.raises(HTTPException) as error:
            await bounded_get(http, "https://api.github.com/repos/a/b", 10)
        assert error.value.detail == "archive_size"
        importer = ProjectImporter(http)
        async with importer.slot(), importer.slot():
            with pytest.raises(HTTPException) as busy:
                async with importer.slot():
                    await asyncio.sleep(0)
            assert busy.value.detail == "project_busy"
