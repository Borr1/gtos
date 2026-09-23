# GTOS Active Monitoring Checkpoint - 2026-05-04 10:15 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: live system health plus live-shadow/follow-data outcome monitoring

## System Health

- Local check time: `2026-05-04T18:15:20+08:00`.
- Latest monitor candle: `2026-05-04T10:15:00+00:00`.
- First `scripts\_live_monitor_iter.py`: `crit=0`, `anom=1`, `pids=7`, `open_pos=0`.
- Anomaly detail: XAGUSD `hb_stale_in_kz` at `60.6s`, barely over threshold.
- Cross-check: XAGUSD evaluated the `10:15` candle, wrote candidate/feature/shadow rows, and `pipeline_state\heartbeat_XAGUSD.json` had `utc=2026-05-04T10:15:25.756797+00:00`.
- Immediate recheck `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- Classification: transient heartbeat-threshold false positive; no restart taken.
- `scripts\verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, JSONL rows inspected `25167`.
- No AI calls, canary calls, order calls, execution calls, or paid Databento calls were made by the monitoring/follow/backfill scripts.

## Shadow Follow Pass

At `10:15 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=15`
- `candidate_path_follow.jsonl`: `15` new rows
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `240` new rows, `1728` seen
- `observer_tick_enrichment`: `1` new EURUSD row, `duplicate_candidate_time=13`, `symbol_filtered=111`
- Gap-closure rows advanced: account truth `1`, LTF path `15`, Databento trigger `1`, FVG/OB resolutions `15`, rollups `15`, structural metadata `1`, missed-opportunity `15`, pending-join `2`, pre-fill resolutions `15`, Sierra status `1`, V2b resolutions `15`
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

## Production Versus Shadow Snapshot

Production as of `10:15 UTC`:

- `NAS100_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- `XAUUSD_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- XAGUSD `07:15` through `09:45`: production path `REJECTED_L2`, blocked by `m15_choch_exists`.
- XAGUSD `10:00` and `10:15`: production path `REJECTED_GATE1_SAFETY`; L2 passed, then Gate1 touch-count safety rejected the candidate.
- Open positions: `0`.

Shadow/path outcomes as of `10:15 UTC`:

- `5` XAGUSD candidates reached `ENTRY_TOUCHED_THEN_TP1`: `07:15`, `07:30`, `07:45`, `08:00`, `08:15`.
- `10` candidates reached `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: NAS100 `07:15`, XAUUSD `07:15`, and XAGUSD `08:30`, `08:45`, `09:00`, `09:15`, `09:30`, `09:45`, `10:00`, `10:15`.
- No candidate in the current shadow path set hit SL by `10:15 UTC`.

## 10:15 XAGUSD Gate Detail

Latest candidate row:

- `candidate=XAGUSD 2026-05-04T10:15:00+00:00`
- `final_outcome_at_log=REJECTED_GATE1_SAFETY`
- `entry=75.471`
- `tp1=74.76`

Touch-count gate row:

- `timestamp_utc=2026-05-04T10:15:23.491326+00:00`
- `candidate_id=XAGUSD_2026-05-04T10_15_05_144064_00_00`
- `framework=ob_retest`
- `gate_target_ob_touch=2`
- `gate_threshold_at_eval=2`
- `gate_decision=REJECT`
- `gate_target_ob_id=XAGUSD_bearish_2026-05-04T03_00_00_00_00`
- `ob_low=75.471`
- `ob_high=75.789`

Interpretation: the `10:15` XAGUSD candidate continues the same post-10:00 pattern: production L2 passed, but Gate1 touch-count safety blocked the trade; shadow path still records the candidate and observed price reaching TP area without production fill.

## Known Boundaries

- Each candidate rollup still has `unresolved_strategy_count=8` for structural/FVG-lock V2/V3 variants whose exact decision-time fields were not present in old source rows.
- XAGUSD/SI Sierra depth remains source-definition blocked for equivalence claims and must not be treated as Databento-equivalent.
- `databento_live_confluence.jsonl`, BE, partial-close, and time-in-trade lanes remain documented waiting lanes.

## Next Monitoring Action

Continue active KZ cadence. London KZ for XAUUSD/US30 ends at `10:30 UTC`; GBPUSD remains active until `12:00 UTC`.
