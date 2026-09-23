# GTOS Active Monitoring Checkpoint - 2026-05-04 10:45 UTC

Status: active monitoring checkpoint
Promotion verdict: `NO_PROMOTION_VERDICT`
Scope: 10:45 closed-candle live monitor and shadow/follow-data update

## System Health

- Local check time: `2026-05-04T18:46:xx+08:00`.
- Latest monitor candle: `2026-05-04T10:45:00+00:00`.
- `scripts\_live_monitor_iter.py`: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- MT5 read-only check: initialized, `last_error=[1,"Success"]`, `orders=[]`, `positions=[]`.
- NAS100 recovery remains stable after the isolated restart: lock and heartbeat are on PID `7312`.
- No AI calls, canary calls, execution/order calls, or paid Databento calls were made by the monitoring/follow scripts.

## Shadow Follow Pass

At `10:46 UTC`, `scripts\follow_live_candidate_paths.py --max-hours 12` reported:

- `candidates_seen=17`
- `candidate_path_follow.jsonl`: `17` new rows
- `live_mechanical_strategy_shadow_outcomes.jsonl`: `272` new rows, `2272` seen
- `observer_tick_enrichment`: `1` new EURUSD row, duplicate-safe for existing rows
- Gap-closure rows advanced: LTF path `17`, FVG/OB resolutions `17`, live rollups `17`, missed-opportunity `17`, pending-limit join `1`, pre-fill resolutions `17`, V2b resolutions `17`
- The 15-minute blocker heartbeat bucket advanced and wrote: external source blocker `6`, ML status `1`, proxy blocker `1`
- `no_ai_calls=true`
- `no_canary_required=true`
- `no_execution=true`
- `paid_data_calls=0`
- `paid_fetch_attempted=false`

`scripts\verify_shadow_log_integrity.py` after the follow pass:

- Overall status: `OK_WITH_DOCUMENTED_WAITING_LANES`
- `issues={}`
- JSONL rows inspected: `26069`

## Candidate Path State

Latest candidate-path distribution:

- `ENTRY_TOUCHED_THEN_TP1=5`
- `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH=11`
- `ENTRY_TOUCHED_THEN_SL=1`

Latest notable rows:

- XAGUSD `09:00` through `10:30`: still `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH` as of `10:45 UTC`.
- NAS100 `10:30`: still `ENTRY_TOUCHED_THEN_SL` as of `10:45 UTC`; production blocked it via `REJECTED_GATE1_SAFETY`, so this is shadow-only evidence.

## Pending Limit State

- NAS100 `lim_2026-05-04_0715`: cancelled wrong-side at `10:15 UTC` with `cancel_reason=price_beyond_sl`; no broker order.
- XAUUSD `lim_2026-05-04_0715`: internal pending lifecycle remains `no_fill_still_pending` at the outside-KZ `10:45 UTC` check. MT5 broker orders are empty, so this is internal intent tracking, not a broker-side pending order.

## Known Boundaries

- `databento_live_confluence.jsonl`, BE, partial-close, time-in-trade, and `ml_shadow_predictions.jsonl` remain documented waiting/approval/paid-data lanes.
- V2/V3 structural variants remain `NOT_SCORED` where exact decision-time metadata is absent.
- Shadow path and mechanical rows remain observational only.

## Next Monitoring Action

Continue active KZ cadence while GBPUSD London observer remains active until `12:00 UTC`; next closed-candle checkpoint expected at `11:00 UTC` unless an urgent/serious issue appears earlier.
