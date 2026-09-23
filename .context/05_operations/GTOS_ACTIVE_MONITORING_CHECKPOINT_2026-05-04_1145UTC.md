# GTOS Active Monitoring Checkpoint - 2026-05-04 11:45 UTC

Status: active monitoring checkpoint
Scope: post-11:45 UTC M15 follow/shadow/data-health pass
Promotion posture: NO_PROMOTION_VERDICT

## Live Monitor

- `python scripts\_live_monitor_iter.py`: `iter=445`, `candle=2026-05-04T11:45:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No verified issue requiring restart.
- Restart standing approval exists from owner if a real component failure appears, but no restart is currently justified.

## Follow / Shadow Rows

`python scripts\follow_live_candidate_paths.py --max-hours 12`:

- `candidates_seen=17`
- `candidate_path_follow.jsonl`: `17` new rows
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `272` new rows
- `candidate_ltf_path_order.jsonl`: `17` new rows
- `v2b_forward_pair_resolutions.jsonl`: `17` new rows
- `prefill_delivery_path_resolutions.jsonl`: `17` new rows
- `fvg_ob_confluence_resolutions.jsonl`: `17` new rows
- `missed_opportunity_shadow.jsonl`: `17` new rows
- `live_candidate_opportunity_clusters.jsonl`: `17` new rows
- `live_candidate_strategy_rollups.jsonl`: `17` new rows
- blocker heartbeat rows: `external=6`, `ml=1`, `proxy=1`
- observer tick enrichment: `1`
- safety flags: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`

## Read-Only Checks

- `python scripts\summarize_live_shadow_opportunities.py`
  - Raw candidates: `17`
  - Countable primary opportunities: `5`
  - Duplicate active setup rows not counted as trades: `12`
  - Countable path labels: `entry_touched_then_reached_tp1=1`, `continued_without_entry_touch_to_tp_area=3`, `went_through_entry_and_continued_to_sl=1`
  - Entry-model proxy R:
    - `LIVE_AI_J46_J49_BASELINE_COMPARATOR=+0.5R`
    - `PENDING_LIMIT_LIFECYCLE=+0.5R`
    - `V2_STRUCT_OB_BOUNDARY=+1.5R`
    - `V2B_OB_BOUNDARY_PROSPECTIVE=+1.5R`
- `python scripts\verify_shadow_log_integrity.py`
  - `overall_status=OK_WITH_DOCUMENTED_WAITING_LANES`
  - `issues={}`
  - `jsonl_rows=27887`
- `python scripts\audit_live_shadow_data_health.py`
  - `status=OK_WITH_DOCUMENTED_LIMITATIONS`
  - `issues={}`
  - `latest_candidates=17`
  - `logs_inspected=18`
  - `raw_rows_inspected=4981`

## Limitations Still Honest

- Exact V2/V3 structural metadata remains `SOURCE_NOT_CAPTURED` for historical candidates and must not be fabricated.
- Databento paid live confluence remains not fetched in monitoring/backfill paths unless a predeclared trigger/budget lane is enabled.
- Sierra local capture is now verified through corrected roots; current readiness is documented separately in the 11:42 UTC checkpoint.
