# Mutual Fund FAQ Assistant

Facts-only Q&A assistant for HDFC mutual fund schemes, using a **closed corpus of five Groww scheme pages**. Built with a lightweight RAG architecture ([docs/phase-wise-architecture.md](docs/phase-wise-architecture.md)).

**Disclaimer:** Facts-only. No investment advice.

---

## Project scope (Phase 0)

| Item | Value |
|------|--------|
| **AMC** | HDFC Mutual Fund ([hdfcfund.com](http://www.hdfcfund.com) — metadata only, **not** in corpus) |
| **Corpus** | Exactly **5** Groww URLs — no AMC, AMFI, SEBI, or other pages |
| **Product context** | Groww-style fund facts (expense ratio, exit load, SIP minimum, benchmark, etc.) |

### Schemes in corpus

| Scheme | Category | Source |
|--------|----------|--------|
| HDFC Mid Cap Fund Direct Growth | Equity — Mid Cap | [Groww](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| HDFC Flexi Cap Direct Plan Growth | Equity — Flexi Cap | [Groww](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| HDFC Small Cap Fund Direct Growth | Equity — Small Cap | [Groww](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth) |
| HDFC Defence Fund Direct Growth | Equity — Thematic | [Groww](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth) |
| HDFC Silver ETF FoF Direct Growth | Commodities — Silver FoF | [Groww](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth) |

**Note:** The Flexi Cap scheme uses the Groww slug `hdfc-equity-fund-direct-growth`; alias **HDFC Equity Fund** is registered in `corpus/schemes.json`.

### Closed-corpus policy

- **Ingestion** may fetch only URLs listed in `corpus/manifest.yaml`.
- **Citations** in every answer or refusal must be one of those five URLs.
- **Default refusal citation:** Flexi Cap Groww page (`hdfc-equity-fund-direct-growth`).
- This project **does not** use the problem statement’s “15–25 official URLs” model; scope is intentionally limited to these five pages.

---

## Repository layout

```
├── corpus/           # manifest.yaml, schemes.json (Phase 0) ✓
├── app/
│   ├── corpus/       # Load & validate allowlist (Phase 0) ✓
│   ├── api/          # FastAPI — Phase 3, 5
│   ├── rag/          # Retrieval — Phase 2
│   └── guardrails/   # Classifier, validator — Phase 3
├── ingestion/        # Pipeline — Phase 1
├── ui/               # Chat UI — Phase 4
├── tests/            # Phase 0+ tests
├── scripts/          # validate_phase0.py
└── docs/             # Architecture & edge cases
```

### Implementation phases

| Phase | Status | Focus |
|-------|--------|--------|
| 0 | **Done** | Scope, manifest, schemes, validation |
| 1.1 | **Done** | Allowlist fetcher → `ingestion/raw/*.html` |
| 1.2 | **Done** | Parse & normalize → `ingestion/parsed/*.json` |
| 1.3 | **Done** | Chunking + provenance → `ingestion/chunks/*.jsonl` |
| 1.4 | **Done** | Embeddings + vector index → `data/chroma/` populated |
| 1.5 | **Done** | Metadata + footer dates |
| 1.6 | **Done** | Pipeline orchestration + smoke test |
| 2 | **Done** | Retrieval & context assembly |
| 3 | **Done** | LLM answers, guardrails, refusals |
| 4 | **Done** | Minimal UI |
| 5 | **Done** | Integration, health, README setup |
| 6 | Pending | Golden tests & sign-off |

---

## Setup (Phase 0)

```bash
cd Mileston2
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Validate corpus
python scripts/validate_phase0.py
pytest tests/test_phase0_corpus.py -v
```

### Phase 1.1 — Fetch allowlisted pages

```bash
python -m ingestion.fetch_all
pytest tests/test_phase1_1_fetcher.py -v
```

Copy environment template for later phases:

```bash
cp .env.example .env
```

---

## Architecture overview

Lightweight **RAG** pipeline:

1. Classify query (factual vs advisory vs performance).
2. Retrieve chunks from the five-page corpus only.
3. Generate ≤3 sentences with **one** allowlisted citation and footer date.
4. Refuse advice, comparisons, and PII-related queries.

Details: [docs/phase-wise-architecture.md](docs/phase-wise-architecture.md)  
Edge cases: [docs/edge-cases/](docs/edge-cases/README.md)

---

## Known limitations (project scope)

- No ELSS or large-cap scheme in the five-URL corpus.
- Facts come from Groww pages only; not verified against AMC factsheets in this milestone.
- English queries only (best effort).
- Groww HTML/layout changes may require re-ingestion (Phase 1).

---

## License

Academic / milestone project — see course requirements.
