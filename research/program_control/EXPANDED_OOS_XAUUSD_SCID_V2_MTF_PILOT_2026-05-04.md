# Phase 3 Path Scaling V2 Structural Level Selector

**Created UTC:** 2026-05-03T20:46:12.828497+00:00
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
| BOUNDED_DIAGNOSTIC | 76 | 30 | 30 | True | 2026-04-16T13:30:00+00:00 | 2026-04-17T17:00:00+00:00 |

## Direct Answers

| question | answer |
| --- | --- |
| Which V2 structural policy leads after 0.05R cost? | STRUCT_BOS_LEVEL_V2 with net_mean_r_cost_0.05=0.77465. |
| Did the best structural policy beat J46 globally? | Best structural minus J46 at 0.05R cost = 0.853118. |
| Did structural selection beat the best fixed-R lock control? | Best fixed-R minus J46 = 1.028468; compare best structural minus J46 = 0.853118. |
| Which variant leads overall? | PATH_LOCK_EARLY_BE_V0 with net_mean_r_cost_0.05=0.95. |
| Did the headline structural result survive pessimistic same-bar stress? | All-enabled pessimistic best structural minus J46 = 0.853118. |
| Where did structural selection look most interesting? | Target-cohort best structural minus J46 at 0.05R cost = None. |
| Which selector fired most often? | DISPLACEMENT_HALFBACK under STRUCT_DISPLACEMENT_HALFBACK_V2 with fires=10. |
| Does this promote live logic? | No. V2 is same-dataset historical research and remains NO_PROMOTION_VERDICT. |

## MTF Coverage

| setup_windows | m1_available_windows | m1_available_rows | m5_available_windows | m5_available_rows | m15_available_windows | m15_available_rows | m15_fallback_windows | selected_timeframes | lower_tf_start_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | 30 | 25650 | 30 | 5145 | 30 | 1725 | 0 | {'M1': 30} | 0 |

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
| BASE_RAW_FIXED_TP | baseline | 30 | 30 | 5 | 5 | 2.5 | 0.5 | 1.5 | 0.6 | 2.8 | 0.0 | 0.0 | 0.0 | 0.0 | 1.704099 | 1.704099 | 1.708312 | -2.090293 | {'NO_ENTRY': 25, 'SL': 2, 'TP': 3} | 0.991430648827 | 0.5 | 2.5 | -2.0 | 0.48 | 2.4 | -2.04 | 0.45 | 2.25 | -2.1 | 0.4 | 2.0 | -2.2 |
| J46_J49_ONLY | j46_j49 | 30 | 30 | 5 | 5 | -0.14234 | -0.028468 | 0.618371 | 0.6 | 8.8 | 0.0 | 0.0 | 0.0 | 0.0 | 2.327789 | 2.327789 | 2.333544 | -2.090293 | {'NO_ENTRY': 25, 'SL': 2, 'TIMEOUT': 3} | 0.999162240127 | -0.028468 | -0.14234 | -2.0 | -0.048468 | -0.24234 | -2.04 | -0.078468 | -0.39234 | -2.1 | -0.128468 | -0.64234 | -2.2 |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 30 | 30 | 5 | 5 | -0.5 | -0.1 | 0.5 | 0.6 | 8.8 | 0.6 | 0.6 | 0.0 | 0.0 | 2.327789 | 2.327789 | 2.333544 | -2.090293 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} | 0.999559186184 | -0.1 | -0.5 | -2.0 | -0.12 | -0.6 | -2.04 | -0.15 | -0.75 | -2.1 | -0.2 | -1.0 | -2.2 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 30 | 30 | 5 | 5 | 1.0 | 0.2 | 1.0 | 0.6 | 6.4 | 0.6 | 0.6 | 0.0 | 0.0 | 2.327789 | 2.327789 | 2.333544 | -2.090293 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} | 0.996757013164 | 0.2 | 1.0 | -2.0 | 0.18 | 0.9 | -2.04 | 0.15 | 0.75 | -2.1 | 0.1 | 0.5 | -2.2 |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 30 | 30 | 3 | 3 | 3.0 | 1.0 | 1.0 | 1.0 | 8.0 | 1.0 | 1.0 | 0.0 | 0.0 | 2.327789 | 2.332585 | 2.335462 | 0.205011 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SAME_BAR': 2} |  | 1.0 | 3.0 | 0.0 | 0.98 | 2.94 | 0.0 | 0.95 | 2.85 | 0.0 | 0.9 | 2.7 | 0.0 |
| STRUCT_SWING_PROTECTED_V2 | swing_structure | 30 | 30 | 5 | 5 | 0.761338 | 0.152268 | 0.76061 | 0.6 | 2.4 | 0.6 | 0.6 | 0.0 | 0.0 | 1.062748 | 1.067127 | 1.120653 | -2.090293 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} | 0.997406491265 | 0.152268 | 0.761338 | -2.0 | 0.132268 | 0.661338 | -2.04 | 0.102268 | 0.511338 | -2.1 | 0.052268 | 0.261338 | -2.2 |
| STRUCT_BOS_LEVEL_V2 | swing_structure | 30 | 30 | 5 | 5 | 4.123249 | 0.82465 | 1.156337 | 1.0 | 2.0 | 1.0 | 1.0 | 0.0 | 0.0 | 1.362453 | 1.362453 | 1.365821 | -0.967002 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} | 0.561215932162 | 0.82465 | 4.123249 | 0.0 | 0.80465 | 4.023249 | 0.0 | 0.77465 | 3.873249 | 0.0 | 0.72465 | 3.623249 | 0.0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | volatility_displacement | 30 | 30 | 5 | 5 | 3.269353 | 0.653871 | 0.900118 | 1.0 | 1.4 | 1.0 | 1.0 | 0.0 | 0.0 | 1.062748 | 1.067127 | 1.120653 | -0.967002 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} | 0.527774144111 | 0.653871 | 3.269353 | 0.0 | 0.633871 | 3.169353 | 0.0 | 0.603871 | 3.019353 | 0.0 | 0.553871 | 2.769353 | 0.0 |
| STRUCT_FVG_MID_EDGE_V2 | poi_boundary | 30 | 30 | 5 | 5 | 2.896666 | 0.579333 | 0.846318 | 1.0 | 1.4 | 1.0 | 1.0 | 0.0 | 0.0 | 1.062748 | 1.062748 | 1.065375 | -0.967002 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} | 0.679786833304 | 0.579333 | 2.896666 | 0.0 | 0.559333 | 2.796666 | 0.0 | 0.529333 | 2.646666 | 0.0 | 0.479333 | 2.396666 | 0.0 |
| STRUCT_OB_BOUNDARY_V2 | poi_boundary | 30 | 30 | 5 | 5 | 3.361197 | 0.672239 | 1.717201 | 0.6 | 5.0 | 0.6 | 0.6 | 0.0 | 0.0 | 2.327789 | 2.327789 | 2.333544 | -2.090293 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} | 0.987741633521 | 0.672239 | 3.361197 | -2.0 | 0.652239 | 3.261197 | -2.04 | 0.622239 | 3.111197 | -2.1 | 0.572239 | 2.861197 | -2.2 |
| STRUCT_LIQUIDITY_RUN_V2 | liquidity | 30 | 30 | 5 | 5 | 0.935101 | 0.18702 | 0.977025 | 0.6 | 2.2 | 0.6 | 0.6 | 0.0 | 0.0 | 1.062748 | 1.062748 | 1.065375 | -2.090293 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} | 0.996938591049 | 0.18702 | 0.935101 | -2.0 | 0.16702 | 0.835101 | -2.04 | 0.13702 | 0.685101 | -2.1 | 0.08702 | 0.435101 | -2.2 |
| STRUCT_COMPOSITE_ANY_V2 | composite | 30 | 30 | 5 | 5 | 3.496519 | 0.699304 | 0.846318 | 1.0 | 1.4 | 1.0 | 1.0 | 0.0 | 0.0 | 1.062748 | 1.062748 | 1.065375 | -0.967002 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} | 0.397767965309 | 0.699304 | 3.496519 | 0.0 | 0.679304 | 3.396519 | 0.0 | 0.649304 | 3.246519 | 0.0 | 0.599304 | 2.996519 | 0.0 |

## Same-Bar Stress Summary

| treatment | group | j46_net_mean_r_cost_0.05 | j46_n | best_structural_variant | best_structural_net_mean_r_cost_0.05 | best_structural_n | best_structural_minus_j46 | best_fixed_r_variant | best_fixed_r_net_mean_r_cost_0.05 | best_fixed_r_n | best_structural_minus_best_fixed_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | all_enabled | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.95 | 3 | -0.17535 |
| exclude_unresolved | all_excluding_gbpusd_control | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.95 | 3 | -0.17535 |
| exclude_unresolved | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| exclude_unresolved | blocked_dominance_controls | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.95 | 3 | -0.17535 |
| samebar_breakeven | all_enabled | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.55 | 5 | 0.22465 |
| samebar_breakeven | all_excluding_gbpusd_control | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.55 | 5 | 0.22465 |
| samebar_breakeven | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_breakeven | blocked_dominance_controls | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_EARLY_BE_V0 | 0.55 | 5 | 0.22465 |
| samebar_pessimistic | all_enabled | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_HALF_GAIN_V0 | 0.15 | 5 | 0.62465 |
| samebar_pessimistic | all_excluding_gbpusd_control | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_HALF_GAIN_V0 | 0.15 | 5 | 0.62465 |
| samebar_pessimistic | target_cohorts |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | primary_controlled_family |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | cleared_non_primary_targets |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | negative_controls |  | 0 |  |  |  |  |  |  |  |  |
| samebar_pessimistic | blocked_dominance_controls | -0.078468 | 5 | STRUCT_BOS_LEVEL_V2 | 0.77465 | 5 | 0.853118 | PATH_LOCK_HALF_GAIN_V0 | 0.15 | 5 | 0.62465 |

## Group Summary

| variant_id | group | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | all_enabled | 5 | 0.5 | 0.45 | 2.5 | 2.25 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TP': 3} |
| BASE_RAW_FIXED_TP | all_excluding_gbpusd_control | 5 | 0.5 | 0.45 | 2.5 | 2.25 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TP': 3} |
| BASE_RAW_FIXED_TP | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| BASE_RAW_FIXED_TP | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| BASE_RAW_FIXED_TP | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| BASE_RAW_FIXED_TP | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| BASE_RAW_FIXED_TP | blocked_dominance_controls | 5 | 0.5 | 0.45 | 2.5 | 2.25 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TP': 3} |
| J46_J49_ONLY | all_enabled | 5 | -0.028468 | -0.078468 | -0.14234 | -0.39234 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TIMEOUT': 3} |
| J46_J49_ONLY | all_excluding_gbpusd_control | 5 | -0.028468 | -0.078468 | -0.14234 | -0.39234 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TIMEOUT': 3} |
| J46_J49_ONLY | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| J46_J49_ONLY | blocked_dominance_controls | 5 | -0.028468 | -0.078468 | -0.14234 | -0.39234 | 0.6 | 0.0 | {'NO_ENTRY': 25, 'SL': 2, 'TIMEOUT': 3} |
| PATH_LOCK_CONSERVATIVE_V0 | all_enabled | 5 | -0.1 | -0.15 | -0.5 | -0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_CONSERVATIVE_V0 | all_excluding_gbpusd_control | 5 | -0.1 | -0.15 | -0.5 | -0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_CONSERVATIVE_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_CONSERVATIVE_V0 | blocked_dominance_controls | 5 | -0.1 | -0.15 | -0.5 | -0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_HALF_GAIN_V0 | all_enabled | 5 | 0.2 | 0.15 | 1.0 | 0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_HALF_GAIN_V0 | all_excluding_gbpusd_control | 5 | 0.2 | 0.15 | 1.0 | 0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_HALF_GAIN_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_HALF_GAIN_V0 | blocked_dominance_controls | 5 | 0.2 | 0.15 | 1.0 | 0.75 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_EARLY_BE_V0 | all_enabled | 3 | 1.0 | 0.95 | 3.0 | 2.85 | 1.0 | 1.0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SAME_BAR': 2} |
| PATH_LOCK_EARLY_BE_V0 | all_excluding_gbpusd_control | 3 | 1.0 | 0.95 | 3.0 | 2.85 | 1.0 | 1.0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SAME_BAR': 2} |
| PATH_LOCK_EARLY_BE_V0 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| PATH_LOCK_EARLY_BE_V0 | blocked_dominance_controls | 3 | 1.0 | 0.95 | 3.0 | 2.85 | 1.0 | 1.0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SAME_BAR': 2} |
| STRUCT_SWING_PROTECTED_V2 | all_enabled | 5 | 0.152268 | 0.102268 | 0.761338 | 0.511338 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_SWING_PROTECTED_V2 | all_excluding_gbpusd_control | 5 | 0.152268 | 0.102268 | 0.761338 | 0.511338 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_SWING_PROTECTED_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_SWING_PROTECTED_V2 | blocked_dominance_controls | 5 | 0.152268 | 0.102268 | 0.761338 | 0.511338 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_BOS_LEVEL_V2 | all_enabled | 5 | 0.82465 | 0.77465 | 4.123249 | 3.873249 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_BOS_LEVEL_V2 | all_excluding_gbpusd_control | 5 | 0.82465 | 0.77465 | 4.123249 | 3.873249 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_BOS_LEVEL_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_BOS_LEVEL_V2 | blocked_dominance_controls | 5 | 0.82465 | 0.77465 | 4.123249 | 3.873249 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_enabled | 5 | 0.653871 | 0.603871 | 3.269353 | 3.019353 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_excluding_gbpusd_control | 5 | 0.653871 | 0.603871 | 3.269353 | 3.019353 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | blocked_dominance_controls | 5 | 0.653871 | 0.603871 | 3.269353 | 3.019353 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_FVG_MID_EDGE_V2 | all_enabled | 5 | 0.579333 | 0.529333 | 2.896666 | 2.646666 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_FVG_MID_EDGE_V2 | all_excluding_gbpusd_control | 5 | 0.579333 | 0.529333 | 2.896666 | 2.646666 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_FVG_MID_EDGE_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_FVG_MID_EDGE_V2 | blocked_dominance_controls | 5 | 0.579333 | 0.529333 | 2.896666 | 2.646666 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_OB_BOUNDARY_V2 | all_enabled | 5 | 0.672239 | 0.622239 | 3.361197 | 3.111197 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_OB_BOUNDARY_V2 | all_excluding_gbpusd_control | 5 | 0.672239 | 0.622239 | 3.361197 | 3.111197 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_OB_BOUNDARY_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_OB_BOUNDARY_V2 | blocked_dominance_controls | 5 | 0.672239 | 0.622239 | 3.361197 | 3.111197 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_LIQUIDITY_RUN_V2 | all_enabled | 5 | 0.18702 | 0.13702 | 0.935101 | 0.685101 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_LIQUIDITY_RUN_V2 | all_excluding_gbpusd_control | 5 | 0.18702 | 0.13702 | 0.935101 | 0.685101 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_LIQUIDITY_RUN_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_LIQUIDITY_RUN_V2 | blocked_dominance_controls | 5 | 0.18702 | 0.13702 | 0.935101 | 0.685101 | 0.6 | 0.6 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_COMPOSITE_ANY_V2 | all_enabled | 5 | 0.699304 | 0.649304 | 3.496519 | 3.246519 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_COMPOSITE_ANY_V2 | all_excluding_gbpusd_control | 5 | 0.699304 | 0.649304 | 3.496519 | 3.246519 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_COMPOSITE_ANY_V2 | target_cohorts | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | primary_controlled_family | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | cleared_non_primary_targets | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | negative_controls | 0 |  |  | 0.0 |  |  |  | {} |
| STRUCT_COMPOSITE_ANY_V2 | blocked_dominance_controls | 5 | 0.699304 | 0.649304 | 3.496519 | 3.246519 | 1.0 | 1.0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |

## Cohort Summary

| variant_id | cohort_key | role | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | same_bar | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.5 | 0.45 | 2.5 | 2.25 | 0.6 | 0.0 | 0 | {'NO_ENTRY': 25, 'SL': 2, 'TP': 3} |
| J46_J49_ONLY | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | -0.028468 | -0.078468 | -0.14234 | -0.39234 | 0.6 | 0.0 | 0 | {'NO_ENTRY': 25, 'SL': 2, 'TIMEOUT': 3} |
| PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | -0.1 | -0.15 | -0.5 | -0.75 | 0.6 | 0.6 | 0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.2 | 0.15 | 1.0 | 0.75 | 0.6 | 0.6 | 0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 3 | 1.0 | 0.95 | 3.0 | 2.85 | 1.0 | 1.0 | 2 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SAME_BAR': 2} |
| STRUCT_SWING_PROTECTED_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.152268 | 0.102268 | 0.761338 | 0.511338 | 0.6 | 0.6 | 0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_BOS_LEVEL_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.82465 | 0.77465 | 4.123249 | 3.873249 | 1.0 | 1.0 | 0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.653871 | 0.603871 | 3.269353 | 3.019353 | 1.0 | 1.0 | 0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_FVG_MID_EDGE_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.579333 | 0.529333 | 2.896666 | 2.646666 | 1.0 | 1.0 | 0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |
| STRUCT_OB_BOUNDARY_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.672239 | 0.622239 | 3.361197 | 3.111197 | 0.6 | 0.6 | 0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_LIQUIDITY_RUN_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.18702 | 0.13702 | 0.935101 | 0.685101 | 0.6 | 0.6 | 0 | {'LOCK_STOP': 3, 'NO_ENTRY': 25, 'SL': 2} |
| STRUCT_COMPOSITE_ANY_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 5 | 0.699304 | 0.649304 | 3.496519 | 3.246519 | 1.0 | 1.0 | 0 | {'LOCK_STOP': 5, 'NO_ENTRY': 25} |

## Selector Fire Summary

| variant_id | selector_id | family | selected_timeframe | side | symbol | session | role | fires | resolved_n | gross_mean_r | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAUUSD | ny | dominance_watchlist | 10 | 10 | 0.780139 | {'LOCK_STOP': 10} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 8 | 8 | 0.679888 | {'LOCK_STOP': 8} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 8 | 8 | 1.795799 | {'LOCK_STOP': 8} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 5 | 5 | 0.82465 | {'LOCK_STOP': 5} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 5 | 5 | 0.904874 | {'LOCK_STOP': 5} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAUUSD | ny | dominance_watchlist | 4 | 4 | 0.961338 | {'LOCK_STOP': 4} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 3 | 3 | 1.00105 | {'LOCK_STOP': 3} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | XAUUSD | ny | dominance_watchlist | 3 | 3 | 0.978367 | {'LOCK_STOP': 3} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 2 | 2 | 0.324736 | {'LOCK_STOP': 2} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 2 | 2 | 0.846318 | {'LOCK_STOP': 2} |

## Structural Event Census

| selected_timeframe | side | selector_id | family | candidate_count |
| --- | --- | --- | --- | --- |
| M1 | LONG | BOS_BROKEN_LEVEL | swing_structure | 2838 |
| M1 | LONG | DISPLACEMENT_HALFBACK | volatility_displacement | 2607 |
| M1 | LONG | EQUAL_HIGH_LOW_RUN | liquidity | 17812 |
| M1 | LONG | FVG_MIDPOINT | poi_boundary | 2799 |
| M1 | LONG | FVG_PROTECTIVE_EDGE | poi_boundary | 2793 |
| M1 | LONG | OB_PROTECTIVE_BOUNDARY | poi_boundary | 2726 |
| M1 | LONG | PATH_HIGH_LOW_RUN | liquidity | 259 |
| M1 | LONG | PROTECTED_CONFIRMED_SWING | swing_structure | 22909 |

## Structural Diagnostic Census

| selected_timeframe | diagnostic_event | count |
| --- | --- | --- |
| M1 | CHOCH_AGAINST_TRADE | 2759 |
| M1 | CONFIRMED_SWING_HIGH | 3435 |
| M1 | CONFIRMED_SWING_LOW | 3155 |
| M1 | FAILED_BREAK_RECLAIM_HIGH | 308 |
| M1 | FAILED_BREAK_RECLAIM_LOW | 329 |
| M1 | SWEEP_AND_RECLAIM | 637 |

## Pairwise Versus J46

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.82465 | 0.853118 | 4.265589 | 1.0 | 0.0 | 5 | 0 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 0 | 0.0 | 0.0 | 2 | 2 | 0 |
| STRUCT_COMPOSITE_ANY_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.699304 | 0.727772 | 3.638859 | 1.0 | 0.0 | 5 | 0 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 0 | 0.0 | 0.0 | 2 | 2 | 0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.653871 | 0.682339 | 3.411693 | 1.0 | 0.0 | 5 | 0 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 0 | 0.0 | 0.0 | 2 | 2 | 0 |
| STRUCT_FVG_MID_EDGE_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.579333 | 0.607801 | 3.039006 | 1.0 | 0.0 | 5 | 0 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 0 | 0.0 | 0.0 | 2 | 2 | 0 |
| STRUCT_LIQUIDITY_RUN_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.18702 | 0.215488 | 1.077441 | 0.6 | 0.0 | 3 | 0 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| STRUCT_OB_BOUNDARY_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.672239 | 0.700707 | 3.503537 | 0.6 | 0.0 | 3 | 0 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| STRUCT_SWING_PROTECTED_V2 | J46_J49_ONLY | 5 | -0.028468 | 0.152268 | 0.180736 | 0.903678 | 0.6 | 0.0 | 3 | 0 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |

## Pairwise Versus Fixed-R Control

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.82465 | 0.62465 | 3.123249 | 1.0 | 0.0 | 5 | 0 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 0 | 0.0 | 0.0 | 2 | 2 | 0 |
| STRUCT_COMPOSITE_ANY_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.699304 | 0.499304 | 2.496519 | 0.6 | 0.4 | 3 | 2 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 2 | 0.155375 | 0.031075 | 2 | 2 | 0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.653871 | 0.453871 | 2.269353 | 0.4 | 0.6 | 2 | 3 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 3 | 0.27191 | 0.054382 | 2 | 2 | 0 |
| STRUCT_FVG_MID_EDGE_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.579333 | 0.379333 | 1.896666 | 0.4 | 0.6 | 2 | 3 | 0 | 3 | 5 | 3 | 0 | 5 | 1.0 | 3 | 0.457559 | 0.091512 | 2 | 2 | 0 |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.18702 | -0.01298 | -0.064899 | 0.0 | 0.6 | 0 | 3 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 3 | 0.064899 | 0.01298 | 0 | 0 | 0 |
| STRUCT_OB_BOUNDARY_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.672239 | 0.472239 | 2.361197 | 0.6 | 0.0 | 3 | 0 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| STRUCT_SWING_PROTECTED_V2 | PATH_LOCK_HALF_GAIN_V0 | 5 | 0.2 | 0.152268 | -0.047732 | -0.238662 | 0.2 | 0.4 | 1 | 2 | 2 | 3 | 3 | 3 | 2 | 3 | 0.6 | 2 | 0.241083 | 0.048217 | 0 | 0 | 0 |

## Methodology Diagnostics

| exit_policy_pbo | pbo_status | pbo_promotion_usable | exit_policy_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- |
|  | BLOCKED_INSUFFICIENT_PERIODS_OR_STRATEGIES | False |  | False |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Cost model | SENSITIVITY_NOT_MEASURED_COST | Historical OHLC does not contain reliable commission/spread/slippage; report uses R-cost sensitivity. |
| Lower-timeframe coverage | QUANTIFIED | M1 windows=30, M5 windows=30, M15 fallback windows=0. |
| Post-decision lower-TF start | PASS | Lower-timeframe rows with close_time <= setup decision clock: 0. |
| Remaining same-bar ambiguity | QUANTIFIED | Total SAME_BAR rows across all variants=2; all-enabled pessimistic best structural minus J46=0.853118. |
| Future-swing leakage | RULED_OUT_BY_SELECTOR_RULE | Confirmed swings are unavailable until two later selected-timeframe bars close; tests cover this. |
| Unimplemented structural catalog | EXPLICITLY_SCOPED | Breaker, round-number, higher-timeframe composite, and reentry require fresh registered hypotheses. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical raw-OHLC structural-level exit-policy ablation. |

## Opened Questions

| question | status | detail |
| --- | --- | --- |
| Does structural path scaling beat J46 on the registered global metric? | ANSWERED | Headline all-enabled best structural minus J46=0.853118. |
| Does the same result survive pessimistic same-bar treatment? | ANSWERED | Pessimistic all-enabled best structural minus J46=0.853118. |
| Does structural selection reduce V1's fixed-R truncation problem? | ANSWERED | Best pairwise structural candidate=STRUCT_BOS_LEVEL_V2 truncation_lost_r=0.0, rescued_to_positive_n=2. |
| Can V2 answer breaker, round-number, or reentry hypotheses? | ANSWERED_NO | Those events require separate registered hypotheses because they add state reconstruction or risk accounting. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Write a fresh validation hypothesis for the winning structural family | V2 can only register a later validation run, not promote live logic. |
| 2 | Audit concentration by symbol/session/cohort before any V3 design | A structural result concentrated in one pocket is not a general path-scaling edge. |

## Synthesis

- V2 tests structural lock floors, not new entries, prompt behavior, live execution, or risk-budgeted reentry.
- Structural candidates are generated only from closed post-decision path rows and are activated on the following selected path row.
- Any favorable V2 result can only justify a later registered validation hypothesis; it cannot promote live logic.
