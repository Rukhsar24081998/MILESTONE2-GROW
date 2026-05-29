# Phase 1 — Corpus Curation and Ingestion: Edge Cases

**Reference:** [Phase 1 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-1--corpus-curation-and-ingestion-week-1)  
**Exit criteria:** Exactly 5 indexed documents; retrieval smoke test passes for 5 sample factual queries.

---

## Allowlist gate (fetcher)

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-01 | P0 | Pipeline invoked with URL not in `manifest.yaml` | **Abort** before HTTP request; log `ALLOWLIST_REJECT` |
| P1-EC-02 | P0 | Batch job includes sixth URL from env typo | Fail entire batch or skip with error; never index non-allowlisted |
| P1-EC-03 | P1 | Redirect (301) to non-Groww domain | Do not follow off-domain; fail or flag document |
| P1-EC-04 | P1 | Redirect to different Groww fund page | Reject if final URL ≠ manifest canonical URL |

---

## HTTP and network failures

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-05 | P1 | Groww returns **429** (rate limit) | Exponential backoff; retry max N times; partial corpus OK for demo with warning |
| P1-EC-06 | P1 | Groww returns **403** / bot block | Log failure; use cached `raw/` if present; surface in `corpus/status` |
| P1-EC-07 | P1 | **Timeout** mid-download | Retry URL; do not write partial file as complete document |
| P1-EC-08 | P1 | **DNS / connection** error for one of five URLs | Index 4/5; status endpoint shows failed URL + last error |
| P1-EC-09 | P2 | Intermittent 5xx on re-ingest | Idempotent upsert; preserve `fetched_at` on success only |

---

## Parsing and content quality

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-10 | P1 | HTML is mostly nav/footer; little fund body text | Log low `text_length`; still chunk; flag in metadata `quality: low` |
| P1-EC-11 | P1 | Page requires JS; static fetch returns empty shell | Prefer saved markdown snapshots (uploads) for dev; document limitation |
| P1-EC-12 | P1 | Duplicate sections (exit load listed 3× with dates) | Chunk with overlap; retain dates in text for factual answers |
| P1-EC-13 | P2 | Unicode/rupee symbol `₹` encoding breaks | UTF-8 throughout; validate parser output |
| P1-EC-14 | P2 | HTML entities (`&amp;`) in expense ratio line | Decode before chunking |
| P1-EC-15 | P3 | PDF link on page but corpus is HTML-only | Ignore PDF fetch; HTML corpus only for this project |

---

## Chunking and indexing

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-16 | P1 | Single page produces 0 chunks (text too short) | Fail ingest for that URL; do not mark document complete |
| P1-EC-17 | P1 | Chunks missing `source_url` metadata | Block index write; every chunk must carry allowlisted URL |
| P1-EC-18 | P2 | Very large page → 200+ chunks | Cap chunks per document or merge small sections; keep provenance |
| P1-EC-19 | P1 | Re-ingest without clearing vector store | Upsert by `chunk_id` or rebuild index; avoid duplicate embeddings |
| P1-EC-20 | P2 | Embedding model changed between runs | Full re-embed all five documents; bump `corpus_version` |

---

## `last_updated` and footer data

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-21 | P1 | NAV date on page (`22 May '26`) not parsed | Fallback `fetched_at` in `corpus/last_updated.json` |
| P1-EC-22 | P2 | Conflicting dates in exit-load history blocks | Use `max(parsed_dates)` or `fetched_at` for footer |
| P1-EC-23 | P2 | `last_updated.json` missing one scheme | Footer uses corpus-level max or per-scheme map |

---

## robots.txt and ethics

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-24 | P1 | `robots.txt` disallows fund path | Do not bypass; use pre-saved corpus files for dev; document in README |
| P1-EC-25 | P2 | Aggressive parallel fetch of 5 URLs | Rate limit (e.g. 1 req/s); polite User-Agent |

---

## Document count invariants

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P1-EC-26 | P0 | Vector DB shows **6** document roots | Investigate duplicate URL variants; must be **5** |
| P1-EC-27 | P1 | Same URL ingested under two `scheme_id`s | Fix manifest mapping; one scheme_id per URL |
| P1-EC-28 | P2 | Smoke test query hits wrong scheme chunks | Verify `scheme_id` filter on chunks from Mid Cap URL only |

---

## Phase 1 test checklist

- [ ] Fetcher rejects sixth URL
- [ ] All 5 allowlisted URLs produce ≥1 chunk each with correct `source_url`
- [ ] `corpus/status` reports `document_count: 5`
- [ ] Re-run pipeline is idempotent (no duplicate chunk explosion)
- [ ] Sample queries: expense ratio (Mid Cap), exit load (Silver FoF), benchmark (Defence) retrieve relevant text
