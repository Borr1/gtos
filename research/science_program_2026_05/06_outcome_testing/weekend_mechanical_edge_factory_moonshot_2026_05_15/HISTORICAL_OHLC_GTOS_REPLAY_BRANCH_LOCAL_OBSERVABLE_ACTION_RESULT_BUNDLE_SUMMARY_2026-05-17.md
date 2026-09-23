# Historical OHLC GTOS Replay Branch-Local Observable Action Result Bundle

Generated UTC: `2026-05-16T19:07:09Z`

Branch-local observable action-result bundle only. It computes research-only proxy score deltas, control requirements, denominator-guard registrations, source repair work rows, horizon work rows, and primitive coverage action rows from the observable execution bundle. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified action-result rows: `1108`
- Control-ready score rows: `14`
- Denominator-guarded registration rows: `262`
- Control lookup requirement rows: `168`
- Source policy action rows: `309`
- Source repair work rows: `98`
- Horizon work-order result rows: `37`
- Coverage action-result rows: `520`

Core result: execution decisions now carry concrete branch-local action results, proxy deltas where controls exist, exact missing-control scopes where controls are absent, and source/horizon repair work rows where source policy requires repair.
