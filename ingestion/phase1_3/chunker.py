"""Phase 1.3 — Chunking with provenance."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from app.config import PROJECT_ROOT
from app.corpus import load_manifest, load_schemes
from app.corpus.loader import _normalize_url, get_allowlisted_urls

PARSED_DIR = PROJECT_ROOT / "ingestion" / "parsed"
CHUNKS_DIR = PROJECT_ROOT / "ingestion" / "chunks"

CHUNK_SIZE = 1200  # characters
CHUNK_OVERLAP = 200  # characters
MAX_CHUNKS_PER_DOC = 150


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_url: str
    scheme_id: str
    scheme_name: str
    document_type: str
    page_section: str | None = None


def _load_parsed_doc(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sliding_window_chunks(text: str, size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >=0 and < size")

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length and len(chunks) < MAX_CHUNKS_PER_DOC:
        end = min(start + size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap
    return chunks


def chunk_one(parsed_path: Path) -> list[Chunk]:
    data = _load_parsed_doc(parsed_path)
    scheme_id = data["scheme_id"]
    scheme_name = data["scheme_name"]
    source_url = _normalize_url(data["source_url"])

    # Ensure provenance URL is in allowlist.
    allowlisted = get_allowlisted_urls()
    if source_url not in allowlisted:
        raise ValueError(f"Parsed doc has non-allowlisted source_url: {source_url}")

    text = data["text"]
    raw_chunks = _sliding_window_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)

    # Deduplicate exact text chunks per document.
    seen: set[str] = set()
    result: list[Chunk] = []
    for idx, ch in enumerate(raw_chunks):
        if ch in seen:
            continue
        seen.add(ch)
        cid = f"{scheme_id}-{idx:04d}-{uuid.uuid4().hex[:8]}"
        result.append(
            Chunk(
                chunk_id=cid,
                text=ch,
                source_url=source_url,
                scheme_id=scheme_id,
                scheme_name=scheme_name,
                document_type="groww_scheme_page",
                page_section=None,
            )
        )
    return result


def save_chunks(chunks: Iterable[Chunk], scheme_id: str, directory: Path | None = None) -> Path:
    directory = directory or CHUNKS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scheme_id}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for ch in chunks:
            f.write(json.dumps(asdict(ch), ensure_ascii=False) + "\n")
    return path


def chunk_all(scheme_ids: Iterable[str] | None = None) -> list[Chunk]:
    manifest = load_manifest()
    schemes = load_schemes()
    id_to_name = {s.id: s.name for s in schemes.schemes}

    all_ids = [e.scheme_id for e in manifest.allowed_urls]
    if scheme_ids is not None:
        all_ids = [i for i in all_ids if i in scheme_ids]

    chunks: list[Chunk] = []
    for sid in all_ids:
        parsed_path = PARSED_DIR / f"{sid}.json"
        if not parsed_path.exists():
            raise FileNotFoundError(f"Parsed file missing for {sid}: {parsed_path}")
        doc_chunks = chunk_one(parsed_path)
        # Ensure scheme_name comes from schemes.json if needed.
        for ch in doc_chunks:
            ch.scheme_name = id_to_name.get(ch.scheme_id, ch.scheme_name)
        save_chunks(doc_chunks, sid)
        chunks.extend(doc_chunks)
    return chunks

