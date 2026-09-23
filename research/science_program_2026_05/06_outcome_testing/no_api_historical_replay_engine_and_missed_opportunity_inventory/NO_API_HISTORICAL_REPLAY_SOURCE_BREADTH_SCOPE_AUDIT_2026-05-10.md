# NO API Historical Replay Source Breadth Scope Audit

- Route: `NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY`
- Generated: `2026-05-10T12:00:00Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- Symbols considered: `60`
- Timeframes considered: `{"D1": 171, "DEPTH": 144, "H1": 166, "H4": 103, "M1": 94, "M15": 264, "M5": 98, "SCID": 86, "TICK": 31, "TICKS": 72, "UNSPECIFIED": 2271}`
- Source families considered: `{"CACHED_ORDERFLOW_OR_VENDOR_CONTEXT": 146, "LOCAL_OHLCV_CSV": 498, "LOCAL_SOURCE_METADATA": 436, "MT5_TICK_PARQUET_CAPTURE": 72, "PRIOR_SOURCE_CONTROL_LEDGER": 1382, "RAW_OHLC_PRE_AI_REPLAY_LOG": 118, "RESEARCH_SOURCE_CONTROL_ARTIFACT": 216, "SHADOW_SOURCE_STATE_LOG": 221, "SIERRA_DERIVED_OHLCV_EXPORT": 271, "SIERRA_NATIVE_CONTEXT": 140}`
- Missed-opportunity kill-zone counts: `{"London": 2297, "NY": 1464, "Tokyo": 91, "derivable_after_intraday_replay": 145, "not_derivable_from_daily_only": 135, "outside_configured_kill_zone": 728}`
