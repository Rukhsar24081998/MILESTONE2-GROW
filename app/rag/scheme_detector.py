"""Phase 2 — Scheme detection from user queries.

Uses keyword matching to detect which scheme a query refers to.
This enables filtered retrieval to avoid cross-scheme contamination
(e.g., "exit load" queries returning wrong scheme).
"""

from __future__ import annotations

from typing import Optional

from app.corpus import load_schemes

# Keyword map for scheme detection
# Built from scheme names, categories, and common aliases
SCHEME_KEYWORDS = {
    "hdfc-mid-cap-direct-growth": ["mid cap", "midcap", "mid-cap"],
    "hdfc-flexi-cap-direct-growth": ["flexi cap", "flexicap", "flexi-cap", "equity fund"],
    "hdfc-small-cap-direct-growth": ["small cap", "smallcap", "small-cap"],
    "hdfc-defence-direct-growth": ["defence", "defense", "thematic"],
    "hdfc-silver-etf-fof-direct-growth": ["silver", "etf", "commodities", "fof"],
}


def detect_scheme(query: str) -> Optional[str]:
    """Detect which scheme a query refers to.
    
    Args:
        query: User query string
        
    Returns:
        scheme_id if detected, None otherwise
    """
    query_lower = query.lower()
    
    # Check each scheme's keywords
    for scheme_id, keywords in SCHEME_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return scheme_id
    
    return None


def detect_scheme_with_confidence(query: str) -> tuple[Optional[str], float]:
    """Detect scheme and return confidence score.
    
    Confidence is based on number of keyword matches.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (scheme_id, confidence) where confidence is 0.0-1.0
    """
    query_lower = query.lower()
    
    best_scheme = None
    best_score = 0.0
    
    for scheme_id, keywords in SCHEME_KEYWORDS.items():
        match_count = sum(1 for keyword in keywords if keyword in query_lower)
        if match_count > 0:
            # Score: ratio of matched keywords, weighted by absolute count
            ratio = match_count / len(keywords)
            score = 0.5 * ratio + 0.5 * min(match_count / 3.0, 1.0)
            
            if score > best_score:
                best_score = score
                best_scheme = scheme_id
    
    return best_scheme, best_score


def get_all_scheme_ids() -> list[str]:
    """Get list of all valid scheme IDs from keyword map."""
    return list(SCHEME_KEYWORDS.keys())


def validate_scheme_id(scheme_id: str) -> bool:
    """Check if a scheme ID is valid."""
    return scheme_id in SCHEME_KEYWORDS
