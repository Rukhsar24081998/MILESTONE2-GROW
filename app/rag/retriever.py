"""Phase 2 — Retriever with scheme-aware filtered search.

Implements hybrid retrieval:
1. Detect scheme from query (optional)
2. Filtered semantic search if scheme detected
3. Keyword reranking for small corpus
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import chromadb

from app.config import VECTOR_STORE_DIR
from app.rag.embedder import get_embedding_function
from app.rag.scheme_detector import detect_scheme


@dataclass
class RetrievalResult:
    """Single retrieval result."""
    chunk_id: str
    text: str
    source_url: str
    scheme_id: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalResponse:
    """Full retrieval response."""
    query: str
    detected_scheme: Optional[str]
    results: list[RetrievalResult]
    total_retrieved: int


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create Chroma persistent client."""
    return chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))


def get_collection(client: chromadb.ClientAPI, collection_name: str = "hdfc_groww_corpus") -> chromadb.Collection:
    """Get existing collection."""
    return client.get_collection(name=collection_name)


def rerank_with_keyword_boost(results: dict, query: str) -> dict:
    """Rerank results by boosting chunks with more query term matches.
    
    Args:
        results: Chroma query results dict
        query: Original query string
        
    Returns:
        Modified results dict with adjusted distances
    """
    query_terms = set(query.lower().split())
    
    if not results["documents"] or not results["documents"][0]:
        return results
    
    for i, doc in enumerate(results["documents"][0]):
        doc_lower = doc.lower()
        match_count = sum(1 for term in query_terms if term in doc_lower)
        
        # Boost: reduce distance for better keyword matches
        # Distance is lower = better, so multiply by factor < 1.0
        if match_count > 0:
            boost_factor = 1.0 - 0.1 * min(match_count, 5)
            results["distances"][0][i] *= boost_factor
    
    return results


def retrieve(
    query: str,
    top_k: int = 5,
    collection_name: str = "hdfc_groww_corpus",
    detect_scheme_flag: bool = True,
) -> RetrievalResponse:
    """Retrieve relevant chunks for a query.
    
    Args:
        query: User query string
        top_k: Number of results to return
        collection_name: Chroma collection name
        detect_scheme_flag: Whether to detect and filter by scheme
        
    Returns:
        RetrievalResponse with detected scheme and ranked results
    """
    # Step 1: Detect scheme
    detected_scheme = None
    if detect_scheme_flag:
        detected_scheme = detect_scheme(query)
    
    # Step 2: Query Chroma
    client = get_chroma_client()
    collection = get_collection(client, collection_name)
    
    # Build query parameters
    query_kwargs = {
        "query_texts": [query],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    
    # Add scheme filter if detected
    if detected_scheme:
        query_kwargs["where"] = {"scheme_id": detected_scheme}
    
    # Execute query
    results = collection.query(**query_kwargs)
    
    # Step 3: Keyword reranking
    results = rerank_with_keyword_boost(results, query)
    
    # Step 4: Build response
    retrieval_results = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            
            retrieval_results.append(RetrievalResult(
                chunk_id=metadata.get("chunk_id", f"chunk_{i}"),
                text=results["documents"][0][i],
                source_url=metadata.get("source_url", ""),
                scheme_id=metadata.get("scheme_id", ""),
                score=1.0 - results["distances"][0][i] if results["distances"] else 0.0,
                metadata=metadata,
            ))
    
    return RetrievalResponse(
        query=query,
        detected_scheme=detected_scheme,
        results=retrieval_results,
        total_retrieved=len(retrieval_results),
    )


def retrieve_with_context(
    query: str,
    top_k: int = 5,
    collection_name: str = "hdfc_groww_corpus",
) -> tuple[str, Optional[str], list[str]]:
    """Retrieve and build context string for LLM.
    
    Args:
        query: User query string
        top_k: Number of chunks to retrieve
        collection_name: Chroma collection name
        
    Returns:
        Tuple of (context_text, detected_scheme, source_urls)
    """
    response = retrieve(query, top_k=top_k, collection_name=collection_name)
    
    # Build context
    context_parts = []
    source_urls = []
    
    for result in response.results:
        context_parts.append(result.text)
        if result.source_url and result.source_url not in source_urls:
            source_urls.append(result.source_url)
    
    context = "\n\n".join(context_parts)
    
    return context, response.detected_scheme, source_urls
