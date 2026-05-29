# Phase 4 Backend API Guide

## 🚀 Quick Start

```bash
# Start the API server
.venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Server runs at: http://localhost:8000
# Auto-reload enabled for development
```

## 📡 API Endpoints

### 1. POST /ask — Main Q&A Endpoint

Process a user query and return answer or refusal.

**Request:**
```json
{
  "query": "What is the expense ratio of HDFC Mid Cap Fund?",
  "session_id": "optional-session-id"
}
```

**Response (Answer):**
```json
{
  "type": "answer",
  "text": "The expense ratio is 0.73%.",
  "citation_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "footer": "Last updated from sources: 2026-05-28",
  "refused": false,
  "reason": null
}
```

**Response (Refusal):**
```json
{
  "type": "refusal",
  "text": "I can only provide factual information...",
  "citation_url": null,
  "footer": "Last updated from sources: 2026-05-28",
  "refused": true,
  "reason": "advisory_query"
}
```

**Validation:**
- Query length: 3-500 characters
- HTML tags stripped automatically
- PII detection (PAN, Aadhaar, phone, email) → fast refusal
- Response validation: ≤3 sentences for answers, exactly 1 URL

---

### 2. GET /health — Liveness Check

Verify API is running.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-05-28T18:38:01.873955",
  "version": "1.0.0"
}
```

---

### 3. GET /corpus/status — Corpus Metadata

Show corpus information and status.

**Response:**
```json
{
  "document_count": 5,
  "corpus_version": "1.0",
  "last_ingest_date": "2026-05-26T18:12:04Z",
  "schemes": [
    {
      "id": "hdfc-mid-cap-direct-growth",
      "name": "HDFC Mid Cap Fund Direct Growth",
      "category": "equity_mid_cap"
    }
    // ... 4 more schemes
  ],
  "allowlist_urls": [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    // ... 4 more URLs
  ]
}
```

---

### 4. GET /examples — Example Questions

Get 3 example questions for UI.

**Response:**
```json
{
  "examples": [
    {
      "query": "What is the expense ratio of HDFC Mid Cap Fund?",
      "category": "expense_ratio",
      "scheme": "hdfc-mid-cap-direct-growth"
    },
    {
      "query": "What is the exit load for HDFC Silver ETF FoF?",
      "category": "exit_load",
      "scheme": "hdfc-silver-etf-fof-direct-growth"
    },
    {
      "query": "What is the minimum SIP amount for HDFC Small Cap Fund?",
      "category": "sip_minimum",
      "scheme": "hdfc-small-cap-direct-growth"
    }
  ]
}
```

---

## 🧪 Testing with curl

```bash
# Test health
curl http://localhost:8000/health

# Get examples
curl http://localhost:8000/examples

# Get corpus status
curl http://localhost:8000/corpus/status

# Ask a factual question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "expense ratio HDFC Mid Cap"}'

# Test advisory refusal
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Which fund should I invest in?"}'

# Test PII refusal
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "My PAN is ABCDE1234F"}'
```

---

## 🔒 Security Features

1. **PII Detection** - Blocks queries with PAN, Aadhaar, phone, email
2. **HTML Stripping** - Removes HTML tags from queries
3. **Query Length Validation** - 3-500 characters only
4. **CORS Configuration** - Configurable origins (currently `*` for dev)
5. **Error Handling** - Graceful error responses, no stack traces exposed

---

## 📊 Response Policies

### Answers (factual queries):
- ✅ Have exactly 1 citation URL
- ✅ ≤3 sentences
- ✅ Include footer date
- ✅ `refused: false`

### Refusals (advisory/PII/out-of-scope):
- ❌ Have NO URL (`citation_url: null`)
- ✅ Include refusal reason
- ✅ Include footer date
- ✅ `refused: true`

---

## 🛠️ Architecture

**Pipeline Flow:**
```
User Query → PII Check → Classification → Retrieval → LLM/Template → Validation → Response
```

**Key Components:**
- `app/api/main.py` - FastAPI endpoints
- `app/guardrails/generator.py` - Query processing pipeline
- `app/guardrails/classifier.py` - Factual vs advisory detection
- `app/guardrails/pii_filter.py` - PII detection
- `app/guardrails/validator.py` - Response validation
- `app/rag/llm.py` - Groq LLM integration (with template fallback)

---

## 📝 Next Steps (Phase 4 Frontend)

The backend is now ready for frontend integration. Next steps:
1. Build React/HTML UI
2. Connect to `/ask` endpoint
3. Display example questions from `/examples`
4. Show corpus status from `/corpus/status`
5. Add disclaimer banner
6. Implement chat interface

**API is production-ready for Phase 4 frontend development!** 🚀
