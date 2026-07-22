"""Phase 1.4 — Embedder factory."""

from __future__ import annotations

import logging
from chromadb.utils import embedding_functions
from app.config import EMBEDDING_MODEL, GROQ_API_KEY

logger = logging.getLogger(__name__)


def get_embedding_function():
    """Return the configured ChromaDB embedding function, or None if unavailable."""
    model = EMBEDDING_MODEL
    logger.info(f"Initializing embedding function for model: {model}")

    try:
        if model == "BAAI/bge-small-en-v1.5":
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-en-v1.5"
            )
        if model in ("text-embedding-3-small", "text-embedding-ada-002"):
            if not GROQ_API_KEY:
                logger.warning(
                    "GROQ_API_KEY is not set but %s is requested. "
                    "Falling back to local BAAI/bge-small-en-v1.5.",
                    model,
                )
                return embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="BAAI/bge-small-en-v1.5"
                )
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=GROQ_API_KEY, model_name=model
            )
        logger.warning(
            "Unknown embedding model '%s'. Using SentenceTransformer fallback with this model name.",
            model,
        )
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
    except Exception as exc:
        # Free-tier deploys omit torch/sentence-transformers; keyword/JSONL still works.
        logger.warning("Embeddings unavailable (%s); using keyword/JSONL retrieval only.", exc)
        return None

