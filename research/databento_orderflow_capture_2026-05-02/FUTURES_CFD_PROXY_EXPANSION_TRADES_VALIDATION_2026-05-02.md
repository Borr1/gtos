# Futures To CFD Mapping Multi-Day Report

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

Multi-day futures-to-CFD mapping validation checks whether CME futures can be used as an orderflow signal source for MT5 CFD execution symbols. This remains a transfer-quality diagnostic, not an alpha or promotion claim.

## Window Results

| Window | Selected shift | Primary median abs corr | Primary min abs corr | GC corr | NQ corr | YM corr | ES->US30 corr |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-23T07:00_2026-04-23T16:59 | -180 | 0.9236 | 0.8569 |  |  |  |  |
| 2026-04-24T07:00_2026-04-24T16:59 | -180 | 0.9201 | 0.9037 |  |  |  |  |
| 2026-04-27T07:00_2026-04-27T16:59 | -180 | 0.9055 | 0.8253 |  |  |  |  |

## Selected Pair Diagnostics

| Window | Pair | Transform | Aligned minutes | Zero-lag corr | Best lag | Best-lag corr | Directional agreement |
|---|---|---|---:|---:|---:|---:|---:|
| 2026-04-23T07:00_2026-04-23T16:59 | SI.v.0->XAGUSD | direct | 600 | 0.9442 | 0 | 0.9442 | 0.8891 |
| 2026-04-23T07:00_2026-04-23T16:59 | 6J.v.0->USDJPY | inverse_return | 593 | 0.8569 | 0 | 0.8569 | 0.9290 |
| 2026-04-23T07:00_2026-04-23T16:59 | 6B.v.0->GBPUSD | direct | 599 | 0.9236 | 0 | 0.9236 | 0.9558 |
| 2026-04-24T07:00_2026-04-24T16:59 | SI.v.0->XAGUSD | direct | 597 | 0.9423 | 0 | 0.9423 | 0.8850 |
| 2026-04-24T07:00_2026-04-24T16:59 | 6J.v.0->USDJPY | inverse_return | 590 | 0.9037 | 0 | 0.9037 | 0.9632 |
| 2026-04-24T07:00_2026-04-24T16:59 | 6B.v.0->GBPUSD | direct | 593 | 0.9201 | 0 | 0.9201 | 0.9311 |
| 2026-04-27T07:00_2026-04-27T16:59 | SI.v.0->XAGUSD | direct | 580 | 0.9065 | 0 | 0.9065 | 0.8818 |
| 2026-04-27T07:00_2026-04-27T16:59 | 6J.v.0->USDJPY | inverse_return | 591 | 0.8253 | 0 | 0.8253 | 0.9362 |
| 2026-04-27T07:00_2026-04-27T16:59 | 6B.v.0->GBPUSD | direct | 590 | 0.9055 | 0 | 0.9055 | 0.9581 |

## Synthesis

- Selected MT5 timestamp shifts: [-180, -180, -180].
- Timestamp correction is stable across tested windows.
- Shift-to-window map: {-180: ['2026-04-23T07:00_2026-04-23T16:59', '2026-04-24T07:00_2026-04-24T16:59', '2026-04-27T07:00_2026-04-27T16:59']}.
- Primary minimum absolute correlation by window: [0.8568818703974235, 0.9036932108363565, 0.8253006067981135].
- Databento estimated cost represented by sidecars: $0.1297 across 3 windows.
- Weak primary-transfer windows needing follow-up: ['2026-04-27T07:00_2026-04-27T16:59'].

## Ambiguity Ledger

- This validates price-transfer quality, not orderflow alpha.
- Sampled windows are still finite and selected for diagnostics, not a formal population proof.
- The exact MT5 server-time/DST transition boundary still needs a full calendar audit.
- Roll-date behavior remains untested unless a selected window spans a futures roll.
- MT5 tick-level alignment is still pending; M1 alignment can hide sub-minute slippage and quote lag.
- Depth/heatmap schemas are not evaluated by trades-only mapping.

## Open Questions

1. What exact date-aware MT5 timestamp policy removes the seasonal -120/-180 shift without per-window hindsight?
2. Do futures orderflow features add signal beyond the already-high futures/CFD price transfer?
3. Which event windows deserve mbp-1/mbp-10 depth pulls after trades-level transfer passes?
4. Does YM remain the best direct US30 proxy in all tested regimes?

## Next Steps

1. Build an event-window manifest from GTOS candidate/opportunity timestamps before any broad depth pull.
2. Add trades-level orderflow features: CVD, delta shift, absorption proxy, trade-count bars, LVN/HVN/POC.
3. Run OF-STRUCTURE-1: LVN-inside-FVG and VWAP-reclaim tests on harvested windows.
4. Only then pull depth/heatmap windows for the subset where price-transfer and trades-level signals pass.
