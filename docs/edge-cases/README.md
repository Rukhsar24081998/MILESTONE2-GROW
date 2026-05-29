# Phase Edge Cases

Edge-case catalogs for each implementation phase of the [Mutual Fund FAQ Assistant](../phase-wise-architecture.md).

| Phase | File | Focus |
|-------|------|--------|
| 0 | [phase-0-edge-cases.md](./phase-0-edge-cases.md) | Scope, manifest, schemes registry |
| 1 | [phase-1-edge-cases.md](./phase-1-edge-cases.md) | Ingestion, parsing, indexing |
| 2 | [phase-2-edge-cases.md](./phase-2-edge-cases.md) | Retrieval, context assembly |
| 3 | [phase-3-edge-cases.md](./phase-3-edge-cases.md) | Generation, guardrails, refusals |
| 4 | [phase-4-edge-cases.md](./phase-4-edge-cases.md) | Minimal UI |
| 5 | [phase-5-edge-cases.md](./phase-5-edge-cases.md) | Integration, ops, hardening |
| 6 | [phase-6-edge-cases.md](./phase-6-edge-cases.md) | Validation, golden tests, sign-off |

**Conventions**

- **Severity:** `P0` (blocker), `P1` (must handle), `P2` (should handle), `P3` (document/limitation)
- **ID format:** `P{n}-EC-{nn}` (phase number + edge-case number)
- **Closed corpus:** Only the [five Groww URLs](../phase-wise-architecture.md#closed-corpus--corpusmanifestyaml-authoritative-allowlist) are valid for ingestion and citations.
