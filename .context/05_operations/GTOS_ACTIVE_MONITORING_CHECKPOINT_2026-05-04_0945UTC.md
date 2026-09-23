# GTOS Active Monitoring Checkpoint - 2026-05-04 09:45 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: live system health plus live-shadow/follow-data outcome monitoring

## System Health

- Local check time: `2026-05-04T17:45:39+08:00`.
- Latest monitor candle: `2026-05-04T09:45:00+00:00`.
- `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- `scripts\verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, JSONL rows inspected `24385`.
- No AI calls, canary calls, order calls, execution calls, or paid Databento calls were made by the monitoring/follow scripts.

## Shadow Follow Pass

At `09:45 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=13`
- `candidate_path_follow.jsonl`: `13` new rows
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `208` new rows, `1264` seen
- `live_candidate_strategy_rollups.jsonl`: `13` new rows
- V2b/pre-fill/FVG/LTF/missed-opportunity/source/account/pending-join rows advanced as expected
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

## Production Versus Shadow Snapshot

Production as of `09:45 UTC`:

- `NAS100_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- `XAUUSD_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- XAGUSD candidates from `07:15` through `09:45`: production path `REJECTED_L2`, blocked by `m15_choch_exists`.
- Open positions: `0`.

Shadow/path outcomes as of `09:45 UTC`:

- `5` XAGUSD candidates reached `ENTRY_TOUCHED_THEN_TP1`: `07:15`, `07:30`, `07:45`, `08:00`, `08:15`.
- `8` candidates reached `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: NAS100 `07:15`, XAUUSD `07:15`, and XAGUSD `08:30`, `08:45`, `09:00`, `09:15`, `09:30`, `09:45`.
- No candidate in the current shadow path set hit SL by `09:45 UTC`.

Interpretation: today's live-shadow sample is materially ahead of production behavior on path outcome, but remains shadow-only and non-promotional. It supports investigation into L2 `m15_choch_exists`, limit-entry strictness, and market/proximity-style comparator behavior; it does not authorize production gate changes.

## Known Boundaries

- Each candidate rollup still has `unresolved_strategy_count=8` for structural/FVG-lock V2/V3 variants whose exact decision-time fields were not present in old source rows.
- XAGUSD/SI Sierra depth remains `SOURCE_DEPTH_DEFINITION_BLOCKED_SI` and must not be treated as Databento-equivalent.
- `databento_live_confluence.jsonl`, BE, partial-close, and time-in-trade lanes remain documented waiting lanes.

## Next Monitoring Action

Continue active KZ cadence. On the next closed M15 candle or any new candidate/log anomaly, rerun:

- `python scripts\_live_monitor_iter.py`
- `python scripts\follow_live_candidate_paths.py --max-hours 12`
- `python scripts\verify_shadow_log_integrity.py`
