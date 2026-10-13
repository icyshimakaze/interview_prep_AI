"""Private stdin/stdout protocol. Never write raw text, filenames or exceptions to logs."""

import json
import logging
import sys
import unicodedata
import warnings
from dataclasses import asdict
from io import BytesIO

from interview_prep.modules.resumes.extraction import extract_evidence
from interview_prep.modules.resumes.worker_limits import restrict_memory

MAX_BYTES = 5 * 1024 * 1024
MAX_TEXT = 100_000
MAX_STREAM = 2 * 1024 * 1024


def parse_pdf(data: bytes) -> dict[str, object]:
    from pypdf import PdfReader, filters

    filters.ZLIB_MAX_OUTPUT_LENGTH = MAX_STREAM
    filters.LZW_MAX_OUTPUT_LENGTH = MAX_STREAM
    filters.RUN_LENGTH_MAX_OUTPUT_LENGTH = MAX_STREAM
    filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH = MAX_STREAM
    filters.MAX_DECLARED_STREAM_LENGTH = MAX_STREAM
    reader = PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted:
        return {"error": "pdf_encrypted"}
    count = len(reader.pages)
    if not 1 <= count <= 20:
        return {"error": "pdf_page_limit"}
    pages: list[str] = []
    total = 0
    for page in reader.pages:
        contents = page.get_contents()
        if contents is not None and len(contents.get_data()) > MAX_STREAM:
            return {"error": "pdf_complex"}
        text = page.extract_text() or ""
        total += len(text)
        if total > MAX_TEXT:
            return {"error": "pdf_complex"}
        text = "".join(
            char
            for char in text
            if char in "\n\t" or not unicodedata.category(char).startswith("C")
        )
        pages.append(text)
    evidence, note = extract_evidence(pages)
    return {
        "page_count": count,
        "extraction_note": note,
        "evidence": [asdict(item) for item in evidence],
    }


def main() -> None:
    logging.disable(logging.CRITICAL)
    warnings.simplefilter("ignore")
    try:
        restrict_memory()
    except Exception:
        sys.stdout.write('{"error":"pdf_worker_unavailable"}')
        return
    try:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        if not data or len(data) > MAX_BYTES:
            result: dict[str, object] = {"error": "pdf_size"}
        else:
            result = parse_pdf(data)
    except MemoryError:
        result = {"error": "pdf_complex"}
    except Exception:
        result = {"error": "pdf_corrupt"}
    # This private pipe is consumed/validated by the parent; it is not a log sink.
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
