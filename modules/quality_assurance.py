"""
Quality Assurance Module.
Evaluates the PII Detector against a Gold Standard dataset.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

import config
from modules import pii_detector
from modules.pii_detector import PIIMatch


def load_gold_standard(path: Path) -> List[Dict[str, Any]]:
    """Loads the JSON dataset of labeled text."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_detection(gold_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Runs the detector against every item in the gold standard.
    Calculates Precision, Recall, and F1-Score.
    """
    total_tp = 0  # True Positives (correctly found)
    total_fp = 0  # False Positives (hallucinated)
    total_fn = 0  # False Negatives (missed)

    details = []

    for doc in gold_data:
        text = doc["text"]
        expected = doc["expected_pii"]
        
        # 1. Run our detector
        detected = pii_detector.detect_pii(text)
        
        # 2. Convert to sets of strings for easy comparison
        # We compare by the actual text found, not the index.
        expected_set = {(item["category"], item["text"]) for item in expected}
        detected_set = {(item.category, item.text) for item in detected}
        
        # 3. Calculate TP, FP, FN for this document
        tp = expected_set.intersection(detected_set)
        fp = detected_set - expected_set
        fn = expected_set - detected_set
        
        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)
        
        details.append({
            "id": doc["id"],
            "true_positives": list(tp),
            "false_positives": list(fp),
            "false_negatives": list(fn)
        })

    # 4. Calculate Metrics (with zero-division protection)
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "details": details
    }