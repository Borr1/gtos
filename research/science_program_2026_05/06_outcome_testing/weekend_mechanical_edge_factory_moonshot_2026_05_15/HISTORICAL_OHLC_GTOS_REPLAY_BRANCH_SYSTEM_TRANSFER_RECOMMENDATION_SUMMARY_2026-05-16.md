# Historical OHLC GTOS Replay Branch System Transfer Recommendation

Generated UTC: `2026-05-16T14:46:41Z`

Branch system-transfer recommendation packet only. It joins branch-local SOURCE/M15/M1/POSITIVE/ENTRY_ADVERSE detail packets over the full 386-branch denominator, computes keep/kill/redesign/repair and transfer classifications by symbol/session/primitive, and keeps market-specific concentration explicit. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch recommendation rows: `386`
- Keep/kill/redesign rows: `386`
- Market/session decision rows: `49`
- Transfer matrix rows: `24`
- Family recommendation rows: `6`
