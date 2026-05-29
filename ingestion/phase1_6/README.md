# Phase 1.6 — Orchestration and smoke test

This phase provides:

- `ingestion/run_pipeline.py`: runs Phase 1 steps end-to-end (`fetch` → `parse` → `chunk` → `index` → `metadata`)
- `ingestion/smoke_retrieval.py`: runs a small set of similarity queries against Chroma and prints top hits
