"""Phase 2 — Retrieval and context assembly tests.

Tests the scheme-aware hybrid retrieval strategy on 10-query golden set.
Exit criteria: ≥80% accuracy (≥8/10 queries return correct scheme in top-3).
"""

import json
from pathlib import Path

import pytest

from app.rag.scheme_detector import (
    detect_scheme,
    detect_scheme_with_confidence,
    validate_scheme_id,
    get_all_scheme_ids,
)
from app.rag.retriever import retrieve, RetrievalResponse
from app.rag.context_assembler import (
    assemble_context,
    get_citation_url,
    deduplicate_results,
    enforce_token_limit,
    estimate_tokens,
)


# Load golden queries
GOLDEN_QUERIES_PATH = Path(__file__).parent / "golden_queries.json"
with open(GOLDEN_QUERIES_PATH) as f:
    GOLDEN_QUERIES = json.load(f)


# ============================================================
# Scheme Detection Tests
# ============================================================

class TestSchemeDetection:
    """Test scheme detection from queries."""

    def test_detect_mid_cap(self):
        assert detect_scheme("expense ratio HDFC Mid Cap") == "hdfc-mid-cap-direct-growth"

    def test_detect_silver_etf(self):
        assert detect_scheme("exit load Silver ETF FoF") == "hdfc-silver-etf-fof-direct-growth"

    def test_detect_small_cap(self):
        assert detect_scheme("minimum SIP Small Cap") == "hdfc-small-cap-direct-growth"

    def test_detect_defence(self):
        assert detect_scheme("benchmark Defence fund") == "hdfc-defence-direct-growth"

    def test_detect_flexi_cap(self):
        assert detect_scheme("exit load Flexi Cap") == "hdfc-flexi-cap-direct-growth"

    def test_no_scheme_detected(self):
        # Generic query without scheme mention
        assert detect_scheme("what is expense ratio") is None

    def test_detect_with_confidence(self):
        scheme, confidence = detect_scheme_with_confidence("HDFC Mid Cap expense ratio")
        assert scheme == "hdfc-mid-cap-direct-growth"
        assert confidence > 0.3  # At least some confidence for single keyword match

    def test_validate_scheme_id(self):
        assert validate_scheme_id("hdfc-mid-cap-direct-growth") is True
        assert validate_scheme_id("invalid-scheme") is False

    def test_get_all_scheme_ids(self):
        scheme_ids = get_all_scheme_ids()
        assert len(scheme_ids) == 5
        assert "hdfc-mid-cap-direct-growth" in scheme_ids


# ============================================================
# Retrieval Tests
# ============================================================

class TestRetrieval:
    """Test scheme-aware retrieval on golden queries."""

    @pytest.mark.parametrize("golden", GOLDEN_QUERIES, ids=[q["query"] for q in GOLDEN_QUERIES])
    def test_scheme_detection_accuracy(self, golden):
        """Test that scheme detection works for all golden queries."""
        query = golden["query"]
        expected_scheme = golden["expected_scheme"]
        
        detected = detect_scheme(query)
        assert detected == expected_scheme, (
            f"Query '{query}': expected {expected_scheme}, got {detected}"
        )

    @pytest.mark.parametrize("golden", GOLDEN_QUERIES, ids=[q["query"] for q in GOLDEN_QUERIES])
    def test_retrieval_returns_correct_scheme(self, golden):
        """Test that top result is from expected scheme."""
        query = golden["query"]
        expected_scheme = golden["expected_scheme"]
        
        response = retrieve(query, top_k=3)
        
        # Should detect scheme
        assert response.detected_scheme == expected_scheme, (
            f"Query '{query}': scheme detection failed"
        )
        
        # Should return results
        assert response.total_retrieved > 0, f"Query '{query}': no results returned"
        
        # Top result should be from correct scheme
        top_result = response.results[0]
        assert top_result.scheme_id == expected_scheme, (
            f"Query '{query}': top result is from {top_result.scheme_id}, expected {expected_scheme}"
        )

    def test_retrieval_with_scheme_filter(self):
        """Test that scheme filter restricts results."""
        response = retrieve("expense ratio", top_k=5, detect_scheme_flag=False)
        
        # Without scheme detection, results may be from any scheme
        assert response.total_retrieved > 0
        assert response.detected_scheme is None

    def test_retrieval_without_scheme_filter(self):
        """Test fallback to unfiltered search."""
        response = retrieve("what is mutual fund", top_k=5, detect_scheme_flag=False)
        assert response.total_retrieved > 0


# ============================================================
# Golden Set Accuracy Test
# ============================================================

class TestGoldenSetAccuracy:
    """Test overall golden set accuracy (exit criteria: ≥80%)."""

    def test_golden_set_accuracy(self):
        """Test that ≥80% of golden queries return correct scheme in top-3."""
        correct = 0
        total = len(GOLDEN_QUERIES)
        failures = []
        
        for golden in GOLDEN_QUERIES:
            query = golden["query"]
            expected_scheme = golden["expected_scheme"]
            
            response = retrieve(query, top_k=3)
            
            # Check if any of top-3 results is from correct scheme
            is_correct = any(
                r.scheme_id == expected_scheme 
                for r in response.results[:3]
            )
            
            if is_correct:
                correct += 1
            else:
                failures.append({
                    "query": query,
                    "expected": expected_scheme,
                    "detected": response.detected_scheme,
                    "top_scheme": response.results[0].scheme_id if response.results else None,
                })
        
        accuracy = correct / total
        
        # Print detailed failures for debugging
        if failures:
            print(f"\n\n{'='*70}")
            print(f"GOLDEN SET ACCURACY: {correct}/{total} ({accuracy:.0%})")
            print(f"{'='*70}")
            for f in failures:
                print(f"❌ {f['query']}")
                print(f"   Expected: {f['expected']}")
                print(f"   Detected: {f['detected']}")
                print(f"   Top result: {f['top_scheme']}")
            print(f"{'='*70}\n")
        
        assert accuracy >= 0.8, (
            f"Golden set accuracy {accuracy:.0%} < 80% threshold. "
            f"{len(failures)}/{total} queries failed."
        )


# ============================================================
# Context Assembly Tests
# ============================================================

class TestContextAssembly:
    """Test context building and formatting."""

    def test_estimate_tokens(self):
        assert estimate_tokens("hello world") > 0
        # Rough estimate: ~2 tokens for 11 chars
        assert estimate_tokens("hello world") >= 1

    def test_deduplicate_results(self, sample_response):
        """Test deduplication removes duplicate chunk_ids."""
        results = sample_response.results
        
        # Add a duplicate
        from app.rag.retriever import RetrievalResult
        duplicate = results[0]
        results_with_dup = results + [duplicate]
        
        deduped = deduplicate_results(results_with_dup)
        assert len(deduped) == len(results)

    def test_enforce_token_limit(self, sample_response):
        """Test token limit enforcement."""
        results = sample_response.results
        
        # Very low limit should reduce results
        limited = enforce_token_limit(results, max_tokens=100)
        assert len(limited) <= len(results)

    def test_assemble_context(self, sample_response):
        """Test full context assembly pipeline."""
        context = assemble_context(sample_response)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "Query:" in context

    def test_get_citation_url(self, sample_response):
        """Test citation URL extraction."""
        url = get_citation_url(sample_response)
        assert url is not None
        assert "groww.in" in url


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_response():
    """Create a sample RetrievalResponse for testing."""
    from app.rag.retriever import RetrievalResult, RetrievalResponse
    
    return RetrievalResponse(
        query="test query",
        detected_scheme="hdfc-mid-cap-direct-growth",
        results=[
            RetrievalResult(
                chunk_id="chunk_1",
                text="Expense ratio is 0.73% for HDFC Mid Cap Fund.",
                source_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
                scheme_id="hdfc-mid-cap-direct-growth",
                score=0.85,
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                text="Minimum SIP is ₹100 for this fund.",
                source_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
                scheme_id="hdfc-mid-cap-direct-growth",
                score=0.75,
            ),
        ],
        total_retrieved=2,
    )
