"""
Home page — the entry point for the Streamlit dashboard.

Run with:  streamlit run app.py
"""
import streamlit as st

import config
from database import db_manager

# Must be the FIRST streamlit call on the page.
st.set_page_config(
    page_title="PII Management System",
    page_icon="🔒",
    layout="wide",
)

# Ensure tables exist. Safe to run every time.
db_manager.init_db()

# ---- Header ----------------------------------------------------------
st.title("🔒 PII Detection, Document Review & Data Quality")
st.caption(
    "Privacy · Document Review · Data Analysis · Quality Assurance — "
    "all statistics shown are computed live from the database."
)

# ---- KPI cards -------------------------------------------------------
counts = db_manager.dashboard_counts()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📄 Documents processed", counts["documents"])
c2.metric("🔍 PII instances detected", counts["pii_instances"])
c3.metric("🛡️ Documents redacted", counts["redactions"])
c4.metric("✅ QA runs", counts["qa_runs"])

# ---- PII breakdown chart --------------------------------------------
st.subheader("PII findings by category")
pii_totals = db_manager.get_pii_totals()
if pii_totals:
    st.bar_chart(pii_totals)
else:
    st.info("No PII has been detected yet. Upload a document to get started.")

# ---- Quick orientation ----------------------------------------------
st.subheader("Getting started")
st.markdown(
    """
1. Go to **Document Upload** to add a PDF, DOCX, or TXT file.
2. Visit **PII Detection** to see what sensitive data was found.
3. Use **PII Redaction** to produce a safe-to-share copy.
4. Open **Data Analysis** for CSV/Excel insights.
5. Run **Quality Assurance** to validate detection on labelled data.
6. Review **Audit Logs** to see every action the system took.
"""
)

st.divider()
st.caption(f"Project folder: `{config.BASE_DIR}`")