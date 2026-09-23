# Historical OHLC GTOS Replay Branch System Transfer Unified Replay Code Candidate

Generated UTC: `2026-05-16T17:33:51Z`

Unified replay code-candidate packet only. It converts replay/acquisition rows into branch-local research code/spec candidates and source-materialization actions. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified code-candidate rows: `1545`
- Entry shadow rule implement rows: `126`
- Avoid shadow filter implement rows: `15`
- Outside-branch market-gap code rows: `300`
- Outside-branch implement code rows: `45`
- Source rows needed to N20 total: `3743`

Core result: replay/acquisition rows now have branch-local mechanical code/spec actions with scope keys and guards.
