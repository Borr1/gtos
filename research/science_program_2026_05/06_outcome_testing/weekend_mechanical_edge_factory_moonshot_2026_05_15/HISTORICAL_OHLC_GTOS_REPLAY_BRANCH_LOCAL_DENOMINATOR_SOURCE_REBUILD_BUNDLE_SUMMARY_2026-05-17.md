# Historical OHLC GTOS Replay Branch-Local Denominator Source Rebuild Bundle

Generated UTC: `2026-05-16T22:04:59Z`

Branch-local denominator/source rebuild bundle only. It joins the control/source split rows to current source materialization, shadow source-guard, and control execution surfaces, then emits exact-control denominator acquisition actions plus source and horizon rebuild actions. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified denominator/source rebuild rows: `190`
- Exact-control target denominator rows: `92`
- Exact-control scope denominator rows: `23`
- Control-member denominator evidence rows: `21252`
- Source materialization rebuild rows: `61`
- Horizon materialization rebuild rows: `37`
- Scope rebuild action rows: `121`

Core result: current rows prove exact-control scopes are guard-only and exact-denominator absent, while source and horizon scopes have direct materialization rows that define the next rebuild actions.
