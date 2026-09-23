# GTOS Active Monitoring Checkpoint - 2026-05-04 10:00 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: live system health plus live-shadow/follow-data outcome monitoring

## System Health

- Local check time: `2026-05-04T18:04:49+08:00`.
- Latest monitor candle: `2026-05-04T10:00:00+00:00`.
- `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- `scripts\verify_shadow_log_integrity.py`: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`, JSONL rows inspected `24763`.
- No AI calls, canary calls, order calls, execution calls, or paid Databento calls were made by the monitoring/follow scripts.

## Shadow Follow Pass

At `10:04 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=14`
- `candidate_path_follow.jsonl`: `93` rows seen, `0` new rows in this pass because all 14 candidate/as-of pairs were already present.
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `1488` rows seen, `0` new rows in this pass because all candidate/strategy/as-of rows were already present.
- Gap-closure rows written in this pass: `0` across account truth, V2b, pre-fill, FVG/OB, LTF path, missed-opportunity, candidate rollup, Sierra, Databento trigger, and pending-join lanes.
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

## Production Versus Shadow Snapshot

Production as of `10:00 UTC`:

- `NAS100_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- `XAUUSD_2026-05-04T07:15:00+00:00`: production limit placed, still not filled.
- XAGUSD `07:15` through `09:45`: production path `REJECTED_L2`, blocked by `m15_choch_exists`.
- XAGUSD `10:00`: production path `REJECTED_GATE1_SAFETY`; L2 passed, then Gate1 touch-count safety rejected the candidate.
- Open positions: `0`.

Shadow/path outcomes as of `10:00 UTC`:

- `5` XAGUSD candidates reached `ENTRY_TOUCHED_THEN_TP1`: `07:15`, `07:30`, `07:45`, `08:00`, `08:15`.
- `9` candidates reached `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: NAS100 `07:15`, XAUUSD `07:15`, and XAGUSD `08:30`, `08:45`, `09:00`, `09:15`, `09:30`, `09:45`, `10:00`.
- No candidate in the current shadow path set hit SL by `10:00 UTC`.

## 10:00 XAGUSD Gate Detail

Latest candidate row:

- `candidate=XAGUSD 2026-05-04T10:00:00+00:00`
- `final_outcome_at_log=REJECTED_GATE1_SAFETY`
- `entry=75.471`
- `tp1=74.804`

L2 interpretation:

- `verification.passed=true` on the candidate row.
- The rejection was not L2. It was Gate1 touch-count safety.

Touch-count gate row:

- `timestamp_utc=2026-05-04T10:00:22.906606+00:00`
- `candidate_id=XAGUSD_2026-05-04T10_00_05_012689_00_00`
- `framework=ob_retest`
- `gate_target_ob_touch=2`
- `gate_threshold_at_eval=2`
- `gate_decision=REJECT`
- `gate_target_ob_id=XAGUSD_bearish_2026-05-04T03_00_00_00_00`
- `ob_low=75.471`
- `ob_high=75.789`

Interpretation: today's live-shadow sample remains materially ahead of production path outcome, but it is still shadow-only and non-promotional. The evidence now separates two production blockers: earlier XAGUSD rows were L2 `m15_choch_exists` rejects; the `10:00` XAGUSD row passed L2 and was rejected by Gate1 touch-count safety.

## Known Boundaries

- Each candidate rollup still has `unresolved_strategy_count=8` for structural/FVG-lock V2/V3 variants whose exact decision-time fields were not present in old source rows.
- XAGUSD/SI Sierra depth remains source-definition blocked for equivalence claims and must not be treated as Databento-equivalent.
- `databento_live_confluence.jsonl`, BE, partial-close, and time-in-trade lanes remain documented waiting lanes.

## Next Monitoring Action

Continue active KZ cadence. On the next closed M15 candle or any new candidate/log anomaly, rerun:

- `python scripts\_live_monitor_iter.py`
- `python scripts\follow_live_candidate_paths.py --max-hours 12`
- `python scripts\verify_shadow_log_integrity.py`
