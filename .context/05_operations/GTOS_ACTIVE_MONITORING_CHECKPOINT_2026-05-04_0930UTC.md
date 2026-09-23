# GTOS Active Monitoring Checkpoint - 2026-05-04 09:30 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: live system health plus live-shadow/follow-data outcome monitoring

## Commands Run

- `python scripts\generate_live_state.py`
- `python scripts\_live_monitor_iter.py`
- `python scripts\follow_live_candidate_paths.py --max-hours 12`
- `python scripts\verify_shadow_log_integrity.py`
- `python scripts\verify_forward_capture_readiness.py --output-json research\program_control\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research\program_control\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`
- `python scripts\watchdog_e2e_verify.py --verbose`
- `python scripts\audit_live_shadow_followup_coverage.py --output-json research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`
- `python scripts\inspect_mt5_tick_availability.py --yes-live-readonly --window current_monitor:2026-05-04T09:20:00Z:2026-05-04T09:26:00Z`
- `python scripts\build_sierra_forward_capture_inventory.py --output-json research\program_control\SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json --output-md research\program_control\SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md`

## System Health

- Local check time: `2026-05-04T17:30:56+08:00`.
- Latest monitor candle: `2026-05-04T09:30:00+00:00`.
- `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- MT5 read-only tick probe: all 7 core symbols returned ticks for `2026-05-04T09:20:00Z` through `09:26:00Z`; terminal connected; no probe errors; no orders sent.
- Orchestrator heartbeats: 7 fresh heartbeat files observed around `09:28 UTC`.
- Tick-capture states: all 7 `.state.json` files present; latest observed mtimes ranged from `09:20:58 UTC` to `09:27:28 UTC`, with lower-cadence symbols treated by market/session context.
- Watchdog E2E: `PASS (PASS=4 WARN=0 FAIL=0)`.
- Forward-capture readiness: `OK=12`, `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE_OR_NOT_YET_WIRED=1`.
- Shadow integrity: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, JSONL rows inspected `24031`.
- Disk free: `62.09 GB` on `C:\`.
- Sierra process: `SierraChart_64` observed running.
- Sierra `.depth` writes: current-day files observed, newest `SIM26-COMEX.2026-05-04.depth` at `09:15:21 UTC`; `NQM26-CME.2026-05-04.depth` at `09:03:05 UTC`; inventory remains partial with `READY_SCID_AND_DEPTH_PRESENT=1` and `BLOCKED_MISSING_LOCAL_SIERRA_FILES=17`.
- Notification queue: latest queued alert was marked `DELIVERED`; worker lock PID `13728` exists.

## Shadow Follow Pass

At `09:30 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=12`
- `candidate_path_follow.jsonl`: `12` new rows
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `192` new rows, `1056` seen
- `live_candidate_strategy_rollups.jsonl`: `12` new rows
- V2b/pre-fill/FVG/LTF/missed-opportunity/source/account/pending-join rows advanced as expected
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

## Candidate Outcomes As Of 09:30 UTC

- `NAS100_2026-05-04T07:15:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production limit remains not filled.
- `XAUUSD_2026-05-04T07:15:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production limit remains not filled.
- `XAGUSD_2026-05-04T07:15:00+00:00`: `ENTRY_TOUCHED_THEN_TP1`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is shadow-only.
- `XAGUSD_2026-05-04T07:30:00+00:00`: `ENTRY_TOUCHED_THEN_TP1`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is shadow-only.
- `XAGUSD_2026-05-04T07:45:00+00:00`: `ENTRY_TOUCHED_THEN_TP1`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is shadow-only.
- `XAGUSD_2026-05-04T08:00:00+00:00`: `ENTRY_TOUCHED_THEN_TP1`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is shadow-only.
- `XAGUSD_2026-05-04T08:15:00+00:00`: `ENTRY_TOUCHED_THEN_TP1`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is shadow-only.
- `XAGUSD_2026-05-04T08:30:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is a shadow-only missed market/proximity-style move, not a filled GTOS trade.
- `XAGUSD_2026-05-04T08:45:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is a shadow-only missed market/proximity-style move, not a filled GTOS trade.
- `XAGUSD_2026-05-04T09:00:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is a shadow-only missed market/proximity-style move, not a filled GTOS trade.
- `XAGUSD_2026-05-04T09:15:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is a shadow-only missed market/proximity-style move, not a filled GTOS trade.
- `XAGUSD_2026-05-04T09:30:00+00:00`: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`; production path was `REJECTED_L2` on `m15_choch_exists`, so this is a shadow-only missed market/proximity-style move, not a filled GTOS trade.

## Known Boundaries

- Each candidate rollup still has `unresolved_strategy_count=8` for the structural/FVG-lock V2/V3 variants whose exact decision-time fields were not present in the old source rows. Keep `SOURCE_NOT_CAPTURED` / missing metadata markers; do not reconstruct from later candles.
- XAGUSD/SI Sierra depth rows have `parity=SOURCE_DEPTH_DEFINITION_BLOCKED_SI` and `interpretation=BLOCKED_DO_NOT_TREAT_AS_DATABENTO_EQUIVALENT`.
- `databento_live_confluence.jsonl` remains a documented waiting lane because no explicit paid/live trigger was enabled.
- BE, partial close, and time-in-trade lanes remain event-driven waiting lanes until a fill/exit trigger exists.

## Next Monitoring Action

Continue active KZ cadence. On the next closed M15 candle, rerun:

- `python scripts\_live_monitor_iter.py`
- `python scripts\follow_live_candidate_paths.py --max-hours 12`
- `python scripts\verify_shadow_log_integrity.py`

Report any new candidate, shadow-only TP/SL/outcome transition, stale candidate-triggered log, production pending-limit state change, or verifier issue immediately.
