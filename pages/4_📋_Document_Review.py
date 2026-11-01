"""
Document Review & Downloads Page.
Final human check before exporting.
"""
import io
from pathlib import Path

import streamlit as st
import fitz

import config
from database import db_manager
from modules import document_processor as dp
from modules import pii_detector
from modules import pii_redactor

st.set_page_config(page_title="Document Review", page_icon="📋", layout="wide")
db_manager.init_db()

if st.button("⬅️ Back to Home"):
    st.switch_page("0_🏠_Home.py")

st.title("📋 Document Review & Downloads")
st.caption("Compare the original and redacted text, then download the safe PDF.")

docs = db_manager.list_documents()
if not docs:
    st.warning("No documents found. Please upload one first.")
    st.stop()

latest_doc = docs[0]
st.info(f"Reviewing: **{latest_doc['original_name']}**")

stored_path = config.UPLOAD_DIR / f"{latest_doc['filename_hash']}.{latest_doc['file_type']}"

if not stored_path.exists():
    st.error("File missing from disk.")
    st.stop()

with st.spinner("Processing document..."):
    doc = dp.extract_document(stored_path)
    matches = pii_detector.detect_pii(doc.text)

if not matches:
    st.success("✅ No PII detected. The document is already safe.")
    st.stop()

# Generate redacted text
strategy = st.radio(
    "Choose Redaction Strategy:",
    options=["redact", "mask"],
    format_func=lambda x: "Full Redaction (e.g. [EMAIL])" if x == "redact" else "Masking (e.g. a***@t***.com)",
    horizontal=True
)
redacted_text = pii_redactor.redact_document(doc.text, matches, strategy=strategy)

# ---- Display Comparison ----------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.subheader("🔍 Original Text")
    st.text_area("Original", doc.text[:2000] + "\n...", height=300, disabled=True, label_visibility="collapsed")

with col2:
    st.subheader("✅ Safe Text")
    st.text_area("Redacted", redacted_text[:2000] + "\n...", height=300, disabled=True, label_visibility="collapsed")

# ---- Generate & Download PDF -----------------------------------------
st.divider()
st.subheader("Download Safe PDF")

if st.button("Generate Safe PDF"):
    # 1. Generate the PDF file on disk
    output_filename = f"safe_{strategy}_{latest_doc['original_name'].rsplit('.', 1)[0]}.pdf"
    output_path = config.REPORTS_DIR / output_filename
    
    with st.spinner("Generating PDF..."):
        pii_redactor.generate_redacted_pdf(redacted_text, str(output_path))
        
        # 2. Save to DB
        db_manager.add_redaction(latest_doc['id'], strategy, str(output_path))
        db_manager.log_event(
            action="pdf_downloaded",
            document_hash=latest_doc['filename_hash'],
            details=f"strategy={strategy}, file={output_filename}"
        )
    
    st.success(f"✅ Safe PDF generated!")
    
    # 3. Provide the download button
    with open(output_path, "rb") as f:
        pdf_bytes = f.read()
        
    st.download_button(
        label="⬇️ Download Safe PDF",
        data=pdf_bytes,
        file_name=output_filename,
        mime="application/pdf"
    )