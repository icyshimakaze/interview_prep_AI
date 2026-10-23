"""Stream validation and a bounded subprocess without filesystem uploads."""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from typing import Literal
from urllib.parse import unquote_to_bytes

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from interview_prep.modules.context.models import EvidenceCategory

MAX_BYTES = 5 * 1024 * 1024
PARSE_SECONDS = 15
READ_SECONDS = 15
MAX_RESULT = 1_500_000


class ExtractedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    category: str
    claim: str = Field(min_length=1, max_length=2000)
    source_excerpt: str = Field(min_length=1, max_length=2000)
    source_page: int = Field(ge=1, le=20)
    source_start: int = Field(ge=0)
    source_end: int = Field(ge=1)


class ParsedPdf(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    page_count: int = Field(ge=1, le=20)
    extraction_note: Literal["no_text", "evidence_limit"] | None
    evidence: list[ExtractedEvidence] = Field(max_length=100)


def safe_filename(encoded: str) -> str:
    try:
        name = unicodedata.normalize("NFKC", unquote_to_bytes(encoded).decode("utf-8"))
    except (UnicodeError, ValueError):
        raise HTTPException(422, detail="pdf_filename") from None
    if (
        not 5 <= len(name) <= 200
        or not name.lower().endswith(".pdf")
        or name.startswith(".")
        or any(char in name for char in "/\\:")
        or any(unicodedata.category(char).startswith("C") for char in name)
    ):
        raise HTTPException(422, detail="pdf_filename")
    return name


async def read_upload(request: Request) -> bytes:
    if request.headers.get("content-type", "").strip().lower() != "application/pdf":
        raise HTTPException(415, detail="pdf_mime")
    declared = request.headers.get("content-length")
    if declared is not None:
        if not declared.isascii() or not declared.isdigit():
            raise HTTPException(422, detail="pdf_size")
        if len(declared) > 12 or int(declared) > MAX_BYTES:
            raise HTTPException(413, detail="pdf_size")
    buffer = bytearray()
    try:
        async with asyncio.timeout(READ_SECONDS):
            async for chunk in request.stream():
                if len(buffer) + len(chunk) > MAX_BYTES:
                    raise HTTPException(413, detail="pdf_size")
                buffer.extend(chunk)
    except TimeoutError:
        raise HTTPException(408, detail="pdf_upload_timeout") from None
    if not re.match(rb"%PDF-[12]\.[0-9](?:\r|\n|\s)", buffer[:12]):
        raise HTTPException(422, detail="pdf_corrupt")
    return bytes(buffer)


def run_worker(data: bytes) -> ParsedPdf:
    # Do not inherit database URLs, identity secrets, proxies, or credential envs.
    environment = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR") if key in os.environ}
    try:
        with (
            tempfile.TemporaryDirectory(prefix="resume-parse-") as directory,
            subprocess.Popen(
                [sys.executable, "-I", "-m", "interview_prep.modules.resumes.worker"],
                cwd=directory,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=environment,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            ) as process,
        ):
            try:
                output, _ = process.communicate(input=data, timeout=PARSE_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise HTTPException(422, detail="pdf_complex") from None
            if process.returncode != 0 or len(output) > MAX_RESULT:
                raise HTTPException(422, detail="pdf_complex")
    except OSError:
        raise HTTPException(503, detail="pdf_worker_unavailable") from None
    try:
        decoded: object = json.loads(output)
        if isinstance(decoded, dict) and "error" in decoded:
            code = decoded["error"]
            allowed = {
                "pdf_corrupt",
                "pdf_encrypted",
                "pdf_page_limit",
                "pdf_complex",
                "pdf_size",
                "pdf_worker_unavailable",
            }
            if isinstance(code, str) and code in allowed:
                raise HTTPException(503 if code == "pdf_worker_unavailable" else 422, detail=code)
            raise ValueError("Invalid worker response")
        parsed = ParsedPdf.model_validate(decoded)
        for item in parsed.evidence:
            EvidenceCategory(item.category)
            if (
                item.source_page > parsed.page_count
                or item.source_end <= item.source_start
                or item.source_end - item.source_start != len(item.source_excerpt)
            ):
                raise ValueError("Invalid evidence provenance")
        return parsed
    except (ValueError, TypeError):
        raise HTTPException(422, detail="pdf_corrupt") from None


class PdfParser:
    def __init__(self, slots: asyncio.Semaphore | None = None) -> None:
        self.slots = slots if slots is not None else asyncio.Semaphore(2)

    async def parse(self, data: bytes) -> ParsedPdf:
        if self.slots.locked():
            raise HTTPException(503, detail="pdf_busy")
        async with self.slots:
            return await self._run(data)

    async def upload(self, request: Request) -> tuple[bytes, ParsedPdf]:
        if self.slots.locked():
            raise HTTPException(503, detail="pdf_busy")
        async with self.slots:
            data = await read_upload(request)
            return data, await self._run(data)

    async def _run(self, data: bytes) -> ParsedPdf:
        task = asyncio.create_task(asyncio.to_thread(run_worker, data))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # Keep the concurrency slot until the worker exits or is killed.
            await task
            raise
