# Branch-Local Unified System Candidate Dispatch Bundle

Generated UTC: `2026-05-17T07:02:03Z`

- Candidate dispatch decision rows: `17916`.
- Candidate dispatch self-test rows: `17916`.
- No-fill dispatch plan rows: `9408`.
- Guard dispatch plan rows: `6232`.
- Market transfer dispatch rows: `1145`.

Branch-local unified system candidate-dispatch bundle. It consumes every executable candidate-runtime row and component/market runtime binding into concrete dispatch surfaces: scorer registry materialization, source/control builder plans, score-with-control plans, no-fill challenger/avoid modules, fail-closed guard bindings, current-claim opportunity routes, recheck plans, and market/timeframe transfer actions. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.
