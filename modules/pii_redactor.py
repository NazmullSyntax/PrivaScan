"""
Redaction Engine.
Takes text and PIIMatch objects, and outputs safe, anonymized text.
"""
from typing import List
import config
from modules.pii_detector import PIIMatch


def mask_text_value(text: str) -> str:
    """
    Masks a string by keeping the first and last character and hiding the rest.
    Example: "alice@test.com" -> "a***@***.com"
    """
    if len(text) <= 2:
        return "*" * len(text)
    
    # Special handling for emails to keep the domain readable
    if "@" in text:
        local, domain = text.split("@", 1)
        masked_local = local[0] + "***"
        masked_domain = domain[0] + "***" + domain[domain.rfind("."):]
        return f"{masked_local}@{masked_domain}"

    # Default masking for other text
    return text[0] + "*" * (len(text) - 2) + text[-1]


def redact_document(text: str, matches: List[PIIMatch], strategy: str = "redact") -> str:
    """
    Applies redaction or masking to the text.
    
    Crucially, we iterate from the END of the text to the BEGINNING.
    This ensures that modifying a string doesn't shift the indices of
    PII matches we haven't processed yet.
    """
    if not matches:
        return text

    # Sort matches from right to left (reverse order)
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
    
    redacted_text = text
    
    for match in sorted_matches:
        # Safety check: ensure the span is valid
        if match.start < 0 or match.end > len(redacted_text):
            continue

        if strategy == "mask":
            replacement = mask_text_value(match.text)
        else:
            # Default: use the tokens from config, fallback to [REDACTED]
            replacement = config.REDACTION_TOKENS.get(match.category, "[REDACTED]")

        # Apply the replacement
        redacted_text = (
            redacted_text[:match.start] + 
            replacement + 
            redacted_text[match.end:]
        )

    return redacted_text