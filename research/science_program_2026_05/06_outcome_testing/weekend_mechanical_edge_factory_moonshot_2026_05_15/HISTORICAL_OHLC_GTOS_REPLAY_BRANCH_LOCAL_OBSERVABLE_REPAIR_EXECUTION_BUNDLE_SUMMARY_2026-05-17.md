# Historical OHLC GTOS Replay Branch-Local Observable Repair Execution Bundle

Generated UTC: `2026-05-16T21:13:59Z`

Branch-local observable repair execution bundle only. It executes exact-control, source-repair, and horizon sidecar work orders from current same-resource rows into proxy/control-scored work-result rows. It preserves the 1,108 module-materialization denominator, keeps horizon and primitive-coverage sidecars separate, does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

- Unified repair execution rows: `190`
- Source repair work execution rows: `98`
- Exact-control repair execution rows: `92`
- Horizon repair sidecar execution rows: `37`
- Primitive coverage carryforward rows: `520`
- Repaired or control-scored rows: `190`

Core result: open repair work orders are now concrete execution outcomes with exact cause, proxy score, control denominator, and next-action fields.
