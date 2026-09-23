# Historical OHLC GTOS Replay Branch SOURCE Bar Spread Recompute

Generated UTC: `2026-05-16T13:16:12Z`

SOURCE bar-spread recompute packet only. It uses local bar spread proxy rows materialized from owned files to select lower-level source descriptors inside the historical SOURCE queue. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch recompute rows: `138`
- Window recompute rows: `257`
- Repair upgraded to challenger review: `9`
- Accepted degraded to repair: `47`