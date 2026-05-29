#!/usr/bin/env python3
"""CLI: Phase 1.5 — Write corpus metadata artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from ingestion.phase1_5.metadata import run_phase1_5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.5: Generate corpus/last_updated.json and data/corpus_meta.db",
    )
    parser.add_argument(
        "--last-updated-path",
        type=Path,
        help="Override output path for last_updated.json",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Override output path for corpus_meta.db",
    )
    args = parser.parse_args(argv)

    run_phase1_5(last_updated_path=args.last_updated_path, db_path=args.db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

