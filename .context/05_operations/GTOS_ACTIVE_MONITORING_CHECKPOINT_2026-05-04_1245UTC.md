# GTOS Active Monitoring Checkpoint - 2026-05-04 12:45 UTC

Status: monitoring continues under active goal
Owner: Codex
Scope: final pre-NY follow/audit pass

## Control Plane

- `scripts\_live_monitor_iter.py` at the 12:45 UTC candle: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No restart is justified at this checkpoint.

## Follow Pass

`python scripts\follow_live_candidate_paths.py --max-hours 12` completed with:

- `candidates_seen=17`
- `candidate_path_follow` rows written: 17
- `live_mechanical_strategy_shadow_outcomes` rows written: 272
- Resolution/rollup rows written for LTF path order, V2b, prefill, FVG/OB, missed opportunity, opportunity clusters, and candidate strategy rollups.
- Safety flags stayed clean: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Shadow Health

- Opportunity summary: 17 raw candidates, 5 countable primary unique opportunities, 12 duplicate active setup rows retained as evidence but not trade-counted.
- Countable path labels remain: 3 no-entry TP-area moves, 1 entry then TP1, 1 entry then SL.
- Integrity verifier: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
- Semantic data-health audit: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=17`, `raw_rows_inspected=6613`.

## Strategy Snapshot

Countable proxy-R remains:

- `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `+0.5R`
- `PENDING_LIMIT_LIFECYCLE`: `+0.5R`
- `V2_STRUCT_OB_BOUNDARY`: `+1.5R` on 4 counted rows, 1 non-OB/not applicable row.
- `V2B_OB_BOUNDARY_PROSPECTIVE`: `+1.5R` on 4 counted rows, 1 non-OB/not applicable row.

Context-only and metadata-blocked strategies remain preserved without synthetic R.

## Next

- NY monitoring starts at 13:00 UTC for XAUUSD, NAS100, XAGUSD, USDJPY, GBPJPY, and GBPUSD observer, with XAUUSD skip-first-NY-candle behavior still production-owned.
- US30 NY starts at 13:30 UTC.
- Continue running follow writer only after new M15 candles, followed by summary, integrity, and data-health readers in order.
