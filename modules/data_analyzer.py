"""
Data Analysis Module.
Handles CSV/Excel uploads, data cleaning, statistics, and PII detection in tabular data.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import re

import config
from database import db_manager


def load_dataset(file_path: str) -> pd.DataFrame:
    """Loads a CSV or Excel file into a Pandas DataFrame."""
    path_lower = file_path.lower()
    if path_lower.endswith(".csv"):
        return pd.read_csv(file_path)
    elif path_lower.endswith((".xls", ".xlsx")):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")


def analyze_dataset(df: pd.DataFrame) -> dict:
    """
    Runs a full analysis on the DataFrame and returns a dictionary of results.
    """
    results = {}
    
    # 1. Basic Stats
    results["total_rows"] = len(df)
    results["total_columns"] = len(df.columns)
    results["column_names"] = list(df.columns)

    # 2. Missing Values
    missing = df.isnull().sum()
    results["missing_total"] = int(missing.sum())
    results["missing_by_column"] = missing[missing > 0].to_dict()

    # 3. Duplicates
    results["duplicate_rows"] = int(df.duplicated().sum())

    # 4. Data Types (for display)
    results["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # 5. Invalid Data (simple check: numeric columns containing strings)
    invalid_counts = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        # Try converting to numeric, count failures
        coerced = pd.to_numeric(df[col], errors='coerce')
        invalid_count = df[col].notnull().sum() - coerced.notnull().sum()
        if invalid_count > 0:
            invalid_counts[col] = int(invalid_count)
    results["invalid_data"] = invalid_counts

    # 6. PII Detection in Columns
    pii_counts = {"EMAIL": 0, "PHONE": 0}
    email_pattern = re.compile(config.PII_PATTERNS["EMAIL"])
    phone_pattern = re.compile(config.PII_PATTERNS["PHONE"])
    
    for col in df.select_dtypes(include=['object']).columns:
        for cell in df[col].dropna():
            cell_str = str(cell)
            if email_pattern.search(cell_str):
                pii_counts["EMAIL"] += 1
            if phone_pattern.search(cell_str):
                pii_counts["PHONE"] += 1
                
    results["pii_found"] = pii_counts

    return results


def generate_summary_chart(df: pd.DataFrame):
    """Generates a Plotly bar chart for the top 5 missing-value columns."""
    missing = df.isnull().sum().sort_values(ascending=False).head(5)
    missing = missing[missing > 0]  # only show columns that actually have missing data
    
    if missing.empty:
        return None
        
    fig = px.bar(
        x=missing.index, 
        y=missing.values,
        labels={'x': 'Column', 'y': 'Missing Values'},
        title="Top Columns with Missing Data",
        color=missing.values,
        color_continuous_scale="Reds"
    )
    return fig