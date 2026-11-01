"""
Home page — the main dashboard.

Run with:  streamlit run 0_🏠_Home.py
"""
import streamlit as st

import config
from database import db_manager

st.set_page_config(
    page_title="PrivaScan — Home",
    page_icon="🔒",
    layout="wide",
)
db_manager.init_db()

# ---- Header ----------------------------------------------------------
st.title("🔒 PrivaScan")
st.caption(
    "PII Detection · Document Review · Data Analysis · Quality Assurance — "
    "all statistics shown are computed live from the database."
)

# ---- Top KPI row -----------------------------------------------------
counts = db_manager.dashboard_counts()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📄 Documents processed", counts["documents"])
c2.metric("🔍 PII instances detected", counts["pii_instances"])
c3.metric("🛡️ Documents redacted", counts["redactions"])
c4.metric("✅ QA runs", counts["qa_runs"])

# ---- PII breakdown chart --------------------------------------------
st.subheader("📊 PII Findings by Category")
pii_totals = db_manager.get_pii_totals()

if pii_totals:
    # Sort largest to smallest
    sorted_pii = dict(sorted(pii_totals.items(), key=lambda x: x[1], reverse=True))
    st.bar_chart(sorted_pii, height=300)
else:
    st.info("No PII has been detected yet. Upload a document on the **Document Upload** page to get started.")

# ---- Recent activity -------------------------------------------------
st.subheader("🕐 Recent Activity")
recent_logs = db_manager.get_audit_logs(limit=5)

if recent_logs:
    for log in recent_logs:
        action = log["action"].replace("_", " ").title()
        timestamp = log["timestamp"][:19].replace("T", " ")
        st.markdown(f"- **{action}** — `{timestamp}`")
else:
    st.info("No activity yet. Your actions will appear here.")

# ---- Navigation tiles -----------------------------------------------
st.divider()
st.subheader("🚀 Quick Actions")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📄 Upload Document", use_container_width=True):
        st.switch_page("pages/1_📄_Document_Upload.py")
with col2:
    if st.button("🔍 Review PII", use_container_width=True):
        st.switch_page("pages/2_🔍_PII_Detection.py")
with col3:
    if st.button("🛡️ Redact", use_container_width=True):
        st.switch_page("pages/3_🛡️_PII_Redaction.py")
with col4:
    if st.button("✅ Run QA", use_container_width=True):
        st.switch_page("pages/6_✅_Quality_Assurance.py")

st.divider()
st.caption(f"Project folder: `{config.BASE_DIR}`")