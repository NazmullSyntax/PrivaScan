"""
PII Detection Page.
Analyzes a document and displays the findings.
"""
import streamlit as st

import config
from database import db_manager
from modules import document_processor as dp
from modules import pii_detector

st.set_page_config(page_title="PII Detection", page_icon="🔍", layout="wide")
db_manager.init_db()

st.title("🔍 PII Detection")
st.caption("Scan text for sensitive data using Regex and AI (spaCy).")

# ---- Retrieve document from DB ----------------------------------------
# For this MVP, we'll just grab the most recently uploaded document.
docs = db_manager.list_documents()
if not docs:
    st.warning("No documents found. Please upload one on the Document Upload page first.")
    st.stop()

latest_doc = docs[0]
st.info(f"Analyzing latest document: **{latest_doc['original_name']}** (ID: {latest_doc['id']})")

# ---- Re-extract the text ---------------------------------------------
# In a real app, we'd save the extracted text in the DB to avoid re-processing.
# For our MVP, we just re-read the file from the uploads folder.
stored_path = config.UPLOAD_DIR / f"{latest_doc['filename_hash']}.{latest_doc['file_type']}"

if not stored_path.exists():
    st.error(f"File missing from disk: {stored_path.name}")
    st.stop()

with st.spinner("Extracting text and running detection..."):
    doc = dp.extract_document(stored_path)
    matches = pii_detector.detect_pii(doc.text)

# ---- Display Results -------------------------------------------------
if not matches:
    st.success("✅ No PII detected in this document.")
    st.stop()

# Save findings to database (if we haven't already)
# In a full app, you'd check if findings already exist for this doc_id.
# We'll save it manually for now.
counts = {}
for m in matches:
    counts[m.category] = counts.get(m.category, 0) + 1

db_manager.add_pii_findings(latest_doc['id'], counts, source="hybrid")
db_manager.log_event(
    action="pii_scanned", 
    document_hash=latest_doc['filename_hash'], 
    details=f"found {len(matches)} items"
)

# Dashboard metrics
col1, col2 = st.columns(2)
col1.metric("Total PII Found", len(matches))
col2.metric("Unique Categories", len(counts))

st.subheader("Findings Table")
# Build a clean list of dicts for Streamlit to render as a table
table_data = [
    {
        "Category": m.category,
        "Text": m.text,
        "Source": m.source,
        "Confidence": f"{m.confidence:.0%}"
    }
    for m in matches
]
st.dataframe(table_data, use_container_width=True)

# Show the raw text with highlights
st.subheader("Document Context")
st.markdown("*Note: In Day 5, this will become a fully styled highlight view.*")

# Simple HTML highlighting for now
highlighted_text = doc.text
# Replace from the end so indices don't shift
for m in sorted(matches, key=lambda x: x.start, reverse=True):
    color = "red" if m.confidence > 0.9 else "orange"
    html_tag = f"<mark style='background-color:{color}; color:white; padding:2px; border-radius:3px;'>"
    highlighted_text = (
        highlighted_text[:m.start] + 
        html_tag + highlighted_text[m.start:m.end] + "</mark>" + 
        highlighted_text[m.end:]
    )

st.markdown(
    f"<div style='background:#f0f2f6; padding:15px; border-radius:5px; line-height:1.6;'>{highlighted_text}</div>", 
    unsafe_allow_html=True
)