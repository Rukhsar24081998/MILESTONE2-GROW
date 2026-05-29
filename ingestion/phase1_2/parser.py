"""Phase 1.2 — Parse and normalize raw HTML into plain-text documents."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from app.config import INGESTION_RAW_DIR, PROJECT_ROOT
from app.corpus import load_manifest, load_schemes
from app.corpus.loader import _normalize_url

PARSED_DIR = PROJECT_ROOT / "ingestion" / "parsed"
SNAPSHOTS_DIR = PROJECT_ROOT / "ingestion" / "snapshots"


@dataclass
class ParsedDocument:
    scheme_id: str
    scheme_name: str
    source_url: str
    text: str
    text_length: int
    quality: str
    has_expense_ratio: bool
    has_exit_load: bool
    has_sip: bool


def _clean_html_to_text(html: str) -> str:
    """Extract reasonably clean visible text from Groww HTML.
    
    Improved version: aggressively removes navigation, footer, calculators,
    and other boilerplate to focus on fund-specific facts.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Drop scripts and styles first
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    
    # Remove common boiler containers by class/ID patterns
    boilerplate_selectors = [
        # Navigation and header/footer
        "header", "footer", "nav", "aside", ".sidebar", ".cookie-banner",
        # Ads and promotional content
        ".ad", ".ads", ".advertisement", ".promo",
        # Groww-specific navigation
        "[class*='header']", "[class*='navbar']", "[class*='navigation']",
        "[class*='Footer']", "[class*='footer']", "[class*='BottomNav']",
        # Calculators and tools (not fund-specific)
        "[class*='Calculator']", "[class*='calculator']", "[class*='Screener']",
        # Compare funds, similar funds sections
        "[class*='Compare']", "[class*='compare']", "[class*='Similar']",
        # App download, social links
        "[class*='AppDownload']", "[class*='Social']", "[class*='Download']",
        # Stock market lists, indices, gainers/losers
        "[class*='Gainer']", "[class*='Loser']", "[class*='Index']",
        "[class*='Stock']", "[class*='Market']",
    ]
    
    for selector in boilerplate_selectors:
        for tag in soup.select(selector):
            tag.decompose()

    # Extract text with structure
    text = soup.get_text(separator="\n", strip=True)
    
    # Normalize whitespace
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # Remove very short lines that are likely UI artifacts
    lines = [ln for ln in lines if len(ln) > 2 or any(c.isdigit() for c in ln)]
    
    return "\n".join(lines)


def _load_raw_html(scheme_id: str) -> str:
    raw_path = INGESTION_RAW_DIR / f"{scheme_id}.html"
    if raw_path.exists():
        return raw_path.read_text(encoding="utf-8", errors="ignore")

    # Optional snapshot fallback for dev (markdown or txt).
    snapshot_md = SNAPSHOTS_DIR / f"{scheme_id}.md"
    snapshot_txt = SNAPSHOTS_DIR / f"{scheme_id}.txt"
    if snapshot_md.exists():
        return snapshot_md.read_text(encoding="utf-8", errors="ignore")
    if snapshot_txt.exists():
        return snapshot_txt.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(f"No raw HTML or snapshot found for {scheme_id}")


def parse_one(scheme_id: str) -> ParsedDocument:
    """Parse a single scheme's HTML into a ParsedDocument."""
    manifest = load_manifest()
    schemes = load_schemes()
    scheme_map = {s.id: s for s in schemes.schemes}

    entry = next(e for e in manifest.allowed_urls if e.scheme_id == scheme_id)
    scheme = scheme_map[scheme_id]

    html = _load_raw_html(scheme_id)
    text = _clean_html_to_text(html)
    text_length = len(text)
    quality = "low" if text_length < 500 else "ok"

    lower = text.lower()
    has_expense_ratio = "expense ratio" in lower
    has_exit_load = "exit load" in lower or "exit-load" in lower
    has_sip = "min. for sip" in lower or "minimum sip" in lower or "sip" in lower

    return ParsedDocument(
        scheme_id=scheme_id,
        scheme_name=scheme.name,
        source_url=_normalize_url(entry.url),
        text=text,
        text_length=text_length,
        quality=quality,
        has_expense_ratio=has_expense_ratio,
        has_exit_load=has_exit_load,
        has_sip=has_sip,
    )


def save_parsed(doc: ParsedDocument, directory: Path | None = None) -> Path:
    directory = directory or PARSED_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{doc.scheme_id}.json"
    path.write_text(json.dumps(asdict(doc), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def parse_all(scheme_ids: Iterable[str] | None = None) -> list[ParsedDocument]:
    manifest = load_manifest()
    ids = [e.scheme_id for e in manifest.allowed_urls]
    if scheme_ids is not None:
        ids = [i for i in ids if i in scheme_ids]
    results: list[ParsedDocument] = []
    for sid in ids:
        doc = parse_one(sid)
        save_parsed(doc)
        results.append(doc)
    return results

