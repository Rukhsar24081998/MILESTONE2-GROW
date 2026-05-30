# Phase 0 — Foundation and Planning: Edge Cases

**Reference:** [Phase 0 in phase-wise-architecture.md](../phase-wise-architecture.md#phase-0--foundation-and-planning-week-0)  
**Exit criteria:** `manifest.yaml` has exactly 20 URLs; `schemes.json` matches; README documents closed-corpus policy.

---

## Scope and corpus policy

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-01 | P0 | `manifest.yaml` lists 21+ URLs (AMC/AMFI URL added) | Reject at review/CI: fail if `len(allowed_urls) != 20` |
| P0-EC-02 | P0 | `manifest.yaml` lists only 19 URLs (one scheme missing) | Block Phase 1 start; document count must be 20 |
| P0-EC-03 | P0 | `hdfcfund.com` or `amfiindia.com` entered as corpus URL | Treat as invalid; AMC website is metadata-only per architecture |
| P0-EC-04 | P1 | Extra Groww URL (e.g. HDFC Large Cap) added “for completeness” | Remove from manifest; only locked twenty URLs allowed |
| P0-EC-05 | P2 | Team assumes problem-statement “15–25 URLs” still applies | README + manifest must state **20-URL closed corpus** override |

---

## URL normalization and allowlist integrity

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-06 | P1 | Trailing slash: `.../hdfc-mid-cap-fund-direct-growth/` | Normalize to canonical URL without trailing slash in manifest |
| P0-EC-07 | P1 | `http://` vs `https://groww.in/...` | Store and match **https** only in allowlist |
| P0-EC-08 | P1 | URL with `www.` prefix | Reject or normalize; single canonical form in manifest |
| P0-EC-09 | P1 | Typos in slug (`hdfc-midcap` vs `hdfc-mid-cap`) | Validation script compares against known twenty slugs |
| P0-EC-10 | P2 | Query params on URL (`?utm_source=...`) | Strip params in manifest; fetcher uses canonical URL |

---

## `schemes.json` ↔ `manifest.yaml` consistency

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-11 | P0 | `scheme_id` in manifest does not exist in `schemes.json` | CI/schema validation fails |
| P0-EC-12 | P1 | `groww_url` in schemes.json differs from manifest `url` for same `scheme_id` | Validation fails with diff report |
| P0-EC-13 | P1 | Duplicate `scheme_id` across two schemes | Reject; IDs must be unique |
| P0-EC-14 | P1 | Twenty schemes in JSON but six entries in manifest | Align counts; one document per scheme URL |
| P0-EC-15 | P2 | `corpus_version` bumped without updating schemes | Document migration note in README |

---

## Scheme naming and aliases

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-16 | P1 | Groww slug `hdfc-equity-fund` vs display name **HDFC Flexi Cap Direct Plan Growth** | Register alias in schemes.json: `aliases: ["HDFC Equity Fund", "hdfc equity fund"]` |
| P0-EC-17 | P1 | User/docs refer to “HDFC Equity Fund” only | Map alias → `hdfc-flexi-cap-direct-growth` in Phase 2 keyword map |
| P0-EC-18 | P2 | Abbreviations: “HDFC defence”, “silver FoF” | Add short aliases for retrieval keyword detection |
| P0-EC-19 | P2 | Two schemes share token “HDFC” with no category hint | Phase 2 must disambiguate or ask clarifying copy in answer (≤3 sentences) |

---

## Category and problem-statement alignment

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-20 | P2 | Reviewer expects ELSS in cohort | Document in README: ELSS included in corpus (NJ ELSS Tax Saver); thematic + commodities cover diversity |
| P0-EC-21 | P3 | “Large-cap” mentioned in problem statement but not in twenty schemes | Note as known scope gap; do not add URLs without architecture change |
| P0-EC-22 | P2 | `document_type` not `groww_scheme_page` in manifest | Standardize all twenty entries to `groww_scheme_page` |

---

## Repository and documentation

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-23 | P1 | README omits closed-corpus policy | Exit criteria fail; add explicit “20 URLs only” section |
| P0-EC-24 | P2 | `.env` committed with API keys during Phase 0 setup | Remove from git; use `.env.example` only (Phase 5) |
| P0-EC-25 | P2 | `corpus/` folder missing at repo init | Create stub `manifest.yaml` + `schemes.json` from architecture templates |

---

## Citation rules (defined in Phase 0, enforced later)

| ID | Severity | Scenario | Expected behavior |
|----|----------|----------|-------------------|
| P0-EC-26 | P1 | Refusal default URL undefined | Default: `https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth` |
| P0-EC-27 | P2 | Named scheme in refusal (“Should I buy Defence fund?”) | Citation may use Defence Groww URL instead of default Flexi Cap |
| P0-EC-28 | P3 | Citation points to `hdfcfund.com` in design doc examples | Update examples to allowlisted Groww URLs only |

---

## Phase 0 test checklist

- [ ] `allowed_urls.length === 20`
- [ ] Every manifest URL ∈ known twenty-slug set
- [ ] Every `scheme_id` in manifest has matching `schemes.json` entry with same `groww_url`
- [ ] README states no AMC/AMFI/SEBI ingestion for this project
- [ ] Flexi Cap aliases documented for `hdfc-equity-fund-direct-growth`
