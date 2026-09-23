# Historical OHLC GTOS Replay Branch System Transfer Unified Shadow Scorer Execution

Generated UTC: `2026-05-16T17:44:31Z`

Unified shadow scorer execution packet only. It scores branch-local code/spec candidates into mechanical shadow actions, source-materialization actions, controls, and denominator guards. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Shadow scorer rows: `1545`
- Implementation enable rows: `444`
- Source materialization queue rows: `309`
- Control/guard rows: `792`
- Outside-branch implementation enable rows: `150`

Core result: code-candidate rows are now executable shadow-scorer actions with implementation, source, control, and guard paths separated.
