# Historical OHLC GTOS Replay Branch System Transfer Tick Primitive Context

Generated UTC: `2026-05-16T14:57:28Z`

Tick primitive context join packet only. It joins every 386 system-transfer branch to all available tick primitive transfer rows for the matching symbol/session/horizon key, preserves unmatched market/session/horizon primitive rows as expansion gaps, and does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch tick context rows: `1930`
- Branch tick summary rows: `386`
- Market gap rows: `400`
- Key coverage rows: `84`
- Family primitive rows: `75`
