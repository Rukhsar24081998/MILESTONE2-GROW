"""Phase 2 — Scheme detection from user queries.

Uses scheme names and aliases from corpus/schemes.json, with HDFC category
keywords as a last-resort fallback for ambiguous short queries (e.g. "Flexi Cap").
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from app.corpus import load_schemes

# HDFC-only generic category keywords — last resort when no name/alias matches.
# Preserves legacy behavior for short queries like "exit load Flexi Cap".
GENERIC_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "hdfc-mid-cap-direct-growth": ["mid cap", "midcap", "mid-cap"],
    "hdfc-flexi-cap-direct-growth": ["flexi cap", "flexicap", "flexi-cap", "equity fund"],
    "hdfc-small-cap-direct-growth": ["small cap", "smallcap", "small-cap"],
    "hdfc-defence-direct-growth": ["defence", "defense", "thematic"],
    "hdfc-silver-etf-fof-direct-growth": ["silver", "etf", "commodities", "fof"],
}

# Backward-compatible alias used in architecture docs / older references.
SCHEME_KEYWORDS = GENERIC_CATEGORY_KEYWORDS


@dataclass(frozen=True)
class _MatchPhrase:
    scheme_id: str
    phrase: str
    tier: int  # 0 = scheme name, 1 = alias


@lru_cache(maxsize=1)
def _scheme_phrases() -> tuple[_MatchPhrase, ...]:
    """Build sorted phrase list: names before aliases; longest phrase first within tier."""
    registry = load_schemes()
    phrases: list[_MatchPhrase] = []

    for scheme in registry.schemes:
        name = scheme.name.strip().lower()
        if name:
            phrases.append(_MatchPhrase(scheme.id, name, 0))
        for alias in scheme.aliases:
            normalized = alias.strip().lower()
            if normalized:
                phrases.append(_MatchPhrase(scheme.id, normalized, 1))

    phrases.sort(key=lambda p: (p.tier, -len(p.phrase)))
    return tuple(phrases)


@lru_cache(maxsize=1)
def _all_scheme_ids() -> frozenset[str]:
    return frozenset(s.id for s in load_schemes().schemes)


def _best_phrase_match(query_lower: str, tier: int) -> Optional[tuple[str, str]]:
    """Return (scheme_id, matched_phrase) for the longest phrase match at a tier."""
    matches = [
        p for p in _scheme_phrases() if p.tier == tier and p.phrase in query_lower
    ]
    if not matches:
        return None
    best = max(matches, key=lambda p: len(p.phrase))
    return best.scheme_id, best.phrase


def _generic_category_match(query_lower: str) -> Optional[str]:
    """Last-resort HDFC category keyword match (longest keyword wins)."""
    best_scheme: Optional[str] = None
    best_len = 0

    for scheme_id, keywords in GENERIC_CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower and len(keyword) > best_len:
                best_scheme = scheme_id
                best_len = len(keyword)

    return best_scheme


def detect_scheme(query: str) -> Optional[str]:
    """Detect which scheme a query refers to.

    Match priority:
    1. Full scheme names (longest match first)
    2. Aliases (longest match first)
    3. Generic HDFC category keywords (legacy fallback)
    """
    query_lower = query.lower().strip()

    name_match = _best_phrase_match(query_lower, tier=0)
    if name_match:
        return name_match[0]

    alias_match = _best_phrase_match(query_lower, tier=1)
    if alias_match:
        return alias_match[0]

    return _generic_category_match(query_lower)


def detect_scheme_with_confidence(query: str) -> tuple[Optional[str], float]:
    """Detect scheme and return confidence score (0.0–1.0)."""
    query_lower = query.lower().strip()
    if not query_lower:
        return None, 0.0

    for tier, base_confidence in ((0, 0.95), (1, 0.75)):
        match = _best_phrase_match(query_lower, tier)
        if match:
            scheme_id, phrase = match
            coverage = len(phrase) / max(len(query_lower), 1)
            confidence = min(1.0, base_confidence * (0.6 + 0.4 * coverage))
            return scheme_id, confidence

    generic_scheme = _generic_category_match(query_lower)
    if generic_scheme:
        return generic_scheme, 0.35

    return None, 0.0


def get_all_scheme_ids() -> list[str]:
    """Get list of all valid scheme IDs from the corpus registry."""
    return sorted(_all_scheme_ids())


def validate_scheme_id(scheme_id: str) -> bool:
    """Check if a scheme ID exists in the corpus registry."""
    return scheme_id in _all_scheme_ids()
