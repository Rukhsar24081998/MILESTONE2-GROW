#!/usr/bin/env python3
"""CLI: fetch all five allowlisted Groww pages (Phase 1.1)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# repo root (…/Mileston2)
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestion.phase1_1.fetcher import (  # noqa: E402
    ALLOWLIST_REJECT,
    AllowlistRejectedError,
    FetchError,
    assert_url_allowlisted,
    count_raw_html_files,
    fetch_all_from_manifest,
)
from app.corpus.loader import EXPECTED_URL_COUNT, load_manifest  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.1: Fetch allowlisted Groww scheme pages into ingestion/raw/",
    )
    parser.add_argument(
        "--scheme-id",
        help="Fetch only this scheme_id from manifest",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if raw HTML already exists",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between requests (default: 1.0)",
    )
    parser.add_argument(
        "--test-reject",
        metavar="URL",
        help="Verify URL is rejected by allowlist (no HTTP); exits 0 if rejected",
    )
    args = parser.parse_args(argv)

    if args.test_reject:
        try:
            assert_url_allowlisted(args.test_reject)
            logger.error("Expected ALLOWLIST_REJECT but URL was allowed: %s", args.test_reject)
            return 1
        except AllowlistRejectedError as exc:
            logger.info("OK: %s", exc)
            assert exc.code == ALLOWLIST_REJECT
            return 0

    try:
        results = fetch_all_from_manifest(
            force=args.force,
            scheme_id=args.scheme_id,
            rate_limit_sec=args.rate_limit,
        )
    except (AllowlistRejectedError, FetchError, ValueError) as exc:
        logger.error("%s", exc)
        return 1

    fetched = sum(1 for r in results if not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    html_count = count_raw_html_files()

    print("\nPhase 1.1 fetch summary")
    print(f"  Processed: {len(results)} ({fetched} fetched, {skipped} skipped)")
    print(f"  Raw HTML files: {html_count} (expected {EXPECTED_URL_COUNT})")
    for r in results:
        status = "skipped" if r.skipped else "ok"
        print(f"  [{status}] {r.scheme_id} -> {r.html_path.name} ({r.content_length} bytes)")

    manifest = load_manifest()
    if html_count < len(manifest.allowed_urls):
        logger.warning(
            "Fewer HTML files than manifest entries. Re-run with --force or check failures."
        )
        return 1

    if html_count != EXPECTED_URL_COUNT:
        logger.warning("Expected exactly %s HTML files, found %s", EXPECTED_URL_COUNT, html_count)

    print("\nOK: Phase 1.1 fetch complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
