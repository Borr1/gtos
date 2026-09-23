# Friday Micro Price-Action Summary

Generated: 2026-05-31T10:28:19.247500+00:00
HEAD at generation: `1196fb4841d96b89f3b89755c211cdb4d4abaf22`

## Denominator

- Primary non-crypto rows: `328`
- Tick bid/ask rows: `328`
- Full D1/H4/H1/M15 MSO context rows: `328`
- Rows with price after Friday close: `0`

## Path Classes

- Terminal path classes: `{"loss_sl_before_partial_trigger": 200, "no_entry_touch_before_friday_close": 2, "partial_trigger_then_open_at_friday_close": 5, "stuck_entry_no_sl_or_1r_before_friday_close": 12, "winner_partial_then_be_return": 73, "winner_partial_then_dynamic_final": 36}`
- Outcome counts: `{"DEFERRED_GTOS_VNEXT_PROP_RESET": 45, "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN": 8, "REJECTED_GATE3_CIRCUIT_BREAKER": 3, "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC": 272}`
- Mechanism counts: `{"cross_asset_lead_lag_failed": 14, "displacement_follow_through": 39, "incomplete_or_open_path": 1, "liquidity_sweep_reclaim": 40, "m1_or_tick_continuation": 20, "spread_cost_large_vs_stop": 67, "stale_selector_risk_bridge_dominated": 13, "stop_first_adverse_path": 69, "structural_distance_follow_through": 10, "sweep_continuation_failure": 26, "volatility_expansion_follow_through": 5, "wrong_direction_or_no_continuation": 24}`
- Placed terminal classes: `{"loss_sl_before_partial_trigger": 4, "partial_trigger_then_open_at_friday_close": 1, "stuck_entry_no_sl_or_1r_before_friday_close": 1, "winner_partial_then_be_return": 2}`

## Boundary

Every row is capped at the clean Friday close boundary `< 2026-05-29T21:00:00Z`; the 21:00 spread-close batch and weekend reopen rows remain excluded from this primary anatomy.
