# Historical OHLC GTOS Replay Branch SOURCE Upgraded/Degraded Implication

Generated UTC: `2026-05-16T14:10:33Z`

SOURCE upgraded/degraded implication packet only. It consumes local bar-spread proxy recompute rows for the SOURCE family, computes branch-level confirmed, degraded, upgraded, ambiguity, and no-scalar implications, and preserves exact tick/source gaps. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch implication rows: `138`
- Accepted confirmed rows: `19`
- Accepted degraded rows: `67`
- Upgraded challenger review rows: `16`
- M15 ambiguity review rows: `30`