"""Exercise the content budget independently of text/font resource detection."""

from io import BytesIO

import pytest
from pypdf import PdfWriter, get_configuration
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from interview_prep.modules.resumes import worker


@pytest.mark.parametrize("resources", [False, True])
@pytest.mark.parametrize("operations, rejected", [(8, False), (10, True)])
def test_content_budget_boundary(
    monkeypatch: pytest.MonkeyPatch, resources: bool, operations: int, rejected: bool
) -> None:
    monkeypatch.setattr(worker, "MAX_PARSE_TOKENS", 8)
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    if resources:
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject()})
    stream = DecodedStreamObject()
    stream.set_data(b"q Q " * (operations // 2))
    page[NameObject("/Contents")] = stream
    buffer = BytesIO()
    writer.write(buffer)
    before = get_configuration()
    result = worker.parse_pdf(buffer.getvalue())
    assert get_configuration() == before
    if rejected:
        assert result == {"error": "pdf_complex"}
    else:
        assert result == {"page_count": 1, "extraction_note": "no_text", "evidence": []}
