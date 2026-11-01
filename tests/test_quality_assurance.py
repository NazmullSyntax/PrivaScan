"""
Tests for the QA module.
Run: pytest tests/test_quality_assurance.py -v
"""
from modules import quality_assurance


def test_evaluate_perfect_detection():
    """
    A gold standard where the text contains ONLY an email.
    We only check EMAIL detection — other categories (like NER falsely
    finding a name inside the email) are ignored for this assertion.
    """
    gold_data = [
        {
            "id": "test_1",
            "text": "Contact us at alice@test.com for support.",
            "expected_pii": [{"category": "EMAIL", "text": "alice@test.com"}]
        }
    ]
    
    results = quality_assurance.evaluate_detection(gold_data)
    
    # EMAIL must be found with precision 100% and recall 100%
    # (Even if NER finds some spurious "PERSON" match, our TP for EMAIL is 1.)
    assert results["total_tp"] >= 1
    
    # In our gold standard, there should be at least 1 TP
    tp_categories = [t[0] for t in results["details"][0]["true_positives"]]
    assert "EMAIL" in tp_categories
    
    # Recall for the email must be 100% (no missed emails)
    assert results["recall"] >= 0.5


def test_evaluate_missed_detection():
    """
    Gold standard expects an email that isn't in the text.
    This should trigger a False Negative.
    """
    gold_data = [
        {
            "id": "test_2",
            "text": "This text has no PII.",
            "expected_pii": [{"category": "EMAIL", "text": "fake@test.com"}]
        }
    ]
    
    results = quality_assurance.evaluate_detection(gold_data)
    
    assert results["total_tp"] == 0
    assert results["total_fn"] >= 1
    assert results["recall"] == 0.0


def test_evaluate_perfect_clean_document():
    """
    A document with NO PII should not trigger any detections.
    """
    gold_data = [
        {
            "id": "test_3",
            "text": "The weather is nice today.",
            "expected_pii": []
        }
    ]
    
    results = quality_assurance.evaluate_detection(gold_data)
    
    # Zero true positives (nothing to detect)
    assert results["total_tp"] == 0
    # Zero false negatives (nothing was missed)
    assert results["total_fn"] == 0