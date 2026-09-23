# Futures To CFD Mapping Multi-Day Report

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

Multi-day futures-to-CFD mapping validation checks whether CME futures can be used as an orderflow signal source for MT5 CFD execution symbols. This remains a transfer-quality diagnostic, not an alpha or promotion claim.

## Window Results

| Window | Selected shift | Primary median abs corr | Primary min abs corr | GC corr | NQ corr | YM corr | ES->US30 corr |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-23T07:00_2026-04-23T16:59 | -180 | 0.8569 | 0.8569 |  |  |  |  |
| 2026-04-24T07:00_2026-04-24T16:59 | -180 | 0.9037 | 0.9037 |  |  |  |  |
| 2026-04-27T07:00_2026-04-27T16:59 | -180 | 0.8253 | 0.8253 |  |  |  |  |
| 2026-01-22T07:00_2026-01-22T16:59 | -120 | 0.8899 | 0.8899 |  |  |  |  |
| 2026-02-12T07:00_2026-02-12T16:59 | -120 | 0.9664 | 0.9664 |  |  |  |  |
| 2026-03-06T07:00_2026-03-06T16:59 | -120 | 0.9628 | 0.9628 |  |  |  |  |
| 2026-03-09T07:00_2026-03-09T16:59 | -180 | 0.9405 | 0.9405 |  |  |  |  |
| 2026-03-16T07:00_2026-03-16T16:59 | -180 | 0.9048 | 0.9048 |  |  |  |  |
| 2026-04-02T07:00_2026-04-02T16:59 | -180 | 0.9066 | 0.9066 |  |  |  |  |

## Selected Pair Diagnostics

| Window | Pair | Transform | Aligned minutes | Zero-lag corr | Best lag | Best-lag corr | Directional agreement |
|---|---|---|---:|---:|---:|---:|---:|
| 2026-04-23T07:00_2026-04-23T16:59 | 6J.v.0->USDJPY | inverse_return | 593 | 0.8569 | 0 | 0.8569 | 0.9290 |
| 2026-04-24T07:00_2026-04-24T16:59 | 6J.v.0->USDJPY | inverse_return | 590 | 0.9037 | 0 | 0.9037 | 0.9632 |
| 2026-04-27T07:00_2026-04-27T16:59 | 6J.v.0->USDJPY | inverse_return | 591 | 0.8253 | 0 | 0.8253 | 0.9362 |
| 2026-01-22T07:00_2026-01-22T16:59 | 6J.v.0->USDJPY | inverse_return | 599 | 0.8899 | 0 | 0.8899 | 0.9384 |
| 2026-02-12T07:00_2026-02-12T16:59 | 6J.v.0->USDJPY | inverse_return | 600 | 0.9664 | 0 | 0.9664 | 0.9695 |
| 2026-03-06T07:00_2026-03-06T16:59 | 6J.v.0->USDJPY | inverse_return | 598 | 0.9628 | 0 | 0.9628 | 0.9725 |
| 2026-03-09T07:00_2026-03-09T16:59 | 6J.v.0->USDJPY | inverse_return | 600 | 0.9405 | 0 | 0.9405 | 0.9629 |
| 2026-03-16T07:00_2026-03-16T16:59 | 6J.v.0->USDJPY | inverse_return | 599 | 0.9048 | 0 | 0.9048 | 0.9624 |
| 2026-04-02T07:00_2026-04-02T16:59 | 6J.v.0->USDJPY | inverse_return | 599 | 0.9066 | 0 | 0.9066 | 0.9554 |

## Synthesis

- Selected MT5 timestamp shifts: [-180, -180, -180, -120, -120, -120, -180, -180, -180].
- Timestamp correction is seasonal/date-dependent across tested windows.
- Shift-to-window map: {-180: ['2026-04-23T07:00_2026-04-23T16:59', '2026-04-24T07:00_2026-04-24T16:59', '2026-04-27T07:00_2026-04-27T16:59', '2026-03-09T07:00_2026-03-09T16:59', '2026-03-16T07:00_2026-03-16T16:59', '2026-04-02T07:00_2026-04-02T16:59'], -120: ['2026-01-22T07:00_2026-01-22T16:59', '2026-02-12T07:00_2026-02-12T16:59', '2026-03-06T07:00_2026-03-06T16:59']}.
- Primary minimum absolute correlation by window: [0.8568818703974235, 0.9036932108363565, 0.8253006067981135, 0.8899286421021061, 0.9663675304976508, 0.9627765099028089, 0.9405317734113732, 0.9047788676157084, 0.90660045577188].
- Databento estimated cost represented by sidecars: $0.2607 across 9 windows.
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
