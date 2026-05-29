"""Phase 2 — Context assembler for LLM generation.

Builds context from retrieved chunks:
- Deduplicates by chunk_id
- Enforces token budget
- Formats with source metadata
"""

from __future__ import annotations

from typing import Optional

from app.rag.retriever import RetrievalResponse, RetrievalResult


# Approximate tokens per character (English text)
TOKENS_PER_CHAR = 0.25


def estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return int(len(text) * TOKENS_PER_CHAR)


def deduplicate_results(results: list[RetrievalResult]) -> list[RetrievalResult]:
    """Remove duplicate chunks by chunk_id.
    
    Args:
        results: List of retrieval results
        
    Returns:
        Deduplicated list preserving order
    """
    seen = set()
    unique = []
    
    for result in results:
        if result.chunk_id not in seen:
            seen.add(result.chunk_id)
            unique.append(result)
    
    return unique


def enforce_token_limit(
    results: list[RetrievalResult],
    max_tokens: int = 3000,
) -> list[RetrievalResult]:
    """Enforce token budget on retrieved chunks.
    
    Args:
        results: Deduplicated retrieval results
        max_tokens: Maximum token budget
        
    Returns:
        Results within token budget
    """
    selected = []
    total_tokens = 0
    
    for result in results:
        chunk_tokens = estimate_tokens(result.text)
        if total_tokens + chunk_tokens <= max_tokens:
            selected.append(result)
            total_tokens += chunk_tokens
        else:
            break
    
    return selected


def format_context(
    results: list[RetrievalResult],
    query: str,
    detected_scheme: Optional[str] = None,
) -> str:
    """Format retrieved chunks into context string for LLM.
    
    Args:
        results: Retrieved and filtered chunks
        query: Original user query
        detected_scheme: Detected scheme ID (optional)
        
    Returns:
        Formatted context string
    """
    if not results:
        return "No relevant information found in the corpus."
    
    context_parts = []
    
    # Add scheme context if detected
    if detected_scheme:
        context_parts.append(f"[Scheme: {detected_scheme}]")
    
    # Add query for reference
    context_parts.append(f"Query: {query}")
    context_parts.append("")
    
    # Add chunks with metadata
    for i, result in enumerate(results, 1):
        chunk_header = f"--- Chunk {i} (source: {result.source_url}) ---"
        context_parts.append(chunk_header)
        context_parts.append(result.text)
        context_parts.append("")
    
    return "\n".join(context_parts)


def assemble_context(
    response: RetrievalResponse,
    max_tokens: int = 3000,
    deduplicate: bool = True,
) -> str:
    """Full context assembly pipeline.
    
    Args:
        response: RetrievalResponse from retriever
        max_tokens: Maximum token budget for context
        deduplicate: Whether to deduplicate chunks
        
    Returns:
        Formatted context string ready for LLM
    """
    results = response.results
    
    # Step 1: Deduplicate
    if deduplicate:
        results = deduplicate_results(results)
    
    # Step 2: Enforce token limit
    results = enforce_token_limit(results, max_tokens)
    
    # Step 3: Format
    context = format_context(
        results=results,
        query=response.query,
        detected_scheme=response.detected_scheme,
    )
    
    return context


def get_citation_url(response: RetrievalResponse) -> Optional[str]:
    """Extract citation URL from top result.
    
    Args:
        response: RetrievalResponse
        
    Returns:
        Source URL from highest-scoring chunk
    """
    if response.results:
        return response.results[0].source_url
    return None
