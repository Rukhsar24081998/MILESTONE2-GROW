#!/usr/bin/env python3
"""Backward-compatible entrypoint for Phase 1.2 parser CLI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.phase1_2.parse_all import main  # noqa: E402,F401


if __name__ == "__main__":
    raise SystemExit(main())

