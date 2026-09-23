# GTOS NY KZ Mini-Synthesis - 2026-05-05

Generated: 2026-05-05 17:12 UTC

Verdict: `NO_PROMOTION_VERDICT`

## Scope

- Sessions covered: 2026-05-05 NY windows through post-close seal at 17:05 UTC.
- Evidence classes: `BROKER_ACCOUNT_TRUTH`, `FORWARD_SHADOW`, `INTERNAL_LIMIT_LIFECYCLE`, `MARKET_TAPE_READ_ONLY`, `SOURCE_STATUS_ONLY`, `APPEND_ONLY_AUDIT`.
- Trading behavior changed: none.
- AI/canary/paid-data policy: no live canary calls, no paid Databento calls, no execution changes.

## System Health

- Final pulse: `_live_monitor_iter.py` iter `634`, candle `2026-05-05T17:00:00+00:00`.
- Status: `crit=0`, `anom=0`, `pids=2`, `open_pos=0`.
- Broker truth: redacted_account balance/equity `101223.36`; broker positions `0`; broker orders `0`; profit `0.0`.
- Final verifier state: `verify_shadow_log_integrity.py` returned `OK_WITH_DOCUMENTED_WAITING_LANES`; `audit_live_shadow_data_health.py` returned `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.
- Operational note: XAUUSD and NAS100 heartbeats remained alive at `17:05:05` after their configured NY end `17:00`; monitor did not classify this as critical/anomalous, and broker exposure stayed zero. Track as `POST_WINDOW_LINGERING_HEARTBEATS_NO_EXPOSURE`.

## Candidate And Path Summary

- Latest candidate count: `76`.
- NY new candidates after the 13:00 UTC open: `10`, all XAGUSD shorts.
- NY outcomes: `10/10` new rows were `REJECTED_L2`; no broker order or position was created.
- Early NY XAGUSD rows repeated the older H1 bearish OB `75.789-75.471`; later rows shifted to a newer H1 bearish OB `73.971-73.222`.
- Primary L2 blocker: `m15_choch_exists`; deterministic verifier found no qualifying bearish M15 CHoCH/BOS displacement.
- Later newer-OB rows also carried an `ob_zone` warning because midpoint `73.60` sat below equilibrium `73.70` for a short.
- Final opportunity health: `12` countable primary unique opportunities, `63` duplicate-active setups, and `1` blocked same-symbol overlap.

## Market Tape

- XAUUSD: sold from the 4580s into the 4550s during NY, with the lowest observed tape near `4553.72`, then closed the monitored window around `4560`.
- XAGUSD: trended lower from the 73.7s to the 72.8-73.1 area; the system repeatedly identified short OB context but L2 refused all rows for missing M15 structure confirmation.
- NAS100: tick-capture remained live while direct read-only MT5 probing failed; latest monitored tick area was near `28002.82`.
- US30: closed flat at 16:00 UTC with no broker exposure; direct side probe failure persisted but tick-capture remained available.
- FX: USDJPY, GBPJPY, and GBPUSD closed flat at 15:30 UTC with no system trade.

## Source And ML Status

- Sierra SI/XAGUSD depth files were present and captured, but interpretation remains blocked by `SOURCE_DEPTH_DEFINITION_BLOCKED_SI`.
- Databento live remained disabled/license-blocked; paid calls `0`.
- K55/ML and V2/V3 structural selector lanes refreshed, but remain observation-only and not promotion-ready.
- Final integrity waiting lanes are expected actual-event-only logs: BE, partial close, and time-in-trade.

## Open Evidence Gaps

- Direct read-only side probe for NAS100 and US30 continued to fail with `Terminal: Call failed`; production tick-capture and monitor lanes remained healthy.
- XAUUSD and NAS100 heartbeats remained alive after configured NY end. This needs operator/watchdog review, but it produced no exposure and no verifier issue.
- SI depth remains source-status-only; do not infer orderflow from the captured SI files.

Final posture: `NO_PROMOTION_VERDICT`
