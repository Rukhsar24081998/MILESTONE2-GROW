"""Phase 3 — PII filter.

Detects personally identifiable information in queries.
Refuses to process queries containing PII for privacy protection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PIIDetection:
    """PII detection result."""
    has_pii: bool
    pii_type: str | None = None
    matched_text: str | None = None


# PII patterns
PII_PATTERNS = {
    "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",  # ABCDE1234F
    "aadhaar": r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b",  # 1234 5678 9012
    "phone": r"\b(\+91[\s-]?)?[0]?[6789]\d{9}\b",  # Indian phone numbers
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "account_number": r"(account\s*(?:number|no|#)|a\/c\s*(?:number|no))[\s\S]*?\b\d{8,}\b",  # Flexible
    "password": r"\b(password|passwd|pwd)[\s:]*\S+\b",
    "otp": r"\b(otp|one.time.password)[\s:]*\d{4,6}\b",
}


def detect_pii(query: str) -> PIIDetection:
    """Detect PII in query string.
    
    Args:
        query: User query string
        
    Returns:
        PIIDetection with has_pii flag and details
    """
    for pii_type, pattern in PII_PATTERNS.items():
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return PIIDetection(
                has_pii=True,
                pii_type=pii_type,
                matched_text=match.group(0),
            )
    
    return PIIDetection(has_pii=False)


def contains_pii(query: str) -> bool:
    """Quick check if query contains PII."""
    return detect_pii(query).has_pii
