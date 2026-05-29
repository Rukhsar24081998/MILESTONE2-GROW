"""Phase 3 — Refusal handler.

Generates refusal responses with NO URL policy:
- Advisory queries: refuse without URL
- PII queries: refuse without URL  
- Out-of-scope queries: refuse without URL
- Unknown answers: refuse without URL
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


# Refusal templates (NO URL attached)
REFUSAL_TEMPLATES = {
    "advisory_query": (
        "I can only provide factual information about specific mutual fund schemes, "
        "not investment advice. For personalized recommendations, please consult a "
        "SEBI-registered financial advisor."
    ),
    "comparison_query": (
        "I don't compare or rank mutual funds. I can only provide factual details "
        "about individual schemes. For comparison tools, please visit the fund house website."
    ),
    "pii_detected": (
        "For your privacy and security, I cannot process queries containing personal "
        "information like PAN, Aadhaar, account numbers, or contact details."
    ),
    "out_of_scope": (
        "I can only answer factual questions about HDFC mutual fund schemes, such as "
        "expense ratios, exit loads, SIP minimums, and fund details. Your question appears "
        "to be outside this scope."
    ),
    "answer_not_found": (
        "I couldn't find specific information to answer your question in the available "
        "fund documents. Please check the fund's official page for detailed information."
    ),
    "unknown_query": (
        "I'm designed to answer factual questions about mutual fund schemes. "
        "Could you please rephrase your question to be more specific about a scheme?"
    ),
}


def create_refusal_response(
    reason: str,
    custom_message: Optional[str] = None,
    footer_date: Optional[str] = None,
) -> dict:
    """Create a refusal response with NO URL.
    
    Args:
        reason: Refusal reason key (e.g., 'advisory_query', 'pii_detected')
        custom_message: Override default message
        footer_date: Last updated date for footer
        
    Returns:
        Refusal response dict with citation_url: null
    """
    message = custom_message or REFUSAL_TEMPLATES.get(
        reason, REFUSAL_TEMPLATES["unknown_query"]
    )
    
    footer = footer_date or f"Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}"
    
    return {
        "type": "refusal",
        "text": message,
        "citation_url": None,  # NO URL for refusals
        "footer": footer,
        "refused": True,
        "reason": reason,
    }


def get_refusal_reason(category: str, has_answer: bool = True) -> str:
    """Map query category to refusal reason.
    
    Args:
        category: Query category from classifier
        has_answer: Whether an answer was found in corpus
        
    Returns:
        Refusal reason key
    """
    if category == "advisory":
        return "advisory_query"
    elif category == "out_of_scope":
        return "out_of_scope"
    elif not has_answer:
        return "answer_not_found"
    else:
        return "unknown_query"
