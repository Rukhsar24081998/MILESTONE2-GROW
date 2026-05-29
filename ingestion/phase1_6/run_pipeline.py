#!/usr/bin/env python3
"""CLI: Phase 1.6 — Run ingestion steps end-to-end."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import app.config
from app.corpus import load_manifest
from ingestion.phase1_1.fetcher import AllowlistRejectedError, FetchError, fetch_one
from ingestion.phase1_2.parser import parse_one, save_parsed
from ingestion.phase1_3.chunker import chunk_one, save_chunks
from ingestion.phase1_4.indexer import (
    DEFAULT_COLLECTION_NAME,
    get_chroma_client,
    get_or_create_collection,
    index_chunks_for_scheme,
)
from ingestion.phase1_5.metadata import write_last_updated


logger = logging.getLogger(__name__)


STEPS = ("fetch", "parse", "chunk", "index", "metadata", "all")


def _scheme_ids_from_manifest(manifest) -> list[str]:
    return [e.scheme_id for e in manifest.allowed_urls]


def _run_fetch(manifest, *, force: bool) -> dict[str, str]:
    errors: dict[str, str] = {}
    for entry in manifest.allowed_urls:
        try:
            fetch_one(entry.scheme_id, entry.url, force=force)
        except (AllowlistRejectedError, FetchError) as exc:
            errors[entry.scheme_id] = str(exc)
            logger.error("%s", exc)
        except Exception as exc:
            errors[entry.scheme_id] = str(exc)
            logger.exception("Unexpected fetch error for %s", entry.scheme_id)
    return errors


def _run_parse(manifest, *, scheme_ids: list[str] | None) -> dict[str, str]:
    errors: dict[str, str] = {}
    target_ids = scheme_ids or _scheme_ids_from_manifest(manifest)
    for sid in target_ids:
        try:
            doc = parse_one(sid)
            save_parsed(doc)
        except Exception as exc:
            errors[sid] = str(exc)
            logger.error("Parse failed for %s: %s", sid, exc)
    return errors


def _run_chunk(manifest, *, scheme_ids: list[str] | None) -> dict[str, str]:
    errors: dict[str, str] = {}
    target_ids = scheme_ids or _scheme_ids_from_manifest(manifest)
    parsed_dir = app.config.PROJECT_ROOT / "ingestion" / "parsed"
    for sid in target_ids:
        try:
            parsed_path = parsed_dir / f"{sid}.json"
            chunks = chunk_one(parsed_path)
            save_chunks(chunks, sid)
        except Exception as exc:
            errors[sid] = str(exc)
            logger.error("Chunking failed for %s: %s", sid, exc)
    return errors


def _run_index(
    manifest,
    *,
    scheme_ids: list[str] | None,
    collection_name: str,
    chunks_dir: Path | None,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    target_ids = scheme_ids or _scheme_ids_from_manifest(manifest)

    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)

    chunks_dir = chunks_dir or (app.config.PROJECT_ROOT / "ingestion" / "chunks")
    for sid in target_ids:
        try:
            index_chunks_for_scheme(sid, collection, chunks_dir)
        except Exception as exc:
            errors[sid] = str(exc)
            logger.error("Indexing failed for %s: %s", sid, exc)
    return errors


def _run_metadata() -> str | None:
    try:
        write_last_updated()
        return None
    except Exception as exc:
        logger.error("Metadata step failed: %s", exc)
        return str(exc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 1.6: Orchestrate ingestion steps (fetch/parse/chunk/index/metadata).",
    )
    parser.add_argument(
        "--step",
        default="all",
        choices=STEPS,
        help="Which step to run (default: all)",
    )
    parser.add_argument(
        "--scheme-id",
        help="Limit run to a single scheme_id from manifest (not used for metadata)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetch during fetch step",
    )
    parser.add_argument(
        "--collection-name",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Chroma collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    manifest = load_manifest()

    scheme_ids: list[str] | None = None
    if args.scheme_id:
        allowed = {e.scheme_id for e in manifest.allowed_urls}
        if args.scheme_id not in allowed:
            parser.error(f"scheme_id not in manifest: {args.scheme_id}")
        scheme_ids = [args.scheme_id]

    step = args.step

    errors: dict[str, dict[str, str] | str] = {}

    if step in ("fetch", "all"):
        errors["fetch"] = _run_fetch(manifest, force=args.force)
    if step in ("parse", "all"):
        errors["parse"] = _run_parse(manifest, scheme_ids=scheme_ids)
    if step in ("chunk", "all"):
        errors["chunk"] = _run_chunk(manifest, scheme_ids=scheme_ids)
    if step in ("index", "all"):
        errors["index"] = _run_index(
            manifest,
            scheme_ids=scheme_ids,
            collection_name=args.collection_name,
            chunks_dir=None,
        )
    if step in ("metadata", "all"):
        meta_error = _run_metadata()
        errors["metadata"] = meta_error or ""

    any_fail = False
    print("\nPhase 1.6 pipeline summary")
    for k in ("fetch", "parse", "chunk", "index"):
        if k not in errors:
            continue
        step_errors = errors[k]
        if isinstance(step_errors, dict) and step_errors:
            any_fail = True
            print(f"  - {k}: failed schemes={len(step_errors)}")
            for sid, msg in sorted(step_errors.items()):
                print(f"      {sid}: {msg}")
        else:
            print(f"  - {k}: ok")

    if "metadata" in errors:
        if errors["metadata"]:
            any_fail = True
            print(f"  - metadata: {errors['metadata']}")
        else:
            print("  - metadata: ok")

    if any_fail:
        print("\nWARNING: Phase 1.6 completed with failures.")
        return 1

    print("\nOK: Phase 1.6 pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

