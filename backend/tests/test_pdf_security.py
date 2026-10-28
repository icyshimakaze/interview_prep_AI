"""Small synthetic regressions for patched PDF resource bounds; no hostile downloads."""

from io import BytesIO

import pytest
from pdf_helpers import pdf_bytes
from pypdf import PdfReader, PdfWriter, get_configuration
from pypdf.generic import DecodedStreamObject, NameObject

from interview_prep.modules.resumes.upload import run_worker
from interview_prep.modules.resumes.worker import MAX_PARSE_TOKENS, parse_pdf


def excessive_operations() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    stream = DecodedStreamObject()
    stream.set_data(b"q Q " * (MAX_PARSE_TOKENS // 2 + 1))
    page[NameObject("/Contents")] = stream
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_content_operations_are_bounded_and_configuration_is_restored() -> None:
    before = get_configuration()
    assert parse_pdf(excessive_operations()) == {"error": "pdf_complex"}
    assert get_configuration() == before
    valid = parse_pdf(pdf_bytes())
    assert valid["page_count"] == 1 and valid["evidence"]
    assert get_configuration() == before


def test_real_worker_rejects_excessive_operations_with_safe_error() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        run_worker(excessive_operations())
    assert error.value.detail == "pdf_complex"


def test_repeated_missing_objects_do_not_rescan_the_stream() -> None:
    # GHSA-6c7f-9265-g8fw: test the patched behavior, not a version-string assertion.
    # The app uses strict mode; exercise the dependency's recovery cache separately.
    class CountingStream(BytesIO):
        scans = 0

        def getbuffer(self) -> memoryview:
            self.scans += 1
            return super().getbuffer()

    stream = CountingStream(pdf_bytes())
    reader = PdfReader(stream, strict=False)
    assert reader.get_object(999999) is None
    first = stream.scans
    assert first > 0
    for _ in range(10):
        assert reader.get_object(999999) is None
    assert stream.scans == first
