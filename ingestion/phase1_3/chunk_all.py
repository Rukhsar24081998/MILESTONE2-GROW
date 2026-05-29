#!/usr/bin/env python3
"""CLI: Phase 1.3 — chunk parsed docs with provenance into JSONL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ingestion.phase1_3.chunker import CHUNKS_DIR, chunk_all
from app.corpus import load_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.3: Chunk parsed docs into ingestion/chunks/*.jsonl",
    )
    parser.add_argument(
        "--scheme-id",
        help="Chunk only this scheme_id from manifest",
    )
    args = parser.parse_args(argv)

    scheme_ids: list[str] | None = None
    if args.scheme_id:
        manifest = load_manifest()
        ids = [e.scheme_id for e in manifest.allowed_urls]
        if args.scheme_id not in ids:
            parser.error(f"scheme_id not in manifest: {args.scheme_id}")
        scheme_ids = [args.scheme_id]

    chunks = chunk_all(scheme_ids)
    print("\nPhase 1.3 chunk summary")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Output dir: {CHUNKS_DIR}")

    # Per-scheme stats
    per_scheme: dict[str, int] = {}
    for ch in chunks:
        per_scheme[ch.scheme_id] = per_scheme.get(ch.scheme_id, 0) + 1
    for sid, count in sorted(per_scheme.items()):
        print(f"  - {sid}: {count} chunks")

    print("\nOK: Phase 1.3 chunking complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

