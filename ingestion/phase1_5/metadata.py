"""Phase 1.5 — Corpus metadata and footer dates."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import app.config
from app.corpus import load_manifest


def _read_raw_meta(raw_dir: Path, scheme_id: str) -> dict:
    path = raw_dir / f"{scheme_id}.meta.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _read_parsed_doc(parsed_dir: Path, scheme_id: str) -> dict | None:
    path = parsed_dir / f"{scheme_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _count_chunks(chunks_dir: Path, scheme_id: str) -> int:
    path = chunks_dir / f"{scheme_id}.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _parse_iso_date(date_str: str) -> datetime:
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)


def build_last_updated(*, raw_dir: Path | None = None) -> dict:
    raw_dir = raw_dir or app.config.INGESTION_RAW_DIR
    manifest = load_manifest()

    schemes: dict[str, dict] = {}
    latest_dt: datetime | None = None

    for entry in manifest.allowed_urls:
        meta_path = raw_dir / f"{entry.scheme_id}.meta.json"
        if not meta_path.exists():
            continue

        meta = _read_raw_meta(raw_dir, entry.scheme_id)
        fetched_at = meta.get("fetched_at")
        if not fetched_at:
            continue

        dt = _parse_iso_date(fetched_at)
        latest_dt = dt if latest_dt is None else max(latest_dt, dt)

        schemes[entry.scheme_id] = {
            "source_url": entry.url,
            "fetched_at": fetched_at,
        }

    payload = {
        "corpus_version": manifest.corpus_version,
        "note": "Populated after Phase 1 ingestion. Footer dates use per-scheme or max(fetched_at).",
        "latest_fetched_at": latest_dt.isoformat().replace("+00:00", "Z") if latest_dt else None,
        "schemes": schemes,
    }
    return payload


def write_last_updated(*, output_path: Path | None = None, raw_dir: Path | None = None) -> Path:
    output_path = output_path or app.config.LAST_UPDATED_PATH
    payload = build_last_updated(raw_dir=raw_dir)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def write_corpus_metadata_db(
    *,
    db_path: Path | None = None,
    raw_dir: Path | None = None,
    parsed_dir: Path | None = None,
    chunks_dir: Path | None = None,
) -> Path:
    db_path = db_path or (app.config.INGESTION_DATA_DIR / "corpus_meta.db")
    raw_dir = raw_dir or app.config.INGESTION_RAW_DIR
    parsed_dir = parsed_dir or (app.config.PROJECT_ROOT / "ingestion" / "parsed")
    chunks_dir = chunks_dir or (app.config.PROJECT_ROOT / "ingestion" / "chunks")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                scheme_id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                fetched_at TEXT,
                chunk_count INTEGER NOT NULL,
                quality TEXT,
                text_length INTEGER
            )
            """
        )

        for entry in manifest.allowed_urls:
            meta_path = raw_dir / f"{entry.scheme_id}.meta.json"
            fetched_at: str | None = None
            if meta_path.exists():
                fetched_at = _read_raw_meta(raw_dir, entry.scheme_id).get("fetched_at")

            parsed = _read_parsed_doc(parsed_dir, entry.scheme_id)
            quality = parsed.get("quality") if parsed else None
            text_length = parsed.get("text_length") if parsed else None
            chunk_count = _count_chunks(chunks_dir, entry.scheme_id)

            conn.execute(
                """
                INSERT INTO documents (scheme_id, source_url, fetched_at, chunk_count, quality, text_length)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scheme_id) DO UPDATE SET
                    source_url=excluded.source_url,
                    fetched_at=excluded.fetched_at,
                    chunk_count=excluded.chunk_count,
                    quality=excluded.quality,
                    text_length=excluded.text_length
                """,
                (entry.scheme_id, entry.url, fetched_at, chunk_count, quality, text_length),
            )

        conn.commit()

    return db_path


def run_phase1_5(
    *,
    last_updated_path: Path | None = None,
    db_path: Path | None = None,
) -> tuple[Path, Path]:
    last_updated_out = write_last_updated(output_path=last_updated_path)
    db_out = write_corpus_metadata_db(db_path=db_path)
    return last_updated_out, db_out
