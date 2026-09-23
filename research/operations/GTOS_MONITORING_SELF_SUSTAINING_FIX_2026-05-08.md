# GTOS Monitoring Self-Sustaining Fix - 2026-05-08

**Generated:** 2026-05-08T08:54:41Z  
**Scope:** Infrastructure/data-quality only. No prompt, trading-logic, risk, execution, or live decision behavior changes.

## Fixed

- Added `scripts/run_live_monitoring_maintenance.py` as a single read-only maintenance wrapper for the live-shadow chain.
- Expanded maintenance catch-up to 72 hours by default so a monitoring gap does not strand candidate path, Sierra status, lifecycle, K55, and downstream audit rows.
- Added a no-AI/no-order `run_shadow_observer.py --once` refresh inside the maintenance chain before observer-dependent readiness audits.
- Corrected audit semantics for explicit waiting rows:
  - `live_candidate_opportunity_clusters.jsonl.asof_latest_candle_utc`
  - `live_candidate_strategy_rollups.jsonl.asof_latest_candle_utc`
- Corrected trade-record/candidate comparison to use effective M5-refined trade geometry when `instrumentation.m5_refinement_details.applied=true`.
- Corrected stale internal-only pending limit intent handling: aged `INTERNAL_CANDLE_POLLED_INTENT` rows with no broker order/ticket/order-send evidence are now documented as stale internal limitations, not live action-required pending orders.
- Allowed append-only audit refresh rows to supersede old rows for pending-limit and trade-index lifecycle audits, while aggregate contract checks still verify the latest row by key.
- Reordered K55 after Sierra/orderflow dependencies so row keys match the final source dependency signature for the maintenance pass.

## Verification

- `python -m py_compile scripts\run_live_monitoring_maintenance.py scripts\audit_live_shadow_data_health.py scripts\verify_shadow_log_integrity.py scripts\backfill_pending_limit_lifecycle_audit.py scripts\backfill_trade_index_lifecycle_audit.py src\research_infra\pending_limit_lifecycle_audit.py` -> pass
- Focused pytest with Windows temp-dir mode workaround:
  - `tests\test_pending_limit_lifecycle_audit.py`
  - `tests\test_live_shadow_data_health_audit.py`
  - `tests\test_verify_shadow_log_integrity.py`
  - Result: `94 passed`
- `python scripts\run_live_monitoring_maintenance.py --max-hours 72 --step-timeout-seconds 300`
  - `status=MAINTENANCE_SEQUENCE_COMPLETED`
  - `failed_steps=[]`
  - `final_integrity_status=OK_WITH_DOCUMENTED_WAITING_LANES`
  - `final_data_health_status=OK_WITH_DOCUMENTED_LIMITATIONS`
- Standalone final verifiers:
  - `python scripts\verify_shadow_log_integrity.py`
    - `overall_status=OK_WITH_DOCUMENTED_WAITING_LANES`
    - `issues={}`
    - `jsonl_files=94`, `jsonl_rows=112961`
  - `python scripts\audit_live_shadow_data_health.py`
    - `status=OK_WITH_DOCUMENTED_LIMITATIONS`
    - `issue_count=0`
    - `latest_candidates=143`

## Remaining Documented Limitations

- BE, partial-close, and time-in-trade logs remain event-only waiting lanes; no-event proof is carried by `exit_management_shadow_status.jsonl`.
- Structural source fields that were never captured at decision time remain documented limitations, not recoverable backfills:
  - `cost_aware_min_r_fields`
  - `fvg_lock_state`
  - `post_lock_reentry_state`
  - `standalone_fvg_entry_geometry`
  - `structural_lock_event_time_price`
  - `swing_protected_lock_level`

