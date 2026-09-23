# Historical OHLC GTOS Replay Branch System Transfer Unified Source Materialization Execution

Generated UTC: `2026-05-16T18:04:02Z`

Unified source materialization execution packet only. It reconstructs current targetable rows, fail-closed horizon rows, source-flag denominators, and source-expansion proxies for the 309 source queue rows. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Source materialization rows: `309`
- Current source flags N20 rows: `37`
- Target horizon fail-closed guard rows: `37`
- Expanded targetable proxy N20 rows: `272`
- Outside-branch materialization rows: `231`

Core result: source rows now carry exact targetable/source/fail-closed/proxy closure causes and decision guards.
