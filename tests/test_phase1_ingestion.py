"""Phase 1.6 tests — Pipeline orchestration and smoke retrieval."""

from __future__ import annotations

import pytest

from ingestion.phase1_6.smoke_retrieval import DEFAULT_QUERIES, run_smoke
from ingestion.phase1_6.run_pipeline import STEPS


def test_smoke_queries_defined():
    """Test that smoke test queries cover all 5 schemes."""
    assert len(DEFAULT_QUERIES) == 5
    scheme_ids = {q[1] for q in DEFAULT_QUERIES}
    assert len(scheme_ids) == 5  # All unique


def test_pipeline_steps_defined():
    """Test that pipeline steps include all expected phases."""
    assert "fetch" in STEPS
    assert "parse" in STEPS
    assert "chunk" in STEPS
    assert "index" in STEPS
    assert "metadata" in STEPS
    assert "all" in STEPS


def test_smoke_retrieval_returns_results():
    """Test that smoke retrieval returns results with improved accuracy.
    
    After Phase 1.2 parser improvement:
    - 3/5 queries return exact scheme match (60%)
    - 2/5 'exit load' queries return Defence (has most detailed exit load section)
    - This is expected; perfect accuracy requires Phase 2 scheme detection
    """
    ok, failures = run_smoke(collection_name="hdfc_groww_corpus", n_results=3)
    
    # At least 60% should be correct (improved from 40%)
    assert len(failures) <= 2, f"Too many smoke query failures: {len(failures)}/5"


def test_smoke_queries_use_allowlisted_schemes():
    """Test that all smoke queries reference valid scheme IDs from manifest."""
    from app.corpus import load_manifest
    
    manifest = load_manifest()
    valid_scheme_ids = {e.scheme_id for e in manifest.allowed_urls}
    
    for query, scheme_id in DEFAULT_QUERIES:
        assert scheme_id in valid_scheme_ids, f"Smoke query '{query}' references invalid scheme: {scheme_id}"
