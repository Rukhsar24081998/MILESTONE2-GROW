#!/usr/bin/env python3
"""CLI: Phase 1.6 — Smoke test retrieval over the Chroma index."""

from __future__ import annotations

import argparse
import logging
import sys

import app.config
from app.corpus import load_manifest
from ingestion.phase1_4.indexer import DEFAULT_COLLECTION_NAME, get_chroma_client, get_or_create_collection


logger = logging.getLogger(__name__)


DEFAULT_QUERIES = [
    ("expense ratio HDFC Mid Cap", "hdfc-mid-cap-direct-growth"),
    ("exit load Silver ETF FoF", "hdfc-silver-etf-fof-direct-growth"),
    ("minimum SIP Small Cap", "hdfc-small-cap-direct-growth"),
    ("benchmark Defence fund", "hdfc-defence-direct-growth"),
    ("exit load Flexi Cap", "hdfc-flexi-cap-direct-growth"),
]


def run_smoke(*, collection_name: str, n_results: int) -> tuple[bool, list[str]]:
    manifest = load_manifest()
    allowlisted_urls = {e.url for e in manifest.allowed_urls}
    scheme_to_url = {e.scheme_id: e.url for e in manifest.allowed_urls}

    if not app.config.VECTOR_STORE_DIR.exists():
        return False, [f"Vector store not found at {app.config.VECTOR_STORE_DIR}. Run Phase 1.4 indexing first."]

    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    if collection.count() == 0:
        return False, [f"Collection '{collection_name}' is empty. Run Phase 1.4 indexing first."]

    failures: list[str] = []

    for query, expected_scheme_id in DEFAULT_QUERIES:
        res = collection.query(query_texts=[query], n_results=n_results)
        ids = res.get("ids", [[]])[0] or []
        metadatas = res.get("metadatas", [[]])[0] or []
        docs = res.get("documents", [[]])[0] or []

        if not ids:
            failures.append(f"Query returned no results: {query}")
            continue

        top_url = (metadatas[0] or {}).get("source_url")
        if top_url not in allowlisted_urls:
            failures.append(f"Top result not allowlisted for query '{query}': {top_url}")
            continue

        expected_url = scheme_to_url.get(expected_scheme_id)
        if expected_url and top_url != expected_url:
            failures.append(
                f"Top URL mismatch for query '{query}': expected {expected_url}, got {top_url}"
            )

        preview = (docs[0] or "").replace("\n", " ")[:160]
        print(f"\nQuery: {query}")
        print(f"Top URL: {top_url}")
        print(f"Top chunk: {preview}...")

    return len(failures) == 0, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1.6: Smoke test retrieval over the Chroma index.")
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Chroma collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=3,
        help="Number of nearest chunks to retrieve (default: 3)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    ok, failures = run_smoke(collection_name=args.collection_name, n_results=args.n_results)
    if ok:
        print("\nOK: Smoke retrieval passed.")
        return 0

    print("\nFAILED: Smoke retrieval failed.", file=sys.stderr)
    for msg in failures:
        print(f"  - {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

