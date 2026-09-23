# GTOS Active Monitoring Checkpoint - 2026-05-04 12:01 UTC

Status: monitoring continues under active goal
Owner: Codex
Scope: live control plane, candidate follow rows, shadow integrity, semantic data health, Sierra/Databento forward capture status

## Control Plane

- `scripts\_live_monitor_iter.py` at the 12:00 UTC candle: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No restart is justified at this checkpoint.
- Notification queue has no pending alert row; the queue file contains the prior heartbeat alert plus `DELIVERED` marker.
- Notification worker PID from `knowledge_base\meta\.notification_queue_worker.lock` is alive, and `logs\notification_queue_worker.log` shows the same PID as the latest worker startup.
- C: free space was approximately 60.76 GB during the pre-12:00 check.

## Follow Data

After the 12:00 UTC candle, `python scripts\follow_live_candidate_paths.py --max-hours 12` completed with:

- `candidates_seen=17`
- `candidate_path_follow` rows written: 17
- `live_mechanical_strategy_shadow_outcomes` rows written: 272
- Resolution/rollup rows written for LTF path order, V2b, prefill, FVG/OB, missed opportunity, opportunity clusters, and candidate strategy rollups.
- Safety flags remained clean: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Shadow Data Health

The dependent readers were run only after the follow writer finished:

1. `python scripts\summarize_live_shadow_opportunities.py`
2. `python scripts\verify_shadow_log_integrity.py`
3. `python scripts\audit_live_shadow_data_health.py`

Results:

- Opportunity summary: 17 raw candidates, 5 countable primary unique opportunities, 12 duplicate active setup rows retained as non-counted evidence.
- Countable path labels: 3 no-entry TP-area moves, 1 entry then TP1, 1 entry then SL.
- Integrity verifier: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
- Semantic data-health audit: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=17`, `logs_inspected=18`, `raw_rows_inspected=5389`.

## Strategy Comparison Snapshot

Countable opportunity proxy-R remains:

- `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `+0.5R` across 5 counted rows.
- `PENDING_LIMIT_LIFECYCLE`: `+0.5R` across 5 counted rows.
- `V2_STRUCT_OB_BOUNDARY`: `+1.5R` across 4 counted rows; 1 row was non-OB/not applicable.
- `V2B_OB_BOUNDARY_PROSPECTIVE`: `+1.5R` across 4 counted rows; 1 row was non-OB/not applicable.
- Context-only or metadata-blocked strategies are preserved in rows but not converted into synthetic R.

## External Confluence

- Sierra inventory refresh: 15 symbols `READY_SCID_AND_DEPTH_PRESENT`, 3 `CAUTION_SCID_PRESENT_DEPTH_MISSING`.
- The 3 Sierra cautions remain understood as non-primary/control lanes: VXM, VXMM, and XAUUSD SCID-only.
- Candidate rows contain Sierra depth features where applicable, including XAGUSD/SI and NAS100/NQ rows.
- Databento live confluence remains an explicit waiting lane because monitoring/backfill is not allowed to perform paid live fetches. Rows correctly show no paid fetch and zero paid calls.

## Limitations

The following historical fields remain `SOURCE_NOT_CAPTURED` for the 17 existing candidates and should not be synthesized from later candles:

- `cost_aware_min_r_fields`
- `fvg_lock_state`
- `post_lock_reentry_state`
- `standalone_fvg_entry_geometry`
- `structural_lock_event_time_price`
- `swing_protected_lock_level`

Backfill is only valid if an original decision-time source row/file contains the exact value.

## Next Cadence

- Continue between-KZ monitoring until NY approaches.
- Run `_live_monitor_iter.py` at least every 5-15 minutes outside active KZ and tighter near KZ boundaries.
- Run `follow_live_candidate_paths.py --max-hours 12` after each new M15 candle during active monitoring, then run summary, integrity, and data-health checks sequentially.
- Restart only a verified failing component; do not broad-restart the fleet without fleet-wide evidence.
