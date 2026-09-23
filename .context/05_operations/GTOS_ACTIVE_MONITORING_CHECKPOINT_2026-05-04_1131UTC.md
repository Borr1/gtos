# GTOS Active Monitoring Checkpoint - 2026-05-04 11:31 UTC

Status: active monitoring checkpoint
Scope: live-shadow data-health hardening and 11:30 UTC monitoring pass
Promotion posture: NO_PROMOTION_VERDICT

## Monitoring State

- `python scripts\_live_monitor_iter.py` after the 11:30 UTC candle: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- `python scripts\follow_live_candidate_paths.py --max-hours 12` saw `17` live candidates and wrote fresh 11:30 follow rows:
  - `candidate_path_follow.jsonl`: `17`
  - `live_mechanical_strategy_shadow_outcomes.jsonl`: `272`
  - `candidate_ltf_path_order.jsonl`: `17`
  - `v2b_forward_pair_resolutions.jsonl`: `17`
  - `prefill_delivery_path_resolutions.jsonl`: `17`
  - `fvg_ob_confluence_resolutions.jsonl`: `17`
  - `missed_opportunity_shadow.jsonl`: `17`
  - `live_candidate_opportunity_clusters.jsonl`: `17`
  - `live_candidate_strategy_rollups.jsonl`: `17`
  - blocker heartbeat rows: `external=6`, `ml=1`, `proxy=1`
  - observer tick enrichment: `1`
- Safety flags from the follow pass: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Data-Health Hardening

Added `scripts/audit_live_shadow_data_health.py` and `tests/test_live_shadow_data_health_audit.py`.

The new audit is read-only and checks:

- every live candidate has dependent rows across the shadow/follow logs,
- candidate identity fields do not conflict across latest or historical candidate-scoped rows,
- dependent rows do not reference candidate IDs absent from `strategy_follow_candidates.jsonl`,
- latest path-aligned logs use the same latest `asof_latest_candle_utc`,
- every registered candidate strategy has a latest mechanical row,
- rollup strategy sets match candidate snapshot strategy sets,
- opportunity-level duplicate counting has exactly one countable primary per opportunity,
- computed mechanical outcomes match path labels,
- Sierra/Databento confluence objects are present and no paid fetch occurred,
- critical null/empty fields are absent,
- allowed/event-dependent nulls are inventoried separately,
- `SOURCE_NOT_CAPTURED` limitations remain explicit and non-fabricated.

Important monitoring procedure update: do not run `follow_live_candidate_paths.py` in parallel with read-only summaries/verifiers. At 11:30 UTC, a parallel command batch briefly produced false data-health issues and an empty opportunity strategy summary because the readers observed files while the writer was still appending. Sequential rerun cleared it. The active goal prompt now requires: follow writer first, then sequential `summarize_live_shadow_opportunities.py`, `verify_shadow_log_integrity.py`, and `audit_live_shadow_data_health.py`.

## Verification

- `python -m py_compile scripts\audit_live_shadow_data_health.py scripts\summarize_live_shadow_opportunities.py`: passed.
- Targeted tests: `python -m pytest tests\test_live_shadow_data_health_audit.py tests\test_live_shadow_opportunity_summary.py tests\test_live_opportunity_dedupe.py tests\test_live_shadow_gap_closure.py tests\test_live_mechanical_shadow.py --basetemp C:\tmp\pytest_live_shadow_data_health_full3 -p no:cacheprovider`
  - Result: `24 passed`.
- `python scripts\verify_shadow_log_integrity.py`
  - `overall_status=OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=27433`.
- `python scripts\audit_live_shadow_data_health.py`
  - `status=OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=17`, `logs_inspected=18`, `raw_rows_inspected=4573`.

## Current Shadow Interpretation

- Raw candidates with latest opportunity clusters: `17`.
- Countable primary opportunities: `5`.
- Duplicate active setup rows not counted as trades: `12`.
- Countable path labels:
  - `entry_touched_then_reached_tp1`: `1`
  - `continued_without_entry_touch_to_tp_area`: `3`
  - `went_through_entry_and_continued_to_sl`: `1`
- Entry-model proxy R after duplicate-aware counting:
  - `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `+0.5R`
  - `PENDING_LIMIT_LIFECYCLE`: `+0.5R`
  - `V2_STRUCT_OB_BOUNDARY`: `+1.5R` over `4` R-counted rows
  - `V2B_OB_BOUNDARY_PROSPECTIVE`: `+1.5R` over `4` R-counted rows

## Known Honest Limitations

- `SOURCE_NOT_CAPTURED` remains for exact structural/V3 fields on all `17` candidates:
  - `cost_aware_min_r_fields`
  - `fvg_lock_state`
  - `post_lock_reentry_state`
  - `standalone_fvg_entry_geometry`
  - `structural_lock_event_time_price`
  - `swing_protected_lock_level`
- Affected strategy rows remain `NOT_SCORED`/`MISSING_REQUIRED_LIVE_METADATA`; do not backfill these unless an original decision-time row/file contains the exact missing value.
- Databento paid live confluence remains not fetched in the monitoring/backfill path: `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Next Monitoring Rule

During active KZ passes:

1. Run `_live_monitor_iter.py`.
2. Run `follow_live_candidate_paths.py --max-hours 12` and wait for it to finish.
3. Run `summarize_live_shadow_opportunities.py`.
4. Run `verify_shadow_log_integrity.py`.
5. Run `audit_live_shadow_data_health.py`.
6. Treat non-empty integrity/data-health issues as `SERIOUS` until verified.
