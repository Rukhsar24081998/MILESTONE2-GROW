"""Tests for Phase 1.4 vector store indexing and embeddings."""

from __future__ import annotations

from pathlib import Path
import pytest

import app.config
from app.rag.embedder import get_embedding_function
from ingestion.phase1_4.indexer import (
    get_chroma_client,
    get_or_create_collection,
    index_all_schemes,
)


def test_embedder_factory(monkeypatch):
    """Test that the embedder factory loads the BGE model correctly."""
    monkeypatch.setattr(app.config, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    emb_fn = get_embedding_function()
    assert emb_fn is not None
    assert hasattr(emb_fn, "__call__")


def test_indexing_idempotency_and_query(tmp_path, monkeypatch):
    """Test that indexing is idempotent and semantic search queries work."""
    # Isolate vector database to tmp directory
    monkeypatch.setattr(app.config, "VECTOR_STORE_DIR", tmp_path / "chroma")
    monkeypatch.setattr(app.config, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    collection_name = "test_collection_pytest"

    # Index all schemes
    results = index_all_schemes(collection_name=collection_name)
    assert len(results) == 5, "Expected all 5 schemes from manifest to be indexed"
    
    total_indexed = sum(results.values())
    assert total_indexed > 0, "Expected at least one chunk to be indexed overall"

    # Fetch collection and check count
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    assert collection.count() == total_indexed, "Chroma count should match total indexed chunks"

    # Verify Idempotency: re-running should not increase count
    results_rerun = index_all_schemes(collection_name=collection_name)
    assert sum(results_rerun.values()) == total_indexed
    assert collection.count() == total_indexed, "Chroma count should remain identical after rerun"

    # Check metadata fields of peeked items
    peek_res = collection.peek(limit=5)
    assert len(peek_res["ids"]) > 0
    for meta in peek_res["metadatas"]:
        assert "source_url" in meta
        assert "scheme_id" in meta
        assert "scheme_name" in meta
        assert "document_type" in meta

    # Run a similarity query and assert results
    query_res = collection.query(
        query_texts=["expense ratio HDFC Mid Cap"],
        n_results=3
    )
    assert len(query_res["ids"]) == 1
    assert len(query_res["ids"][0]) > 0
    
    # Verify details are correct on top hit
    top_meta = query_res["metadatas"][0][0]
    assert "source_url" in top_meta
    assert "scheme_id" in top_meta
