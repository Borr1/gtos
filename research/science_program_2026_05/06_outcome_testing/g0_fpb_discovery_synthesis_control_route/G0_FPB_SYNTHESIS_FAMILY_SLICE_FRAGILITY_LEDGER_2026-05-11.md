# G0 FPB Family Slice Fragility Ledger

- Route: `G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE`
- Evidence class: `NO_API_G0_DISCOVERY_SYNTHESIS_CONTROL_ONLY`
- Generated: `2026-05-11T07:57:49+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Summary

- `policy`: `Any future validation must predefine leave-one-source/symbol/timeframe/session/KZ/regime stress checks and concentration caps.`

## Rows

- `ob_retest`: {"family_id": "ob_retest", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96880895, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.65062561, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.65828913, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `fvg_fill`: {"family_id": "fvg_fill", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96112881, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.70056673, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.66143195, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `breaker_re_entry`: {"family_id": "breaker_re_entry", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.84942523, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.63940007, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.62953278, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `opening_drive_no_fill_lifecycle`: {"family_id": "opening_drive_no_fill_lifecycle", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96879145, "top_slice": "LOCAL_OHLCV_CSV"}], "fragility_status": "FRAGILE"}
- `session_kz_sweep`: {"family_id": "session_kz_sweep", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96636915, "top_slice": "LOCAL_OHLCV_CSV"}], "fragility_status": "FRAGILE"}
- `liquidity_stop_run_context`: {"family_id": "liquidity_stop_run_context", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.97042956, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.66657979, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.66705241, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `baseline_random_session_control`: {"family_id": "baseline_random_session_control", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.97091623, "top_slice": "LOCAL_OHLCV_CSV"}], "fragility_status": "FRAGILE"}
- `baseline_shifted_entry_control`: {"family_id": "baseline_shifted_entry_control", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96701351, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.65324577, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.65911525, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `baseline_momentum_continuation`: {"family_id": "baseline_momentum_continuation", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96519679, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.66641751, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.68871225, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `baseline_mean_reversion`: {"family_id": "baseline_mean_reversion", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96419754, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.65937988, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.66018466, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}
- `adjacent_range_compression_breakout`: {"family_id": "adjacent_range_compression_breakout", "fragility_flags": [{"dimension": "source_family", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.96566789, "top_slice": "LOCAL_OHLCV_CSV"}, {"dimension": "timeframe", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.64202175, "top_slice": "M1"}, {"dimension": "session_or_kill_zone", "risk": "single_slice_dependence_requires_holdout_or_cap", "share": 0.71370481, "top_slice": "outside_configured_kill_zone"}], "fragility_status": "FRAGILE"}

## Boundary

This artifact is discovery/control-only. It does not validate an edge, promote a family, score R/PnL/win-rate/expectancy/performance, call AI/API, use broker account/order/history/deal/position evidence, or change live trading behavior.
