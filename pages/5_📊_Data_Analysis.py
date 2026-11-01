"""
Data Analysis Page.
Upload CSV/Excel, run analysis, and view visualizations.
"""
import pandas as pd
import streamlit as st

import config
from modules import data_analyzer

st.set_page_config(page_title="Data Analysis", page_icon="📊", layout="wide")

if st.button("⬅️ Back to Home"):
    st.switch_page("0_🏠_Home.py")

st.title("📊 Data Analysis")
st.caption("Upload a CSV or Excel file to analyze data quality, missing values, and PII.")

uploaded_file = st.file_uploader("Upload a dataset", type=["csv", "xlsx", "xls"])

if uploaded_file is None:
    st.info("⬆️ Please upload a CSV or Excel file to begin.")
    st.stop()

# ---- Save file to disk -----------------------------------------------
# For this MVP, we save it to the uploads folder using a hash
import hashlib
file_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
ext = uploaded_file.name.split(".")[-1]
stored_path = config.UPLOAD_DIR / f"{file_hash}.{ext}"

with open(stored_path, "wb") as f:
    f.write(uploaded_file.getvalue())

# ---- Load and Analyze ------------------------------------------------
with st.spinner("Analyzing data..."):
    df = data_analyzer.load_dataset(str(stored_path))
    results = data_analyzer.analyze_dataset(df)

# ---- Display Metrics -------------------------------------------------
st.subheader("Dataset Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rows", results["total_rows"])
col2.metric("Total Columns", results["total_columns"])
col3.metric("Missing Values", results["missing_total"])
col4.metric("Duplicate Rows", results["duplicate_rows"])

# ---- PII Found -------------------------------------------------------
st.subheader("PII Detected in Dataset")
pii_col1, pii_col2 = st.columns(2)
pii_col1.metric("📧 Emails Found", results["pii_found"]["EMAIL"])
pii_col2.metric("📞 Phones Found", results["pii_found"]["PHONE"])

if results["missing_by_column"]:
    st.warning(f"⚠️ Columns with missing data: {', '.join(results['missing_by_column'].keys())}")

# ---- Chart -----------------------------------------------------------
st.subheader("Visualization")
fig = data_analyzer.generate_summary_chart(df)
if fig:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("✅ No missing data to visualize. Excellent data quality!")

# ---- Data Preview ----------------------------------------------------
st.subheader("Data Preview (First 10 Rows)")
st.dataframe(df.head(10), use_container_width=True)

# ---- Download Report -------------------------------------------------
st.divider()
st.subheader("Download Report")
report_text = f"""DATA ANALYSIS REPORT
====================
File: {uploaded_file.name}
Total Rows: {results['total_rows']}
Total Columns: {results['total_columns']}
Missing Values: {results['missing_total']}
Duplicate Rows: {results['duplicate_rows']}

PII DETECTED:
- Emails: {results['pii_found']['EMAIL']}
- Phones: {results['pii_found']['PHONE']}

Missing Data by Column:
{results['missing_by_column']}
"""

st.download_button(
    label="⬇️ Download Analysis Report (TXT)",
    data=report_text,
    file_name=f"analysis_{uploaded_file.name}.txt",
    mime="text/plain"
)