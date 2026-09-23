# V2B Forward Pair Collector Status - 2026-05-04

**Status:** `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Collector

- Helper: `src/research_infra/forward_capture.py::build_v2b_forward_pair_row`
- Log path: `shadow_logs/v2b_forward_pairs.jsonl`
- Current rows: `207`
- Forward trigger: Future qualifying post-cutoff setup/candidate/context row.

## Required Metadata

`schema_version`, `created_at_utc`, `symbol`, `broker_symbol`, `source_symbol`, `session`, `kill_zone`, `side`, `regime`, `candidate_id`, `trade_id`, `evidence_class`, `decision_time_utc`, `asof_cutoff_utc`, `source_file`, `source_hash`, `no_leak_status`, `promotion_verdict`
