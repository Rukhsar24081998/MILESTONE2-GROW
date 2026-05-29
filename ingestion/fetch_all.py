#!/usr/bin/env python3
"""CLI: fetch all five allowlisted Groww pages (Phase 1.1)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Canonical CLI implementation lives here.
from ingestion.phase1_1.fetch_all import main  # noqa: E402,F401


if __name__ == "__main__":
    sys.exit(main())
