# GTOS Active Monitoring Checkpoint - 2026-05-04 13:00 UTC

Status: monitoring continues under active goal
Owner: Codex
Scope: NY boundary follow/audit pass

## Control Plane

- `scripts\_live_monitor_iter.py` at the 13:00 UTC candle: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No restart is justified at this checkpoint.
- This is the NY boundary pass for XAUUSD, NAS100, XAGUSD, USDJPY, GBPJPY, and GBPUSD observer lanes. US30 NY starts at 13:30 UTC.

## Follow Pass

`python scripts\follow_live_candidate_paths.py --max-hours 12` completed after the 13:00 candle with:

- `candidates_seen=17`
- `candidate_path_follow` rows seen after write: 295
- `live_mechanical_strategy_shadow_outcomes` rows seen after write: 4720
- Fresh rows written for candidate path follow, mechanical strategy shadows, LTF path order, V2b, prefill, FVG/OB, missed-opportunity, opportunity clusters, candidate strategy rollups, blocker/status rows, and observer tick enrichment.
- Safety flags stayed clean: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Shadow Health

- Opportunity summary: 17 raw candidates, 5 countable primary unique opportunities, 12 duplicate active setup rows retained as evidence but not trade-counted.
- Countable path labels changed to: 2 no-entry TP-area moves, 1 entry then TP1, and 2 `M15_PATH_AMBIGUOUS_TP1_AND_SL`.
- Raw path labels: 10 no-entry TP-area moves, 5 entry then TP1, and 2 M15-ambiguous TP1/SL rows.
- Integrity verifier: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, `jsonl_rows=30032`.
- Semantic data-health audit: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`, `latest_candidates=17`, `raw_rows_inspected=7021`.
- Documented `SOURCE_NOT_CAPTURED` fields remain unchanged and must not be synthesized from later candles.

## Strategy Snapshot

Duplicate-aware countable proxy-R currently reports:

- `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `+1.5R` across 5 counted rows.
- `PENDING_LIMIT_LIFECYCLE`: `+1.5R` across 5 counted rows.
- `V2_STRUCT_OB_BOUNDARY`: `+1.5R` across 4 counted/scored rows, with 1 non-applicable countable row.
- `V2B_OB_BOUNDARY_PROSPECTIVE`: `+1.5R` across 4 counted/scored rows, with 1 non-applicable countable row.

Interpretation caveat: the two M15-ambiguous rows are not cleanly resolved wins or losses from M15 alone. Treat the current proxy-R as the tool's path-bounded entry-model score, not as broker-realized production R or a final lower-timeframe ordering verdict.

## Next

- Run the 13:15 UTC active-KZ monitor/follow/read sequence after the next M15 candle closes.
- Watch XAUUSD after the skip-first-NY-candle window, and watch JPY/GBPUSD observer lanes for new candidate rows.
- At 13:30 UTC, tighten checks for US30 NY start while NAS100 continues inside its 13:00-17:00 configured NY window.
