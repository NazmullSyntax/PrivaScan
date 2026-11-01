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

# ---- PII Detection Configuration -------------------------------------

# Confidence scores (0.0 to 1.0) used to resolve overlapping matches
CONFIDENCE_REGEX = 0.95    # High, because rules are precise
CONFIDENCE_NER = 0.85      # Slightly lower, because AI can be wrong

# Tokens used later for redaction (Day 4)
REDACTION_TOKENS = {
    "EMAIL": "[EMAIL]",
    "PHONE": "[PHONE]",
    "NATIONAL_ID": "[SSN]",
    "PASSPORT": "[PASSPORT]",
    "BANK_ACCOUNT": "[BANK_ACCOUNT]",
    "PERSON": "[PERSON]",
    "ADDRESS": "[ADDRESS]",
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
# ---- Document processing ---------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_MB = 25          # reject files larger than this