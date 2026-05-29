#!/usr/bin/env python3
"""CLI: Phase 1.4 — Index chunks into Chroma vector database."""

from __future__ import annotations

import argparse
import logging
import sys
from app.corpus import load_manifest
from ingestion.phase1_4.indexer import DEFAULT_COLLECTION_NAME, index_all_schemes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.4: Index chunk files (ingestion/chunks/*.jsonl) into Chroma DB",
    )
    parser.add_argument(
        "--scheme-id",
        help="Index only this scheme_id from manifest",
    )
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Chroma collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    args = parser.parse_args(argv)

    scheme_ids: list[str] | None = None
    if args.scheme_id:
        manifest = load_manifest()
        ids = [e.scheme_id for e in manifest.allowed_urls]
        if args.scheme_id not in ids:
            parser.error(f"scheme_id not in manifest: {args.scheme_id}")
        scheme_ids = [args.scheme_id]

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    print(f"\nPhase 1.4: Starting chunk indexing into collection '{args.collection_name}'...")
    results = index_all_schemes(scheme_ids, collection_name=args.collection_name)

    print("\nPhase 1.4 Indexing Summary:")
    total = 0
    for sid, count in sorted(results.items()):
        print(f"  - {sid}: {count} chunks indexed")
        total += count
    print(f"  Total chunks indexed: {total}")
    print("\nOK: Phase 1.4 indexing complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
