"""
Document Upload page — the entry point for getting files into the system.

Flow:
1. User drops a PDF/DOCX/TXT file.
2. We extract text → show it.
3. We store the file safely (hash name).
4. We log the upload to the audit trail.
"""
import shutil
import tempfile
from pathlib import Path

import streamlit as st

import config
from database import db_manager
from modules import document_processor as dp

st.set_page_config(page_title="Document Upload", page_icon="📄", layout="wide")
db_manager.init_db()

st.title("📄 Document Upload")
st.caption(
    "Upload a PDF, DOCX, or TXT file. Text is extracted immediately "
    "so downstream modules can inspect it for PII."
)

uploaded = st.file_uploader(
    "Choose a file",
    type=["pdf", "docx", "txt"],
    help=f"Max size: {config.MAX_FILE_SIZE_MB} MB",
)

if uploaded is None:
    st.info("⬆️ Drop a file above to get started.")
    st.stop()

# ---- Save the incoming bytes to a temp file (extractor works on paths) ----
with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
    tmp.write(uploaded.getvalue())
    tmp_path = Path(tmp.name)

# ---- Extract ----------------------------------------------------------
try:
    doc = dp.extract_document(tmp_path)
    stored_path = dp.store_uploaded_file(tmp_path, doc.file_hash)
except (dp.UnsupportedFileError, dp.FileTooLargeError,
        dp.TextExtractionError, FileNotFoundError) as exc:
    st.error(f"❌ {exc}")
    st.stop()
finally:
    # Always clean up the temp file — regardless of success.
    tmp_path.unlink(missing_ok=True)

# ---- Record in the database ------------------------------------------
document_id = db_manager.add_document(
    filename_hash=doc.file_hash,
    original_name=doc.filename,
    file_type=doc.file_type,
    size_bytes=doc.size_bytes,
)
db_manager.log_event(
    action="document_uploaded",
    document_hash=doc.file_hash,
    actor="user",
    details=f"type={doc.file_type}, size={doc.size_bytes}, doc_id={document_id}",
)

# ---- Show summary ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("File type", doc.file_type.upper())
col2.metric("Size", f"{doc.size_bytes / 1024:.1f} KB")
col3.metric("Pages / paragraphs", doc.page_count)
col4.metric("Characters", len(doc.text))

for warning in doc.warnings:
    st.warning(f"⚠️ {warning}")

st.success(
    f"✅ Extracted successfully. Stored as `{stored_path.name}` "
    f"(DB record id: {document_id})."
)

# ---- Preview --------------------------------------------------------
with st.expander("👀 Preview extracted text", expanded=True):
    st.text_area(
        "Extracted text",
        value=doc.text[:5000] + ("\n\n…(truncated for preview)" if len(doc.text) > 5000 else ""),
        height=350,
        disabled=True,
        label_visibility="collapsed",
    )

st.caption(
    f"Original filename: `{doc.filename}` · "
    f"sha256: `{doc.file_hash[:16]}…`"
)
# Add a back button at the top
if st.button("⬅️ Back to Home"):
    st.switch_page("0_🏠_Home.py")