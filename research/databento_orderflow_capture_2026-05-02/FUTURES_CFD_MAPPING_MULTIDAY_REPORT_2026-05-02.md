# Futures To CFD Mapping Multi-Day Report

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

Multi-day futures-to-CFD mapping validation checks whether CME futures can be used as an orderflow signal source for MT5 CFD execution symbols. This remains a transfer-quality diagnostic, not an alpha or promotion claim.

## Window Results

| Window | Selected shift | Primary median abs corr | Primary min abs corr | GC corr | NQ corr | YM corr | ES->US30 corr |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-01-15T00:00_2026-01-15T23:59 | -120 | 0.9861 | 0.9813 | 0.9861 | 0.9921 | 0.9813 | 0.5576 |
| 2026-02-12T00:00_2026-02-12T23:59 | -120 | 0.9730 | 0.9722 | 0.9766 | 0.9730 | 0.9722 | 0.8459 |
| 2026-03-13T00:00_2026-03-13T20:59 | -180 | 0.9853 | 0.9833 | 0.9833 | 0.9927 | 0.9853 | 0.9419 |
| 2026-04-02T00:00_2026-04-02T23:59 | -180 | 0.9898 | 0.9837 | 0.9898 | 0.9929 | 0.9837 | 0.9456 |
| 2026-04-24T00:00_2026-04-24T20:59 | -180 | 0.9776 | 0.9693 | 0.9776 | 0.9891 | 0.9693 | 0.7845 |

## Synthesis

- Selected MT5 timestamp shifts: [-120, -120, -180, -180, -180].
- Timestamp correction is seasonal/date-dependent across tested windows.
- Shift-to-window map: {-120: ['2026-01-15T00:00_2026-01-15T23:59', '2026-02-12T00:00_2026-02-12T23:59'], -180: ['2026-03-13T00:00_2026-03-13T20:59', '2026-04-02T00:00_2026-04-02T23:59', '2026-04-24T00:00_2026-04-24T20:59']}.
- Primary minimum absolute correlation by window: [0.9813431836973587, 0.9722354039483271, 0.9833384662152923, 0.9837488513936967, 0.9693170828381485].
- Databento estimated cost represented by sidecars: $8.0208 across 5 windows.
- All tested windows passed the provisional primary-transfer correlation floor.

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
