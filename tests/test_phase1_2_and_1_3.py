"""Phase 1.2 & 1.3 tests — parsed docs and chunks."""

from __future__ import annotations

import json
from pathlib import Path

from app.corpus import load_manifest, load_schemes
from ingestion.phase1_2.parser import PARSED_DIR, parse_all
from ingestion.phase1_3.chunker import CHUNKS_DIR, chunk_all


def test_phase1_2_parsed_files_exist_and_have_text(tmp_path: Path, monkeypatch):
    # Run parse_all against real raw HTML (ingestion/raw)
    docs = parse_all()
    manifest = load_manifest()
    assert len(docs) == len(manifest.allowed_urls) == 5

    for d in docs:
        path = PARSED_DIR / f"{d.scheme_id}.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["scheme_id"] == d.scheme_id
        assert isinstance(data["text"], str)
        assert data["text_length"] == len(data["text"])
        # Require some non-empty text; quality may be low but not empty.
        assert data["text_length"] > 0


def test_phase1_3_chunks_have_provenance_and_allowlisted_urls():
    # Use parsed docs from previous test; chunk_all should succeed.
    chunks = chunk_all()
    manifest = load_manifest()
    schemes = load_schemes()
    allowlisted_urls = {e.url for e in manifest.allowed_urls}
    scheme_ids = {e.scheme_id for e in manifest.allowed_urls}
    scheme_names = {s.name for s in schemes.schemes}

    assert chunks, "Expected at least one chunk overall"

    by_scheme: dict[str, int] = {}
    for ch in chunks:
        assert ch.scheme_id in scheme_ids
        assert ch.scheme_name in scheme_names
        assert ch.source_url in allowlisted_urls
        assert ch.document_type == "groww_scheme_page"
        assert ch.text.strip()
        by_scheme[ch.scheme_id] = by_scheme.get(ch.scheme_id, 0) + 1

    # Every allowlisted scheme should have at least one chunk.
    for sid in scheme_ids:
        assert by_scheme.get(sid, 0) >= 1

    # Verify files exist
    for sid in scheme_ids:
        path = CHUNKS_DIR / f"{sid}.jsonl"
        assert path.exists()

