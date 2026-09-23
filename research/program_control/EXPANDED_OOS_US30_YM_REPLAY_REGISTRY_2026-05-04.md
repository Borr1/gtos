# Expanded OOS US30/YM Replay Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch ID:** `sierra_ym_to_us30_cash_pilot_20260504`  

This registry is written before opening a YM futures-proxy replay slice for the frozen `US30_cash|ny|bullish|H4+H1_consensus` blocked-control cohort.

| Field | Value |
| --- | --- |
| Source | `C:\SierraChart\Data\YMM26-CBOT.scid` |
| Output file symbol | `US30_cash` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Price transform | `identity` |
| Conversion timeframes | `M1`, `M5`, `M15`, `H1`, `D1` |
| Replay opened slice | `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` |
| Reserved holdout | `2026-04-20T00:00:00Z` to `2026-05-01T21:00:00Z` |

Boundary: YM futures proxy evidence is not redacted_account/MT5 `US30_cash` broker execution truth. All results remain `NO_PROMOTION_VERDICT`.
