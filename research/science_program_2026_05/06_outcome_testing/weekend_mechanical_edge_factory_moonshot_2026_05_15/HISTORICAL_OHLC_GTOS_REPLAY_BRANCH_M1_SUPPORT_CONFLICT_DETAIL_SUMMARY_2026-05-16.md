# Historical OHLC GTOS Replay Branch M1 Support Conflict Detail

Generated UTC: `2026-05-16T13:33:33Z`

M1 support-conflict detail packet only. It consumes accepted primary M1 rows and full M1 sidecar context, computes support/conflict detail from historical M1 proxy ledgers, and preserves exact tick-order limits. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Scope rows: `110`
- Accepted primary M1 rows: `70`
- Stable challenger rows: `47`
- Conflict split rows: `23`
- Accepted signature support rows: `801`