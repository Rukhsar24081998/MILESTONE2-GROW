#!/usr/bin/env python3
"""Script to display embeddings information from the ChromaDB vector store."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.phase1_4.indexer import get_chroma_client, get_or_create_collection
from app.config import EMBEDDING_MODEL


def show_embeddings_summary():
    """Display summary information about the embeddings in the vector store."""
    print("=" * 60)
    print("EMBEDDINGS SUMMARY")
    print("=" * 60)
    print(f"\nEmbedding Model: {EMBEDDING_MODEL}")
    
    # Connect to ChromaDB
    client = get_chroma_client()
    
    # List all collections
    collections = client.list_collections()
    print(f"\nCollections found: {len(collections)}")
    
    for col in collections:
        print(f"\n{'-' * 40}")
        print(f"Collection Name: {col.name}")
        
        # Get the collection with embedding function
        collection = get_or_create_collection(client, col.name)
        
        # Get collection info
        count = collection.count()
        print(f"Total Embeddings: {count}")
        
        if count > 0:
            # Get a sample to show embedding dimensions
            sample = collection.get(limit=1, include=["embeddings"])
            if sample and sample["embeddings"] and len(sample["embeddings"]) > 0:
                embedding_dim = len(sample["embeddings"][0])
                print(f"Embedding Dimension: {embedding_dim}")
            
            # Show metadata distribution
            all_data = collection.get(include=["metadatas"])
            metadata = all_data["metadatas"]
            
            if metadata:
                # Count by scheme
                schemes = {}
                doc_types = {}
                for m in metadata:
                    scheme = m.get("scheme_id", "unknown")
                    doc_type = m.get("document_type", "unknown")
                    schemes[scheme] = schemes.get(scheme, 0) + 1
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                print(f"\nChunks by Scheme:")
                for scheme, count in sorted(schemes.items()):
                    print(f"  - {scheme}: {count} chunks")
                
                print(f"\nChunks by Document Type:")
                for doc_type, count in sorted(doc_types.items()):
                    print(f"  - {doc_type}: {count} chunks")
    
    print(f"\n{'=' * 60}")
    print("Vector store location: data/chroma/")
    print("=" * 60)


if __name__ == "__main__":
    show_embeddings_summary()