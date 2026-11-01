"""
Audit Logs Page.
Shows every action recorded in the system for compliance.
"""
import pandas as pd
import streamlit as st

from database import db_manager

st.set_page_config(page_title="Audit Logs", page_icon="📋", layout="wide")
db_manager.init_db()

if st.button("⬅️ Back to Home"):
    st.switch_page("0_🏠_Home.py")

st.title("📋 Audit Logs")
st.caption("Every action the system has taken. Compliance-ready.")


# ---- Retrieve logs ---------------------------------------------------
logs = db_manager.get_audit_logs(limit=500)

if not logs:
    st.info("No audit logs yet. Actions will appear here as you use the system.")
    st.stop()


# ---- Convert to DataFrame for filtering -----------------------------
rows = [
    {
        "Timestamp": log["timestamp"][:19].replace("T", " "),
        "Action": log["action"],
        "Document Hash": (log["document_hash"][:16] + "...") if log["document_hash"] else "-",
        "Actor": log["actor"],
        "Details": log["details"] or "-",
    }
    for log in logs
]
df = pd.DataFrame(rows)


# ---- Filters ---------------------------------------------------------
st.subheader("Filter Logs")
col1, col2 = st.columns(2)

with col1:
    unique_actions = sorted(df["Action"].unique())
    selected_action = st.selectbox(
        "Filter by action",
        options=["All"] + unique_actions,
    )

with col2:
    search_term = st.text_input("Search in details", placeholder="e.g. EMAIL or doc_id")


# ---- Apply filters ---------------------------------------------------
filtered = df.copy()
if selected_action != "All":
    filtered = filtered[filtered["Action"] == selected_action]

if search_term:
    filtered = filtered[filtered["Details"].str.contains(search_term, case=False, na=False)]


# ---- Metrics ---------------------------------------------------------
st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("Total Events", len(df))
col2.metric("Showing", len(filtered))
col3.metric("Unique Actions", len(unique_actions))


# ---- Table -----------------------------------------------------------
st.subheader("Log Entries")
st.dataframe(filtered, use_container_width=True, hide_index=True)


# ---- Export ----------------------------------------------------------
st.download_button(
    label="⬇️ Download Audit Logs (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="audit_logs.csv",
    mime="text/csv",
)