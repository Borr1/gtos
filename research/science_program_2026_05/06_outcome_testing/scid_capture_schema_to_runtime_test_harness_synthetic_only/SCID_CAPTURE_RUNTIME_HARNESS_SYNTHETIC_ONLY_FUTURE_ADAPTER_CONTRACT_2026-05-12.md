# Future Runtime Adapter Contract

No adapter is wired in this route. A future implementation must provide a
pure function with this shape:

```python
def parse_capture_rows(source_bytes: bytes, schema_bundle_hash: str) -> HarnessValidationReport:
    ...
```

Required adapter behavior:
- Accept append-only JSONL or equivalent structured rows only.
- Recompute or verify `source_hash` before validation.
- Preserve `candidate_input_row_id` and `duplicate_proxy_denominator_key`.
- Validate every row through the accepted schema bundle before any downstream use.
- Fail closed on missing fields, stale as-of timestamps, forbidden identifiers,
  unsafe flags, schema-version mismatches, duplicate-key drift, and unavailable
  non-market-context source status.
- Keep broker/account/order/deal/position records, raw market blobs, AI/API,
  validation/result labels, strategy edge claims, and live behavior outside this
  adapter unless a later CEO-approved route explicitly changes scope.
