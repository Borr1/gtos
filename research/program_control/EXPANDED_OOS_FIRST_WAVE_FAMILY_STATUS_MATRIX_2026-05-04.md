# Expanded OOS First-Wave Family Status Matrix - 2026-05-04

**Status:** `FIRST_WAVE_STATUS_MATRIX_CURRENT_NOT_TERMINAL`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; no live trading logic, prompts, risk, execution, safety, AI/API calls, or new Databento pulls.

## Summary

| Metric | Count |
|---|---:|
| Required first-wave families | 11 |
| Families with OHLCV adapter status | 11 |
| Families with converted M15 rows | 11 |
| Families with replay or label status | 6 |
| Families missing replay or label status | 5 |
| Families with depth status | 5 |

## Family Matrix

| Family | OHLCV status | Replay/label status | Depth status | Next action |
|---|---|---|---|---|
| NAS100/NDX100 with NQ/MNQ | converted | `PATH_WORKS_NO_FROZEN_COHORT_MATCH` | `NQ` exact cached MBP10 match | Use only for registered proxy diagnostics; not broker truth |
| US30/US30_cash with YM/MYM | converted | m15 actions, V2 MTF all no-entry | `YM` exact cached MBP10 match | Needs resolved lower-timeframe labels |
| XAUUSD with XAUUSD.scid and GC/MGC | converted | small-n same-market diagnostic positive | `GC` near match | Extend only with frozen slices and sample floors |
| XAGUSD with SI/SIL | converted, sparse | m15 positive but V2 MTF not portable | `SI` source/depth-definition blocked | Resolve continuous-contract/source mapping first |
| USDJPY with 6J | converted, inverse transform | path works, no actions | not audited | Keep proxy caution explicit |
| GBPUSD with 6B | converted | path works, no actions | sampling-policy alignment required | Add/common-second sampling alignment before depth use |
| EURUSD with EURUSD/6E | converted | not opened | not audited | Register replay/label-status slice before outcomes |
| S&P with ES/MES | converted | not opened control/expansion | not audited | Keep as expansion/control until registered |
| CL macro/liquidity proxy/control | converted | not opened control | not audited | Use only after registered cross-instrument question |
| ZN macro/rates proxy/control | converted | not opened control | not audited | Use only after registered cross-instrument question |
| VIX/VXM controls | converted, VXMM sparse | not opened control | not audited | Preserve sparse warning |

## Completion Gap

This matrix narrows the active gap; it does not complete the goal.

- Replay or label-status artifacts are still missing for `EURUSD/6E`, `ES/MES`, `CL`, `ZN`, and `VIX/VXM`.
- Candidate survival table by evidence class is not complete.
- Instrument/source expansion scorecard remains preliminary without unopened-family label-status artifacts.
- Opened/burned/reserved slice ledger is partial and should be promoted into a goal-level ledger before final synthesis.
- No final synthesis for the full-unblocking goal exists after the depth and sampling audits.
