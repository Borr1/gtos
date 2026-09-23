# Historical OHLC GTOS Replay Branch-Local Observable Execution Decision Bundle

Generated UTC: `2026-05-16T18:53:21Z`

Branch-local observable execution decision bundle only. It computes research shadow execution decisions for observable specs, source policies, controls, denominator guards, horizon repair work orders, and primitive coverage actions. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified execution rows: `1108`
- Observable execution rows: `444`
- Source policy execution rows: `309`
- Control execution rows: `231`
- Denominator execution rows: `124`
- Horizon work orders: `37`
- Primitive coverage action rows: `520`

Core result: observable/scorer implementation specs have been converted into branch-local execution decisions with source, control, denominator, horizon repair, and coverage actions preserved.
