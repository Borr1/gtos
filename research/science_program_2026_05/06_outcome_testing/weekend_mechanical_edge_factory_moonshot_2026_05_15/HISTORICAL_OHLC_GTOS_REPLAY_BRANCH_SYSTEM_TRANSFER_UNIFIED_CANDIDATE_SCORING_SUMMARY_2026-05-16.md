# Historical OHLC GTOS Replay Branch System Transfer Unified Candidate Scoring

Generated UTC: `2026-05-16T16:32:17Z`

Unified implementation-candidate scoring packet only. It scores all 386 branch-local candidates and all 400 market-gap primitive candidates from the unified execution decision layer, producing concrete branch-local scorer, source-expansion, entry-geometry, and avoid/inverse execution actions. It does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Branch score rows: `386`
- Market-gap score rows: `400`
- Implementation score rows: `786`
- Source-expansion execution rows: `309`
- Entry-geometry execution rows: `68`
- Avoid/inverse execution rows: `23`

Core result: every unified implementation candidate now has a deterministic score class and next action.
