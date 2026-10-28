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
MAX_PARSE_TOKENS = 100_000


def parse_pdf(data: bytes) -> dict[str, object]:
    from pypdf import Configuration, apply_configuration
    from pypdf.errors import LimitReachedError

    # Use the supported context-local API; byte caps alone do not bound the
    # object graph created by many tiny operations/array entries (pypdf advisories).
    limits = Configuration(
        zlib_maximum_output_length=MAX_STREAM,
        lzw_maximum_output_length=MAX_STREAM,
        run_length_maximum_output_length=MAX_STREAM,
        array_based_stream_maximum_output_length=MAX_STREAM,
        maximum_declared_stream_length=MAX_STREAM,
        stream_parsing_work_maximum_count=MAX_PARSE_TOKENS,
        array_maximum_element_count=10_000,
        dictionary_maximum_element_count=10_000,
        jbig2dec_binary=None,
    )
    try:
        with apply_configuration(limits):
            return _read_pdf(data)
    except LimitReachedError:
        return {"error": "pdf_complex"}


def _read_pdf(data: bytes) -> dict[str, object]:
    from pypdf import PdfReader

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
        if contents is not None:
            if len(contents.get_data()) > MAX_STREAM:
                return {"error": "pdf_complex"}
            # Parsing is lazy, and extract_text skips streams without font
            # resources. Enforce the configured work budget on those pages too.
            if len(contents.operations) > MAX_PARSE_TOKENS:
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
