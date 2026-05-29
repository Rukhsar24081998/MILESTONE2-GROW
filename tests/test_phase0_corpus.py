"""Phase 0 exit criteria tests — corpus manifest and schemes registry."""

from __future__ import annotations

import json

import yaml

from app.config import MANIFEST_PATH, SCHEMES_PATH
from app.corpus.loader import (
    EXPECTED_URL_COUNT,
    KNOWN_SLUGS,
    get_allowlisted_urls,
    get_default_refusal_url,
    load_manifest,
    load_schemes,
    validate_corpus,
)


def test_manifest_has_exactly_five_urls():
    manifest = load_manifest()
    assert len(manifest.allowed_urls) == EXPECTED_URL_COUNT


def test_manifest_closed_allowlist_policy():
    manifest = load_manifest()
    assert manifest.policy == "closed_allowlist"


def test_all_urls_are_known_groww_slugs():
    manifest = load_manifest()
    for entry in manifest.allowed_urls:
        slug = entry.url.rstrip("/").split("/")[-1]
        assert slug in KNOWN_SLUGS


def test_validate_corpus_returns_no_errors():
    assert validate_corpus() == []


def test_schemes_json_matches_manifest_urls():
    manifest = load_manifest()
    schemes = load_schemes()
    by_id = {s.id: s for s in schemes.schemes}
    for entry in manifest.allowed_urls:
        assert entry.scheme_id in by_id
        assert by_id[entry.scheme_id].groww_url == entry.url


def test_flexi_cap_has_equity_fund_alias():
    schemes = load_schemes()
    flexi = next(s for s in schemes.schemes if s.id == "hdfc-flexi-cap-direct-growth")
    assert "HDFC Equity Fund" in flexi.aliases


def test_default_refusal_url_is_flexi_cap_groww_page():
    url = get_default_refusal_url()
    assert url == "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
    assert url in get_allowlisted_urls()


def test_no_blocked_hosts_in_manifest_file():
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    blob = json.dumps(raw).lower()
    assert "hdfcfund.com" not in blob
    assert "amfiindia.com" not in blob


def test_schemes_count_is_five():
    schemes = load_schemes()
    assert len(schemes.schemes) == 5


def test_categories_cover_diversity():
    schemes = load_schemes()
    categories = {s.category for s in schemes.schemes}
    assert "equity_mid_cap" in categories
    assert "equity_flexi_cap" in categories
    assert "equity_small_cap" in categories
    assert "equity_thematic" in categories
    assert "commodities_silver_fof" in categories
