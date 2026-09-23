# Shadow JSONL Repair - 2026-05-04

**Schema:** `shadow_jsonl_repair_report_v1`
**Source:** `shadow_logs\d1_bias_lag.jsonl`
**Status:** `REPAIRED_WITH_QUARANTINED_FRAGMENTS`
**Raw backup:** `research\program_control\raw_shadow_log_quarantine\d1_bias_lag.jsonl.raw_20260504T080331Z_bc2a992877b0.bak`
**Quarantine:** `shadow_logs\d1_bias_lag_recovery.jsonl`

## Counts

- Raw lines: `336`
- Valid JSON object rows kept: `333`
- Invalid fragments quarantined: `3`
- Invalid line numbers: `[153, 230, 241]`

## Policy

Invalid fragments were not promoted into canonical shadow rows because exact timestamps and full fields were not recoverable from the raw log alone.
