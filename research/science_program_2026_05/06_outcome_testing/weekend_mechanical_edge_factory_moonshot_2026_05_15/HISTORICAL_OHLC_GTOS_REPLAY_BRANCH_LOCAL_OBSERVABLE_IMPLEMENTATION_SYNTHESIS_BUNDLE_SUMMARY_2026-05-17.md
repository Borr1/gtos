# Historical OHLC GTOS Replay Branch-Local Observable Implementation Synthesis Bundle

Generated UTC: `2026-05-16T20:24:41Z`

Branch-local observable implementation synthesis bundle only. It consumes the scorer execution bundle and turns all scorer, observable, control-scope, source-repair, control, and denominator execution rows into research-only register/build/repair/guard decisions while preserving horizon and primitive-coverage sidecars. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified implementation synthesis rows: `1108`
- Scorer registration rows: `225`
- Controlled scorer registration rows: `14`
- Source proxy scorer registration rows: `211`
- Observable registry rows: `262`
- Control-scope implementation rows: `168`
- Exact control build rows: `92`
- Source repair action rows: `98`
- Horizon sidecar synthesis rows: `37`
- Coverage sidecar synthesis rows: `520`

Core result: scorer execution rows are now branch-local implementation decisions: register, guard, build exact controls, repair source/horizon rows, or preserve context without denominator inflation.
