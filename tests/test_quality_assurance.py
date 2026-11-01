"""
Tests for the QA module.
Run: pytest tests/test_quality_assurance.py -v
"""
from modules import quality_assurance
import pytest
import config

def test_evaluate_perfect_detection():
    # A mock dataset where the system will get it 100% right
    gold_data = [
        {
            "id": "test_1",
            "text": "Email me at alice@test.com",
            "expected_pii": [{"category": "EMAIL", "text": "alice@test.com"}]
        }
    ]
    
    results = quality_assurance.evaluate_detection(gold_data)
    
    # The system should find exactly the email, no false positives
    assert results["total_tp"] == 1
    assert results["total_fp"] == 0
    assert results["total_fn"] == 0
    assert results["precision"] == 1.0
    assert results["recall"] == 1.0
    assert results["f1"] == 1.0


def test_evaluate_missed_detection():
    # A mock dataset where the system will miss the PII (False Negative)
    gold_data = [
        {
            "id": "test_2",
            "text": "This text has no PII.",
            "expected_pii": [{"category": "EMAIL", "text": "fake@test.com"}]
        }
    ]
    
    results = quality_assurance.evaluate_detection(gold_data)
    
    assert results["total_tp"] == 0
    assert results["total_fp"] == 0
    assert results["total_fn"] == 1
    assert results["precision"] == 0.0
    assert results["recall"] == 0.0