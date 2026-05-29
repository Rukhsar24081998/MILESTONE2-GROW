#!/usr/bin/env python3
"""Backward-compatible entrypoint for Phase 1.4 indexer CLI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.phase1_4.index_chunks import main  # noqa: E402,F401


if __name__ == "__main__":
    raise SystemExit(main())
