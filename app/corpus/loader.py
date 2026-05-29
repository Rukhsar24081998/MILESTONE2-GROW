"""Load and validate corpus manifest + schemes registry."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import yaml

from app.config import MANIFEST_PATH, SCHEMES_PATH
from app.corpus.models import (
    AllowedUrl,
    CitationRules,
    Manifest,
    Scheme,
    SchemesRegistry,
)

EXPECTED_URL_COUNT = 5
ALLOWED_HOST = "groww.in"
ALLOWED_DOCUMENT_TYPE = "groww_scheme_page"
KNOWN_SLUGS = frozenset(
    {
        "hdfc-mid-cap-fund-direct-growth",
        "hdfc-equity-fund-direct-growth",
        "hdfc-small-cap-fund-direct-growth",
        "hdfc-defence-fund-direct-growth",
        "hdfc-silver-etf-fof-direct-growth",
    }
)
BLOCKED_HOSTS = frozenset({"hdfcfund.com", "www.hdfcfund.com", "amfiindia.com", "www.sebi.gov.in"})


def _normalize_url(url: str) -> str:
    """Canonical form: https, no trailing slash, no query params."""
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    return f"https://{parsed.netloc.replace('www.', '')}{path}"


def _slug_from_groww_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def load_manifest(path: Path | None = None) -> Manifest:
    path = path or MANIFEST_PATH
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    rules = data["citation_rules"]
    return Manifest(
        corpus_version=data["corpus_version"],
        policy=data["policy"],
        citation_rules=CitationRules(
            factual=rules["factual"],
            refusal_default_scheme_id=rules["refusal_default_scheme_id"],
        ),
        allowed_urls=[
            AllowedUrl(
                url=entry["url"],
                scheme_id=entry["scheme_id"],
                document_type=entry["document_type"],
            )
            for entry in data["allowed_urls"]
        ],
    )


def load_schemes(path: Path | None = None) -> SchemesRegistry:
    path = path or SCHEMES_PATH
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    amc = data["amc"]
    return SchemesRegistry(
        amc_name=amc["name"],
        amc_website=amc["website"],
        product_context=data["product_context"],
        schemes=[
            Scheme(
                id=s["id"],
                name=s["name"],
                category=s["category"],
                groww_url=s["groww_url"],
                aliases=s.get("aliases", []),
            )
            for s in data["schemes"]
        ],
    )


def validate_corpus(
    manifest: Manifest | None = None,
    schemes: SchemesRegistry | None = None,
) -> list[str]:
    """
    Validate Phase 0 exit criteria. Returns list of error messages (empty = pass).
    """
    errors: list[str] = []
    manifest = manifest or load_manifest()
    schemes = schemes or load_schemes()

    if manifest.policy != "closed_allowlist":
        errors.append(f"Expected policy 'closed_allowlist', got '{manifest.policy}'")

    if len(manifest.allowed_urls) != EXPECTED_URL_COUNT:
        errors.append(
            f"Expected exactly {EXPECTED_URL_COUNT} allowed_urls, "
            f"got {len(manifest.allowed_urls)}"
        )

    scheme_by_id = {s.id: s for s in schemes.schemes}
    if len(scheme_by_id) != len(schemes.schemes):
        errors.append("Duplicate scheme id in schemes.json")

    seen_urls: set[str] = set()
    seen_scheme_ids: set[str] = set()

    for entry in manifest.allowed_urls:
        if entry.document_type != ALLOWED_DOCUMENT_TYPE:
            errors.append(
                f"{entry.scheme_id}: document_type must be '{ALLOWED_DOCUMENT_TYPE}'"
            )

        if entry.scheme_id in seen_scheme_ids:
            errors.append(f"Duplicate scheme_id in manifest: {entry.scheme_id}")
        seen_scheme_ids.add(entry.scheme_id)

        normalized = _normalize_url(entry.url)
        if normalized in seen_urls:
            errors.append(f"Duplicate URL in manifest: {normalized}")
        seen_urls.add(normalized)

        if entry.url != normalized:
            errors.append(
                f"URL must be canonical (https, no trailing slash): {entry.url}"
            )

        parsed = urlparse(entry.url)
        host = parsed.netloc.replace("www.", "")
        if host != ALLOWED_HOST:
            errors.append(f"URL host must be {ALLOWED_HOST}: {entry.url}")
        if parsed.scheme != "https":
            errors.append(f"URL must use https: {entry.url}")
        if parsed.query or parsed.fragment:
            errors.append(f"URL must not have query/fragment: {entry.url}")

        for blocked in BLOCKED_HOSTS:
            if blocked in entry.url:
                errors.append(f"Blocked host in corpus URL: {entry.url}")

        slug = _slug_from_groww_url(entry.url)
        if slug not in KNOWN_SLUGS:
            errors.append(f"Unknown Groww slug: {slug}")

        if entry.scheme_id not in scheme_by_id:
            errors.append(f"scheme_id '{entry.scheme_id}' missing from schemes.json")
            continue

        scheme = scheme_by_id[entry.scheme_id]
        if _normalize_url(scheme.groww_url) != normalized:
            errors.append(
                f"URL mismatch for {entry.scheme_id}: "
                f"manifest={entry.url} schemes={scheme.groww_url}"
            )

    manifest_ids = {e.scheme_id for e in manifest.allowed_urls}
    for scheme in schemes.schemes:
        if scheme.id not in manifest_ids:
            errors.append(f"Scheme '{scheme.id}' in schemes.json but not in manifest")

    default_id = manifest.citation_rules.refusal_default_scheme_id
    if default_id not in scheme_by_id:
        errors.append(f"refusal_default_scheme_id invalid: {default_id}")

    return errors


def get_allowlisted_urls(manifest: Manifest | None = None) -> frozenset[str]:
    manifest = manifest or load_manifest()
    return frozenset(_normalize_url(e.url) for e in manifest.allowed_urls)


def get_scheme_by_id(scheme_id: str, schemes: SchemesRegistry | None = None) -> Scheme | None:
    schemes = schemes or load_schemes()
    for s in schemes.schemes:
        if s.id == scheme_id:
            return s
    return None


def get_default_refusal_url(manifest: Manifest | None = None, schemes: SchemesRegistry | None = None) -> str:
    manifest = manifest or load_manifest()
    schemes = schemes or load_schemes()
    scheme = get_scheme_by_id(manifest.citation_rules.refusal_default_scheme_id, schemes)
    if scheme is None:
        raise ValueError("Default refusal scheme not found")
    return scheme.groww_url


def is_url_allowlisted(url: str, manifest: Manifest | None = None) -> bool:
    return _normalize_url(url) in get_allowlisted_urls(manifest)
