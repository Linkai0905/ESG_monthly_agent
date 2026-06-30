from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class PDFParserTool:
    name = "pdf_parser"

    def invoke(self, data: bytes) -> str:
        reader = PdfReader(BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
