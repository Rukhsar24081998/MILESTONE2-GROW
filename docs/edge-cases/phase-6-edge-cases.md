# Phase 6 — Validation and Success Criteria: Edge Cases

**Reference:** [Phase 6 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-6--validation-and-success-criteria-week-34)  
**Exit criteria:** Golden tests pass; success criteria mapped to problem statement; limitations documented.

---

## Golden query set design

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-01 | P0 | Golden factual answer cites non-allowlisted URL | Automated test **fails** |
| P6-EC-02 | P1 | Golden set includes ELSS lock-in query | Remove or mark `expected: refusal` — ELSS not in corpus |
| P6-EC-03 | P1 | Golden set references sixth HDFC scheme | Restrict to five documented schemes only |
| P6-EC-04 | P2 | Expected expense ratio hardcoded; Groww page changed | Prefer structure checks (URL, footer, ≤3 sentences) over exact % |
| P6-EC-05 | P2 | Duplicate golden queries differing only by punctuation | Normalize before hash/compare |

---

## Retrieval accuracy threshold (80%)

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-06 | P1 | 7/10 golden queries pass top-3 chunk test (70%) | Fail Phase 6 gate; tune Phase 2 or re-ingest |
| P6-EC-07 | P2 | Pass rate 80% but human review finds wrong facts | Add human review for borderline queries |
| P6-EC-08 | P2 | “Benchmark” query passes retrieval but LLM wrong | Split tests: retrieval golden vs E2E golden |

---

## Facts-only and refusal coverage

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-09 | P0 | Advisory golden query returns factual answer | CI failure |
| P6-EC-10 | P1 | Borderline: “Is Mid Cap good for beginners?” | Must refuse (advice) |
| P6-EC-11 | P1 | Comparison golden without scheme names | Refuse |
| P6-EC-12 | P2 | Refusal missing `refused: true` in JSON | Schema test fails |

---

## Citation allowlist automation

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-13 | P0 | `citation_url` with trailing slash fails strict string match | Normalize URLs in test helper |
| P6-EC-14 | P1 | Citation uses `http://groww.in` vs `https://` | Normalize to https canonical |
| P6-EC-15 | P2 | Answer embeds URL in text **and** `citation_url` field | Both must be allowlisted; still only **one** distinct URL allowed |
| P6-EC-16 | P2 | UTM params appended in LLM output | Strip params in validator before allowlist check |

---

## UI success criteria checklist

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-17 | P1 | Manual UX checklist: footer missing on one example | Fail sign-off |
| P6-EC-18 | P2 | Example chip answer correct but disclaimer off-screen on iPhone SE | Fail responsive checklist |
| P6-EC-19 | P3 | Automated UI tests flaky on LLM wording | Assert on URL + `refused` + sentence count, not exact prose |

---

## Performance-query golden cases

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-20 | P1 | “How did Mid Cap perform last year?” returns return % and rank | Fail — must link to Groww page only |
| P6-EC-21 | P2 | Performance answer includes category average comparison | Fail — no comparison math |
| P6-EC-22 | P2 | Performance answer correct link but 4 sentences | Fail format validator |

---

## Corpus drift and regression

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-23 | P1 | Groww redesign breaks HTML parser | Ingestion test fails; document in known limitations |
| P6-EC-24 | P2 | Re-run golden tests after re-ingest only | Version tag `corpus_version` in test report |
| P6-EC-25 | P3 | LLM model upgrade changes phrasing | Golden tests remain structural |

---

## Problem statement alignment

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-26 | P2 | Reviewer expects AMFI citation per problem statement | README limitation: project uses **5 Groww URLs only** |
| P6-EC-27 | P2 | “Statement download” factual query in golden set | Expect low confidence or refusal — likely not on Groww pages |
| P6-EC-28 | P1 | Success criteria met but PII logged in Phase 5 | Block sign-off until logging edge cases pass |

---

## Sign-off artifacts

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P6-EC-29 | P1 | `tests/golden_queries.json` missing refusal cases | Add minimum 3 refusals + 3 factual + 1 performance |
| P6-EC-30 | P2 | Known limitations omit closed-corpus constraint | README section required |
| P6-EC-31 | P2 | Human review disagrees with automated pass | Escalate query to golden set or fix retrieval |

---

## Phase 6 test checklist

- [ ] `golden_queries.json` covers all 5 schemes at least once
- [ ] Automated: 100% refusals on advisory set
- [ ] Automated: 100% `citation_url ∈ allowlist`
- [ ] Automated: sentence count ≤3 for answers
- [ ] Retrieval golden ≥80% (or documented waiver)
- [ ] README known limitations: 5-URL corpus, Groww freshness, no ELSS
- [ ] Manual UI checklist completed (disclaimer, examples, footer, refusal UX)

---

## Cross-phase edge cases (regression)

| ID | Phases | Scenario | Expected behavior |
|----|--------|----------|-------------------|
| P6-EC-32 | 0→1 | Manifest URL edited without re-ingest | Tests fail until pipeline re-run |
| P6-EC-33 | 2→3 | Retrieval improves but validator still fails | Fix Phase 3 not Phase 6 thresholds |
| P6-EC-34 | 4→5 | UI points to wrong API port in demo | E2E golden fails; fix env in Phase 5 |
