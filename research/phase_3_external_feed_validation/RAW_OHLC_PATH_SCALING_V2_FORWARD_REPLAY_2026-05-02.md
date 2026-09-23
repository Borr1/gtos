# Phase 3 Path Scaling V2 Structural Level Selector

**Created UTC:** 2026-05-02T07:28:40.316865+00:00
**Replay spec:** `research\phase_3_external_feed_validation\RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`
**V2 spec:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_SPEC_V1.json`
**V2 protocol:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_PROTOCOL_2026-05-02.md`
**V1 forensics:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_FAILURE_FORENSICS_2026-05-02.md`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- V2 uses V1 MTF path resolution and adds structural lock floors only after the trade is already filled.
- Reentry, breaker reconstruction, round-number selectors, and higher-timeframe composite selectors are not tested.
- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.

## Run Scope

| source_scope | rows_replayed | take_rows_seen | setup_ok_rows | include_blocked_controls | first_take_clock | last_take_clock |
| --- | --- | --- | --- | --- | --- | --- |
| BOUNDED_DIAGNOSTIC | 204 | 22 | 0 | True | 2026-05-01T00:15:00+00:00 | 2026-05-01T09:30:00+00:00 |

## Direct Answers

| question | answer |
| --- | --- |
| Which V2 structural policy leads after 0.05R cost? | STRUCT_SWING_PROTECTED_V2 with net_mean_r_cost_0.05=None. |
| Did the best structural policy beat J46 globally? | Best structural minus J46 at 0.05R cost = None. |
| Did structural selection beat the best fixed-R lock control? | Best fixed-R minus J46 = None; compare best structural minus J46 = None. |
| Which variant leads overall? | BASE_RAW_FIXED_TP with net_mean_r_cost_0.05=None. |
| Did the headline structural result survive pessimistic same-bar stress? | All-enabled pessimistic best structural minus J46 = None. |
| Where did structural selection look most interesting? | Target-cohort best structural minus J46 at 0.05R cost = None. |
| Which selector fired most often? | None under None with fires=None. |
| Does this promote live logic? | No. V2 is same-dataset historical research and remains NO_PROMOTION_VERDICT. |

## MTF Coverage

| setup_windows | m1_available_windows | m1_available_rows | m5_available_windows | m5_available_rows | m15_available_windows | m15_available_rows | m15_fallback_windows | selected_timeframes | lower_tf_start_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} | 0 |

## Structural Selector Rules

| swing_confirmation_lag_bars | displacement_threshold | candidate_floor_rule | activation_rule | multiple_candidates_rule |
| --- | --- | --- | --- | --- |
| 2 | body >= 1.5x prior closed-body average | floor must be non-negative R, behind current close, and improve pending stop | new structural floors activate on the next selected path row | highest floor R wins |

## Policies

| variant_id | family | description | final_target_r | time_stop_bars | pending_expiry_bars | use_setup_tp | lock_steps | structural_selectors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | Current raw mechanical fixed TP/SL with 96 M15-bar max hold. |  | 96 | 96 | True | [] |  |
| J46_J49_ONLY | j46_j49 | 0% partial, 3R trigger to BE, 6R final target, 12 M15-bar time stop after fill. | 6.0 | 12 | 96 | False | [{'trigger_r': 3.0, 'floor_r': 0.0}] |  |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | Lock-only ladder: 1.5R->0R, 2R->0.5R, 3R->1R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.5, 'floor_r': 0.0}, {'trigger_r': 2.0, 'floor_r': 0.5}, {'trigger_r': 3.0, 'floor_r': 1.0}] |  |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | Lock-only ladder: 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.5, 'floor_r': 0.5}, {'trigger_r': 2.0, 'floor_r': 1.0}, {'trigger_r': 3.0, 'floor_r': 1.5}] |  |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | Lock-only ladder: 1R->0R, 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.0, 'floor_r': 0.0}, {'trigger_r': 1.5, 'floor_r': 0.5}, {'trigger_r': 2.0, 'floor_r': 1.0}, {'trigger_r': 3.0, 'floor_r': 1.5}] |  |
| STRUCT_SWING_PROTECTED_V2 | swing_structure | Lock behind the latest confirmed pullback swing in trade direction. | 6.0 | 12 | 96 | False | [] | ['PROTECTED_CONFIRMED_SWING'] |
| STRUCT_BOS_LEVEL_V2 | swing_structure | Lock behind a confirmed swing level broken by an in-trade-direction BOS close. | 6.0 | 12 | 96 | False | [] | ['BOS_BROKEN_LEVEL'] |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | volatility_displacement | Lock behind the body halfback of an in-trade-direction displacement candle. | 6.0 | 12 | 96 | False | [] | ['DISPLACEMENT_HALFBACK'] |
| STRUCT_FVG_MID_EDGE_V2 | poi_boundary | Lock behind the best valid in-trade-direction FVG midpoint or protective edge. | 6.0 | 12 | 96 | False | [] | ['FVG_MIDPOINT', 'FVG_PROTECTIVE_EDGE'] |
| STRUCT_OB_BOUNDARY_V2 | poi_boundary | Lock behind the protective boundary of the last opposing candle before an in-direction BOS close. | 6.0 | 12 | 96 | False | [] | ['OB_PROTECTIVE_BOUNDARY'] |
| STRUCT_LIQUIDITY_RUN_V2 | liquidity | Lock behind prior path or equal high/low liquidity after an in-direction close through it. | 6.0 | 12 | 96 | False | [] | ['PATH_HIGH_LOW_RUN', 'EQUAL_HIGH_LOW_RUN'] |
| STRUCT_COMPOSITE_ANY_V2 | composite | Lock behind the best valid floor from all registered V2 structural selectors. | 6.0 | 12 | 96 | False | [] | ['PROTECTED_CONFIRMED_SWING', 'BOS_BROKEN_LEVEL', 'DISPLACEMENT_HALFBACK', 'FVG_MIDPOINT', 'FVG_PROTECTIVE_EDGE', 'OB_PROTECTIVE_BOUNDARY', 'PATH_HIGH_LOW_RUN', 'EQUAL_HIGH_LOW_RUN'] |

## Variant Summary

| variant_id | family | actions_seen | setup_ok | entries_filled | resolved_n | gross_sum_r | gross_mean_r | gross_median_r | gross_win_rate | avg_bars_in_trade | lock_trigger_rate | lock_then_stop_rate | direct_3r_available_rate | direct_6r_available_rate | mfe_p50 | mfe_p75 | mfe_p90 | mae_p10 | outcomes | same_dataset_dsr_p_gross | net_mean_r_cost_0 | net_sum_r_cost_0 | net_max_drawdown_r_cost_0 | net_mean_r_cost_0.02 | net_sum_r_cost_0.02 | net_max_drawdown_r_cost_0.02 | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | net_max_drawdown_r_cost_0.05 | net_mean_r_cost_0.1 | net_sum_r_cost_0.1 | net_max_drawdown_r_cost_0.1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| J46_J49_ONLY | j46_j49 | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_SWING_PROTECTED_V2 | swing_structure | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_BOS_LEVEL_V2 | swing_structure | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | volatility_displacement | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_FVG_MID_EDGE_V2 | poi_boundary | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_OB_BOUNDARY_V2 | poi_boundary | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_LIQUIDITY_RUN_V2 | liquidity | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |
| STRUCT_COMPOSITE_ANY_V2 | composite | 22 | 0 | 0 | 0 | 0.0 |  |  |  |  |  |  |  |  |  |  |  |  | {'SETUP_NOT_REFINABLE': 22} |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Same-Bar Stress Summary

| treatment | group | j46_net_mean_r_cost_0.05 | j46_n | best_structural_variant | best_structural_net_mean_r_cost_0.05 | best_structural_n | best_structural_minus_j46 | best_fixed_r_variant | best_fixed_r_net_mean_r_cost_0.05 | best_fixed_r_n | best_structural_minus_best_fixed_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | all_enabled |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | all_excluding_gbpusd_control |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | blocked_dominance_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | all_enabled |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | all_excluding_gbpusd_control |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | blocked_dominance_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | all_enabled |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | all_excluding_gbpusd_control |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | blocked_dominance_controls |  | 0 |  |  |  |  |  |  |  |  |

## Group Summary

| variant_id | group | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| BASE_RAW_FIXED_TP | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| BASE_RAW_FIXED_TP | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| BASE_RAW_FIXED_TP | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| BASE_RAW_FIXED_TP | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| BASE_RAW_FIXED_TP | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| BASE_RAW_FIXED_TP | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| J46_J49_ONLY | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| J46_J49_ONLY | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| J46_J49_ONLY | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| J46_J49_ONLY | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| J46_J49_ONLY | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_CONSERVATIVE_V0 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_CONSERVATIVE_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_CONSERVATIVE_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_CONSERVATIVE_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_HALF_GAIN_V0 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_HALF_GAIN_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_HALF_GAIN_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_HALF_GAIN_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_HALF_GAIN_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_EARLY_BE_V0 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_EARLY_BE_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| PATH_LOCK_EARLY_BE_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_EARLY_BE_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_EARLY_BE_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_SWING_PROTECTED_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_SWING_PROTECTED_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_SWING_PROTECTED_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_SWING_PROTECTED_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_SWING_PROTECTED_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_BOS_LEVEL_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_BOS_LEVEL_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_BOS_LEVEL_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_BOS_LEVEL_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_BOS_LEVEL_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_FVG_MID_EDGE_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_FVG_MID_EDGE_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_FVG_MID_EDGE_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_FVG_MID_EDGE_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_FVG_MID_EDGE_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_OB_BOUNDARY_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_OB_BOUNDARY_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_OB_BOUNDARY_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_OB_BOUNDARY_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_OB_BOUNDARY_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_LIQUIDITY_RUN_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_LIQUIDITY_RUN_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_LIQUIDITY_RUN_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_LIQUIDITY_RUN_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | all_enabled | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_COMPOSITE_ANY_V2 | all_excluding_gbpusd_control | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_COMPOSITE_ANY_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 22} |
| STRUCT_COMPOSITE_ANY_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_COMPOSITE_ANY_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_COMPOSITE_ANY_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | blocked_dominance_controls | 0 |  |  | 0.0 |  |  |  | {} |

## Cohort Summary

| variant_id | cohort_key | role | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | same_bar | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| J46_J49_ONLY | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 10} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 0 |  |  | 0.0 |  |  |  | 0 | {'SETUP_NOT_REFINABLE': 12} |

## Selector Fire Summary

_No rows._

## Structural Event Census

_No rows._

## Structural Diagnostic Census

_No rows._

## Pairwise Versus J46

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_COMPOSITE_ANY_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_FVG_MID_EDGE_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_LIQUIDITY_RUN_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_OB_BOUNDARY_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_SWING_PROTECTED_V2 | J46_J49_ONLY | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |

## Pairwise Versus Fixed-R Control

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_COMPOSITE_ANY_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_FVG_MID_EDGE_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_OB_BOUNDARY_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |
| STRUCT_SWING_PROTECTED_V2 | PATH_LOCK_HALF_GAIN_V0 | 0 |  |  |  | 0.0 |  |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0.0 |  | 0 | 0 | 0 |

## Methodology Diagnostics

| exit_policy_pbo | pbo_status | pbo_promotion_usable | exit_policy_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- |
|  | BLOCKED_EMPTY_MATRIX | False |  | False |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Cost model | SENSITIVITY_NOT_MEASURED_COST | Historical OHLC does not contain reliable commission/spread/slippage; report uses R-cost sensitivity. |
| Lower-timeframe coverage | QUANTIFIED | M1 windows=0, M5 windows=0, M15 fallback windows=0. |
| Post-decision lower-TF start | PASS | Lower-timeframe rows with close_time <= setup decision clock: 0. |
| Remaining same-bar ambiguity | QUANTIFIED | Total SAME_BAR rows across all variants=0; all-enabled pessimistic best structural minus J46=None. |
| Future-swing leakage | RULED_OUT_BY_SELECTOR_RULE | Confirmed swings are unavailable until two later selected-timeframe bars close; tests cover this. |
| Unimplemented structural catalog | EXPLICITLY_SCOPED | Breaker, round-number, higher-timeframe composite, and reentry require fresh registered hypotheses. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical raw-OHLC structural-level exit-policy ablation. |

## Opened Questions

| question | status | detail |
| --- | --- | --- |
| Does structural path scaling beat J46 on the registered global metric? | ANSWERED | Headline all-enabled best structural minus J46=None. |
| Does the same result survive pessimistic same-bar treatment? | ANSWERED | Pessimistic all-enabled best structural minus J46=None. |
| Does structural selection reduce V1's fixed-R truncation problem? | ANSWERED | Best pairwise structural candidate=STRUCT_BOS_LEVEL_V2 truncation_lost_r=0.0, rescued_to_positive_n=0. |
| Can V2 answer breaker, round-number, or reentry hypotheses? | ANSWERED_NO | Those events require separate registered hypotheses because they add state reconstruction or risk accounting. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Reject or archive V2 structural lock-only as diagnostic evidence | The registered global and pessimistic same-bar tests did not clear the next-stage gate. |
| 2 | Use selector forensics to decide whether a fresh non-lock-only hypothesis is justified | If a selector rescues losses but still truncates winners, the problem is exit architecture rather than level detection. |
| 3 | Do not proceed to reentry without a separate risk-budgeted hypothesis | V2 contains no composite risk accounting or second-fill cost model. |

## Synthesis

- V2 tests structural lock floors, not new entries, prompt behavior, live execution, or risk-budgeted reentry.
- Structural candidates are generated only from closed post-decision path rows and are activated on the following selected path row.
- Any favorable V2 result can only justify a later registered validation hypothesis; it cannot promote live logic.
