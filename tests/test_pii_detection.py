"""
Tests for modules/pii_detector.py.
Run: pytest tests/test_pii_detection.py -v
"""
from modules import pii_detector as pd


def test_detect_email():
    text = "Contact me at alice.testerson@example.com for details."
    matches = pd.detect_pii(text)
    emails = [m for m in matches if m.category == "EMAIL"]
    
    assert len(emails) == 1
    assert emails[0].text == "alice.testerson@example.com"
    assert emails[0].source == "regex"


def test_detect_phone_and_ssn():
    text = "SSN: 123-45-6789. Phone: +1-555-010-2030."
    matches = pd.detect_pii(text)
    
    categories = {m.category for m in matches}
    assert "NATIONAL_ID" in categories
    assert "PHONE" in categories


def test_detect_spacy_person():
    text = "Alice Testerson works in the Data department."
    matches = pd.detect_pii(text)
    persons = [m for m in matches if m.category == "PERSON"]
    
    assert len(persons) >= 1
    assert persons[0].text == "Alice Testerson"
    assert persons[0].source == "ner"


def test_overlap_resolution():
    # An SSN is a strong regex match. spaCy might also flag the numbers.
    # Our resolver should keep the SSN and drop the weaker NER match.
    text = "My ID is 123-45-6789."
    matches = pd.detect_pii(text)
    
    # There should be exactly 1 match for this span (the SSN)
    assert len(matches) == 1
    assert matches[0].category == "NATIONAL_ID"
    assert matches[0].confidence == 0.95


def test_empty_text():
    assert pd.detect_pii("") == []
    assert pd.detect_pii("No PII here, just a normal sentence.") == []