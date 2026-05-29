"""Phase 1.4 — Indexer for loading chunks into ChromaDB."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

import chromadb
import app.config
from app.corpus import load_manifest
from app.rag.embedder import get_embedding_function

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION_NAME = "hdfc_groww_corpus"


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client."""
    app.config.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(app.config.VECTOR_STORE_DIR))


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str = DEFAULT_COLLECTION_NAME
) -> chromadb.Collection:
    """Get or create the ChromaDB collection using the configured embedding function."""
    emb_fn = get_embedding_function()
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=emb_fn
    )


def index_chunks_for_scheme(
    scheme_id: str,
    collection: chromadb.Collection,
    chunks_dir: Path
) -> int:
    """Load JSONL chunks for a scheme and upsert them into the vector store.

    Returns the number of chunks successfully indexed.
    """
    jsonl_path = chunks_dir / f"{scheme_id}.jsonl"
    if not jsonl_path.exists():
        logger.error("Chunk file not found: %s", jsonl_path)
        raise FileNotFoundError(f"Chunk file not found: {jsonl_path}")

    ids = []
    documents = []
    metadatas = []

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)

            ids.append(data["chunk_id"])
            documents.append(data["text"])

            # Prepare metadata (filtering out None values to keep chromadb happy)
            meta = {
                "source_url": data["source_url"],
                "scheme_id": data["scheme_id"],
                "scheme_name": data["scheme_name"],
                "document_type": data["document_type"]
            }
            if data.get("page_section"):
                meta["page_section"] = data["page_section"]

            metadatas.append(meta)

    if not ids:
        logger.warning("No chunks found in %s", jsonl_path)
        return 0

    # Upsert to Chroma to ensure idempotency.
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    logger.info("Successfully upserted %d chunks for scheme '%s'", len(ids), scheme_id)
    return len(ids)


def index_all_schemes(
    scheme_ids: Iterable[str] | None = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    chunks_dir: Path | None = None
) -> dict[str, int]:
    """Index chunks for all schemes in the manifest (or a filtered list)."""
    from app.config import PROJECT_ROOT
    chunks_dir = chunks_dir or (PROJECT_ROOT / "ingestion" / "chunks")

    manifest = load_manifest()
    allowed_ids = [entry.scheme_id for entry in manifest.allowed_urls]

    target_ids = allowed_ids
    if scheme_ids is not None:
        target_ids = [sid for sid in allowed_ids if sid in scheme_ids]

    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)

    results = {}
    for sid in target_ids:
        count = index_chunks_for_scheme(sid, collection, chunks_dir)
        results[sid] = count

    return results
