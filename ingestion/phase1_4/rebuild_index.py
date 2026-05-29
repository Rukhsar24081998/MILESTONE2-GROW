#!/usr/bin/env python3
"""CLI: Phase 1.4 — Rebuild the Chroma collection by resetting it."""

from __future__ import annotations

import argparse
import logging
import sys
from ingestion.phase1_4.indexer import (
    DEFAULT_COLLECTION_NAME,
    get_chroma_client,
    index_all_schemes,
)

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.4: Rebuild vector index from scratch",
    )
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Chroma collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    client = get_chroma_client()

    print(f"\nPhase 1.4: Resetting index for collection '{args.collection_name}'...")
    try:
        client.delete_collection(name=args.collection_name)
        print(f"  Deleted existing collection '{args.collection_name}'.")
    except Exception:
        # Collection does not exist.
        print(f"  Collection '{args.collection_name}' does not exist or could not be deleted; proceeding.")
        pass

    results = index_all_schemes(collection_name=args.collection_name)

    print("\nPhase 1.4 Rebuild Summary:")
    total = 0
    for sid, count in sorted(results.items()):
        print(f"  - {sid}: {count} chunks indexed")
        total += count
    print(f"  Total chunks indexed: {total}")
    print("\nOK: Rebuild complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
