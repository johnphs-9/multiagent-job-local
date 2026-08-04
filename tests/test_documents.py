from io import BytesIO

import pytest
from docx import Document

from interview_local.documents import DocumentError, extract_document


def test_extract_text_document() -> None:
    assert extract_document("jd.txt", b"Data scientist\nPython and SQL") == (
        "Data scientist\nPython and SQL"
    )


def test_extract_docx_document() -> None:
    buffer = BytesIO()
    document = Document()
    document.add_heading("Candidate", 1)
    document.add_paragraph("Built reliable data pipelines.")
    document.save(buffer)

    text = extract_document("candidate.docx", buffer.getvalue())

    assert "Candidate" in text
    assert "data pipelines" in text


def test_reject_unsupported_document() -> None:
    with pytest.raises(DocumentError, match="Unsupported"):
        extract_document("resume.pages", b"content")

