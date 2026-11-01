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
import fitz  # PyMuPDF

def generate_redacted_pdf(redacted_text: str, output_path: str) -> None:
    """
    Generates a clean, safe PDF from the redacted text.
    
    Note: This creates a NEW plain-text PDF. It does not preserve 
    the original layout/images. This is a documented MVP limitation.
    """
    pdf = fitz.open()
    page = pdf.new_page()
    
    # Insert text with basic wrapping
    y_position = 72  # Start 1 inch from top
    margin_left = 72
    line_height = 14
    max_width = 450  # Max chars per line before wrapping
    
    for line in redacted_text.splitlines():
        # Very basic wrapping for long lines
        while len(line) > max_width:
            # Find the last space before max_width
            break_point = line.rfind(' ', 0, max_width)
            if break_point == -1:
                break_point = max_width  # Force break if no space found
            
            chunk = line[:break_point]
            page.insert_text((margin_left, y_position), chunk, fontsize=11)
            line = line[break_point:].lstrip()
            y_position += line_height
            
            # Add a new page if we run out of room
            if y_position > 750:
                page = pdf.new_page()
                y_position = 72

        # Write the remaining part of the line
        page.insert_text((margin_left, y_position), line, fontsize=11)
        y_position += line_height
        
        # Add a new page if we run out of room
        if y_position > 750:
            page = pdf.new_page()
            y_position = 72

    pdf.save(output_path)
    pdf.close()