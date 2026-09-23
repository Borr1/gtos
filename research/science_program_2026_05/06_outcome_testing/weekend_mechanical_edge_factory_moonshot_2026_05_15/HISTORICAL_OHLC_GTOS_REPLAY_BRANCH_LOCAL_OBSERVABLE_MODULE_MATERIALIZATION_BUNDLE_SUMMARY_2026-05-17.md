# Historical OHLC GTOS Replay Branch-Local Observable Module Materialization Bundle

Generated UTC: `2026-05-16T20:55:42Z`

Branch-local observable module materialization bundle only. It consumes code integration candidate rows and materializes research-only scorer, registry, and source/control repair module records. It preserves exact-control, horizon, and primitive-coverage sidecars separately. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified module materialization rows: `1108`
- Scorer module materialization rows: `225`
- Registry module materialization rows: `785`
- Source repair module materialization rows: `98`
- Exact control work-order rows: `92`
- Horizon work-order sidecar rows: `37`
- Coverage registry sidecar rows: `520`

Core result: code-action candidates now have concrete branch-local research module materialization records, with open repair work preserved as executable work orders.
