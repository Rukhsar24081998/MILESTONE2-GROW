# Phase 2 — Retrieval and Context Assembly: Edge Cases

**Reference:** [Phase 2 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-2--retrieval-and-context-assembly-week-12)  
**Exit criteria:** Top-3 chunks contain answer-bearing text for ≥80% of 10-query golden set.

---

## Query input

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-01 | P1 | Empty string `""` | Return 400 from API layer; retrieval not invoked |
| P2-EC-02 | P1 | Whitespace-only query | Treat as empty; reject |
| P2-EC-03 | P2 | Query >500 chars | Truncate or reject per API contract before embed |
| P2-EC-04 | P2 | Non-English query (Hindi scheme name) | Best-effort keyword match on aliases; may miss → low score |
| P2-EC-05 | P2 | HTML/script in query | Strip tags before embed |

---

## Scheme detection and ambiguity

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-06 | P1 | “HDFC fund expense ratio” — no scheme specified | No metadata filter; top chunks may mix schemes; answer phase should clarify or pick highest score |
| P2-EC-07 | P1 | “HDFC Equity Fund” (alias for Flexi Cap) | Map to `hdfc-flexi-cap-direct-growth`; filter chunks |
| P2-EC-08 | P1 | “Mid cap vs small cap expense ratio” (two schemes) | Retrieve both; context builder includes both URLs’ chunks; generation must pick **one** citation |
| P2-EC-09 | P1 | Scheme **not** in corpus (e.g. HDFC Large Cap) | No filter match; retrieval may return irrelevant low scores → Phase 3 empty/low-confidence path |
| P2-EC-10 | P2 | Typo: `HDFC Midcap Fund` | Fuzzy match alias list; fallback no filter |
| P2-EC-11 | P2 | Groww slug mentioned in query (`hdfc-defence-fund-direct-growth`) | Direct `scheme_id` filter |

---

## Retrieval quality

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-12 | P1 | All similarity scores below threshold | Return empty context flag `low_confidence: true` |
| P2-EC-13 | P1 | “Exit load” query retrieves NAV/holdings chunks only | Hybrid BM25 should surface “Exit load” section; tune weights |
| P2-EC-14 | P2 | Semantic search favors wrong scheme (Defence vs Mid Cap) | Apply scheme filter when confidence > threshold |
| P2-EC-15 | P2 | Identical top-k from two URLs after fusion | Dedupe by `source_url`; keep higher score chunk |
| P2-EC-16 | P3 | Reranker unavailable | Fall back to RRF semantic+keyword only |

---

## Context assembly

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-17 | P1 | Top-7 chunks exceed 4k token budget | Trim lowest scores until under cap |
| P2-EC-18 | P2 | All top chunks from same section (duplicate text) | Dedupe near-duplicate chunk text |
| P2-EC-19 | P1 | Context includes chunk with non-allowlisted `source_url` | Drop chunk; log integrity error (should not happen post-Phase 1) |
| P2-EC-20 | P2 | `PROCESS` query: “download capital gains report” | May have **no** matching chunks in Groww pages → low_confidence |

---

## Hybrid search edge cases

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-21 | P2 | Keyword “SIP” matches many schemes’ min investment | Prefer scheme-filtered BM25 when scheme detected |
| P2-EC-22 | P2 | “Silver” matches Silver FoF and unrelated “silver” token in holdings | Boost `scheme_id: hdfc-silver-etf-fof-direct-growth` |
| P2-EC-23 | P3 | Empty index (Phase 1 not run) | Retriever throws clear error: `INDEX_NOT_READY` |

---

## Debug and observability

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P2-EC-24 | P2 | `python -m app.rag.debug` with scheme filter | Print scores, `source_url`, `scheme_id` per chunk |
| P2-EC-25 | P2 | Golden query expects 0.73% expense ratio (Mid Cap) | Top-3 must contain `0.73` or “Expense ratio” section |

---

## Phase 2 test checklist

- [ ] 10 golden factual queries: ≥8/10 have answer text in top-3 chunks
- [ ] Alias `HDFC Equity Fund` filters Flexi Cap URL only
- [ ] Unknown scheme query sets `low_confidence` or irrelevant scores
- [ ] Token cap never exceeded in assembled context
- [ ] Every chunk in context has `source_url` ∈ twenty URL allowlist
