"""Safe text extraction for uploaded job descriptions and candidate profiles."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARACTERS = 60_000
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


class DocumentError(ValueError):
    """Raised when an uploaded document cannot be safely converted to text."""


def _clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[\u0001-\u0008\u000b\u000c\u000e-\u001f]", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = text.strip()
    if not text:
        raise DocumentError("The document contains no extractable text.")
    if len(text) > MAX_TEXT_CHARACTERS:
        raise DocumentError(
            f"Extracted text exceeds {MAX_TEXT_CHARACTERS:,} characters. "
            "Shorten the document before uploading it."
        )
    return text


def extract_document(filename: str, content: bytes) -> str:
    """Extract text from TXT, Markdown, PDF, or DOCX bytes."""
    if not content:
        raise DocumentError("The uploaded document is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise DocumentError(f"Files must be no larger than {MAX_FILE_BYTES // 1024 // 1024} MB.")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise DocumentError(f"Unsupported file type `{suffix or 'unknown'}`. Use: {supported}.")

    try:
        if suffix in {".txt", ".md"}:
            text = content.decode("utf-8-sig", errors="replace")
        elif suffix == ".pdf":
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise DocumentError("Encrypted PDFs are not supported.")
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            document = Document(BytesIO(content))
            parts = [paragraph.text for paragraph in document.paragraphs]
            for table in document.tables:
                parts.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
            text = "\n".join(parts)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"Could not read `{filename}`: {exc}") from exc

    return _clean_text(text)

