"""Phase 1.5 tests — last_updated.json + corpus metadata DB."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import app.config
from app.corpus import load_manifest
from ingestion.phase1_5.metadata import build_last_updated, write_corpus_metadata_db


def test_build_last_updated_has_entries_for_existing_raw_meta():
    manifest = load_manifest()
    payload = build_last_updated()
    assert payload["corpus_version"] == manifest.corpus_version

    schemes = payload["schemes"]
    assert isinstance(schemes, dict)

    for entry in manifest.allowed_urls:
        meta_path = app.config.INGESTION_RAW_DIR / f"{entry.scheme_id}.meta.json"
        if meta_path.exists():
            assert entry.scheme_id in schemes
            assert schemes[entry.scheme_id]["source_url"] == entry.url
            assert "fetched_at" in schemes[entry.scheme_id]


def test_write_corpus_metadata_db_creates_rows(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "corpus_meta.db"
    out = write_corpus_metadata_db(db_path=db_path)
    assert out.exists()

    manifest = load_manifest()
    with sqlite3.connect(str(out)) as conn:
        rows = conn.execute("SELECT scheme_id, source_url, chunk_count FROM documents").fetchall()
    assert len(rows) == len(manifest.allowed_urls)

    by_id = {r[0]: r for r in rows}
    for entry in manifest.allowed_urls:
        assert entry.scheme_id in by_id
        assert by_id[entry.scheme_id][1] == entry.url
        assert isinstance(by_id[entry.scheme_id][2], int)

