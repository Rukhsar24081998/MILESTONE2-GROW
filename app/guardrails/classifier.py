"""Phase 3 — Query classifier.

Classifies queries into categories:
- FACTUAL: Can be answered from corpus
- ADVISORY: Investment advice, comparisons
- OUT_OF_SCOPE: Personal info, predictions, non-MF topics
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class QueryCategory(str, Enum):
    FACTUAL = "factual"
    ADVISORY = "advisory"
    OUT_OF_SCOPE = "out_of_scope"


# Advisory patterns (should refuse)
ADVISORY_PATTERNS = [
    r"\b(should i|should we|can i invest|good fund|better fund|best fund|good investment)\b",
    r"\b(which.*better|which.*invest|which.*choose|which.*good)\b",
    r"\b(recommend|suggest|advice|advise|opinion)\b",
    r"\b(will.*profit|will.*gain|will.*get|will.*return|future.*return|next year)\b",
    r"\b(predict|forecast|guess|estimate.*future)\b",
    r"\b(is.*good|is.*better|is.*best)\b",
]

# Out-of-scope patterns
OUT_OF_SCOPE_PATTERNS = [
    r"\b(my.*account|my.*portfolio|my.*investment)\b",
    r"\b(login|password|otp|pin)\b",
    r"\b(stock.*tip|intraday.*tip|quick.*money)\b",
    r"\b(lottery|gambling|betting)\b",
]

# Factual indicators (must have scheme mention + fact keyword)
FACTUAL_KEYWORDS = [
    "expense ratio", "exit load", "minimum sip", "min sip", "sip amount",
    "benchmark", "fund manager", "aum", "fund size", "assets under management", 
    "nav", "net asset value", "risk", "riskometer", "risk classification",
    "lock-in", "lock in", "elss", "tax", "dividend", "returns", "performance",
    "holding", "portfolio", "sector", "investment objective"
]


def classify_query(query: str) -> tuple[QueryCategory, Optional[str]]:
    """Classify a query into category with reason.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (category, reason)
    """
    query_lower = query.lower().strip()
    
    # Check advisory patterns
    for pattern in ADVISORY_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryCategory.ADVISORY, "investment_advice_or_comparison"
    
    # Check out-of-scope patterns
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryCategory.OUT_OF_SCOPE, "personal_or_irrelevant"
    
    # Check if it's a factual query about mutual funds
    has_factual_keyword = any(kw in query_lower for kw in FACTUAL_KEYWORDS)
    
    # Must mention a scheme or fund to be factual
    has_scheme_mention = any(kw in query_lower for kw in [
        "mid cap", "midcap", "small cap", "smallcap", "flexi cap", 
        "flexicap", "defence", "silver", "etf", "fund", "scheme"
    ])
    
    if has_factual_keyword and has_scheme_mention:
        return QueryCategory.FACTUAL, "factual_query_about_scheme"
    
    # Default: out of scope if we can't determine it's factual
    return QueryCategory.OUT_OF_SCOPE, "unknown_or_unclear_query"


def is_factual(query: str) -> bool:
    """Quick check if query is factual."""
    category, _ = classify_query(query)
    return category == QueryCategory.FACTUAL


def is_advisory(query: str) -> bool:
    """Quick check if query is advisory."""
    category, _ = classify_query(query)
    return category == QueryCategory.ADVISORY


def is_out_of_scope(query: str) -> bool:
    """Quick check if query is out of scope."""
    category, _ = classify_query(query)
    return category == QueryCategory.OUT_OF_SCOPE
