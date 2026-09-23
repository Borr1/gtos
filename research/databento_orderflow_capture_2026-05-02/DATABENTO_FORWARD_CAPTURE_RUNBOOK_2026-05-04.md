# Databento Forward Capture Runbook - 2026-05-04

**Status:** `RESEARCH_ARTIFACT_DONE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Manifest

- Request ledger: `research\databento_orderflow_capture_2026-05-02\databento_forward_requests_2026-05-04.jsonl`
- Declared rows: `5`

## Policy

- Use cached data first.
- Before any paid pull, write a request row with dataset, schema, symbol, window, reason, expected fields, expected cost, and no-leak policy.
- Fetch only declared windows.
- Do not use a fetched window for both tuning and validation.
- Record actual cost and cache path after any fetch.

## Future Fetch Trigger

Run declared fetch through scripts/fetch_databento_manifest.py or a future dedicated wrapper after API/network approval and cost cap confirmation.

## Approval Command Pattern

`python scripts/fetch_databento_manifest.py --manifest <declared_manifest> --output-dir data/external/raw/databento_forward --cost-cap-usd <cap>`
