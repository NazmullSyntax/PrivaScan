"""
Tests for modules/document_processor.py.

Run:  pytest tests/test_document_processing.py -v
"""
import hashlib
from pathlib import Path

import pytest

from modules import document_processor as dp


@pytest.fixture
def synthetic_files(tmp_path):
    """Create tiny fresh files for each test — do not depend on committed samples."""
    txt = tmp_path / "note.txt"
    txt.write_text("Alice's email is alice.testerson@example.com", encoding="utf-8")

    docx_path = tmp_path / "note.docx"
    from docx import Document
    doc = Document()
    doc.add_paragraph("Bob's phone is +1-555-010-2030")
    doc.save(str(docx_path))

    pdf_path = tmp_path / "note.pdf"
    import fitz
    pdf = fitz.open()
    p = pdf.new_page()
    p.insert_text((72, 72), "Carol lives on 742 Evergreen Avenue.")
    pdf.save(str(pdf_path))
    pdf.close()

    return {"txt": txt, "docx": docx_path, "pdf": pdf_path}


def test_txt_extraction(synthetic_files):
    doc = dp.extract_document(synthetic_files["txt"])
    assert doc.file_type == "txt"
    assert "alice.testerson@example.com" in doc.text
    assert doc.page_count == 1
    assert doc.file_hash  # non-empty
    assert len(doc.file_hash) == 64  # sha256 hex length


def test_docx_extraction(synthetic_files):
    doc = dp.extract_document(synthetic_files["docx"])
    assert doc.file_type == "docx"
    assert "+1-555-010-2030" in doc.text


def test_pdf_extraction(synthetic_files):
    doc = dp.extract_document(synthetic_files["pdf"])
    assert doc.file_type == "pdf"
    assert "Evergreen Avenue" in doc.text
    assert doc.page_count == 1


def test_hash_is_deterministic(synthetic_files):
    a = dp.extract_document(synthetic_files["txt"])
    b = dp.extract_document(synthetic_files["txt"])
    assert a.file_hash == b.file_hash
    assert a.file_hash == hashlib.sha256(synthetic_files["txt"].read_bytes()).hexdigest()


def test_unsupported_extension(tmp_path):
    bad = tmp_path / "report.xlsx"
    bad.write_bytes(b"fake")
    with pytest.raises(dp.UnsupportedFileError):
        dp.extract_document(bad)


def test_file_too_large(tmp_path, monkeypatch):
    monkeypatch.setattr("config.MAX_FILE_SIZE_MB", 0.000001)  # 1 byte
    big = tmp_path / "big.txt"
    big.write_text("hello world", encoding="utf-8")
    with pytest.raises(dp.FileTooLargeError):
        dp.extract_document(big)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        dp.extract_document(tmp_path / "does_not_exist.txt")


def test_store_uploaded_file_uses_hash_name(synthetic_files):
    doc = dp.extract_document(synthetic_files["txt"])
    stored = dp.store_uploaded_file(synthetic_files["txt"], doc.file_hash)
    assert stored.name == f"{doc.file_hash}.txt"
    assert stored.exists()
    assert stored.read_bytes() == synthetic_files["txt"].read_bytes()