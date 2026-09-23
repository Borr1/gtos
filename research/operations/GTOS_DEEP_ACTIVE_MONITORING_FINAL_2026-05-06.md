# GTOS Deep Active Monitoring Final Report - 2026-05-06

Generated: 2026-05-06 17:12 UTC

Promotion posture: `NO_PROMOTION_VERDICT`

## Overall Status

- Overall readiness: `COMPLETE_WITH_DOCUMENTED_LIMITATIONS`.
- Production safety: clean. Final MT5 truth showed balance/equity/free margin `101223.36`, `trade_allowed=True`, broker positions `0`, broker orders `0`.
- Final monitor: `_live_monitor_iter.py` iter `769`, candle `2026-05-06T17:00:00+00:00`, `crit=0`, `anom=0`, `pids=1`, `open_pos=0`.
- Trading behavior changed: none. No prompt, risk, execution, safety-gate, selector, or order-behavior promotion.
- Code/context changes made during monitoring: `9dec9be5 fix: recover stale live data monitoring`; `64895cf1 docs: record stale data monitoring incident`.

## Production Safety Status

| Area | Status | Evidence |
|---|---|---|
| Broker account | `OK_FLAT` | MT5 account `0`, balance/equity/free margin `101223.36` |
| Broker exposure | `OK_NONE` | positions `0`, orders `0` |
| Active GTOS sessions | `CLOSED` | all configured KZ windows ended by 17:00 UTC |
| Active process after close | `EXPECTED_WITH_PENDING` | one NAS100 orchestrator remains for internal pending intent |
| Watchdog | `WARN_CANARY_ONLY` | `WATCHDOG E2E: WARN`; only owner-approved stale canary cache |
| Tick capture | `OK_FRESH` | all seven daemon progress heartbeats fresh at close |
| Data health | `OK_WITH_DOCUMENTED_LIMITATIONS` | `issue_count=0`, latest candidates `86` |
| Shadow integrity | `OK_WITH_DOCUMENTED_WAITING_LANES` | JSONL issues `{}` |

## Process / MT5 / Sierra / Storage

- MT5 was readable at close and confirmed zero exposure.
- XAUUSD and XAGUSD shut down cleanly after NY close.
- NAS100 PID remained alive because internal pending intent `lim_NAS100_2026-05-06_071526` is still candle-polled.
- Sierra Chart process `SierraChart_64` was running/responding. Latest checked `.depth` writes for GC/NQ/SI were around 16:29-16:31 UTC and latest `.scid` writes around 16:34 UTC, so source/orderflow evidence remains status/context only at close.
- Databento live remained disabled/no API key; paid data calls `0`.
- Notification queue worker last logged startup PID `21908` on 2026-05-06.
- Storage check required escalated read-only access and returned C: free space `58.35 GB` of `237.6 GB`.

## Candidate And Pending Lifecycle

| Metric | Value |
|---|---:|
| Raw candidates latest cluster | `86` |
| Unique opportunity IDs | `22` |
| Countable primary opportunities | `21` |
| Duplicate active setups | `64` |
| Same-symbol overlap blocked | `1` |

Latest countable path labels:

- `continued_without_entry_touch_to_tp_area`: `8`
- `entry_touched_then_reached_tp1`: `1`
- `entry_touched_tp_and_sl_m15_ambiguous`: `2`
- `went_through_entry_and_continued_to_sl`: `10`

Per-symbol countable opportunities:

- GBPJPY `5`, NAS100 `5`, XAGUSD `5`, XAUUSD `4`, US30_cash `1`, USDJPY `1`.

Open internal pending:

| Intent | Symbol | Side | Entry / SL / TP1 | Broker state | Path state |
|---|---|---|---|---|---|
| `lim_NAS100_2026-05-06_071526` | NAS100 | LONG | `27646.2 / 27580.9 / 27744.1` | no broker order, no ticket, no position | TP area reached without entry touch; internal still pending |

This is a design limitation, not broker exposure. Current internal pending logic does not cancel solely because price reached TP area without touching entry.

## Market Tape Timeline

### Tokyo

- USDJPY and GBPJPY moved, but production stayed flat.
- USDJPY was mainly blocked by multi-timeframe conflict.
- GBPJPY had deterministic bullish checks but no qualifying H1 POI or AI no-trade outcomes.

### London

- XAUUSD expired-POI event: yesterday's old short POI touched/rejected before/around London, then later invalidated through old SL. The eventual path confirmed that forcing the old setup back into execution would have lost.
- The expired-POI limitation was engineered into a shadow watcher, then terminal-close hardening prevented duplicate/stale active watches.
- Multi-market burst: indices, metals, GBPUSD moved higher while USDJPY stayed heavy. US30/NAS100/XAUUSD/XAGUSD all had major tape movement that needed AI observation rows because not every market event was a production candidate.
- US30 09:15 rejected L2 path later reached TP area without touching entry: market intelligence, not broker PnL.
- XAGUSD rejected short went adverse and hit SL area by path, confirming the L2 rejection protected the account.

### NY

- No broker trades, no broker orders, no broker positions.
- XAUUSD/XAGUSD/NAS100 late-NY monitoring was interrupted by stale MT5 sessions after the internet outage. The issue was fixed and verified before close.
- Final NY close was broker-flat, data-health clean, and source/orderflow status-only.

## Shadow / ML / Strategy Observations

Current countable proxy-R does not prove improvement:

- `LIVE_AI_J46_J49_BASELINE_COMPARATOR`: `-8.5R` over `19` counted rows.
- `PENDING_LIMIT_LIFECYCLE`: `-6.5R` over `20` counted rows.
- `V2_STRUCT_OB_BOUNDARY` / `V2B_OB_BOUNDARY_PROSPECTIVE`: `-7.5R` over `16` counted rows.
- K55 rows refreshed but remain `NO_PROMOTION_VERDICT`; model artifact/inference limitations remain.
- V2 structural selector remains `NOT_READY`.

Do not claim the shadow systems are better than production from this sample. The current forward evidence is negative or insufficient.

## Source / Orderflow Status

- Sierra local source context exists, but several lanes remain source-status only.
- US30/YM has registered proxy context; full depth feature extraction is still pending/deferred where heavy files require guarded scans.
- NAS100/NQ Databento trigger metadata exists, but Databento live was disabled/no API key.
- XAGUSD/SI depth exists but remains source-definition blocked and cannot be interpreted as promoted orderflow.
- GBPJPY still lacks a clean registered futures/orderflow proxy.
- LTO031/LTO032 May 6 source-unblocking audit remains research/source-readiness only: no source/model promoted, no paid fetch, no validation-safe external bundle, FlashAlpha forward-context only, and `NO_PROMOTION_VERDICT`.

## Incidents, Fixes, And False Positives

- Expired POI limitation: XAUUSD old short was owner-reapproved visually but no approved GTOS execution path existed. Shadow watcher and terminal-close hardening now preserve and close this context correctly. The setup later invalidated at old SL.
- MT5 IPC outage: direct MT5 account reads failed around 11:20 UTC; relaunch/reconnect recovered account truth and confirmed zero exposure.
- Stale data liveness gap: PIDs/heartbeats were fresh but strategy evaluations and tick-capture progress stopped after the internet interruption. Commit `9dec9be5` fixed the source issue and watchdog coverage; the affected components were restarted safely.
- Equity anomaly JSONL corruption: two malformed rows were repaired, and the source writer now uses locked JSONL writing.
- Canary warning: watchdog canary cache remains stale by design under owner-approved cost-control skip until 2026-12-31.

## Open Blockers And Triggers

- Internal pending stale-opportunity policy: decide whether a pending intent should cancel when TP area is reached without entry touch.
- Stale-data recovery monitoring: continue treating PID/heartbeat freshness as insufficient; active KZ health must include strategy-evaluation freshness and tick `last_progress_utc`.
- Broker actual-R sample growth remains the promotion bottleneck.
- Databento live license/API and paid-source approval remain blocked.
- SI/XAGUSD depth semantics remain blocked.
- K55 model artifact/inference remains not promotion-ready.
- V2 readiness remains `NOT_READY` until broker actual-R / lifecycle / metadata floors are met.

## Final Posture

Monitoring for 2026-05-06 is complete. Production remained broker-flat and safe. The day produced useful operational fixes and research intelligence, but no live strategy, source, ML, risk, prompt, or execution rule is promoted.

Final verdict: `NO_PROMOTION_VERDICT`.
