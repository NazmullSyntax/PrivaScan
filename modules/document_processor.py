"""
Document text extraction for PDF, DOCX, and TXT files.

Design goals:
- One function per format, all returning the SAME dataclass type.
- The rest of the app never needs to know whether text came from PDF/DOCX/TXT.
- Fail loudly with clear error types — silent failures are the enemy of QA.
"""
from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF — imported as 'fitz' historically
from docx import Document

import config


# ---- Custom exceptions -----------------------------------------------
# Specific exception types let the UI show meaningful messages
# and let tests assert on the exact failure mode.
class UnsupportedFileError(ValueError):
    """File extension is not one of .pdf, .docx, .txt."""


class FileTooLargeError(ValueError):
    """File exceeds config.MAX_FILE_SIZE_MB."""


class TextExtractionError(RuntimeError):
    """We accepted the file but couldn't extract text from it."""


# ---- Data class ------------------------------------------------------
@dataclass
class DocumentText:
    """
    The universal 'extracted document' object.

    Whatever the source format, downstream code works with THIS type.
    """
    filename: str            # original filename (safe to show to user)
    file_type: str           # 'pdf', 'docx', or 'txt'
    text: str                # the extracted plain text
    page_count: int = 1      # pages for PDFs; paragraphs for DOCX; 1 for TXT
    size_bytes: int = 0
    file_hash: str = ""      # sha256 of the file contents
    warnings: list[str] = field(default_factory=list)  # non-fatal issues


# ---- Helpers ---------------------------------------------------------
def _validate_file(path: Path) -> str:
    """Return the file type ('pdf'|'docx'|'txt') or raise."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise UnsupportedFileError(f"Not a file: {path}")

    ext = path.suffix.lower()
    if ext not in config.SUPPORTED_EXTENSIONS:
        raise UnsupportedFileError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {sorted(config.SUPPORTED_EXTENSIONS)}"
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > config.MAX_FILE_SIZE_MB:
        raise FileTooLargeError(
            f"File is {size_mb:.1f} MB; limit is {config.MAX_FILE_SIZE_MB} MB."
        )
    return ext.lstrip(".")


def _sha256_of_file(path: Path) -> str:
    """
    Return sha256 hex digest of the whole file.

    Read in 8 KB chunks so huge files don't load into RAM all at once.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- Format-specific extractors --------------------------------------
def _extract_pdf(path: Path) -> tuple[str, int, list[str]]:
    """Return (text, page_count, warnings) for a PDF."""
    warnings: list[str] = []
    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise TextExtractionError(f"Could not open PDF: {exc}") from exc

    pages: list[str] = []
    try:
        for i, page in enumerate(doc):
            page_text = page.get_text("text")
            if not page_text.strip():
                warnings.append(
                    f"Page {i + 1} has no selectable text "
                    f"(may be a scanned image — OCR not supported)."
                )
            pages.append(page_text)
        page_count = doc.page_count
    finally:
        doc.close()

    return "\n\n".join(pages).strip(), page_count, warnings


def _extract_docx(path: Path) -> tuple[str, int, list[str]]:
    """Return (text, paragraph_count, warnings) for a DOCX."""
    try:
        doc = Document(str(path))
    except Exception as exc:
        raise TextExtractionError(f"Could not open DOCX: {exc}") from exc

    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)

    # Tables are very common in business docs — extract them too.
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    text = "\n".join(parts).strip()
    warnings: list[str] = []
    if not text:
        warnings.append("DOCX contains no readable text.")

    return text, len(doc.paragraphs), warnings


def _extract_txt(path: Path) -> tuple[str, int, list[str]]:
    """
    Return (text, 1, warnings) for a TXT.

    We try UTF-8 first, then fall back to latin-1 so users aren't
    blocked by an odd byte in an otherwise fine file.
    """
    warnings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        warnings.append(
            "File was not valid UTF-8. Fell back to latin-1 (some characters may look odd)."
        )
        text = path.read_text(encoding="latin-1", errors="replace")
    return text.strip(), 1, warnings


# ---- Main entry point ------------------------------------------------
_EXTRACTORS = {
    "pdf": _extract_pdf,
    "docx": _extract_docx,
    "txt": _extract_txt,
}


def extract_document(path: Path | str) -> DocumentText:
    """
    Extract text from a single file. This is the function everything else calls.

    Raises:
        UnsupportedFileError, FileTooLargeError, FileNotFoundError,
        TextExtractionError
    """
    path = Path(path)
    file_type = _validate_file(path)
    file_hash = _sha256_of_file(path)
    size_bytes = path.stat().st_size

    extractor = _EXTRACTORS[file_type]
    text, count, warnings = extractor(path)

    if not text:
        # Empty text after successful parse is still a valid extraction
        # (e.g., a blank DOCX), but we flag it so callers can decide.
        warnings.append("Extracted text is empty.")

    return DocumentText(
        filename=path.name,
        file_type=file_type,
        text=text,
        page_count=count,
        size_bytes=size_bytes,
        file_hash=file_hash,
        warnings=warnings,
    )


# ---- Safe storage ----------------------------------------------------
def store_uploaded_file(source_path: Path | str, file_hash: str) -> Path:
    """
    Copy an uploaded file into data/uploads/ under its hash name.

    Security note: we use ONLY the hash + original extension for the
    stored filename. No user-supplied name reaches the filesystem,
    so path-traversal attacks like "../../etc/passwd" are impossible.

    Returns the new stored path.
    """
    source_path = Path(source_path)
    extension = source_path.suffix.lower()
    safe_name = f"{file_hash}{extension}"
    dest = config.UPLOAD_DIR / safe_name

    if dest.exists():
        # Same file uploaded before — reuse, don't duplicate.
        return dest

    shutil.copy2(source_path, dest)
    return dest