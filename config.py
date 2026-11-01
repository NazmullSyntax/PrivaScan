"""
Central configuration for the PII Management System.
"""
from pathlib import Path

# ---- Folder paths -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DOCS = DATA_DIR / "sample_documents"
SAMPLE_DATASETS = DATA_DIR / "sample_datasets"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = DATA_DIR / "pii_system.db"

# Make sure the folders exist
for _folder in (DATA_DIR, SAMPLE_DOCS, SAMPLE_DATASETS, UPLOAD_DIR, REPORTS_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# ---- NLP model --------------------------------------------------------
SPACY_MODEL = "en_core_web_sm"

# ---- Document processing ---------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_MB = 25

# ---- PII regex patterns ----------------------------------------------
PII_PATTERNS = {
    "EMAIL":        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE":        r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
    "NATIONAL_ID":  r"\b\d{3}-\d{2}-\d{4}\b",          
    "PASSPORT":     r"\b[A-Z]{1,2}\d{6,8}\b",           
    "BANK_ACCOUNT": r"\b\d{10,17}\b",                    
    "ADDRESS_HINT": r"\b\d{1,5}\s+[A-Za-z0-9.\s]{3,40}(?:Street|St|Road|Rd|Ave|Avenue|Blvd|Lane|Ln)\b",
}

# ---- spaCy entity → our category mapping -----------------------------
SPACY_ENTITIES = {
    "PERSON": "PERSON",
    "GPE":    "ADDRESS",
    "LOC":    "ADDRESS",
}

# ---- PII Detection Configuration -------------------------------------
CONFIDENCE_REGEX = 0.95    
CONFIDENCE_NER = 0.85      

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

# ---- Redaction Configuration -----------------------------------------
# Strategy: "redact" (replace entirely) or "mask" (keep first/last char)
DEFAULT_REDACTION_STRATEGY = "redact"