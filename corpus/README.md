# Corpus

Closed allowlist for the Mutual Fund FAQ Assistant.

| File | Purpose |
|------|---------|
| `manifest.yaml` | Authoritative list of **5** Groww URLs (ingestion + citations) |
| `schemes.json` | AMC metadata, scheme names, categories, aliases |
| `last_updated.json` | Per-scheme footer dates (filled in Phase 1) |

**Policy:** No URL outside `manifest.yaml` may be fetched, indexed, or cited.

Validate Phase 0:

```bash
python scripts/validate_phase0.py
```
