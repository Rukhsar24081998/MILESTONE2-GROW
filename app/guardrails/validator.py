"""Phase 3 — Output validator.

Validates generated responses:
- Factual answers: ≤3 sentences, exactly 1 URL
- Refusals: NO URL (citation_url must be null)
- No banned phrases
"""

from __future__ import annotations

import re


# Banned phrases (advisory language)
BANNED_PHRASES = [
    r"you should invest",
    r"you should buy",
    r"you should sell",
    r"i recommend",
    r"i suggest",
    r"best fund",
    r"better option",
    r"good investment",
]


def count_sentences(text: str) -> int:
    """Count sentences in text."""
    # Split on sentence-ending punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty strings
    return len([s for s in sentences if s.strip()])


def count_urls(text: str) -> int:
    """Count URLs in text."""
    url_pattern = r'https?://[^\s<>"\']+'
    return len(re.findall(url_pattern, text))


def contains_banned_phrases(text: str) -> list[str]:
    """Check for banned advisory phrases."""
    text_lower = text.lower()
    found = []
    for pattern in BANNED_PHRASES:
        if re.search(pattern, text_lower):
            found.append(pattern)
    return found


def validate_answer_response(response: dict) -> tuple[bool, list[str]]:
    """Validate a factual answer response.
    
    Args:
        response: Response dict
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    text = response.get("text", "")
    citation_url = response.get("citation_url")
    
    # Check sentence count
    sentence_count = count_sentences(text)
    if sentence_count > 3:
        errors.append(f"Too many sentences: {sentence_count} (max 3)")
    
    # Check URL presence
    if not citation_url:
        errors.append("Factual answer must have citation_url")
    
    # Check for banned phrases
    banned = contains_banned_phrases(text)
    if banned:
        errors.append(f"Contains banned phrases: {', '.join(banned)}")
    
    return len(errors) == 0, errors


def validate_refusal_response(response: dict) -> tuple[bool, list[str]]:
    """Validate a refusal response (NO URL policy).
    
    Args:
        response: Response dict
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    citation_url = response.get("citation_url")
    refused = response.get("refused")
    
    # Refusal MUST have null URL
    if citation_url is not None:
        errors.append(f"Refusal must have citation_url: null, got: {citation_url}")
    
    # Must be marked as refused
    if not refused:
        errors.append("Refusal must have refused: true")
    
    return len(errors) == 0, errors


def validate_response(response: dict) -> tuple[bool, list[str]]:
    """Validate any response based on type.
    
    Args:
        response: Response dict with 'type' field
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    response_type = response.get("type")
    
    if response_type == "answer":
        return validate_answer_response(response)
    elif response_type == "refusal":
        return validate_refusal_response(response)
    else:
        return False, [f"Unknown response type: {response_type}"]
