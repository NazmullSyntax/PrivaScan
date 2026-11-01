"""
PII Redaction Page.
Generates safe, anonymized copies of documents.
"""
import streamlit as st

import config
from database import db_manager
from modules import document_processor as dp
from modules import pii_detector
from modules import pii_redactor

st.set_page_config(page_title="PII Redaction", page_icon="🛡️", layout="wide")
db_manager.init_db()

st.title("🛡️ PII Redaction")
st.caption("Create a safe, anonymized version of your document.")

docs = db_manager.list_documents()
if not docs:
    st.warning("No documents found. Please upload one first.")
    st.stop()

latest_doc = docs[0]
st.info(f"Target Document: **{latest_doc['original_name']}**")

# ---- Re-process document ---------------------------------------------
stored_path = config.UPLOAD_DIR / f"{latest_doc['filename_hash']}.{latest_doc['file_type']}"

if not stored_path.exists():
    st.error("File missing from disk.")
    st.stop()

with st.spinner("Scanning for PII..."):
    doc = dp.extract_document(stored_path)
    matches = pii_detector.detect_pii(doc.text)

if not matches:
    st.success("✅ No PII detected. This document is already safe!")
    st.stop()

# ---- User Options ----------------------------------------------------
st.subheader("Redaction Options")
strategy = st.radio(
    "Choose a strategy:",
    options=["redact", "mask"],
    format_func=lambda x: "Full Redaction (e.g. [EMAIL])" if x == "redact" else "Masking (e.g. a***@t***.com)",
    horizontal=True
)

# Generate the redacted text based on the chosen strategy
redacted_text = pii_redactor.redact_document(doc.text, matches, strategy=strategy)

# ---- Display Side-by-Side --------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Original Text")
    st.text_area("Original", doc.text[:1500] + "\n...", height=400, disabled=True, label_visibility="collapsed")

with col2:
    st.subheader("Redacted Text")
    st.text_area("Redacted", redacted_text[:1500] + "\n...", height=400, disabled=True, label_visibility="collapsed")

# ---- Save to Disk & DB -----------------------------------------------
st.divider()
st.subheader("Save Redacted Document")

if st.button("Generate & Save Redacted File"):
    # For the MVP, we just save the redacted output as a .txt file.
    # (Generating a new PDF is complex, so we do TXT for now and document this limitation).
    output_filename = f"redacted_{strategy}_{latest_doc['original_name'].rsplit('.', 1)[0]}.txt"
    output_path = config.REPORTS_DIR / output_filename
    
    # Write file
    output_path.write_text(redacted_text, encoding="utf-8")
    
    # Update Database
    db_manager.add_redaction(latest_doc['id'], strategy, str(output_path))
    db_manager.log_event(
        action="document_redacted",
        document_hash=latest_doc['filename_hash'],
        details=f"strategy={strategy}"
    )
    
    st.success(f"✅ Redacted file saved to: `reports/{output_filename}`")
    st.balloons()
    # Add a back button at the top
if st.button("⬅️ Back to Home"):
    st.switch_page("0_🏠_Home.py")