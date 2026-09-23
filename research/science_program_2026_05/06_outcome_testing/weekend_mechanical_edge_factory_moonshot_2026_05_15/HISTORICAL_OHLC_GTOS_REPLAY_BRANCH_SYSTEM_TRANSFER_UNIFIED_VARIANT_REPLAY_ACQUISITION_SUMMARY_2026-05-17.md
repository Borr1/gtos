# Historical OHLC GTOS Replay Branch System Transfer Unified Variant Replay Acquisition

Generated UTC: `2026-05-16T17:16:17Z`

Unified variant replay/acquisition decision packet only. It converts the full variant, market-gap, branch-action, R-style proxy, scorer-spec, and concentration denominators into concrete source-acquisition, entry-replay, avoid/inverse, keep/kill/redesign/implement, and branch-local scorer-spec decisions. It does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Source acquisition/proxy result rows: `309`
- Entry variant replay score rows: `272`
- Avoid/inverse policy replay rows: `46`
- Market-gap replay/acquisition synthesis rows: `400`
- Market-gap family/symbol/session proxy-R rows: `56`
- Branch keep/kill/redesign/implement rows: `386`
- Concentration replay test rows: `124`

Core result: variant rows now alter concrete replay/acquisition and implementation decisions rather than remaining score-now queues.
