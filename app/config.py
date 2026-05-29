"""Application configuration and paths (Phase 0)."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Repository root (parent of app/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIR = PROJECT_ROOT / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.yaml"
SCHEMES_PATH = CORPUS_DIR / "schemes.json"
LAST_UPDATED_PATH = CORPUS_DIR / "last_updated.json"

INGESTION_RAW_DIR = PROJECT_ROOT / "ingestion" / "raw"
INGESTION_DATA_DIR = PROJECT_ROOT / "data"
VECTOR_STORE_DIR = INGESTION_DATA_DIR / "chroma"

# Environment (used in later phases)
# LLM Configuration (Groq)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))  # Low for factual answers
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "300"))  # Limit response length

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
