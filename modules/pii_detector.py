"""
Hybrid PII Detector.

Combines Regex (for strict formats) and spaCy (for Names/Addresses).
"""
import re
from dataclasses import dataclass
from typing import List

import spacy

import config


# ---- Data Model ------------------------------------------------------
@dataclass
class PIIMatch:
    """Represents a single piece of found PII."""
    text: str          # The actual sensitive string (e.g. "alice@test.com")
    category: str      # e.g. "EMAIL"
    start: int         # Character index where it starts
    end: int           # Character index where it ends
    confidence: float  # 0.0 to 1.0
    source: str        # "regex" or "ner"


# ---- Global NLP Model ------------------------------------------------
# We load the model ONCE. Loading it takes ~2 seconds, so we don't
# want to do it every time we scan a document.
try:
    NLP = spacy.load(config.SPACY_MODEL)
except OSError:
    raise ImportError(
        f"spaCy model '{config.SPACY_MODEL}' not found. "
        f"Run: python -m spacy download {config.SPACY_MODEL}"
    )


# ---- Detection Logic -------------------------------------------------
def detect_pii(text: str) -> List[PIIMatch]:
    """
    Scans text and returns a sorted list of non-overlapping PIIMatch objects.
    """
    if not text:
        return []

    matches: List[PIIMatch] = []

    # 1. Run Regex Detectors
    matches.extend(_detect_regex(text))

    # 2. Run spaCy Detector
    matches.extend(_detect_spacy(text))

    # 3. Resolve overlaps (keep the highest confidence)
    clean_matches = _resolve_overlaps(matches)

    # 4. Sort by position in the text (left to right)
    clean_matches.sort(key=lambda m: m.start)

    return clean_matches


def _detect_regex(text: str) -> List[PIIMatch]:
    """Finds patterns defined in config.PII_PATTERNS."""
    found = []
    for category, pattern in config.PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            # Skip empty matches
            if not match.group().strip():
                continue
            found.append(PIIMatch(
                text=match.group(),
                category=category,
                start=match.start(),
                end=match.end(),
                confidence=config.CONFIDENCE_REGEX,
                source="regex"
            ))
    return found


def _detect_spacy(text: str) -> List[PIIMatch]:
    """Finds names and addresses using the spaCy AI model."""
    found = []
    # spaCy has a max text length limit (usually 1,000,000 chars).
    # We truncate to be safe for the MVP.
    doc = NLP(text[:900_000]) 

    for ent in doc.ents:
        # Map spaCy's entity labels (PERSON, GPE) to our categories
        category = config.SPACY_ENTITIES.get(ent.label_)
        if category:
            found.append(PIIMatch(
                text=ent.text,
                category=category,
                start=ent.start_char,
                end=ent.end_char,
                confidence=config.CONFIDENCE_NER,
                source="ner"
            ))
    return found


def _resolve_overlaps(matches: List[PIIMatch]) -> List[PIIMatch]:
    """
    If two matches overlap, keep the one with higher confidence.
    
    Example: Regex finds "123-45-6789" (SSN). 
    spaCy finds "123" (Number). 
    Regex has higher confidence, so we keep the SSN and drop the Number.
    """
    if not matches:
        return []

    # Sort by highest confidence first
    matches.sort(key=lambda m: m.confidence, reverse=True)
    
    # Track spans we've already accepted
    accepted = []
    for m in matches:
        # Check if this match overlaps with any already accepted match
        if not any(_overlaps(m, a) for a in accepted):
            accepted.append(m)
            
    return accepted


def _overlaps(a: PIIMatch, b: PIIMatch) -> bool:
    """Returns True if the two spans share any characters."""
    return max(a.start, b.start) < min(a.end, b.end)