from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def pdf_bytes(
    text: str = "Python FastAPI PostgreSQL Docker",
    pages: int = 1,
    encrypted: bool = False,
    compressed: bool = False,
) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=595, height=842)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            }
        )
        stream = DecodedStreamObject()
        lines = [
            line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            for line in text.splitlines()
        ]
        stream.set_data(
            (
                "BT /F1 12 Tf 50 780 Td 16 TL "
                + " ".join(f"({line}) Tj T*" for line in lines)
                + " ET"
            ).encode("ascii")
        )
        page[NameObject("/Contents")] = stream.flate_encode() if compressed else stream
    if encrypted:
        writer.encrypt("test-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
