# Ingestion (`ingestion`)

| Phase | Deliverables |
|-------|----------------|
| **1.1** ✓ | `phase1_1/fetcher.py`, `phase1_1/fetch_all.py` — allowlisted fetch → `raw/*.html` |
| **1.2** ✓ | parse → `parsed/*.json` |
| **1.3** ✓ | chunk → `chunks/*.jsonl` |
| **1.4** ✓ | embed + index → `../data/chroma/` |
| **1.5** ✓ | `metadata.py` → `corpus/last_updated.json`, `data/corpus_meta.db` |
| 1.6 | `run_pipeline.py` — full pipeline |

**Allowlist:** Only URLs in `corpus/manifest.yaml`. Fetcher aborts on any other URL.

## Phase 1.1 — Fetch

```bash
python -m ingestion.fetch_all              # fetch 5 URLs (~1 req/s)
python -m ingestion.fetch_all --force      # re-download
python -m ingestion.fetch_all --scheme-id hdfc-mid-cap-direct-growth
python -m ingestion.fetch_all --test-reject "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
```

| Path | Purpose |
|------|---------|
| `raw/{scheme_id}.html` | Cached HTML per allowlisted URL |
| `raw/{scheme_id}.meta.json` | `fetched_at`, `status_code`, `content_length` |
| `../data/chroma/` | Vector index (Phase 1.4) |
