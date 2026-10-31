"""
Central configuration for the PII Management System.

Every module imports from here so that settings live in ONE place.
If you need to change a regex pattern or a folder path, change it here.
"""
from pathlib import Path

# ---- Folder paths -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DOCS = DATA_DIR / "sample_documents"
SAMPLE_DATASETS = DATA_DIR / "sample_datasets"
UPLOAD_DIR = DATA_DIR / "uploads"        # files uploaded via Streamlit
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = DATA_DIR / "pii_system.db"

# Make sure the folders exist. mkdir(parents=True) is safe to call repeatedly.
for _folder in (DATA_DIR, SAMPLE_DOCS, SAMPLE_DATASETS, UPLOAD_DIR, REPORTS_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# ---- NLP model --------------------------------------------------------
SPACY_MODEL = "en_core_web_sm"

# ---- PII regex patterns ----------------------------------------------
# IMPORTANT: These are SAMPLE patterns for synthetic test data only.
# Real-world national ID / passport formats differ per country.
# We document this limitation in README.md.
PII_PATTERNS = {
    "EMAIL":        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE":        r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
    "NATIONAL_ID":  r"\b\d{3}-\d{2}-\d{4}\b",          # sample SSN-like format
    "PASSPORT":     r"\b[A-Z]{1,2}\d{6,8}\b",           # sample format
    "BANK_ACCOUNT": r"\b\d{10,17}\b",                    # broad on purpose; refined Day 3
    "ADDRESS_HINT": r"\b\d{1,5}\s+[A-Za-z0-9.\s]{3,40}(?:Street|St|Road|Rd|Ave|Avenue|Blvd|Lane|Ln)\b",
}

# ---- Redaction replacement tokens ------------------------------------
REDACTION_TOKENS = {
    "EMAIL":        "[EMAIL]",
    "PHONE":        "[PHONE]",
    "NATIONAL_ID":  "[NATIONAL_ID]",
    "PASSPORT":     "[PASSPORT]",
    "BANK_ACCOUNT": "[BANK_ACCOUNT]",
    "PERSON":       "[PERSON]",
    "ADDRESS":      "[ADDRESS]",
}

# ---- spaCy entity → our category mapping -----------------------------
SPACY_ENTITIES = {
    "PERSON": "PERSON",
    "GPE":    "ADDRESS",
    "LOC":    "ADDRESS",
}