# Historical OHLC GTOS Replay Branch ENTRY_ADVERSE Redesign Detail

Generated UTC: `2026-05-16T14:29:26Z`

ENTRY_ADVERSE redesign detail packet only. It consumes branch-local accepted-builder and redesign ledgers, preserves the full ENTRY_ADVERSE denominator, computes accepted entry/adverse variant detail rows and combined branch-local redesign variants, and keeps rejected/context rows explicit. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Full scope rows: `386`
- Accepted primary branch detail rows: `5`
- Rejected primary repair rows: `1`
- Sidecar/context rows: `380`
- Combined variant rows: `20`
