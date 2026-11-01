"""
Tests for modules/data_analyzer.py.
Run: pytest tests/test_data_analysis.py -v
"""
import pandas as pd
from modules import data_analyzer

def test_analyze_clean_data():
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35]
    })
    results = data_analyzer.analyze_dataset(df)
    
    assert results["total_rows"] == 3
    assert results["total_columns"] == 2
    assert results["missing_total"] == 0
    assert results["duplicate_rows"] == 0

def test_analyze_messy_data():
    df = pd.DataFrame({
        "Email": ["alice@test.com", None, "bob@test.com", "alice@test.com"],
        "Age": [25, 30, 35, 25]
    })
    results = data_analyzer.analyze_dataset(df)
    
    # 1 missing in Email
    assert results["missing_total"] == 1
    # 1 duplicate row (Alice)
    assert results["duplicate_rows"] == 1
    # 2 emails found
    assert results["pii_found"]["EMAIL"] == 2