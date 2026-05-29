"""Phase 2 — Debug CLI for testing retrieval.

Usage:
    python -m app.rag.debug "expense ratio HDFC Mid Cap"
    python -m app.rag.debug "exit load Silver ETF" --top-k 3
"""

from __future__ import annotations

import argparse
import sys

from app.rag.retriever import retrieve
from app.rag.context_assembler import assemble_context, get_citation_url
from app.rag.scheme_detector import detect_scheme_with_confidence


def main():
    parser = argparse.ArgumentParser(description="Debug retrieval for a query")
    parser.add_argument("query", type=str, help="Query string to test")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--no-scheme-detect", action="store_true", help="Disable scheme detection")
    parser.add_argument("--context", action="store_true", help="Show assembled context")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"QUERY: {args.query}")
    print("=" * 70)
    
    # Show scheme detection
    if not args.no_scheme_detect:
        scheme, confidence = detect_scheme_with_confidence(args.query)
        print(f"\n🔍 SCHEME DETECTION:")
        if scheme:
            print(f"   Detected: {scheme}")
            print(f"   Confidence: {confidence:.2f}")
        else:
            print(f"   No scheme detected (will use unfiltered search)")
    
    # Retrieve
    print(f"\n📊 RETRIEVAL (top-{args.top_k}):")
    print("-" * 70)
    
    response = retrieve(
        query=args.query,
        top_k=args.top_k,
        detect_scheme_flag=not args.no_scheme_detect,
    )
    
    print(f"Detected scheme: {response.detected_scheme or 'None'}")
    print(f"Results returned: {response.total_retrieved}")
    print()
    
    # Show results
    for i, result in enumerate(response.results, 1):
        print(f"Result #{i}:")
        print(f"  Score: {result.score:.4f}")
        print(f"  Scheme: {result.scheme_id}")
        print(f"  URL: {result.source_url}")
        print(f"  Text (first 200 chars): {result.text[:200]}...")
        print()
    
    # Show context if requested
    if args.context:
        print("=" * 70)
        print("ASSEMBLED CONTEXT:")
        print("=" * 70)
        context = assemble_context(response)
        print(context)
        print()
    
    # Show citation
    citation = get_citation_url(response)
    print("=" * 70)
    print(f"CITATION URL: {citation}")
    print("=" * 70)


if __name__ == "__main__":
    main()
