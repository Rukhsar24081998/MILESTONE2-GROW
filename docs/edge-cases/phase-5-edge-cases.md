# Phase 5 — Integration, Observability, and Hardening: Edge Cases

**Reference:** [Phase 5 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-5--integration-observability-and-hardening-week-3)  
**Exit criteria:** Fresh clone → ingest → run → 3 example questions answerable (excluding LLM latency).

---

## Configuration and secrets

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-01 | P0 | `OPENAI_API_KEY` (or equivalent) missing | API fails fast with clear startup error |
| P5-EC-02 | P1 | `.env` present but empty key | `/ask` returns 503 “LLM not configured” |
| P5-EC-03 | P1 | Wrong API base URL | Log connection error; no silent hang |
| P5-EC-04 | P2 | `.env.example` missing a required var | Document all vars in README |

---

## Health and corpus status

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-05 | P1 | `GET /health` OK but vector index empty | `health` may be `degraded`; `corpus/status` shows `document_count: 0` |
| P5-EC-06 | P0 | `corpus/status` reports `document_count: 4` | Alert/warn; expected **5** |
| P5-EC-07 | P2 | `corpus/status` shows stale `last_ingest` >30 days | README warns to re-run ingestion |
| P5-EC-08 | P2 | `allowlist_version` mismatch vs `manifest.yaml` | Status includes version; ingest bumps version |

---

## Logging and privacy

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-09 | P0 | Query containing PAN logged at INFO | Redact in logs; log `pii_detected: true` only |
| P5-EC-10 | P1 | Full user query logged in production mode | Config flag `LOG_QUERIES=false` default for demo |
| P5-EC-11 | P2 | Logs include embedding vectors | Omit large payloads; log latency + scores only |
| P5-EC-12 | P2 | Refusal reason not logged | Log `classification: ADVISORY` without advice text |

---

## Rate limiting and caching

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-13 | P1 | Same IP exceeds `/ask` rate limit | 429 with `Retry-After` |
| P5-EC-14 | P2 | Cache hit after corpus re-ingest (new expense ratio) | Invalidate cache on ingest complete or TTL 24h |
| P5-EC-15 | P2 | Cache key collision on normalized queries | Normalize lowercase + trim before hash |
| P5-EC-16 | P3 | Cached refusal for factual query (classifier bug) | Do not cache refusals and answers under same key without classification in key |

---

## Docker and deployment

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-17 | P1 | Chroma volume not mounted; index lost on restart | Document volume mount; ingest on first boot |
| P5-EC-18 | P2 | UI container cannot reach API (`localhost` from browser) | Use host-accessible API URL in UI env |
| P5-EC-19 | P2 | API starts before ingest completes | `corpus/status` guides operator; UI shows degraded |
| P5-EC-20 | P3 | Port 8000 already in use | Clear error in compose logs |

---

## Concurrent operations

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-21 | P1 | Ingestion pipeline runs while `/ask` active | Read-only retrieve during ingest or brief lock |
| P5-EC-22 | P2 | Two ingestion jobs parallel | File lock or queue; prevent corrupt index |

---

## README and onboarding

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P5-EC-23 | P1 | New developer skips ingest step | README step order: install → ingest → run API → run UI |
| P5-EC-24 | P2 | README still mentions 15–25 official URLs | Align with 5-URL closed corpus |
| P5-EC-25 | P2 | Setup works on Windows path with spaces | Document Python venv commands |

---

## Phase 5 test checklist

- [ ] Fresh clone: ingest + API + UI per README
- [ ] `/health` and `/corpus/status` accurate after ingest
- [ ] Rate limit returns 429
- [ ] PII test query not stored in logs verbatim
- [ ] Re-ingest invalidates or outdates cached answers
