"""Phase 3 — Guardrails and response generation tests.

Exit criteria:
- 100% of factual queries answered with exactly 1 URL
- 100% of refusal queries refused with NO URL (citation_url: null)
- 100% of PII queries refused with NO URL
- All responses include footer date
- Answer responses ≤3 sentences
"""

import pytest

from app.guardrails.classifier import classify_query, QueryCategory
from app.guardrails.pii_filter import detect_pii, contains_pii
from app.guardrails.refusal import create_refusal_response
from app.guardrails.validator import (
    validate_response,
    count_sentences,
    count_urls,
    contains_banned_phrases,
)
from app.guardrails.generator import process_query, _extract_exit_load_answer
from app.rag.llm import HAS_GROQ


# ============================================================
# Golden Queries
# ============================================================

FACTUAL_QUERIES = [
    ("expense ratio HDFC Mid Cap", "hdfc-mid-cap-direct-growth"),
    ("exit load Silver ETF FoF", "hdfc-silver-etf-fof-direct-growth"),
    ("minimum SIP Small Cap", "hdfc-small-cap-direct-growth"),
    ("benchmark Defence fund", "hdfc-defence-direct-growth"),
    ("exit load Flexi Cap", "hdfc-flexi-cap-direct-growth"),
]

ADVISORY_QUERIES = [
    "Should I invest in HDFC Mid Cap Fund?",
    "Which fund is better, HDFC Defence or HDFC Small Cap?",
    "What returns will I get next year from HDFC Silver ETF?",
    "Can you recommend a good mutual fund?",
    "Is HDFC Mid Cap a good investment?",
]

PII_QUERIES = [
    "My PAN is ABCDE1234F, check my investment",
    "My Aadhaar is 1234 5678 9012, find my account",
    "My phone number is 9876543210, login to my portfolio",
    "My email is user@example.com, send my statement",
    "My account number is 1234567890123, check balance",
]

OUT_OF_SCOPE_QUERIES = [
    "What is the weather today?",
    "Tell me a joke",
    "How to cook pasta?",
    "What are stock market tips for intraday?",
]

NON_HDFC_FACTUAL_QUERIES = [
    ("What is the expense ratio of Nippon India Large Cap?", "nippon-india-large-cap-direct-growth"),
    ("What is the exit load for Motilal Oswal Small Cap?", "motilal-oswal-small-cap-direct-growth"),
    ("What is the minimum SIP for Bajaj Finserv Flexi Cap?", "bajaj-finserv-flexi-cap-direct-growth"),
]


# ============================================================
# Classifier Tests
# ============================================================

class TestQueryClassifier:
    """Test query classification."""

    def test_factual_classification(self):
        for query, expected_scheme in FACTUAL_QUERIES:
            category, reason = classify_query(query)
            assert category == QueryCategory.FACTUAL, (
                f"Query '{query}' should be FACTUAL, got {category}"
            )

    def test_advisory_classification(self):
        for query in ADVISORY_QUERIES:
            category, reason = classify_query(query)
            assert category == QueryCategory.ADVISORY, (
                f"Query '{query}' should be ADVISORY, got {category}"
            )

    def test_out_of_scope_classification(self):
        for query in OUT_OF_SCOPE_QUERIES:
            category, reason = classify_query(query)
            assert category == QueryCategory.OUT_OF_SCOPE, (
                f"Query '{query}' should be OUT_OF_SCOPE, got {category}"
            )

    def test_non_hdfc_factual_classification(self):
        for query, _ in NON_HDFC_FACTUAL_QUERIES:
            category, reason = classify_query(query)
            assert category == QueryCategory.FACTUAL, (
                f"Query '{query}' should be FACTUAL, got {category}"
            )


# ============================================================
# PII Filter Tests
# ============================================================

class TestPIIFilter:
    """Test PII detection."""

    def test_pan_detection(self):
        assert contains_pii("My PAN is ABCDE1234F") is True
        detection = detect_pii("My PAN is ABCDE1234F")
        assert detection.pii_type == "pan"

    def test_aadhaar_detection(self):
        assert contains_pii("My Aadhaar is 1234 5678 9012") is True
        detection = detect_pii("My Aadhaar is 1234 5678 9012")
        assert detection.pii_type == "aadhaar"

    def test_phone_detection(self):
        assert contains_pii("My phone is 9876543210") is True

    def test_email_detection(self):
        assert contains_pii("My email is user@example.com") is True

    def test_no_pii_in_factual_query(self):
        assert contains_pii("What is the expense ratio of HDFC Mid Cap?") is False


# ============================================================
# Response Validation Tests
# ============================================================

class TestResponseValidation:
    """Test response validation."""

    def test_valid_answer(self):
        response = {
            "type": "answer",
            "text": "The expense ratio is 0.73%. This is charged annually.",
            "citation_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "footer": "Last updated from sources: 2026-05-20",
            "refused": False,
        }
        is_valid, errors = validate_response(response)
        assert is_valid is True, f"Validation failed: {errors}"

    def test_answer_too_many_sentences(self):
        response = {
            "type": "answer",
            "text": "First sentence. Second sentence. Third sentence. Fourth sentence.",
            "citation_url": "https://groww.in/mutual-funds/test",
            "footer": "Last updated from sources: 2026-05-20",
            "refused": False,
        }
        is_valid, errors = validate_response(response)
        assert is_valid is False
        assert "Too many sentences" in errors[0]

    def test_answer_missing_url(self):
        response = {
            "type": "answer",
            "text": "The expense ratio is 0.73%.",
            "citation_url": None,
            "footer": "Last updated from sources: 2026-05-20",
            "refused": False,
        }
        is_valid, errors = validate_response(response)
        assert is_valid is False
        assert "must have citation_url" in errors[0]

    def test_valid_refusal_no_url(self):
        response = {
            "type": "refusal",
            "text": "I cannot provide investment advice.",
            "citation_url": None,
            "footer": "Last updated from sources: 2026-05-20",
            "refused": True,
            "reason": "advisory_query",
        }
        is_valid, errors = validate_response(response)
        assert is_valid is True, f"Validation failed: {errors}"

    def test_refusal_with_url_fails(self):
        response = {
            "type": "refusal",
            "text": "I cannot provide investment advice.",
            "citation_url": "https://groww.in/mutual-funds/test",
            "footer": "Last updated from sources: 2026-05-20",
            "refused": True,
            "reason": "advisory_query",
        }
        is_valid, errors = validate_response(response)
        assert is_valid is False
        assert "must have citation_url: null" in errors[0]

    def test_banned_phrases(self):
        text = "I think you should invest in this fund because it's a good investment"
        banned = contains_banned_phrases(text)
        assert len(banned) > 0


# ============================================================
# Integration Tests: Full Pipeline
# ============================================================

class TestFullPipeline:
    """Test the complete query processing pipeline."""

    def test_factual_queries_return_url(self):
        """Test that factual queries return answers with exactly 1 URL."""
        for query, expected_scheme in FACTUAL_QUERIES:
            response = process_query(query)
            
            # Must be an answer
            assert response["type"] == "answer", (
                f"Query '{query}' should return answer, got: {response}"
            )
            
            # Must have URL
            assert response["citation_url"] is not None, (
                f"Query '{query}' must have citation_url"
            )
            
            # Must be Groww URL
            assert "groww.in" in response["citation_url"], (
                f"Query '{query}' URL must be from groww.in"
            )
            
            # Must have footer
            assert "Last updated from sources:" in response["footer"], (
                f"Query '{query}' must have footer date"
            )
            
            # Must be ≤3 sentences
            sentence_count = count_sentences(response["text"])
            assert sentence_count <= 3, (
                f"Query '{query}' has {sentence_count} sentences (max 3)"
            )

    def test_advisory_queries_refused_no_url(self):
        """Test that advisory queries are refused with NO URL."""
        for query in ADVISORY_QUERIES:
            response = process_query(query)
            
            # Must be a refusal
            assert response["type"] == "refusal", (
                f"Query '{query}' should be refused, got: {response}"
            )
            
            # Must have NO URL
            assert response["citation_url"] is None, (
                f"Query '{query}' must have citation_url: null, got: {response['citation_url']}"
            )
            
            # Must be marked as refused
            assert response["refused"] is True
            
            # Must have reason
            assert response["reason"] is not None
            
            # Must have footer
            assert "Last updated from sources:" in response["footer"]

    def test_pii_queries_refused_no_url(self):
        """Test that PII queries are refused with NO URL."""
        for query in PII_QUERIES:
            response = process_query(query)
            
            # Must be a refusal
            assert response["type"] == "refusal", (
                f"Query '{query}' should be refused, got: {response}"
            )
            
            # Must have NO URL
            assert response["citation_url"] is None, (
                f"Query '{query}' must have citation_url: null, got: {response['citation_url']}"
            )
            
            # Must be marked as refused
            assert response["refused"] is True
            
            # Must have PII reason
            assert response["reason"] == "pii_detected", (
                f"Query '{query}' should have reason 'pii_detected', got: {response['reason']}"
            )

    def test_out_of_scope_queries_refused_no_url(self):
        """Test that out-of-scope queries are refused with NO URL."""
        for query in OUT_OF_SCOPE_QUERIES:
            response = process_query(query)
            
            # Must be a refusal
            assert response["type"] == "refusal", (
                f"Query '{query}' should be refused, got: {response}"
            )
            
            # Must have NO URL
            assert response["citation_url"] is None, (
                f"Query '{query}' must have citation_url: null, got: {response['citation_url']}"
            )
            
            # Must be marked as refused
            assert response["refused"] is True


# ============================================================
# Exit Criteria Validation
# ============================================================

class TestExitCriteria:
    """Validate Phase 3 exit criteria."""

    def test_100_percent_factual_have_url(self):
        """Exit criteria: 100% of factual queries have exactly 1 URL."""
        factual_with_url = 0
        total = len(FACTUAL_QUERIES)
        
        for query, _ in FACTUAL_QUERIES:
            response = process_query(query)
            if response["type"] == "answer" and response["citation_url"] is not None:
                factual_with_url += 1
        
        accuracy = factual_with_url / total
        assert accuracy == 1.0, (
            f"Factual queries with URL: {factual_with_url}/{total} ({accuracy:.0%})"
        )

    def test_100_percent_refusals_no_url(self):
        """Exit criteria: 100% of refusals have NO URL."""
        all_queries = ADVISORY_QUERIES + PII_QUERIES + OUT_OF_SCOPE_QUERIES
        refusals_no_url = 0
        total = len(all_queries)
        
        for query in all_queries:
            response = process_query(query)
            if response["type"] == "refusal" and response["citation_url"] is None:
                refusals_no_url += 1
        
        accuracy = refusals_no_url / total
        assert accuracy == 1.0, (
            f"Refusals with no URL: {refusals_no_url}/{total} ({accuracy:.0%})"
        )

    def test_all_responses_have_footer(self):
        """Exit criteria: All responses include footer date."""
        all_queries = [q for q, _ in FACTUAL_QUERIES] + ADVISORY_QUERIES[:2] + PII_QUERIES[:2]
        
        for query in all_queries:
            response = process_query(query)
            assert "Last updated from sources:" in response["footer"], (
                f"Query '{query}' missing footer date"
            )

    def test_all_answers_max_3_sentences(self):
        """Exit criteria: All answers ≤3 sentences."""
        for query, _ in FACTUAL_QUERIES:
            response = process_query(query)
            if response["type"] == "answer":
                sentence_count = count_sentences(response["text"])
                assert sentence_count <= 3, (
                    f"Query '{query}' has {sentence_count} sentences (max 3)"
                )


# ============================================================
# Exit Load Extraction Tests
# ============================================================

class TestExitLoadExtraction:
    """Exit load answers must be a single sentence (≤3) even from multi-sentence chunks."""

    def test_extracts_sentence_from_about_paragraph(self):
        context = (
            "The HDFC Silver ETF FoF Direct Growth is rated Very High risk. "
            "Minimum SIP Investment is set to ₹100. Minimum Lumpsum Investment is ₹100. "
            "Exit load of 1%, if redeemed within 15 days."
        )
        answer = _extract_exit_load_answer(context)
        assert answer == "Exit load of 1%, if redeemed within 15 days."
        assert count_sentences(answer) == 1

    def test_extracts_standalone_exit_load_line(self):
        context = "Exit load of 1% if redeemed within 1 year"
        answer = _extract_exit_load_answer(context)
        assert answer == "Exit load of 1% if redeemed within 1 year."
        assert count_sentences(answer) == 1

    def test_extracts_nil_exit_load(self):
        context = "Exit load\nNil\nStamp duty on investment"
        answer = _extract_exit_load_answer(context)
        assert answer == "Exit load is Nil."


# ============================================================
# Groq LLM Integration Tests
# ============================================================

class TestGroqLLMIntegration:
    """Test Groq LLM integration."""

    def test_groq_package_available(self):
        """Test that Groq package is installed."""
        assert HAS_GROQ is True, "groq package not installed"

    def test_llm_fallback_works(self):
        """Test that template fallback works when LLM is not configured."""
        # Even without GROQ_API_KEY set, queries should work via fallback
        response = process_query("expense ratio HDFC Mid Cap")
        
        # Should return a valid response (either LLM or template)
        assert response["type"] == "answer", f"Expected answer, got: {response}"
        assert response["text"] is not None
        assert len(response["text"]) > 0

    def test_llm_response_structure(self):
        """Test that LLM responses have correct structure."""
        import os
        from app.guardrails.generator import generate_answer
        from app.rag.retriever import retrieve
        from app.rag.context_assembler import assemble_context, get_citation_url
        
        # Only run if GROQ_API_KEY is set
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")
        
        query = "expense ratio HDFC Mid Cap"
        retrieval = retrieve(query, top_k=3)
        context = assemble_context(retrieval)
        citation_url = get_citation_url(retrieval)
        footer = "Last updated from sources: 2026-05-27"
        
        response = generate_answer(query, context, citation_url, footer)
        
        # Validate structure
        assert response["type"] == "answer"
        assert response["citation_url"] is not None
        assert response["footer"] == footer
        assert response["refused"] is False
        
        # Validate content (LLM should generate natural language)
        assert len(response["text"]) > 10
        sentence_count = count_sentences(response["text"])
        assert sentence_count <= 3
