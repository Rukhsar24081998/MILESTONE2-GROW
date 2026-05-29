"""Phase 4/5 — FastAPI backend for Mutual Fund FAQ Assistant.

Endpoints:
- POST /ask — Main Q&A endpoint with guardrails
- GET /health — Liveness check
- GET /corpus/status — Corpus metadata and status
- GET /examples — Example questions for UI
"""

import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.guardrails.generator import process_query
from app.guardrails.validator import validate_response
from app.guardrails.pii_filter import contains_pii
from app.config import (
    PROJECT_ROOT,
    CORPUS_DIR,
    SCHEMES_PATH,
    LAST_UPDATED_PATH,
    MANIFEST_PATH,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="Facts-only mutual fund Q&A system with closed corpus (5 Groww URLs)",
    version="1.0.0",
)

# Add CORS middleware for UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="User question about mutual funds",
        example="What is the expense ratio of HDFC Mid Cap Fund?",
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for tracking",
    )

    @validator('query')
    def strip_html(cls, v):
        """Strip HTML tags from query."""
        return re.sub(r'<[^>]+>', '', v).strip()


class QueryResponse(BaseModel):
    """Response model for /ask endpoint."""
    type: str = Field(..., description="Response type: 'answer' or 'refusal'")
    text: str = Field(..., description="Response text")
    citation_url: Optional[str] = Field(None, description="Source URL (null for refusals)")
    footer: str = Field(..., description="Last updated date from sources")
    refused: bool = Field(..., description="Whether the query was refused")
    reason: Optional[str] = Field(None, description="Refusal reason (if refused)")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


class CorpusStatusResponse(BaseModel):
    """Corpus status response."""
    document_count: int
    corpus_version: str
    last_ingest_date: Optional[str]
    schemes: list
    allowlist_urls: list


@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Process a user query and return answer or refusal.
    
    This is the main Q&A endpoint that:
    1. Validates query (length, PII check)
    2. Processes through guardrails pipeline
    3. Validates response format
    4. Returns answer with citation or refusal
    """
    start_time = time.time()
    
    # Strip HTML from query
    query = request.query.strip()
    
    # Validate query length
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query too short (min 3 chars)")
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query too long (max 500 chars)")
    
    # Quick PII check before processing
    if contains_pii(query):
        logger.warning("PII detected in query, refusing")
        # Return fast refusal without full pipeline
        return {
            "type": "refusal",
            "text": "For your privacy and security, I cannot process queries containing personal information like PAN, Aadhaar, phone numbers, or email addresses.",
            "citation_url": None,
            "footer": f"Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}",
            "refused": True,
            "reason": "pii_detected",
        }
    
    logger.info(f"Processing query: {query[:50]}...")
    
    # Process through guardrails pipeline
    response = process_query(query)
    
    # Validate response
    is_valid, errors = validate_response(response)
    if not is_valid:
        logger.error(f"Response validation failed: {errors}")
        # Safety fallback
        response = {
            "type": "refusal",
            "text": "I'm sorry, I couldn't process your question. Please try rephrasing.",
            "citation_url": None,
            "footer": response.get("footer", f"Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}"),
            "refused": True,
            "reason": "validation_error",
        }
    
    # Log timing
    elapsed = time.time() - start_time
    logger.info(f"Query processed in {elapsed:.2f}s - type: {response['type']}")
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness check - verifies API is running."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/corpus/status", response_model=CorpusStatusResponse)
async def corpus_status():
    """Return corpus metadata and status.
    
    Shows:
    - Document count (should be 5)
    - Corpus version
    - Last ingest date
    - Scheme list
    - Allowlisted URLs
    """
    import json
    import yaml
    
    # Read schemes.json
    schemes = []
    if SCHEMES_PATH.exists():
        with open(SCHEMES_PATH, 'r') as f:
            schemes_data = json.load(f)
            schemes = schemes_data.get('schemes', [])
    
    # Read last_updated.json
    last_ingest_date = None
    if LAST_UPDATED_PATH.exists():
        with open(LAST_UPDATED_PATH, 'r') as f:
            last_updated = json.load(f)
            # Get schemes dict
            schemes_dict = last_updated.get('schemes', {})
            # Get most recent fetch date
            dates = [
                v.get('fetched_at') 
                for v in schemes_dict.values() 
                if isinstance(v, dict) and v.get('fetched_at')
            ]
            if dates:
                last_ingest_date = max(dates)
    
    # Read manifest.yaml for allowlist
    allowlist_urls = []
    corpus_version = "1.0"
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            manifest = yaml.safe_load(f)
            corpus_version = manifest.get('corpus_version', '1.0')
            allowed_urls = manifest.get('allowed_urls', [])
            allowlist_urls = [url_data.get('url', '') for url_data in allowed_urls]
    
    return {
        "document_count": len(schemes),
        "corpus_version": corpus_version,
        "last_ingest_date": last_ingest_date,
        "schemes": [
            {
                "id": s.get('id'),
                "name": s.get('name'),
                "category": s.get('category'),
            }
            for s in schemes
        ],
        "allowlist_urls": allowlist_urls,
    }


@app.get("/examples")
async def get_examples():
    """Return example questions for UI.
    
    Returns 3 example questions covering different schemes and topics.
    """
    return {
        "examples": [
            {
                "query": "What is the expense ratio of HDFC Mid Cap Fund?",
                "category": "expense_ratio",
                "scheme": "hdfc-mid-cap-direct-growth",
            },
            {
                "query": "What is the exit load for HDFC Silver ETF FoF?",
                "category": "exit_load",
                "scheme": "hdfc-silver-etf-fof-direct-growth",
            },
            {
                "query": "What is the minimum SIP amount for HDFC Small Cap Fund?",
                "category": "sip_minimum",
                "scheme": "hdfc-small-cap-direct-growth",
            },
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": "Internal server error. Please try again later.",
        }
    )
