#!/usr/bin/env python3
"""Script to export embeddings from ChromaDB to parquet format for visualization."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.phase1_4.indexer import get_chroma_client, get_or_create_collection
from app.config import EMBEDDING_MODEL, VECTOR_STORE_DIR


def export_embeddings_to_parquet(
    output_path: str | None = None,
    collection_name: str = "hdfc_groww_corpus"
) -> str:
    """Export embeddings from ChromaDB to parquet format.
    
    Args:
        output_path: Path to save the parquet file. Defaults to data/embeddings.parquet
        collection_name: Name of the ChromaDB collection to export
        
    Returns:
        Path to the created parquet file
    """
    if output_path is None:
        output_path = str(VECTOR_STORE_DIR.parent / "embeddings.parquet")
    
    print("=" * 60)
    print("EXPORTING EMBEDDINGS TO PARQUET")
    print("=" * 60)
    print(f"\nEmbedding Model: {EMBEDDING_MODEL}")
    print(f"Collection: {collection_name}")
    print(f"Output: {output_path}")
    
    # Connect to ChromaDB
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)
    
    # Get all data with embeddings
    print("\nFetching data from ChromaDB...")
    all_data = collection.get(
        include=["embeddings", "documents", "metadatas"]
    )
    
    count = len(all_data["ids"])
    print(f"Found {count} embeddings")
    
    if count == 0:
        print("No embeddings found in collection")
        return output_path
    
    # Create DataFrame
    print("\nCreating DataFrame...")
    df_data = {
        "chunk_id": all_data["ids"],
        "text": all_data["documents"],
        "embedding": all_data["embeddings"],
    }
    
    # Add metadata fields
    metadata_fields = set()
    for meta in all_data["metadatas"]:
        metadata_fields.update(meta.keys())
    
    for field in sorted(metadata_fields):
        df_data[field] = [meta.get(field) for meta in all_data["metadatas"]]
    
    df = pd.DataFrame(df_data)
    
    # Expand embedding vectors into separate columns for easier visualization
    print("Expanding embedding vectors...")
    embedding_dim = len(df["embedding"].iloc[0])
    print(f"Embedding dimension: {embedding_dim}")
    
    # Create column names for embedding dimensions
    embedding_cols = [f"dim_{i}" for i in range(embedding_dim)]
    embedding_df = pd.DataFrame(df["embedding"].tolist(), columns=embedding_cols)
    
    # Combine with metadata
    export_df = pd.concat([df.drop(columns=["embedding"]), embedding_df], axis=1)
    
    # Reorder columns for better visualization
    cols_to_front = ["chunk_id", "text", "source_url", "scheme_id", "scheme_name"]
    other_cols = [c for c in export_df.columns if c not in cols_to_front and not c.startswith("dim_")]
    dim_cols = [c for c in export_df.columns if c.startswith("dim_")]
    
    export_df = export_df[cols_to_front + other_cols + dim_cols]
    
    # Save to parquet
    print(f"\nSaving to parquet: {output_path}")
    table = pa.Table.from_pandas(export_df)
    pq.write_table(table, output_path)
    
    print(f"\n✅ Export complete!")
    print(f"   Rows: {len(export_df)}")
    print(f"   Columns: {len(export_df.columns)}")
    print(f"   File size: {Path(output_path).stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\nYou can now open {output_path} in a parquet visualizer.")
    print("=" * 60)
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export ChromaDB embeddings to parquet for visualization"
    )
    parser.add_argument(
        "--output",
        help="Output parquet file path (default: data/embeddings.parquet)"
    )
    parser.add_argument(
        "--collection",
        default="hdfc_groww_corpus",
        help="ChromaDB collection name (default: hdfc_groww_corpus)"
    )
    
    args = parser.parse_args()
    export_embeddings_to_parquet(args.output, args.collection)
