"""
Tests for PDF generation.
Run: pytest tests/test_review_and_pdf.py -v
"""
from pathlib import Path
import pytest
import fitz
from modules import pii_redactor

def test_generate_pdf(tmp_path):
    # Setup
    test_text = "This is a safe document.\n\n[EMAIL]\n[PERSON]"
    output_path = tmp_path / "test_output.pdf"
    
    # Generate
    pii_redactor.generate_redacted_pdf(test_text, str(output_path))
    
    # Verify
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify contents using PyMuPDF
    pdf = fitz.open(str(output_path))
    extracted = pdf[0].get_text()
    pdf.close()
    
    assert "This is a safe document." in extracted
    assert "[EMAIL]" in extracted