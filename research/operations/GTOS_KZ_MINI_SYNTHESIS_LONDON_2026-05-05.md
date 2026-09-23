# GTOS London KZ Mini-Synthesis - 2026-05-05

Generated: 2026-05-05 12:02 UTC

Verdict: `NO_PROMOTION_VERDICT`

## Scope

- Sessions covered: 2026-05-05 London coverage through GBPUSD close at 12:00 UTC.
- Evidence classes: `BROKER_ACCOUNT_TRUTH`, `FORWARD_SHADOW`, `INTERNAL_LIMIT_LIFECYCLE`, `MARKET_TAPE_READ_ONLY`, `SOURCE_STATUS_ONLY`.
- Trading behavior changed: none.
- AI/canary/paid-data policy: no live canary calls, no paid Databento calls, no execution changes.

## System Health

- Latest pulse: `_live_monitor_iter.py` iter `575`, candle `2026-05-05T12:00:00+00:00`.
- Status: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- Broker truth: MT5 connected and trade-enabled; redacted_account balance/equity `101223.36`; broker positions `0`; broker orders `0`; profit `0.0`.
- Final London verifier state: `verify_shadow_log_integrity.py` returned `OK_WITH_DOCUMENTED_WAITING_LANES`; `audit_live_shadow_data_health.py` returned `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.

## Candidate And Path Summary

- Raw 2026-05-05 candidates observed so far: `15`.
- London candidates: `14` (`NAS100=1`, `XAUUSD=2`, `XAGUSD=11`).
- GBPUSD London rows: pre-AI MSO rows every 15 minutes through 12:00 UTC, all `PRESCREEN_FAILED_PRE_AI`; no GBPUSD candidate, no AI call, no execution.
- Countability at close: `11` countable primary opportunities and `55` duplicate active setups in the current registry.
- London production `LIMIT_PLACED` rows:
  - `NAS100_2026-05-05T07:15:00+00:00`, LONG `27646.2 / 27598.4 / 27717.8`, internal `no_fill_still_pending`, broker order/position absent, path `continued_without_entry_touch_to_tp_area`.
  - `XAUUSD_2026-05-05T08:15:00+00:00`, SHORT `4668.45 / 4679.89 / 4651.28`, internal `no_fill_still_pending`, broker order/position absent, path `continued_without_entry_touch_to_tp_area`.
- Other notable London candidates:
  - `XAUUSD_2026-05-05T08:00:00+00:00` was `REJECTED_GATE1_SAFETY`; later path touched the rejected entry area, but no order existed.
  - `XAGUSD_2026-05-05T07:30:00+00:00` through `10:30:00+00:00` were repeated duplicate active short setup rows, all `REJECTED_L2`, all `continued_without_entry_touch_to_tp_area`.

## Market Tape

- GBPUSD: London late tape was two-sided but prescreen stayed blocked. It swept down to `1.35307` on the 11:15 candle, rejected up, failed near `1.35472`, and closed the 12:00 checkpoint near `1.35403`.
- XAUUSD: bounced hard from the 11:00 low area (`4539.89`) into the late-London high near `4564.88`, then eased to `4561.82` at 12:00. This stayed far below the stale XAUUSD short entry `4668.45`.
- XAGUSD: recovered from the 11:00 low area to the `73.7x` zone, but all repeated short observations were already rejected and duplicate/not countable.
- NAS100/US30: both firmed into late London, with NAS100 near `27819.4` and US30 near `49122.8` at the 12:00 read.
- USDJPY/GBPJPY: JPY pairs firmed into the close; no new London candidate path issue came from them.

## Source And ML Status

- Sierra source rows remained available with caveats:
  - NQ/NAS100 context usable for registered depth diagnostics.
  - GC/XAUUSD context remains source-status/same-market-context only until full bounds are registered.
  - SI/XAGUSD remains source-definition blocked and must not be treated as Databento-equivalent orderflow.
- Databento live remained disabled/license-blocked; paid calls `0`.
- K55/ML rows were refreshed after the final London dependency signatures. Inference remains disabled by missing model artifact; all ML/selector output is observation-only.
- V2/V3 structural selector variants remain not ready because current live rows still lack lock/reentry/FVG metadata required for promotion-grade scoring.

## Open Evidence Gaps

- Two production internal limit intents remain open internally (`NAS100`, `XAUUSD`) but have no broker order/position; continue following them during NY.
- XAGUSD duplicate rejected short setup is useful market-learning evidence, but duplicate counting and SI source blockage prevent any promotion claim.
- GBPUSD provided clean negative evidence: repeated pre-AI prescreen failure despite live tape movement.

## Next Watch

- Between-session cadence until NY starts at 13:00 UTC.
- Watch stale sources, pending internal limit lifecycle changes, watchdog/heartbeat/tick freshness, and final pre-NY source status.
- Resume active 5-minute cadence at NY open.

Final posture: `NO_PROMOTION_VERDICT`
