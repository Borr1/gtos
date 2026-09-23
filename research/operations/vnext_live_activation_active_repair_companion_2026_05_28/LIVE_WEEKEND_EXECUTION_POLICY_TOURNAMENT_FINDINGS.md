# Weekend vNext Execution Policy Tournament Findings

Generated: 2026-05-31T07:41:38.239541+00:00
HEAD: 91e28b198a878d45e4987bbe42561e67b5979fde

## Denominator

- Candidate rows: 604
- Policy variants: 18
- Tournament rows: 10872

## Policy Results

- Best policy by gross R: `no_trade_baseline`.
- Current selected policy gross R: `-127.60944487551178`.
- Best real trailing policy: `trailing_1_5r_gap_0_5_cap_3r` at `-165.752173208566`.
- Trailing decision: `do_not_promote_trailing_primary_from_weekend_only`.
- Quality-gated current selected gross R: `0.0`.
- Quality-gated best trailing gross R: `0.0`.

## Quality Gate

- Quality classifications: `{"insufficient_current_proof": 38, "no_trade_by_evidence": 95, "repair_before_execution": 471}`.
- Quality reasons: `{"dynamic_router_refusal_requires_exact_selector_risk_bridge": 397, "gate1_stop_geometry_failed_current_repair_required": 74, "gate3_spread_rejected_no_trade_by_current_broker_cost": 78, "h20_21_liquidity_sweep_long_negative_slice": 5, "historical_prop_deferral_requires_current_account_risk_reconstruction": 45, "missing_selected_policy_or_execution_policy_id": 84, "no_current_quality_exclusion_from_weekend_asof_fields": 8, "off_session_crypto_liquidity_sweep_long_negative_slice": 7, "spread_r_at_candidate_ge_0_20": 51, "spread_r_at_candidate_ge_0_30": 98, "weekend_negative_ny_short_origin_slice": 46}`.
- Tradeable rule summary: `{"weekend_london_displacement_continuation_positive_current_selected": {"candidate_rows": 27, "classified_tradeable_now_rows": 0, "current_selected_policy_gross_r_sum_from_rows": 3.4824055581254663, "known_current_policy_r_rows": 27, "origin_family": "displacement_continuation", "rule_id": "weekend_london_displacement_continuation_positive_current_selected", "session": "london", "weekend_current_selected_avg_r": 0.14, "weekend_current_selected_gross_r": 3.5, "weekend_rows": 25}, "weekend_london_liquidity_sweep_reclaim_positive_current_selected": {"candidate_rows": 20, "classified_tradeable_now_rows": 0, "current_selected_policy_gross_r_sum_from_rows": 7.0, "known_current_policy_r_rows": 20, "origin_family": "liquidity_sweep_reclaim", "rule_id": "weekend_london_liquidity_sweep_reclaim_positive_current_selected", "session": "london", "weekend_current_selected_avg_r": 0.35, "weekend_current_selected_gross_r": 7.0, "weekend_rows": 20}}`.
- Runtime recommendation: `allow_configured_positive_session_origin_rules_after_current_bridge_risk_spread_proof`.

## Repair Decisions

- `trailing_runner_proxy_replaced_by_executable_tournament`: `implemented` - real trailing variants are replayed tick-by-tick with bid/ask fills, stop movement, broker stop/freeze checks, M1 ambiguity flags, and no MFE-minus-gap proxy authority
- `production_policy_mismatch_partial_dominance`: `classified` - current_selected_policy is computed from row selected_policy; weekend partial dominance is expected when router selected partial_be_runner for most rows, not evidence that momentum primary executed globally
- `trailing_policy_promotion`: `do_not_promote_trailing_primary_from_weekend_only` - best real trailing variant trailing_1_5r_gap_0_5_cap_3r gross_r=-165.752173208566, m1_ambiguous_rows=0, max_abs_symbol_r_share=0.10157800533697008

## Production Boundary

This tournament replaces the old trailing proxy as evidence. It does not perform broker actions and does not promote a live policy because every raw and quality-gated executable policy remains negative on the current weekend denominator.
