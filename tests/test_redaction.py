"""
Tests for modules/pii_redactor.py.
Run: pytest tests/test_redaction.py -v
"""
from modules.pii_detector import PIIMatch
from modules import pii_redactor

def test_basic_redaction():
    text = "Email me at alice@test.com today."
    # Mock a PIIMatch for the email
    match = PIIMatch(
        text="alice@test.com", category="EMAIL", 
        start=12, end=26, confidence=0.99, source="regex"
    )
    safe_text = pii_redactor.redact_document(text, [match], strategy="redact")
    assert safe_text == "Email me at [EMAIL] today."

def test_masking_email():
    text = "Contact alice@test.com"
    match = PIIMatch(
        text="alice@test.com", category="EMAIL", 
        start=8, end=22, confidence=0.99, source="regex"
    )
    safe_text = pii_redactor.redact_document(text, [match], strategy="mask")
    assert safe_text == "Contact a***@t***.com"

def test_multiple_overlapping_redactions():
    # If we process right-to-left, the indices of the first match 
    # shouldn't break when we replace the second match.
    text = "Alice's email is alice@test.com"
    match1 = PIIMatch(text="Alice", category="PERSON", start=0, end=5, confidence=0.9, source="ner")
    match2 = PIIMatch(text="alice@test.com", category="EMAIL", start=17, end=31, confidence=0.95, source="regex")
    
    # If we process left-to-right without care, replacing "Alice" 
    # changes the index of the email.
    safe_text = pii_redactor.redact_document(text, [match1, match2], strategy="redact")
    assert safe_text == "[PERSON]'s email is [EMAIL]"