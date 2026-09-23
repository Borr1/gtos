# Historical OHLC GTOS Replay Branch System Transfer Market-Gap Primitive Expansion

Generated UTC: `2026-05-16T15:47:18Z`

Branch system-transfer market-gap primitive expansion packet only. It preserves the 400 tick primitive market-gap combinations outside the current 386-branch denominator, routes them into source-expansion, entry-geometry, avoid/inverse, residual-transfer, and no-fill sidecar queues, and does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Market-gap combo rows: `400`
- Key rows: `80`
- Source-expansion queue rows: `309`
- Entry-geometry queue rows: `68`
- Avoid/inverse queue rows: `23`
- Residual transfer rows: `18`
- Residual mutation rows: `54`
