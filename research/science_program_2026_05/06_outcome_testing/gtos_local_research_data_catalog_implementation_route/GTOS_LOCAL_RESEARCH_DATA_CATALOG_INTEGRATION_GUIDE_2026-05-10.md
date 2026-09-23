# GTOS Local Research Data Catalog Integration Guide

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Use In Future Goal Prompts

Run the route-local builder before any data-absence claim:

```powershell
python research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py
```

Then inspect:

- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_2026-05-10.jsonl` for bounded local source/control rows.
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json` for positive and negative query evidence.
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_2026-05-10.json` for recoverable market-data versus source-state gaps.
- `GTOS_LOCAL_RESEARCH_DATA_CATALOG_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_2026-05-10.json` for exact owner/export/read-only-extraction actions.

Catalog presence remains `SOURCE_CONTROL_ONLY`; it does not make any file validation-safe or promotable.
A future result lane must separately bind source hashes, as-of rules, duplicate policy, no-leak controls, and label family.
