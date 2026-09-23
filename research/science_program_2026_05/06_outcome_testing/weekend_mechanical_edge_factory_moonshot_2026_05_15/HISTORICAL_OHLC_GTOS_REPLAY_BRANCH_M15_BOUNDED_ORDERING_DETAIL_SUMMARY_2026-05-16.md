# Historical OHLC GTOS Replay Branch M15 Bounded Ordering Detail

Generated UTC: `2026-05-16T13:42:55Z`

M15 bounded-ordering detail packet only. It consumes accepted primary M15 rows and full M15 sidecar/rejected context, computes target-first versus bounds-split detail from historical M15 interval proxy ledgers, and preserves exact chronology limits. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Scope rows: `186`
- Accepted primary M15 rows: `66`
- Target-first conservative challenger rows: `58`
- Bounds-split positive-midpoint rows: `8`
- Accepted same-M15 ambiguity support rows: `1154`