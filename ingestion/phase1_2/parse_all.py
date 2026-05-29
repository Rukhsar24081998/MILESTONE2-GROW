#!/usr/bin/env python3
"""CLI: Phase 1.2 — parse and normalize raw HTML into parsed JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.corpus import load_manifest
from ingestion.phase1_2.parser import PARSED_DIR, parse_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.2: Parse raw HTML (ingestion/raw) into parsed JSON (ingestion/parsed)",
    )
    parser.add_argument(
        "--scheme-id",
        help="Parse only this scheme_id from manifest",
    )
    args = parser.parse_args(argv)

    scheme_ids: list[str] | None = None
    if args.scheme_id:
        manifest = load_manifest()
        ids = [e.scheme_id for e in manifest.allowed_urls]
        if args.scheme_id not in ids:
            parser.error(f"scheme_id not in manifest: {args.scheme_id}")
        scheme_ids = [args.scheme_id]

    docs = parse_all(scheme_ids)
    print("\nPhase 1.2 parse summary")
    print(f"  Parsed documents: {len(docs)}")
    print(f"  Output dir: {PARSED_DIR}")
    for d in docs:
        print(f"  - {d.scheme_id}: length={d.text_length} quality={d.quality}")

    # Basic exit check: expect same count as manifest allowlist when no filter
    if not args.scheme_id:
        manifest = load_manifest()
        if len(docs) != len(manifest.allowed_urls):
            print(
                f"WARNING: Parsed {len(docs)} docs, but manifest has "
                f"{len(manifest.allowed_urls)} URLs.",
                file=sys.stderr,
            )

    print("\nOK: Phase 1.2 parse complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

