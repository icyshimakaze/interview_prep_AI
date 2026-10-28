import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import HTTPException, Request

from interview_prep.modules.projects.archive import MAX_ARCHIVE
from interview_prep.modules.projects.schemas import StaticAnalysis

ERRORS: dict[str, tuple[int, str]] = {
    "github_url": (
        422,
        "Use an HTTPS public github.com/owner/repository URL without a branch, query or "
        "credentials.",
    ),
    "github_unavailable": (
        503,
        "GitHub could not provide this public repository. Check its URL, rate limits and "
        "availability, or upload a ZIP.",
    ),
    "archive_size": (413, "Provide a ZIP archive no larger than 10 MiB."),
    "archive_corrupt": (422, "The source archive is invalid or unsupported."),
    "archive_path": (422, "The archive contains unsafe or ambiguous paths."),
    "archive_duplicate": (422, "The archive contains duplicate or conflicting paths."),
    "archive_link": (422, "Archives containing symlinks or special files are unsupported."),
    "archive_format": (422, "Use an unencrypted ZIP with stored or deflated entries."),
    "archive_limits": (422, "The archive exceeds safe file, size, expansion or processing limits."),
    "archive_no_source": (422, "No supported source or configuration files were found."),
    "project_worker_unavailable": (503, "Source analysis is temporarily unavailable."),
    "project_busy": (503, "Source analysis is busy. Try again shortly."),
    "project_timeout": (408, "The import timed out. Try a smaller ZIP."),
    "project_mime": (415, "Upload a ZIP using application/zip."),
    "project_limit": (
        409,
        "You can retain up to five project snapshots. Delete one before importing another.",
    ),
    "defense_state": (
        409,
        "This practice session changed or the action is unavailable. Reload your saved answers.",
    ),
    "defense_limit": (409, "You can retain up to twenty defense sessions per snapshot."),
}


def github_coordinates(url: str) -> tuple[str, str]:
    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,100})/?", url
    )
    if not match or match[2] in {".", "..", ".git"}:
        raise HTTPException(422, detail="github_url")
    repository = match[2].removesuffix(".git").lower()
    if repository in {".", ".."}:
        raise HTTPException(422, detail="github_url")
    return match[1].lower(), repository


async def bounded_get(http: httpx.AsyncClient, url: str, maximum: int) -> bytes:
    async with http.stream(
        "GET",
        url,
        headers={"Accept-Encoding": "identity", "User-Agent": "InterviewPrep-StaticAnalysis/1"},
        follow_redirects=False,
        timeout=15,
    ) as response:
        if (
            response.status_code != 200
            or response.headers.get("content-encoding", "identity") != "identity"
        ):
            raise HTTPException(503, detail="github_unavailable")
        result = bytearray()
        async for chunk in response.aiter_bytes(65536):
            if len(result) + len(chunk) > maximum:
                raise HTTPException(413, detail="archive_size")
            result.extend(chunk)
        return bytes(result)


async def github_archive(http: httpx.AsyncClient, url: str) -> tuple[bytes, str, str, str]:
    owner, repository = github_coordinates(url)
    try:
        async with asyncio.timeout(40):
            metadata = json.loads(
                await bounded_get(http, f"https://api.github.com/repos/{owner}/{repository}", 65536)
            )
            if not isinstance(metadata, dict) or metadata.get("private") is not False:
                raise ValueError("Not a public repository")
            commits = json.loads(
                await bounded_get(
                    http,
                    f"https://api.github.com/repos/{owner}/{repository}/commits?per_page=1",
                    65536,
                )
            )
            sha = commits[0]["sha"]
            if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
                raise ValueError("Invalid commit")
            data = await bounded_get(
                http, f"https://codeload.github.com/{owner}/{repository}/zip/{sha}", MAX_ARCHIVE
            )
            return data, owner, repository, sha
    except (httpx.HTTPError, TimeoutError, ValueError, TypeError, KeyError, IndexError):
        raise HTTPException(503, detail="github_unavailable") from None


async def read_zip(request: Request) -> bytes:
    if request.headers.get("content-type", "").lower() != "application/zip":
        raise HTTPException(415, detail="project_mime")
    declared = request.headers.get("content-length")
    if declared and (
        not declared.isascii()
        or not declared.isdigit()
        or len(declared) > 10
        or int(declared) > MAX_ARCHIVE
    ):
        raise HTTPException(413, detail="archive_size")
    result = bytearray()
    try:
        async with asyncio.timeout(20):
            async for chunk in request.stream():
                if len(result) + len(chunk) > MAX_ARCHIVE:
                    raise HTTPException(413, detail="archive_size")
                result.extend(chunk)
    except TimeoutError:
        raise HTTPException(408, detail="project_timeout") from None
    return bytes(result)


def run_worker(data: bytes) -> StaticAnalysis:
    environment = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR") if key in os.environ}
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW
    try:
        with (
            tempfile.TemporaryDirectory(prefix="project-static-") as directory,
            subprocess.Popen(
                [sys.executable, "-I", "-m", "interview_prep.modules.projects.worker"],
                cwd=directory,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            ) as process,
        ):
            try:
                output, _ = process.communicate(input=data, timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise HTTPException(422, detail="archive_limits") from None
            if process.returncode != 0 or len(output) > 1_500_000:
                raise HTTPException(422, detail="archive_limits")
    except OSError:
        raise HTTPException(503, detail="project_worker_unavailable") from None
    try:
        decoded = json.loads(output)
        if isinstance(decoded, dict) and isinstance(decoded.get("error"), str):
            code = decoded["error"]
            if code in ERRORS:
                raise HTTPException(ERRORS[code][0], detail=code)
        parsed = StaticAnalysis.model_validate(decoded)
        files = {f.path: f for f in parsed.files}
        if (
            len(files) != len(parsed.files)
            or not files
            or any(f.path not in files or f.line > files[f.path].line_count for f in parsed.facts)
        ):
            raise ValueError("Invalid citations")
        return parsed
    except (ValueError, TypeError):
        raise HTTPException(422, detail="archive_corrupt") from None


class ProjectImporter:
    def __init__(self, http: httpx.AsyncClient, slots: asyncio.Semaphore | None = None) -> None:
        self.http = http
        self.slots = slots if slots is not None else asyncio.Semaphore(2)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        if self.slots.locked():
            raise HTTPException(503, detail="project_busy")
        async with self.slots:
            yield

    async def parse(self, data: bytes) -> StaticAnalysis:
        task = asyncio.create_task(asyncio.to_thread(run_worker, data))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            await task  # Keep the slot occupied until this bounded process exits.
            raise
