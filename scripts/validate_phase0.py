#!/usr/bin/env python3
"""Validate Phase 0 corpus exit criteria."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.corpus.loader import (  # noqa: E402
    EXPECTED_URL_COUNT,
    get_allowlisted_urls,
    get_default_refusal_url,
    load_manifest,
    load_schemes,
    validate_corpus,
)


def main() -> int:
    print("Phase 0 corpus validation\n")
    manifest = load_manifest()
    schemes = load_schemes()

    print(f"  AMC: {schemes.amc_name} (metadata only: {schemes.amc_website})")
    print(f"  Corpus version: {manifest.corpus_version}")
    print(f"  Policy: {manifest.policy}")
    print(f"  Allowlisted URLs: {len(manifest.allowed_urls)} (expected {EXPECTED_URL_COUNT})")
    print(f"  Default refusal URL: {get_default_refusal_url()}\n")

    print("  Schemes:")
    for s in schemes.schemes:
        print(f"    - {s.name} [{s.category}]")
        print(f"      {s.groww_url}")

    errors = validate_corpus(manifest, schemes)
    if errors:
        print("\nFAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"\nOK: All {len(get_allowlisted_urls())} URLs validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
