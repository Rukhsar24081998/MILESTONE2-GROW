"""Phase 2 — Retriever with scheme-aware filtered search.

Implements hybrid retrieval:
1. Detect scheme from query (optional)
2. Filtered semantic search if scheme detected
3. Keyword reranking for small corpus
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import chromadb

from app.config import PROJECT_ROOT, VECTOR_STORE_DIR
from app.rag.embedder import get_embedding_function
from app.rag.scheme_detector import detect_scheme

logger = logging.getLogger(__name__)

_embedding_fn = None


def _get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = get_embedding_function()
    return _embedding_fn


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


def get_collection(
    client: chromadb.ClientAPI,
    collection_name: str = "hdfc_groww_corpus",
    *,
    for_query: bool = False,
) -> chromadb.Collection | None:
    """Get existing collection, or None if the index has not been built yet."""
    try:
        if for_query:
            return client.get_collection(
                name=collection_name,
                embedding_function=_get_embedding_function(),
            )
        return client.get_collection(name=collection_name)
    except (ValueError, Exception):
        return None


def _keyword_fallback_retrieve(
    client: chromadb.ClientAPI,
    collection_name: str,
    query: str,
    detected_scheme: Optional[str],
    top_k: int,
) -> list[RetrievalResult]:
    """Fallback when embedding-based query fails (e.g. model load on small hosts)."""
    collection = get_collection(client, collection_name, for_query=False)
    if collection is None:
        return []

    get_kwargs: dict = {"include": ["documents", "metadatas"], "limit": 500}
    if detected_scheme:
        get_kwargs["where"] = {"scheme_id": detected_scheme}

    try:
        batch = collection.get(**get_kwargs)
    except Exception as exc:
        logger.warning("Keyword fallback get() failed: %s", exc)
        get_kwargs.pop("where", None)
        batch = collection.get(**get_kwargs)
    docs = batch.get("documents") or []
    metas = batch.get("metadatas") or []
    if not docs:
        return []

    query_terms = [t for t in query.lower().split() if len(t) > 2]
    scored: list[tuple[float, int]] = []
    for i, doc in enumerate(docs):
        if not doc:
            continue
        doc_lower = doc.lower()
        matches = sum(1 for term in query_terms if term in doc_lower)
        if matches == 0:
            continue
        scored.append((matches / max(len(query_terms), 1), i))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[RetrievalResult] = []
    for score, idx in scored[:top_k]:
        metadata = metas[idx] if idx < len(metas) and metas[idx] else {}
        results.append(
            RetrievalResult(
                chunk_id=metadata.get("chunk_id", f"chunk_{idx}"),
                text=docs[idx],
                source_url=metadata.get("source_url", ""),
                scheme_id=metadata.get("scheme_id", ""),
                score=score,
                metadata=metadata,
            )
        )
    return results


def _keyword_fallback_from_jsonl(
    query: str,
    detected_scheme: Optional[str],
    top_k: int,
) -> list[RetrievalResult]:
    """Last-resort retrieval from committed chunk files (no Chroma dependency)."""
    chunks_dir = PROJECT_ROOT / "ingestion" / "chunks"
    if not chunks_dir.is_dir():
        return []

    query_terms = [t for t in query.lower().split() if len(t) > 2]
    if not query_terms:
        return []

    paths = sorted(chunks_dir.glob("*.jsonl"))
    if detected_scheme:
        preferred = chunks_dir / f"{detected_scheme}.jsonl"
        if preferred.exists():
            paths = [preferred] + [p for p in paths if p != preferred]

    scored: list[tuple[float, RetrievalResult]] = []
    for path in paths:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                text = data.get("text", "")
                if not text:
                    continue
                text_lower = text.lower()
                matches = sum(1 for term in query_terms if term in text_lower)
                if matches == 0:
                    continue
                score = matches / max(len(query_terms), 1)
                scored.append(
                    (
                        score,
                        RetrievalResult(
                            chunk_id=data.get("chunk_id", ""),
                            text=text,
                            source_url=data.get("source_url", ""),
                            scheme_id=data.get("scheme_id", ""),
                            score=score,
                            metadata={
                                k: data[k]
                                for k in ("scheme_name", "document_type", "page_section")
                                if data.get(k)
                            },
                        ),
                    )
                )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


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
    collection = get_collection(client, collection_name, for_query=True)
    if collection is None:
        return RetrievalResponse(
            query=query,
            detected_scheme=detected_scheme,
            results=[],
            total_retrieved=0,
        )

    retrieval_results: list[RetrievalResult] = []
    try:
        query_kwargs = {
            "query_texts": [query],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if detected_scheme:
            query_kwargs["where"] = {"scheme_id": detected_scheme}

        results = collection.query(**query_kwargs)
        results = rerank_with_keyword_boost(results, query)

        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                retrieval_results.append(
                    RetrievalResult(
                        chunk_id=metadata.get("chunk_id", f"chunk_{i}"),
                        text=results["documents"][0][i],
                        source_url=metadata.get("source_url", ""),
                        scheme_id=metadata.get("scheme_id", ""),
                        score=1.0 - results["distances"][0][i] if results["distances"] else 0.0,
                        metadata=metadata,
                    )
                )
    except Exception as exc:
        logger.warning("Semantic search failed, using keyword fallback: %s", exc)
        retrieval_results = _keyword_fallback_retrieve(
            client, collection_name, query, detected_scheme, top_k
        )

    if not retrieval_results:
        logger.info("No semantic hits; trying keyword fallback")
        retrieval_results = _keyword_fallback_retrieve(
            client, collection_name, query, detected_scheme, top_k
        )
    if not retrieval_results and detected_scheme:
        retrieval_results = _keyword_fallback_retrieve(
            client, collection_name, query, None, top_k
        )
    if not retrieval_results:
        retrieval_results = _keyword_fallback_from_jsonl(
            query, detected_scheme, top_k
        )

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
