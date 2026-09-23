# Phase 3 Path Scaling V2 Structural Level Selector

**Created UTC:** 2026-05-01T22:31:35.810558+00:00
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
| FULL_AVAILABLE_CORPUS | 205197 | 23483 | 12831 | True | 2022-02-07T13:30:00+00:00 | 2026-04-30T17:00:00+00:00 |

## Direct Answers

| question | answer |
| --- | --- |
| Which V2 structural policy leads after 0.05R cost? | STRUCT_SWING_PROTECTED_V2 with net_mean_r_cost_0.05=0.188405. |
| Did the best structural policy beat J46 globally? | Best structural minus J46 at 0.05R cost = 0.024511. |
| Did structural selection beat the best fixed-R lock control? | Best fixed-R minus J46 = -0.022329; compare best structural minus J46 = 0.024511. |
| Which variant leads overall? | STRUCT_SWING_PROTECTED_V2 with net_mean_r_cost_0.05=0.188405. |
| Did the headline structural result survive pessimistic same-bar stress? | All-enabled pessimistic best structural minus J46 = 0.05872. |
| Where did structural selection look most interesting? | Target-cohort best structural minus J46 at 0.05R cost = 0.041158. |
| Which selector fired most often? | PROTECTED_CONFIRMED_SWING under STRUCT_SWING_PROTECTED_V2 with fires=457. |
| Does this promote live logic? | No. V2 is same-dataset historical research and remains NO_PROMOTION_VERDICT. |

## MTF Coverage

| setup_windows | m1_available_windows | m1_available_rows | m5_available_windows | m5_available_rows | m15_available_windows | m15_available_rows | m15_fallback_windows | selected_timeframes | lower_tf_start_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12831 | 774 | 1005608 | 5512 | 1408564 | 12830 | 1092041 | 7319 | {'M1': 774, 'M15': 7319, 'M5': 4738} | 0 |

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
| BASE_RAW_FIXED_TP | baseline | 23483 | 12831 | 3905 | 3898 | 805.111736 | 0.206545 | -0.091581 | 0.491534 | 11.584915 | 0.0 | 0.0 | 0.00744 | 0.0 | 1.193556 | 1.609821 | 1.870665 | -1.529894 | {'NO_ENTRY': 7631, 'SAME_BAR': 1295, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1888, 'TIMEOUT': 301, 'TP': 1716} | 0.0 | 0.206545 | 805.111736 | -88.887538 | 0.186545 | 727.151736 | -91.147538 | 0.156545 | 610.211736 | -94.537538 | 0.106545 | 415.311736 | -100.187538 |
| J46_J49_ONLY | j46_j49 | 23483 | 12831 | 4487 | 4477 | 957.601655 | 0.213894 | -0.108364 | 0.466384 | 8.200581 | 0.098507 | 0.00624 | 0.101407 | 0.019433 | 1.029804 | 1.861024 | 3.014877 | -1.548182 | {'BE_STOP': 28, 'NO_ENTRY': 7631, 'SAME_BAR': 713, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1953, 'TIMEOUT': 2419, 'TP': 87} | 0.0 | 0.213894 | 957.601655 | -121.921318 | 0.193894 | 868.061655 | -125.561318 | 0.163894 | 733.751655 | -131.021318 | 0.113894 | 509.901655 | -142.224131 |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 23483 | 12831 | 3891 | 3884 | 731.530537 | 0.188345 | 0.0 | 0.476313 | 8.147528 | 0.318941 | 0.112824 | 0.07415 | 0.013903 | 0.975389 | 1.755434 | 2.64587 | -1.482079 | {'BE_STOP': 216, 'LOCK_STOP': 223, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1965, 'TP': 41} | 3e-12 | 0.188345 | 731.530537 | -139.052438 | 0.168345 | 653.850537 | -148.512438 | 0.138345 | 537.330537 | -162.702438 | 0.088345 | 343.130537 | -188.443787 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 23483 | 12831 | 3891 | 3884 | 744.039507 | 0.191565 | 0.164554 | 0.531926 | 7.734809 | 0.318941 | 0.177846 | 0.066684 | 0.009784 | 0.975389 | 1.695892 | 2.498677 | -1.477386 | {'LOCK_STOP': 692, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1722, 'TP': 31} | 0.0 | 0.191565 | 744.039507 | -109.271251 | 0.171565 | 666.359507 | -119.531251 | 0.141565 | 549.839507 | -134.921251 | 0.091565 | 355.639507 | -160.571251 |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 23483 | 12831 | 3211 | 3206 | 466.501659 | 0.145509 | 0.0 | 0.482533 | 7.678104 | 0.47493 | 0.246652 | 0.056145 | 0.00811 | 0.901665 | 1.553687 | 2.279789 | -1.336221 | {'BE_STOP': 322, 'LOCK_STOP': 470, 'NO_ENTRY': 7631, 'SAME_BAR': 1989, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1057, 'TIMEOUT': 1343, 'TP': 19} | 5.8589e-07 | 0.145509 | 466.501659 | -86.781514 | 0.125509 | 402.381659 | -95.741514 | 0.095509 | 306.201659 | -109.181514 | 0.045509 | 145.901659 | -139.347879 |
| STRUCT_SWING_PROTECTED_V2 | swing_structure | 23483 | 12831 | 4545 | 4530 | 1079.974166 | 0.238405 | 0.173019 | 0.604194 | 5.619205 | 0.493069 | 0.39538 | 0.073068 | 0.013907 | 0.738306 | 1.607816 | 2.588432 | -1.50447 | {'LOCK_STOP': 1797, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1609, 'TIMEOUT': 1078, 'TP': 61} | 0.0 | 0.238405 | 1079.974166 | -84.686266 | 0.218405 | 989.374166 | -96.106266 | 0.188405 | 853.474166 | -113.236266 | 0.138405 | 626.974166 | -159.362068 |
| STRUCT_BOS_LEVEL_V2 | swing_structure | 23483 | 12831 | 4545 | 4530 | 1028.570056 | 0.227057 | 0.067193 | 0.525607 | 6.415894 | 0.360616 | 0.318592 | 0.080574 | 0.019868 | 0.901665 | 1.675807 | 2.73872 | -1.554814 | {'LOCK_STOP': 1448, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1863, 'TIMEOUT': 1167, 'TP': 67} | 0.0 | 0.227057 | 1028.570056 | -121.523664 | 0.207057 | 937.970056 | -139.742562 | 0.177057 | 802.070056 | -168.632562 | 0.127057 | 575.570056 | -216.782562 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | volatility_displacement | 23483 | 12831 | 4545 | 4530 | 763.74945 | 0.168598 | 0.153481 | 0.601545 | 4.841722 | 0.540374 | 0.49659 | 0.064901 | 0.004415 | 0.733026 | 1.597131 | 2.497687 | -1.508965 | {'LOCK_STOP': 2257, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1594, 'TIMEOUT': 683, 'TP': 11} | 0.0 | 0.168598 | 763.74945 | -112.517917 | 0.148598 | 673.14945 | -122.717917 | 0.118598 | 537.24945 | -148.551691 | 0.068598 | 310.74945 | -192.501691 |
| STRUCT_FVG_MID_EDGE_V2 | poi_boundary | 23483 | 12831 | 4545 | 4530 | 1069.77945 | 0.236154 | 0.175563 | 0.587417 | 5.37947 | 0.535534 | 0.454345 | 0.073731 | 0.013907 | 0.832363 | 1.663544 | 2.51185 | -1.535582 | {'LOCK_STOP': 2065, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1671, 'TIMEOUT': 758, 'TP': 51} | 0.0 | 0.236154 | 1069.77945 | -138.056118 | 0.216154 | 979.17945 | -156.856118 | 0.186154 | 843.27945 | -185.056118 | 0.136154 | 616.77945 | -233.436901 |
| STRUCT_OB_BOUNDARY_V2 | poi_boundary | 23483 | 12831 | 4545 | 4530 | 1031.777617 | 0.227765 | 0.026708 | 0.507064 | 7.426269 | 0.283608 | 0.171617 | 0.101545 | 0.021854 | 0.969538 | 1.842796 | 3.015815 | -1.554814 | {'LOCK_STOP': 780, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1914, 'TIMEOUT': 1764, 'TP': 87} | 0.0 | 0.227765 | 1031.777617 | -116.728128 | 0.207765 | 941.177617 | -135.988128 | 0.177765 | 805.277617 | -164.878128 | 0.127765 | 578.777617 | -213.028128 |
| STRUCT_LIQUIDITY_RUN_V2 | liquidity | 23483 | 12831 | 4545 | 4530 | 970.11142 | 0.214153 | 0.119612 | 0.530022 | 6.320971 | 0.345215 | 0.311991 | 0.082561 | 0.014128 | 0.869142 | 1.686894 | 2.724871 | -1.547065 | {'LOCK_STOP': 1418, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1857, 'TIMEOUT': 1218, 'TP': 52} | 0.0 | 0.214153 | 970.11142 | -119.983921 | 0.194153 | 879.51142 | -139.283921 | 0.164153 | 743.61142 | -168.233921 | 0.114153 | 517.11142 | -216.793706 |
| STRUCT_COMPOSITE_ANY_V2 | composite | 23483 | 12831 | 4545 | 4530 | 778.383086 | 0.171828 | 0.184814 | 0.659823 | 3.679912 | 0.653245 | 0.630583 | 0.048124 | 0.001766 | 0.673889 | 1.271354 | 2.047967 | -1.47295 | {'LOCK_STOP': 2866, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1430, 'TIMEOUT': 243, 'TP': 6} | 0.0 | 0.171828 | 778.383086 | -79.531016 | 0.151828 | 687.783086 | -96.48984 | 0.121828 | 551.883086 | -124.022287 | 0.071828 | 325.383086 | -171.022287 |

## Same-Bar Stress Summary

| treatment | group | j46_net_mean_r_cost_0.05 | j46_n | best_structural_variant | best_structural_net_mean_r_cost_0.05 | best_structural_n | best_structural_minus_j46 | best_fixed_r_variant | best_fixed_r_net_mean_r_cost_0.05 | best_fixed_r_n | best_structural_minus_best_fixed_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | all_enabled | 0.163894 | 4477 | STRUCT_SWING_PROTECTED_V2 | 0.188405 | 4530 | 0.024511 | PATH_LOCK_HALF_GAIN_V0 | 0.141565 | 3884 | 0.04684 |
| exclude_unresolved | all_excluding_gbpusd_control | 0.229402 | 3762 | STRUCT_SWING_PROTECTED_V2 | 0.261569 | 3815 | 0.032167 | PATH_LOCK_CONSERVATIVE_V0 | 0.205819 | 3214 | 0.05575 |
| exclude_unresolved | target_cohorts | 0.409292 | 1406 | STRUCT_OB_BOUNDARY_V2 | 0.45045 | 1421 | 0.041158 | PATH_LOCK_CONSERVATIVE_V0 | 0.472889 | 1270 | -0.022439 |
| exclude_unresolved | primary_controlled_family | 0.395481 | 674 | STRUCT_LIQUIDITY_RUN_V2 | 0.431485 | 686 | 0.036004 | PATH_LOCK_CONSERVATIVE_V0 | 0.423483 | 596 | 0.008002 |
| exclude_unresolved | cleared_non_primary_targets | 0.422008 | 732 | STRUCT_OB_BOUNDARY_V2 | 0.471964 | 735 | 0.049956 | PATH_LOCK_EARLY_BE_V0 | 0.584256 | 576 | -0.112292 |
| exclude_unresolved | negative_controls | -0.150354 | 1518 | STRUCT_FVG_MID_EDGE_V2 | -0.103685 | 1561 | 0.046669 | PATH_LOCK_HALF_GAIN_V0 | -0.16443 | 1426 | 0.060745 |
| exclude_unresolved | blocked_dominance_controls | 0.248889 | 1553 | STRUCT_FVG_MID_EDGE_V2 | 0.33436 | 1548 | 0.085471 | PATH_LOCK_HALF_GAIN_V0 | 0.190875 | 1188 | 0.143485 |
| samebar_breakeven | all_enabled | 0.134509 | 5190 | STRUCT_SWING_PROTECTED_V2 | 0.162887 | 5073 | 0.028378 | PATH_LOCK_HALF_GAIN_V0 | 0.093277 | 5193 | 0.06961 |
| samebar_breakeven | all_excluding_gbpusd_control | 0.186843 | 4438 | STRUCT_SWING_PROTECTED_V2 | 0.224258 | 4334 | 0.037415 | PATH_LOCK_CONSERVATIVE_V0 | 0.135139 | 4441 | 0.089119 |
| samebar_breakeven | target_cohorts | 0.372344 | 1529 | STRUCT_OB_BOUNDARY_V2 | 0.418471 | 1518 | 0.046127 | PATH_LOCK_CONSERVATIVE_V0 | 0.384032 | 1530 | 0.034439 |
| samebar_breakeven | primary_controlled_family | 0.359065 | 734 | STRUCT_LIQUIDITY_RUN_V2 | 0.399998 | 734 | 0.040933 | PATH_LOCK_CONSERVATIVE_V0 | 0.334463 | 734 | 0.065535 |
| samebar_breakeven | cleared_non_primary_targets | 0.384604 | 795 | STRUCT_OB_BOUNDARY_V2 | 0.439341 | 784 | 0.054737 | PATH_LOCK_HALF_GAIN_V0 | 0.44659 | 796 | -0.007249 |
| samebar_breakeven | negative_controls | -0.137299 | 1745 | STRUCT_FVG_MID_EDGE_V2 | -0.098385 | 1732 | 0.038914 | PATH_LOCK_HALF_GAIN_V0 | -0.143511 | 1745 | 0.045126 |
| samebar_breakeven | blocked_dominance_controls | 0.192262 | 1916 | STRUCT_FVG_MID_EDGE_V2 | 0.276379 | 1823 | 0.084117 | PATH_LOCK_HALF_GAIN_V0 | 0.099197 | 1918 | 0.177182 |
| samebar_pessimistic | all_enabled | -0.002871 | 5190 | STRUCT_SWING_PROTECTED_V2 | 0.055849 | 5073 | 0.05872 | PATH_LOCK_HALF_GAIN_V0 | -0.158793 | 5193 | 0.214642 |
| samebar_pessimistic | all_excluding_gbpusd_control | 0.034522 | 4438 | STRUCT_SWING_PROTECTED_V2 | 0.104508 | 4334 | 0.069986 | PATH_LOCK_CONSERVATIVE_V0 | -0.14115 | 4441 | 0.245658 |
| samebar_pessimistic | target_cohorts | 0.291899 | 1529 | STRUCT_OB_BOUNDARY_V2 | 0.354571 | 1518 | 0.062672 | PATH_LOCK_CONSERVATIVE_V0 | 0.214097 | 1530 | 0.140474 |
| samebar_pessimistic | primary_controlled_family | 0.277322 | 734 | STRUCT_LIQUIDITY_RUN_V2 | 0.334603 | 734 | 0.057281 | PATH_LOCK_CONSERVATIVE_V0 | 0.146452 | 734 | 0.188151 |
| samebar_pessimistic | cleared_non_primary_targets | 0.305359 | 795 | STRUCT_OB_BOUNDARY_V2 | 0.376841 | 784 | 0.071482 | PATH_LOCK_HALF_GAIN_V0 | 0.293323 | 796 | 0.083518 |
| samebar_pessimistic | negative_controls | -0.267385 | 1745 | STRUCT_FVG_MID_EDGE_V2 | -0.197114 | 1732 | 0.070271 | PATH_LOCK_HALF_GAIN_V0 | -0.326319 | 1745 | 0.129205 |
| samebar_pessimistic | blocked_dominance_controls | 0.002805 | 1916 | STRUCT_FVG_MID_EDGE_V2 | 0.125529 | 1823 | 0.122724 | PATH_LOCK_HALF_GAIN_V0 | -0.281408 | 1918 | 0.406937 |

## Group Summary

| variant_id | group | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | all_enabled | 3898 | 0.206545 | 0.156545 | 805.111736 | 610.211736 | 0.491534 | 0.0 | {'NO_ENTRY': 7631, 'SAME_BAR': 1295, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1888, 'TIMEOUT': 301, 'TP': 1716} |
| BASE_RAW_FIXED_TP | all_excluding_gbpusd_control | 3228 | 0.280789 | 0.230789 | 906.385429 | 744.985429 | 0.522924 | 0.0 | {'NO_ENTRY': 6751, 'SAME_BAR': 1213, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1474, 'TIMEOUT': 243, 'TP': 1517} |
| BASE_RAW_FIXED_TP | target_cohorts | 1270 | 0.40674 | 0.35674 | 516.559471 | 453.059471 | 0.569291 | 0.0 | {'NO_ENTRY': 2610, 'SAME_BAR': 260, 'SETUP_NOT_REFINABLE': 4081, 'SL': 514, 'TIMEOUT': 98, 'TP': 659} |
| BASE_RAW_FIXED_TP | primary_controlled_family | 596 | 0.393097 | 0.343097 | 234.285883 | 204.485883 | 0.57047 | 0.0 | {'NO_ENTRY': 1095, 'SAME_BAR': 138, 'SETUP_NOT_REFINABLE': 2257, 'SL': 247, 'TIMEOUT': 45, 'TP': 304} |
| BASE_RAW_FIXED_TP | cleared_non_primary_targets | 674 | 0.418804 | 0.368804 | 282.273588 | 248.573588 | 0.568249 | 0.0 | {'NO_ENTRY': 1515, 'SAME_BAR': 122, 'SETUP_NOT_REFINABLE': 1824, 'SL': 267, 'TIMEOUT': 53, 'TP': 355} |
| BASE_RAW_FIXED_TP | negative_controls | 1426 | -0.102844 | -0.152844 | -146.655466 | -217.955466 | 0.367461 | 0.0 | {'NO_ENTRY': 2021, 'SAME_BAR': 319, 'SETUP_NOT_REFINABLE': 3836, 'SL': 868, 'TIMEOUT': 104, 'TP': 457} |
| BASE_RAW_FIXED_TP | blocked_dominance_controls | 1202 | 0.36207 | 0.31207 | 435.207731 | 375.107731 | 0.556572 | 0.0 | {'NO_ENTRY': 3000, 'SAME_BAR': 716, 'SETUP_NOT_REFINABLE': 2735, 'SL': 506, 'TIMEOUT': 99, 'TP': 600} |
| J46_J49_ONLY | all_enabled | 4477 | 0.213894 | 0.163894 | 957.601655 | 733.751655 | 0.466384 | 0.098507 | {'BE_STOP': 28, 'NO_ENTRY': 7631, 'SAME_BAR': 713, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1953, 'TIMEOUT': 2419, 'TP': 87} |
| J46_J49_ONLY | all_excluding_gbpusd_control | 3762 | 0.279402 | 0.229402 | 1051.109876 | 863.009876 | 0.488836 | 0.108194 | {'BE_STOP': 21, 'NO_ENTRY': 6751, 'SAME_BAR': 676, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1572, 'TIMEOUT': 2101, 'TP': 77} |
| J46_J49_ONLY | target_cohorts | 1406 | 0.459292 | 0.409292 | 645.764249 | 575.464249 | 0.559744 | 0.117188 | {'NO_ENTRY': 2610, 'SAME_BAR': 123, 'SETUP_NOT_REFINABLE': 4081, 'SL': 461, 'TIMEOUT': 913, 'TP': 34} |
| J46_J49_ONLY | primary_controlled_family | 674 | 0.445481 | 0.395481 | 300.254056 | 266.554056 | 0.60089 | 0.102374 | {'NO_ENTRY': 1095, 'SAME_BAR': 60, 'SETUP_NOT_REFINABLE': 2257, 'SL': 186, 'TIMEOUT': 478, 'TP': 10} |
| J46_J49_ONLY | cleared_non_primary_targets | 732 | 0.472008 | 0.422008 | 345.510193 | 308.910193 | 0.521858 | 0.13079 | {'NO_ENTRY': 1515, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 1824, 'SL': 275, 'TIMEOUT': 435, 'TP': 24} |
| J46_J49_ONLY | negative_controls | 1518 | -0.100354 | -0.150354 | -152.337192 | -228.237192 | 0.410408 | 0.029586 | {'BE_STOP': 7, 'NO_ENTRY': 2021, 'SAME_BAR': 227, 'SETUP_NOT_REFINABLE': 3836, 'SL': 740, 'TIMEOUT': 764, 'TP': 10} |
| J46_J49_ONLY | blocked_dominance_controls | 1553 | 0.298889 | 0.248889 | 464.174598 | 386.524598 | 0.436574 | 0.148909 | {'BE_STOP': 21, 'NO_ENTRY': 3000, 'SAME_BAR': 363, 'SETUP_NOT_REFINABLE': 2735, 'SL': 752, 'TIMEOUT': 742, 'TP': 43} |
| PATH_LOCK_CONSERVATIVE_V0 | all_enabled | 3884 | 0.188345 | 0.138345 | 731.530537 | 537.330537 | 0.476313 | 0.318941 | {'BE_STOP': 216, 'LOCK_STOP': 223, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1965, 'TP': 41} |
| PATH_LOCK_CONSERVATIVE_V0 | all_excluding_gbpusd_control | 3214 | 0.255819 | 0.205819 | 822.201394 | 661.501394 | 0.504667 | 0.344099 | {'BE_STOP': 211, 'LOCK_STOP': 196, 'NO_ENTRY': 6751, 'SAME_BAR': 1227, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1084, 'TIMEOUT': 1698, 'TP': 31} |
| PATH_LOCK_CONSERVATIVE_V0 | target_cohorts | 1270 | 0.522889 | 0.472889 | 664.068411 | 600.568411 | 0.579528 | 0.372935 | {'BE_STOP': 87, 'LOCK_STOP': 75, 'NO_ENTRY': 2610, 'SAME_BAR': 260, 'SETUP_NOT_REFINABLE': 4081, 'SL': 296, 'TIMEOUT': 792, 'TP': 21} |
| PATH_LOCK_CONSERVATIVE_V0 | primary_controlled_family | 596 | 0.473483 | 0.423483 | 282.196076 | 252.396076 | 0.597315 | 0.315436 | {'BE_STOP': 26, 'LOCK_STOP': 17, 'NO_ENTRY': 1095, 'SAME_BAR': 138, 'SETUP_NOT_REFINABLE': 2257, 'SL': 133, 'TIMEOUT': 413, 'TP': 7} |
| PATH_LOCK_CONSERVATIVE_V0 | cleared_non_primary_targets | 674 | 0.566576 | 0.516576 | 381.872335 | 348.172335 | 0.563798 | 0.423704 | {'BE_STOP': 61, 'LOCK_STOP': 58, 'NO_ENTRY': 1515, 'SAME_BAR': 122, 'SETUP_NOT_REFINABLE': 1824, 'SL': 163, 'TIMEOUT': 379, 'TP': 14} |
| PATH_LOCK_CONSERVATIVE_V0 | negative_controls | 1426 | -0.119888 | -0.169888 | -170.960098 | -242.260098 | 0.396213 | 0.204339 | {'BE_STOP': 26, 'LOCK_STOP': 37, 'NO_ENTRY': 2021, 'SAME_BAR': 319, 'SETUP_NOT_REFINABLE': 3836, 'SL': 696, 'TIMEOUT': 660, 'TP': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | blocked_dominance_controls | 1188 | 0.200692 | 0.150692 | 238.422224 | 179.022224 | 0.462121 | 0.398825 | {'BE_STOP': 103, 'LOCK_STOP': 111, 'NO_ENTRY': 3000, 'SAME_BAR': 730, 'SETUP_NOT_REFINABLE': 2735, 'SL': 454, 'TIMEOUT': 513, 'TP': 10} |
| PATH_LOCK_HALF_GAIN_V0 | all_enabled | 3884 | 0.191565 | 0.141565 | 744.039507 | 549.839507 | 0.531926 | 0.318941 | {'LOCK_STOP': 692, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1722, 'TP': 31} |
| PATH_LOCK_HALF_GAIN_V0 | all_excluding_gbpusd_control | 3214 | 0.253533 | 0.203533 | 814.854068 | 654.154068 | 0.570317 | 0.344099 | {'LOCK_STOP': 639, 'NO_ENTRY': 6751, 'SAME_BAR': 1227, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1084, 'TIMEOUT': 1476, 'TP': 21} |
| PATH_LOCK_HALF_GAIN_V0 | target_cohorts | 1270 | 0.489021 | 0.439021 | 621.056505 | 557.556505 | 0.648031 | 0.372935 | {'LOCK_STOP': 245, 'NO_ENTRY': 2610, 'SAME_BAR': 260, 'SETUP_NOT_REFINABLE': 4081, 'SL': 296, 'TIMEOUT': 716, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | primary_controlled_family | 596 | 0.37881 | 0.32881 | 225.771054 | 195.971054 | 0.64094 | 0.315436 | {'LOCK_STOP': 92, 'NO_ENTRY': 1095, 'SAME_BAR': 138, 'SETUP_NOT_REFINABLE': 2257, 'SL': 133, 'TIMEOUT': 371} |
| PATH_LOCK_HALF_GAIN_V0 | cleared_non_primary_targets | 674 | 0.586477 | 0.536477 | 395.285451 | 361.585451 | 0.654303 | 0.423704 | {'LOCK_STOP': 153, 'NO_ENTRY': 1515, 'SAME_BAR': 122, 'SETUP_NOT_REFINABLE': 1824, 'SL': 163, 'TIMEOUT': 345, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | negative_controls | 1426 | -0.11443 | -0.16443 | -163.176597 | -234.476597 | 0.414446 | 0.204339 | {'LOCK_STOP': 147, 'NO_ENTRY': 2021, 'SAME_BAR': 319, 'SETUP_NOT_REFINABLE': 3836, 'SL': 696, 'TIMEOUT': 576, 'TP': 10} |
| PATH_LOCK_HALF_GAIN_V0 | blocked_dominance_controls | 1188 | 0.240875 | 0.190875 | 286.159599 | 226.759599 | 0.548822 | 0.398825 | {'LOCK_STOP': 300, 'NO_ENTRY': 3000, 'SAME_BAR': 730, 'SETUP_NOT_REFINABLE': 2735, 'SL': 454, 'TIMEOUT': 430, 'TP': 7} |
| PATH_LOCK_EARLY_BE_V0 | all_enabled | 3206 | 0.145509 | 0.095509 | 466.501659 | 306.201659 | 0.482533 | 0.47493 | {'BE_STOP': 322, 'LOCK_STOP': 470, 'NO_ENTRY': 7631, 'SAME_BAR': 1989, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1057, 'TIMEOUT': 1343, 'TP': 19} |
| PATH_LOCK_EARLY_BE_V0 | all_excluding_gbpusd_control | 2627 | 0.24171 | 0.19171 | 634.97138 | 503.62138 | 0.523791 | 0.522615 | {'BE_STOP': 294, 'LOCK_STOP': 440, 'NO_ENTRY': 6751, 'SAME_BAR': 1816, 'SETUP_NOT_REFINABLE': 10400, 'SL': 731, 'TIMEOUT': 1147, 'TP': 19} |
| PATH_LOCK_EARLY_BE_V0 | target_cohorts | 1113 | 0.477437 | 0.427437 | 531.387158 | 475.737158 | 0.613657 | 0.578097 | {'BE_STOP': 110, 'LOCK_STOP': 174, 'NO_ENTRY': 2610, 'SAME_BAR': 417, 'SETUP_NOT_REFINABLE': 4081, 'SL': 202, 'TIMEOUT': 614, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | primary_controlled_family | 537 | 0.309229 | 0.259229 | 166.055806 | 139.205806 | 0.594041 | 0.543762 | {'BE_STOP': 69, 'LOCK_STOP': 70, 'NO_ENTRY': 1095, 'SAME_BAR': 197, 'SETUP_NOT_REFINABLE': 2257, 'SL': 85, 'TIMEOUT': 313} |
| PATH_LOCK_EARLY_BE_V0 | cleared_non_primary_targets | 576 | 0.634256 | 0.584256 | 365.331352 | 336.531352 | 0.631944 | 0.610052 | {'BE_STOP': 41, 'LOCK_STOP': 104, 'NO_ENTRY': 1515, 'SAME_BAR': 220, 'SETUP_NOT_REFINABLE': 1824, 'SL': 117, 'TIMEOUT': 301, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | negative_controls | 1229 | -0.186156 | -0.236156 | -228.786274 | -290.236274 | 0.376729 | 0.323314 | {'BE_STOP': 80, 'LOCK_STOP': 108, 'NO_ENTRY': 2021, 'SAME_BAR': 517, 'SETUP_NOT_REFINABLE': 3836, 'SL': 575, 'TIMEOUT': 468} |
| PATH_LOCK_EARLY_BE_V0 | blocked_dominance_controls | 864 | 0.1897 | 0.1397 | 163.900775 | 120.700775 | 0.46412 | 0.557737 | {'BE_STOP': 132, 'LOCK_STOP': 188, 'NO_ENTRY': 3000, 'SAME_BAR': 1055, 'SETUP_NOT_REFINABLE': 2735, 'SL': 280, 'TIMEOUT': 261, 'TP': 5} |
| STRUCT_SWING_PROTECTED_V2 | all_enabled | 4530 | 0.238405 | 0.188405 | 1079.974166 | 853.474166 | 0.604194 | 0.493069 | {'LOCK_STOP': 1797, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1609, 'TIMEOUT': 1078, 'TP': 61} |
| STRUCT_SWING_PROTECTED_V2 | all_excluding_gbpusd_control | 3815 | 0.311569 | 0.261569 | 1188.636073 | 997.886073 | 0.635649 | 0.518673 | {'LOCK_STOP': 1574, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1256, 'TIMEOUT': 948, 'TP': 51} |
| STRUCT_SWING_PROTECTED_V2 | target_cohorts | 1421 | 0.450889 | 0.400889 | 640.713904 | 569.663904 | 0.729064 | 0.605762 | {'LOCK_STOP': 703, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 327, 'TIMEOUT': 379, 'TP': 14} |
| STRUCT_SWING_PROTECTED_V2 | primary_controlled_family | 686 | 0.41475 | 0.36475 | 284.518239 | 250.218239 | 0.753644 | 0.623907 | {'LOCK_STOP': 378, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 131, 'TIMEOUT': 177} |
| STRUCT_SWING_PROTECTED_V2 | cleared_non_primary_targets | 735 | 0.48462 | 0.43462 | 356.195665 | 319.445665 | 0.706122 | 0.588874 | {'LOCK_STOP': 325, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 196, 'TIMEOUT': 202, 'TP': 14} |
| STRUCT_SWING_PROTECTED_V2 | negative_controls | 1561 | -0.091779 | -0.141779 | -143.266811 | -221.316811 | 0.502242 | 0.388107 | {'LOCK_STOP': 492, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 697, 'TIMEOUT': 365, 'TP': 10} |
| STRUCT_SWING_PROTECTED_V2 | blocked_dominance_controls | 1548 | 0.376309 | 0.326309 | 582.527073 | 505.127073 | 0.592377 | 0.495507 | {'LOCK_STOP': 602, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 585, 'TIMEOUT': 334, 'TP': 37} |
| STRUCT_BOS_LEVEL_V2 | all_enabled | 4530 | 0.227057 | 0.177057 | 1028.570056 | 802.070056 | 0.525607 | 0.360616 | {'LOCK_STOP': 1448, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1863, 'TIMEOUT': 1167, 'TP': 67} |
| STRUCT_BOS_LEVEL_V2 | all_excluding_gbpusd_control | 3815 | 0.297422 | 0.247422 | 1134.664139 | 943.914139 | 0.552818 | 0.374771 | {'LOCK_STOP': 1281, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1480, 'TIMEOUT': 1001, 'TP': 67} |
| STRUCT_BOS_LEVEL_V2 | target_cohorts | 1421 | 0.463143 | 0.413143 | 658.126142 | 587.076142 | 0.634764 | 0.43078 | {'LOCK_STOP': 537, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 405, 'TIMEOUT': 458, 'TP': 23} |
| STRUCT_BOS_LEVEL_V2 | primary_controlled_family | 686 | 0.464857 | 0.414857 | 318.891994 | 284.591994 | 0.693878 | 0.465015 | {'LOCK_STOP': 295, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 155, 'TIMEOUT': 226, 'TP': 10} |
| STRUCT_BOS_LEVEL_V2 | cleared_non_primary_targets | 735 | 0.461543 | 0.411543 | 339.234148 | 302.484148 | 0.579592 | 0.398915 | {'LOCK_STOP': 242, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 250, 'TIMEOUT': 232, 'TP': 13} |
| STRUCT_BOS_LEVEL_V2 | negative_controls | 1561 | -0.099138 | -0.149138 | -154.75451 | -232.80451 | 0.445227 | 0.292199 | {'LOCK_STOP': 409, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 747, 'TIMEOUT': 408} |
| STRUCT_BOS_LEVEL_V2 | blocked_dominance_controls | 1548 | 0.339275 | 0.289275 | 525.198424 | 447.798424 | 0.50646 | 0.365212 | {'LOCK_STOP': 502, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 711, 'TIMEOUT': 301, 'TP': 44} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_enabled | 4530 | 0.168598 | 0.118598 | 763.74945 | 537.24945 | 0.601545 | 0.540374 | {'LOCK_STOP': 2257, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1594, 'TIMEOUT': 683, 'TP': 11} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | all_excluding_gbpusd_control | 3815 | 0.2243 | 0.1743 | 855.704585 | 664.954585 | 0.623591 | 0.556542 | {'LOCK_STOP': 1969, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1267, 'TIMEOUT': 582, 'TP': 11} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | target_cohorts | 1421 | 0.384762 | 0.334762 | 546.746867 | 475.696867 | 0.719916 | 0.642305 | {'LOCK_STOP': 834, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 326, 'TIMEOUT': 263} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | primary_controlled_family | 686 | 0.40005 | 0.35005 | 274.434416 | 240.134416 | 0.769679 | 0.655977 | {'LOCK_STOP': 407, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 119, 'TIMEOUT': 160} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | cleared_non_primary_targets | 735 | 0.370493 | 0.320493 | 272.312451 | 235.562451 | 0.673469 | 0.629579 | {'LOCK_STOP': 427, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 207, 'TIMEOUT': 103} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | negative_controls | 1561 | -0.066877 | -0.116877 | -104.394473 | -182.444473 | 0.530429 | 0.485934 | {'LOCK_STOP': 711, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 648, 'TIMEOUT': 205} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | blocked_dominance_controls | 1548 | 0.207621 | 0.157621 | 321.397056 | 243.997056 | 0.564599 | 0.501926 | {'LOCK_STOP': 712, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 620, 'TIMEOUT': 215, 'TP': 11} |
| STRUCT_FVG_MID_EDGE_V2 | all_enabled | 4530 | 0.236154 | 0.186154 | 1069.77945 | 843.27945 | 0.587417 | 0.535534 | {'LOCK_STOP': 2065, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1671, 'TIMEOUT': 758, 'TP': 51} |
| STRUCT_FVG_MID_EDGE_V2 | all_excluding_gbpusd_control | 3815 | 0.292988 | 0.242988 | 1117.75042 | 927.00042 | 0.606553 | 0.547401 | {'LOCK_STOP': 1807, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1335, 'TIMEOUT': 646, 'TP': 41} |
| STRUCT_FVG_MID_EDGE_V2 | target_cohorts | 1421 | 0.393099 | 0.343099 | 558.593086 | 487.543086 | 0.677692 | 0.609979 | {'LOCK_STOP': 751, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 372, 'TIMEOUT': 300} |
| STRUCT_FVG_MID_EDGE_V2 | primary_controlled_family | 686 | 0.417693 | 0.367693 | 286.537372 | 252.237372 | 0.709913 | 0.623907 | {'LOCK_STOP': 392, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 138, 'TIMEOUT': 156} |
| STRUCT_FVG_MID_EDGE_V2 | cleared_non_primary_targets | 735 | 0.370144 | 0.320144 | 272.055714 | 235.305714 | 0.647619 | 0.597015 | {'LOCK_STOP': 359, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 234, 'TIMEOUT': 144} |
| STRUCT_FVG_MID_EDGE_V2 | negative_controls | 1561 | -0.053685 | -0.103685 | -83.802282 | -161.852282 | 0.506726 | 0.464194 | {'LOCK_STOP': 604, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 690, 'TIMEOUT': 260, 'TP': 10} |
| STRUCT_FVG_MID_EDGE_V2 | blocked_dominance_controls | 1548 | 0.38436 | 0.33436 | 594.988646 | 517.588646 | 0.585917 | 0.539153 | {'LOCK_STOP': 710, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 609, 'TIMEOUT': 198, 'TP': 41} |
| STRUCT_OB_BOUNDARY_V2 | all_enabled | 4530 | 0.227765 | 0.177765 | 1031.777617 | 805.277617 | 0.507064 | 0.283608 | {'LOCK_STOP': 780, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1914, 'TIMEOUT': 1764, 'TP': 87} |
| STRUCT_OB_BOUNDARY_V2 | all_excluding_gbpusd_control | 3815 | 0.286667 | 0.236667 | 1093.636138 | 902.886138 | 0.531586 | 0.296161 | {'LOCK_STOP': 698, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1528, 'TIMEOUT': 1525, 'TP': 78} |
| STRUCT_OB_BOUNDARY_V2 | target_cohorts | 1421 | 0.50045 | 0.45045 | 711.139185 | 640.089185 | 0.613652 | 0.331694 | {'LOCK_STOP': 251, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 421, 'TIMEOUT': 717, 'TP': 34} |
| STRUCT_OB_BOUNDARY_V2 | primary_controlled_family | 686 | 0.477399 | 0.427399 | 327.495597 | 293.195597 | 0.658892 | 0.35277 | {'LOCK_STOP': 129, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 167, 'TIMEOUT': 380, 'TP': 10} |
| STRUCT_OB_BOUNDARY_V2 | cleared_non_primary_targets | 735 | 0.521964 | 0.471964 | 383.643588 | 346.893588 | 0.571429 | 0.312076 | {'LOCK_STOP': 122, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 254, 'TIMEOUT': 337, 'TP': 24} |
| STRUCT_OB_BOUNDARY_V2 | negative_controls | 1561 | -0.071437 | -0.121437 | -111.513063 | -189.563063 | 0.436259 | 0.216113 | {'LOCK_STOP': 197, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 754, 'TIMEOUT': 604, 'TP': 9} |
| STRUCT_OB_BOUNDARY_V2 | blocked_dominance_controls | 1548 | 0.279168 | 0.229168 | 432.151495 | 354.751495 | 0.48062 | 0.307445 | {'LOCK_STOP': 332, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 739, 'TIMEOUT': 443, 'TP': 44} |
| STRUCT_LIQUIDITY_RUN_V2 | all_enabled | 4530 | 0.214153 | 0.164153 | 970.11142 | 743.61142 | 0.530022 | 0.345215 | {'LOCK_STOP': 1418, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1857, 'TIMEOUT': 1218, 'TP': 52} |
| STRUCT_LIQUIDITY_RUN_V2 | all_excluding_gbpusd_control | 3815 | 0.268346 | 0.218346 | 1023.740014 | 832.990014 | 0.550983 | 0.353356 | {'LOCK_STOP': 1224, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1500, 'TIMEOUT': 1053, 'TP': 52} |
| STRUCT_LIQUIDITY_RUN_V2 | target_cohorts | 1421 | 0.456562 | 0.406562 | 648.774151 | 577.724151 | 0.66221 | 0.475755 | {'LOCK_STOP': 609, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 390, 'TIMEOUT': 404, 'TP': 20} |
| STRUCT_LIQUIDITY_RUN_V2 | primary_controlled_family | 686 | 0.481485 | 0.431485 | 330.298383 | 295.998383 | 0.698251 | 0.489796 | {'LOCK_STOP': 312, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 153, 'TIMEOUT': 211, 'TP': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | cleared_non_primary_targets | 735 | 0.4333 | 0.3833 | 318.475768 | 281.725768 | 0.628571 | 0.462687 | {'LOCK_STOP': 297, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 237, 'TIMEOUT': 193, 'TP': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | negative_controls | 1561 | -0.060809 | -0.110809 | -94.923563 | -172.973563 | 0.459962 | 0.308184 | {'LOCK_STOP': 441, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 721, 'TIMEOUT': 402} |
| STRUCT_LIQUIDITY_RUN_V2 | blocked_dominance_controls | 1548 | 0.268902 | 0.218902 | 416.260832 | 338.860832 | 0.479328 | 0.263158 | {'LOCK_STOP': 368, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 746, 'TIMEOUT': 412, 'TP': 32} |
| STRUCT_COMPOSITE_ANY_V2 | all_enabled | 4530 | 0.171828 | 0.121828 | 778.383086 | 551.883086 | 0.659823 | 0.653245 | {'LOCK_STOP': 2866, 'NO_DATA': 1, 'NO_ENTRY': 7742, 'SAME_BAR': 543, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1430, 'TIMEOUT': 243, 'TP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | all_excluding_gbpusd_control | 3815 | 0.23146 | 0.18146 | 883.021516 | 692.271516 | 0.686763 | 0.679028 | {'LOCK_STOP': 2503, 'NO_DATA': 1, 'NO_ENTRY': 6849, 'SAME_BAR': 519, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1116, 'TIMEOUT': 204, 'TP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | target_cohorts | 1421 | 0.370509 | 0.320509 | 526.493978 | 455.443978 | 0.776918 | 0.770907 | {'LOCK_STOP': 1054, 'NO_ENTRY': 2621, 'SAME_BAR': 97, 'SETUP_NOT_REFINABLE': 4081, 'SL': 279, 'TIMEOUT': 90} |
| STRUCT_COMPOSITE_ANY_V2 | primary_controlled_family | 686 | 0.351203 | 0.301203 | 240.925426 | 206.625426 | 0.801749 | 0.801749 | {'LOCK_STOP': 538, 'NO_ENTRY': 1095, 'SAME_BAR': 48, 'SETUP_NOT_REFINABLE': 2257, 'SL': 111, 'TIMEOUT': 37} |
| STRUCT_COMPOSITE_ANY_V2 | cleared_non_primary_targets | 735 | 0.388529 | 0.338529 | 285.568552 | 248.818552 | 0.753741 | 0.742198 | {'LOCK_STOP': 516, 'NO_ENTRY': 1526, 'SAME_BAR': 49, 'SETUP_NOT_REFINABLE': 1824, 'SL': 168, 'TIMEOUT': 53} |
| STRUCT_COMPOSITE_ANY_V2 | negative_controls | 1561 | -0.063361 | -0.113361 | -98.907023 | -176.957023 | 0.565663 | 0.56202 | {'LOCK_STOP': 863, 'NO_ENTRY': 2034, 'SAME_BAR': 171, 'SETUP_NOT_REFINABLE': 3836, 'SL': 624, 'TIMEOUT': 77} |
| STRUCT_COMPOSITE_ANY_V2 | blocked_dominance_controls | 1548 | 0.226612 | 0.176612 | 350.796131 | 273.396131 | 0.647287 | 0.637356 | {'LOCK_STOP': 949, 'NO_DATA': 1, 'NO_ENTRY': 3087, 'SAME_BAR': 275, 'SETUP_NOT_REFINABLE': 2735, 'SL': 527, 'TIMEOUT': 76, 'TP': 6} |

## Cohort Summary

| variant_id | cohort_key | role | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | same_bar | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 394 | 0.39032 | 0.340319 | 153.785883 | 134.085883 | 0.576142 | 0.0 | 87 | {'NO_ENTRY': 730, 'SAME_BAR': 87, 'SETUP_NOT_REFINABLE': 1530, 'SL': 158, 'TIMEOUT': 45, 'TP': 191} |
| BASE_RAW_FIXED_TP | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 670 | -0.151155 | -0.201155 | -101.273693 | -134.773693 | 0.340299 | 0.0 | 82 | {'NO_ENTRY': 880, 'SAME_BAR': 82, 'SETUP_NOT_REFINABLE': 252, 'SL': 414, 'TIMEOUT': 58, 'TP': 199} |
| BASE_RAW_FIXED_TP | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 575 | 0.330513 | 0.280513 | 190.045212 | 161.295212 | 0.546087 | 0.0 | 368 | {'NO_ENTRY': 1072, 'SAME_BAR': 368, 'SETUP_NOT_REFINABLE': 1425, 'SL': 258, 'TIMEOUT': 39, 'TP': 280} |
| BASE_RAW_FIXED_TP | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 179 | 0.266851 | 0.216851 | 47.766274 | 38.816274 | 0.49162 | 0.0 | 248 | {'NO_ENTRY': 778, 'SAME_BAR': 248, 'SETUP_NOT_REFINABLE': 110, 'SL': 88, 'TIMEOUT': 6, 'TP': 85} |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 139 | 0.582734 | 0.532734 | 81.0 | 74.05 | 0.633094 | 0.0 | 36 | {'NO_ENTRY': 324, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 619, 'SL': 51, 'TP': 88} |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bullish\|D1 | negative_control | 332 | 0.016208 | -0.033792 | 5.381197 | -11.218803 | 0.400602 | 0.0 | 101 | {'NO_ENTRY': 511, 'SAME_BAR': 101, 'SETUP_NOT_REFINABLE': 1635, 'SL': 193, 'TIMEOUT': 13, 'TP': 128} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 202 | 0.398515 | 0.348515 | 80.5 | 70.4 | 0.559406 | 0.0 | 51 | {'NO_ENTRY': 365, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 727, 'SL': 89, 'TP': 113} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 231 | 0.390185 | 0.340185 | 90.132697 | 78.582697 | 0.554113 | 0.0 | 36 | {'NO_ENTRY': 329, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 94, 'SL': 85, 'TIMEOUT': 32, 'TP': 114} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bullish\|D1 | negative_control | 424 | -0.119724 | -0.169724 | -50.76297 | -71.96297 | 0.384434 | 0.0 | 136 | {'NO_ENTRY': 630, 'SAME_BAR': 136, 'SETUP_NOT_REFINABLE': 1949, 'SL': 261, 'TIMEOUT': 33, 'TP': 130} |
| BASE_RAW_FIXED_TP | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 304 | 0.365595 | 0.315595 | 111.140891 | 95.940891 | 0.549342 | 0.0 | 50 | {'NO_ENTRY': 862, 'SAME_BAR': 50, 'SETUP_NOT_REFINABLE': 1111, 'SL': 131, 'TIMEOUT': 21, 'TP': 153} |
| BASE_RAW_FIXED_TP | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 448 | 0.440617 | 0.390617 | 197.396245 | 174.996245 | 0.595982 | 0.0 | 100 | {'NO_ENTRY': 1150, 'SAME_BAR': 100, 'SETUP_NOT_REFINABLE': 1200, 'SL': 160, 'TIMEOUT': 54, 'TP': 235} |
| J46_J49_ONLY | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.164197 | 0.114197 | 74.709562 | 51.959562 | 0.547253 | 0.035165 | 26 | {'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 137, 'TIMEOUT': 318} |
| J46_J49_ONLY | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.130781 | -0.180781 | -93.508221 | -129.258221 | 0.348252 | 0.047486 | 37 | {'BE_STOP': 7, 'NO_ENTRY': 880, 'SAME_BAR': 37, 'SETUP_NOT_REFINABLE': 252, 'SL': 381, 'TIMEOUT': 318, 'TP': 10} |
| J46_J49_ONLY | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 775 | 0.34423 | 0.29423 | 266.777931 | 228.027931 | 0.415484 | 0.159178 | 166 | {'BE_STOP': 16, 'NO_ENTRY': 1072, 'SAME_BAR': 166, 'SETUP_NOT_REFINABLE': 1425, 'SL': 391, 'TIMEOUT': 340, 'TP': 32} |
| J46_J49_ONLY | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 298 | 0.097095 | 0.047095 | 28.93442 | 14.03442 | 0.365772 | 0.191275 | 129 | {'BE_STOP': 1, 'NO_ENTRY': 778, 'SAME_BAR': 129, 'SETUP_NOT_REFINABLE': 110, 'SL': 183, 'TIMEOUT': 112, 'TP': 2} |
| J46_J49_ONLY | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 149 | 1.108757 | 1.058757 | 165.204719 | 157.754719 | 0.657718 | 0.214765 | 26 | {'NO_ENTRY': 324, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 101, 'TP': 10} |
| J46_J49_ONLY | USDJPY\|london\|bullish\|D1 | negative_control | 346 | 0.036215 | -0.013785 | 12.530235 | -4.769765 | 0.511561 | 0.020115 | 87 | {'NO_ENTRY': 511, 'SAME_BAR': 87, 'SETUP_NOT_REFINABLE': 1635, 'SL': 152, 'TIMEOUT': 196} |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 219 | 1.029884 | 0.979884 | 225.544494 | 214.594494 | 0.712329 | 0.242009 | 34 | {'NO_ENTRY': 365, 'SAME_BAR': 34, 'SETUP_NOT_REFINABLE': 727, 'SL': 49, 'TIMEOUT': 160, 'TP': 10} |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.036767 | -0.013233 | 9.449007 | -3.400993 | 0.36965 | 0.104651 | 9 | {'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 123, 'TIMEOUT': 135} |
| J46_J49_ONLY | USDJPY\|tokyo\|bullish\|D1 | negative_control | 457 | -0.156147 | -0.206147 | -71.359206 | -94.209206 | 0.431072 | 0.008753 | 103 | {'NO_ENTRY': 630, 'SAME_BAR': 103, 'SETUP_NOT_REFINABLE': 1949, 'SL': 207, 'TIMEOUT': 250} |
| J46_J49_ONLY | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 326 | 0.5241 | 0.4741 | 170.856467 | 154.556467 | 0.579755 | 0.11315 | 28 | {'NO_ENTRY': 862, 'SAME_BAR': 28, 'SETUP_NOT_REFINABLE': 1111, 'SL': 114, 'TIMEOUT': 199, 'TP': 14} |
| J46_J49_ONLY | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 480 | 0.350963 | 0.300963 | 168.462247 | 144.462247 | 0.514583 | 0.106029 | 68 | {'BE_STOP': 4, 'NO_ENTRY': 1150, 'SAME_BAR': 68, 'SETUP_NOT_REFINABLE': 1200, 'SL': 178, 'TIMEOUT': 290, 'TP': 9} |
| PATH_LOCK_CONSERVATIVE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 394 | 0.274052 | 0.224052 | 107.976353 | 88.276353 | 0.568528 | 0.251269 | 87 | {'BE_STOP': 13, 'LOCK_STOP': 12, 'NO_ENTRY': 730, 'SAME_BAR': 87, 'SETUP_NOT_REFINABLE': 1530, 'SL': 90, 'TIMEOUT': 279} |
| PATH_LOCK_CONSERVATIVE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 670 | -0.13533 | -0.18533 | -90.670857 | -124.170857 | 0.340299 | 0.198212 | 82 | {'BE_STOP': 5, 'LOCK_STOP': 27, 'NO_ENTRY': 880, 'SAME_BAR': 82, 'SETUP_NOT_REFINABLE': 252, 'SL': 362, 'TIMEOUT': 267, 'TP': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 571 | 0.076533 | 0.026533 | 43.700229 | 15.150229 | 0.394046 | 0.418848 | 372 | {'BE_STOP': 70, 'LOCK_STOP': 54, 'NO_ENTRY': 1072, 'SAME_BAR': 372, 'SETUP_NOT_REFINABLE': 1425, 'SL': 247, 'TIMEOUT': 196, 'TP': 6} |
| PATH_LOCK_CONSERVATIVE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 169 | 0.083788 | 0.033788 | 14.160141 | 5.710141 | 0.455621 | 0.47929 | 258 | {'BE_STOP': 6, 'LOCK_STOP': 17, 'NO_ENTRY': 778, 'SAME_BAR': 258, 'SETUP_NOT_REFINABLE': 110, 'SL': 84, 'TIMEOUT': 60, 'TP': 2} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 139 | 0.745596 | 0.695596 | 103.637904 | 96.687904 | 0.561151 | 0.582734 | 36 | {'BE_STOP': 20, 'LOCK_STOP': 21, 'NO_ENTRY': 324, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 619, 'SL': 28, 'TIMEOUT': 70} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 332 | -0.005567 | -0.055567 | -1.848323 | -18.448323 | 0.490964 | 0.269461 | 101 | {'BE_STOP': 9, 'LOCK_STOP': 3, 'NO_ENTRY': 511, 'SAME_BAR': 101, 'SETUP_NOT_REFINABLE': 1635, 'SL': 143, 'TIMEOUT': 179} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 202 | 0.862474 | 0.812474 | 174.219723 | 164.119723 | 0.653465 | 0.440594 | 51 | {'BE_STOP': 13, 'LOCK_STOP': 5, 'NO_ENTRY': 365, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 727, 'SL': 43, 'TIMEOUT': 134, 'TP': 7} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 231 | 0.323121 | 0.273121 | 74.641011 | 63.091011 | 0.0 | 0.38961 | 36 | {'BE_STOP': 41, 'LOCK_STOP': 12, 'NO_ENTRY': 329, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 94, 'SL': 53, 'TIMEOUT': 125} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 424 | -0.185002 | -0.235002 | -78.440918 | -99.640918 | 0.410377 | 0.162736 | 136 | {'BE_STOP': 12, 'LOCK_STOP': 7, 'NO_ENTRY': 630, 'SAME_BAR': 136, 'SETUP_NOT_REFINABLE': 1949, 'SL': 191, 'TIMEOUT': 214} |
| PATH_LOCK_CONSERVATIVE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 304 | 0.669715 | 0.619715 | 203.59342 | 188.39342 | 0.671053 | 0.377049 | 50 | {'LOCK_STOP': 25, 'NO_ENTRY': 862, 'SAME_BAR': 50, 'SETUP_NOT_REFINABLE': 1111, 'SL': 82, 'TIMEOUT': 184, 'TP': 14} |
| PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 448 | 0.40304 | 0.35304 | 180.561854 | 158.161854 | 0.551339 | 0.342984 | 100 | {'BE_STOP': 27, 'LOCK_STOP': 40, 'NO_ENTRY': 1150, 'SAME_BAR': 100, 'SETUP_NOT_REFINABLE': 1200, 'SL': 123, 'TIMEOUT': 257, 'TP': 2} |
| PATH_LOCK_HALF_GAIN_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 394 | 0.308233 | 0.258233 | 121.443879 | 101.743879 | 0.601523 | 0.251269 | 87 | {'LOCK_STOP': 37, 'NO_ENTRY': 730, 'SAME_BAR': 87, 'SETUP_NOT_REFINABLE': 1530, 'SL': 90, 'TIMEOUT': 267} |
| PATH_LOCK_HALF_GAIN_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 670 | -0.105693 | -0.155693 | -70.814561 | -104.314561 | 0.347761 | 0.198212 | 82 | {'LOCK_STOP': 53, 'NO_ENTRY': 880, 'SAME_BAR': 82, 'SETUP_NOT_REFINABLE': 252, 'SL': 362, 'TIMEOUT': 246, 'TP': 10} |
| PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 571 | 0.109613 | 0.059613 | 62.588978 | 34.038978 | 0.516637 | 0.418848 | 372 | {'LOCK_STOP': 165, 'NO_ENTRY': 1072, 'SAME_BAR': 372, 'SETUP_NOT_REFINABLE': 1425, 'SL': 247, 'TIMEOUT': 156, 'TP': 5} |
| PATH_LOCK_HALF_GAIN_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 169 | 0.119986 | 0.069986 | 20.277672 | 11.827672 | 0.491124 | 0.47929 | 258 | {'LOCK_STOP': 57, 'NO_ENTRY': 778, 'SAME_BAR': 258, 'SETUP_NOT_REFINABLE': 110, 'SL': 84, 'TIMEOUT': 26, 'TP': 2} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 139 | 0.641204 | 0.591204 | 89.127341 | 82.177341 | 0.705036 | 0.582734 | 36 | {'LOCK_STOP': 52, 'NO_ENTRY': 324, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 619, 'SL': 28, 'TIMEOUT': 59} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 332 | -0.005241 | -0.055241 | -1.740112 | -18.340112 | 0.518072 | 0.269461 | 101 | {'LOCK_STOP': 45, 'NO_ENTRY': 511, 'SAME_BAR': 101, 'SETUP_NOT_REFINABLE': 1635, 'SL': 143, 'TIMEOUT': 146} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 202 | 0.516471 | 0.466471 | 104.327175 | 94.227175 | 0.717822 | 0.440594 | 51 | {'LOCK_STOP': 55, 'NO_ENTRY': 365, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 727, 'SL': 43, 'TIMEOUT': 104} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 231 | 0.43174 | 0.38174 | 99.731964 | 88.181964 | 0.601732 | 0.38961 | 36 | {'LOCK_STOP': 55, 'NO_ENTRY': 329, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 94, 'SL': 53, 'TIMEOUT': 123} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 424 | -0.213731 | -0.263731 | -90.621924 | -111.821924 | 0.438679 | 0.162736 | 136 | {'LOCK_STOP': 49, 'NO_ENTRY': 630, 'SAME_BAR': 136, 'SETUP_NOT_REFINABLE': 1949, 'SL': 191, 'TIMEOUT': 184} |
| PATH_LOCK_HALF_GAIN_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 304 | 0.679033 | 0.629033 | 206.426146 | 191.226146 | 0.671053 | 0.377049 | 50 | {'LOCK_STOP': 46, 'NO_ENTRY': 862, 'SAME_BAR': 50, 'SETUP_NOT_REFINABLE': 1111, 'SL': 82, 'TIMEOUT': 163, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 448 | 0.453779 | 0.403779 | 203.292949 | 180.892949 | 0.611607 | 0.342984 | 100 | {'LOCK_STOP': 78, 'NO_ENTRY': 1150, 'SAME_BAR': 100, 'SETUP_NOT_REFINABLE': 1200, 'SL': 123, 'TIMEOUT': 248} |
| PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 347 | 0.203132 | 0.153132 | 70.486825 | 53.136825 | 0.533141 | 0.533141 | 134 | {'BE_STOP': 62, 'LOCK_STOP': 24, 'NO_ENTRY': 730, 'SAME_BAR': 134, 'SETUP_NOT_REFINABLE': 1530, 'SL': 49, 'TIMEOUT': 212} |
| PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 579 | -0.290967 | -0.340967 | -168.469721 | -197.419721 | 0.295337 | 0.258621 | 173 | {'BE_STOP': 28, 'LOCK_STOP': 30, 'NO_ENTRY': 880, 'SAME_BAR': 173, 'SETUP_NOT_REFINABLE': 252, 'SL': 326, 'TIMEOUT': 196} |
| PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 423 | 0.014595 | -0.035405 | 6.173756 | -14.976244 | 0.390071 | 0.531765 | 520 | {'BE_STOP': 76, 'LOCK_STOP': 90, 'NO_ENTRY': 1072, 'SAME_BAR': 520, 'SETUP_NOT_REFINABLE': 1425, 'SL': 155, 'TIMEOUT': 99, 'TP': 5} |
| PATH_LOCK_EARLY_BE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 133 | 0.118855 | 0.068855 | 15.807684 | 9.157684 | 0.43609 | 0.609023 | 294 | {'BE_STOP': 25, 'LOCK_STOP': 43, 'NO_ENTRY': 778, 'SAME_BAR': 294, 'SETUP_NOT_REFINABLE': 110, 'SL': 48, 'TIMEOUT': 17} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 124 | 0.66635 | 0.61635 | 82.627341 | 76.427341 | 0.701613 | 0.717742 | 51 | {'BE_STOP': 6, 'LOCK_STOP': 41, 'NO_ENTRY': 324, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 619, 'SL': 18, 'TIMEOUT': 59} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 280 | -0.013847 | -0.063847 | -3.877234 | -17.877234 | 0.45 | 0.427046 | 154 | {'BE_STOP': 32, 'LOCK_STOP': 34, 'NO_ENTRY': 511, 'SAME_BAR': 154, 'SETUP_NOT_REFINABLE': 1635, 'SL': 105, 'TIMEOUT': 110} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 0.502995 | 0.452995 | 95.568981 | 86.068981 | 0.705263 | 0.563158 | 63 | {'BE_STOP': 7, 'LOCK_STOP': 46, 'NO_ENTRY': 365, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 727, 'SL': 36, 'TIMEOUT': 101} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 174 | 0.460609 | 0.410609 | 80.145967 | 71.445967 | 0.568966 | 0.5 | 93 | {'BE_STOP': 13, 'LOCK_STOP': 19, 'NO_ENTRY': 329, 'SAME_BAR': 93, 'SETUP_NOT_REFINABLE': 94, 'SL': 39, 'TIMEOUT': 103} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 370 | -0.152539 | -0.202539 | -56.439319 | -74.939319 | 0.448649 | 0.345946 | 190 | {'BE_STOP': 20, 'LOCK_STOP': 44, 'NO_ENTRY': 630, 'SAME_BAR': 190, 'SETUP_NOT_REFINABLE': 1949, 'SL': 144, 'TIMEOUT': 162} |
| PATH_LOCK_EARLY_BE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 278 | 0.728626 | 0.678626 | 202.558044 | 188.658044 | 0.640288 | 0.630824 | 76 | {'BE_STOP': 22, 'LOCK_STOP': 44, 'NO_ENTRY': 862, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1111, 'SL': 60, 'TIMEOUT': 139, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 308 | 0.460777 | 0.410777 | 141.919335 | 126.519335 | 0.577922 | 0.571429 | 241 | {'BE_STOP': 31, 'LOCK_STOP': 55, 'NO_ENTRY': 1150, 'SAME_BAR': 241, 'SETUP_NOT_REFINABLE': 1200, 'SL': 77, 'TIMEOUT': 145} |
| STRUCT_SWING_PROTECTED_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.304824 | 0.254824 | 138.694979 | 115.944979 | 0.762637 | 0.683516 | 26 | {'LOCK_STOP': 285, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 82, 'TIMEOUT': 88} |
| STRUCT_SWING_PROTECTED_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.151975 | -0.201975 | -108.661907 | -144.411907 | 0.436364 | 0.356145 | 24 | {'LOCK_STOP': 223, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 353, 'TIMEOUT': 130, 'TP': 10} |
| STRUCT_SWING_PROTECTED_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.430679 | 0.380679 | 327.746649 | 289.696649 | 0.538765 | 0.425228 | 133 | {'LOCK_STOP': 228, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 325, 'TIMEOUT': 183, 'TP': 33} |
| STRUCT_SWING_PROTECTED_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.149285 | 0.099285 | 46.427682 | 30.877682 | 0.495177 | 0.444089 | 83 | {'LOCK_STOP': 101, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 157, 'TIMEOUT': 53, 'TP': 2} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.688236 | 0.638236 | 109.429585 | 101.479585 | 0.811321 | 0.63522 | 16 | {'LOCK_STOP': 77, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 27, 'TIMEOUT': 55} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | 0.01811 | -0.03189 | 6.555982 | -11.544018 | 0.596685 | 0.447802 | 71 | {'LOCK_STOP': 121, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 142, 'TIMEOUT': 101} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.63127 | 0.58127 | 145.82326 | 134.27326 | 0.735931 | 0.506494 | 22 | {'LOCK_STOP': 93, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 49, 'TIMEOUT': 89} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.257092 | 0.207092 | 66.072692 | 53.222692 | 0.657588 | 0.523256 | 9 | {'LOCK_STOP': 98, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 80, 'TIMEOUT': 80} |
| STRUCT_SWING_PROTECTED_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.085043 | -0.135043 | -41.160886 | -65.360886 | 0.528926 | 0.390496 | 76 | {'LOCK_STOP': 148, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 202, 'TIMEOUT': 134} |
| STRUCT_SWING_PROTECTED_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.566437 | 0.516437 | 180.693388 | 164.743388 | 0.69279 | 0.61875 | 24 | {'LOCK_STOP': 150, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 89, 'TIMEOUT': 67, 'TP': 14} |
| STRUCT_SWING_PROTECTED_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.437716 | 0.387716 | 208.352742 | 184.552742 | 0.741597 | 0.642857 | 59 | {'LOCK_STOP': 273, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 103, 'TIMEOUT': 98, 'TP': 2} |
| STRUCT_BOS_LEVEL_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.306874 | 0.256874 | 139.627595 | 116.877595 | 0.701099 | 0.483516 | 26 | {'LOCK_STOP': 198, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 94, 'TIMEOUT': 163} |
| STRUCT_BOS_LEVEL_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.148383 | -0.198383 | -106.094083 | -141.844083 | 0.38042 | 0.284916 | 24 | {'LOCK_STOP': 167, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 383, 'TIMEOUT': 166} |
| STRUCT_BOS_LEVEL_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.342059 | 0.292059 | 260.306765 | 222.256765 | 0.479632 | 0.327698 | 133 | {'LOCK_STOP': 217, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 372, 'TIMEOUT': 147, 'TP': 33} |
| STRUCT_BOS_LEVEL_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.08404 | 0.03404 | 26.136523 | 10.586523 | 0.389068 | 0.217252 | 83 | {'LOCK_STOP': 68, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 190, 'TIMEOUT': 53, 'TP': 2} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.867547 | 0.817547 | 137.93994 | 129.98994 | 0.710692 | 0.471698 | 16 | {'LOCK_STOP': 71, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 40, 'TP': 10} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | 0.002933 | -0.047067 | 1.061799 | -17.038201 | 0.533149 | 0.32967 | 71 | {'LOCK_STOP': 109, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 152, 'TIMEOUT': 103} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.776036 | 0.726036 | 179.264399 | 167.714399 | 0.679654 | 0.428571 | 22 | {'LOCK_STOP': 97, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 61, 'TIMEOUT': 63, 'TP': 10} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | -0.030487 | -0.080487 | -7.83527 | -20.68527 | 0.396887 | 0.25969 | 9 | {'LOCK_STOP': 35, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 123, 'TIMEOUT': 100} |
| STRUCT_BOS_LEVEL_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.102732 | -0.152732 | -49.722226 | -73.922226 | 0.475207 | 0.274793 | 76 | {'LOCK_STOP': 133, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 212, 'TIMEOUT': 139} |
| STRUCT_BOS_LEVEL_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.655578 | 0.605578 | 209.129478 | 193.179478 | 0.661442 | 0.475 | 24 | {'LOCK_STOP': 136, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 89, 'TIMEOUT': 92, 'TP': 3} |
| STRUCT_BOS_LEVEL_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.501586 | 0.451586 | 238.755136 | 214.955136 | 0.62605 | 0.523109 | 59 | {'LOCK_STOP': 217, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 149, 'TIMEOUT': 101, 'TP': 9} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.333278 | 0.283278 | 151.641569 | 128.891569 | 0.769231 | 0.659341 | 26 | {'LOCK_STOP': 274, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 66, 'TIMEOUT': 115} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.128609 | -0.178609 | -91.955135 | -127.705135 | 0.483916 | 0.453911 | 24 | {'LOCK_STOP': 288, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 327, 'TIMEOUT': 101} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.158822 | 0.108822 | 120.863791 | 82.813791 | 0.541393 | 0.460338 | 133 | {'LOCK_STOP': 326, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 330, 'TIMEOUT': 105, 'TP': 8} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.247314 | 0.197314 | 76.914632 | 61.364632 | 0.482315 | 0.43131 | 83 | {'LOCK_STOP': 124, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 159, 'TIMEOUT': 28, 'TP': 2} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.401675 | 0.351675 | 63.866264 | 55.916264 | 0.716981 | 0.704403 | 16 | {'LOCK_STOP': 102, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 19} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | -0.014848 | -0.064848 | -5.374852 | -23.474852 | 0.577348 | 0.527473 | 71 | {'LOCK_STOP': 180, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 138, 'TIMEOUT': 46} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.531571 | 0.481571 | 122.792847 | 111.242847 | 0.770563 | 0.649351 | 22 | {'LOCK_STOP': 133, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 53, 'TIMEOUT': 45} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.151628 | 0.101628 | 38.968298 | 26.118298 | 0.571984 | 0.5 | 9 | {'LOCK_STOP': 118, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 93, 'TIMEOUT': 47} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.014596 | -0.064596 | -7.064486 | -31.264486 | 0.56405 | 0.502066 | 76 | {'LOCK_STOP': 243, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 183, 'TIMEOUT': 58} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.531279 | 0.481279 | 169.477889 | 153.527889 | 0.733542 | 0.696875 | 24 | {'LOCK_STOP': 207, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 76, 'TIMEOUT': 37} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.259703 | 0.209703 | 123.618633 | 99.818633 | 0.655462 | 0.615546 | 59 | {'LOCK_STOP': 262, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 131, 'TIMEOUT': 82, 'TP': 1} |
| STRUCT_FVG_MID_EDGE_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.37249 | 0.32249 | 169.482726 | 146.732726 | 0.712088 | 0.615385 | 26 | {'LOCK_STOP': 267, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 82, 'TIMEOUT': 106} |
| STRUCT_FVG_MID_EDGE_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.067092 | -0.117092 | -47.97097 | -83.72097 | 0.485315 | 0.472067 | 24 | {'LOCK_STOP': 258, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 336, 'TIMEOUT': 112, 'TP': 10} |
| STRUCT_FVG_MID_EDGE_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.415445 | 0.365445 | 316.153931 | 278.103931 | 0.542707 | 0.486346 | 133 | {'LOCK_STOP': 300, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 330, 'TIMEOUT': 106, 'TP': 33} |
| STRUCT_FVG_MID_EDGE_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.19281 | 0.14281 | 59.963781 | 44.413781 | 0.472669 | 0.399361 | 83 | {'LOCK_STOP': 117, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 164, 'TIMEOUT': 30, 'TP': 2} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.46156 | 0.41156 | 73.388102 | 65.438102 | 0.710692 | 0.603774 | 16 | {'LOCK_STOP': 76, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 45} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | -0.017377 | -0.067377 | -6.290458 | -24.390458 | 0.533149 | 0.464286 | 71 | {'LOCK_STOP': 139, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 156, 'TIMEOUT': 69} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.50673 | 0.45673 | 117.054646 | 105.504646 | 0.705628 | 0.640693 | 22 | {'LOCK_STOP': 125, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 56, 'TIMEOUT': 50} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.101448 | 0.051448 | 26.07225 | 13.22225 | 0.536965 | 0.468992 | 9 | {'LOCK_STOP': 88, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 111, 'TIMEOUT': 59} |
| STRUCT_FVG_MID_EDGE_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.061035 | -0.111035 | -29.540854 | -53.740854 | 0.518595 | 0.452479 | 76 | {'LOCK_STOP': 207, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 198, 'TIMEOUT': 79} |
| STRUCT_FVG_MID_EDGE_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.541051 | 0.491051 | 172.595362 | 156.645362 | 0.705329 | 0.696875 | 24 | {'LOCK_STOP': 195, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 85, 'TIMEOUT': 40} |
| STRUCT_FVG_MID_EDGE_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.459813 | 0.409813 | 218.870934 | 195.070934 | 0.728992 | 0.716387 | 59 | {'LOCK_STOP': 293, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 115, 'TIMEOUT': 62, 'TP': 6} |
| STRUCT_OB_BOUNDARY_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.27889 | 0.22889 | 126.89503 | 104.14503 | 0.648352 | 0.378022 | 26 | {'LOCK_STOP': 93, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 106, 'TIMEOUT': 256} |
| STRUCT_OB_BOUNDARY_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.086515 | -0.136515 | -61.858521 | -97.608521 | 0.376224 | 0.21648 | 24 | {'LOCK_STOP': 82, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 386, 'TIMEOUT': 239, 'TP': 9} |
| STRUCT_OB_BOUNDARY_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.286388 | 0.236388 | 217.941385 | 179.891385 | 0.452037 | 0.273082 | 133 | {'LOCK_STOP': 118, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 391, 'TIMEOUT': 227, 'TP': 33} |
| STRUCT_OB_BOUNDARY_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | -0.011466 | -0.061466 | -3.565884 | -19.115884 | 0.382637 | 0.204473 | 83 | {'LOCK_STOP': 60, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 190, 'TIMEOUT': 61, 'TP': 2} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 1.078068 | 1.028068 | 171.412851 | 163.462851 | 0.710692 | 0.389937 | 16 | {'LOCK_STOP': 32, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 79, 'TP': 10} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | -0.008325 | -0.058325 | -3.013808 | -21.113808 | 0.522099 | 0.222527 | 71 | {'LOCK_STOP': 56, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 156, 'TIMEOUT': 152} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.868401 | 0.818401 | 200.600567 | 189.050567 | 0.679654 | 0.30303 | 22 | {'LOCK_STOP': 36, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 61, 'TIMEOUT': 124, 'TP': 10} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.017222 | -0.032778 | 4.426174 | -8.423826 | 0.396887 | 0.155039 | 9 | {'LOCK_STOP': 19, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 123, 'TIMEOUT': 116} |
| STRUCT_OB_BOUNDARY_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.096365 | -0.146365 | -46.640734 | -70.840734 | 0.460744 | 0.210744 | 76 | {'LOCK_STOP': 59, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 212, 'TIMEOUT': 213} |
| STRUCT_OB_BOUNDARY_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.651425 | 0.601425 | 207.804563 | 191.854563 | 0.642633 | 0.4 | 24 | {'LOCK_STOP': 71, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 93, 'TIMEOUT': 142, 'TP': 14} |
| STRUCT_OB_BOUNDARY_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.457513 | 0.407513 | 217.775994 | 193.975994 | 0.590336 | 0.430672 | 59 | {'LOCK_STOP': 154, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 158, 'TIMEOUT': 155, 'TP': 9} |
| STRUCT_LIQUIDITY_RUN_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.367371 | 0.317371 | 167.153968 | 144.403968 | 0.701099 | 0.527473 | 26 | {'LOCK_STOP': 216, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 94, 'TIMEOUT': 145} |
| STRUCT_LIQUIDITY_RUN_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.075005 | -0.125005 | -53.628594 | -89.378594 | 0.418182 | 0.301676 | 24 | {'LOCK_STOP': 194, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 357, 'TIMEOUT': 165} |
| STRUCT_LIQUIDITY_RUN_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.20975 | 0.15975 | 159.619394 | 121.569394 | 0.450723 | 0.209363 | 133 | {'LOCK_STOP': 153, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 392, 'TIMEOUT': 198, 'TP': 26} |
| STRUCT_LIQUIDITY_RUN_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.059713 | 0.009713 | 18.570732 | 3.020732 | 0.385852 | 0.246006 | 83 | {'LOCK_STOP': 75, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 186, 'TIMEOUT': 52} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.850926 | 0.800926 | 135.297229 | 127.347229 | 0.710692 | 0.433962 | 16 | {'LOCK_STOP': 68, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 43, 'TP': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | 0.008531 | -0.041469 | 3.088109 | -15.011891 | 0.522099 | 0.335165 | 71 | {'LOCK_STOP': 112, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 156, 'TIMEOUT': 96} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.706253 | 0.656253 | 163.144415 | 151.594415 | 0.692641 | 0.415584 | 22 | {'LOCK_STOP': 96, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 59, 'TIMEOUT': 66, 'TP': 10} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.042775 | -0.007225 | 10.993203 | -1.856797 | 0.494163 | 0.348837 | 9 | {'LOCK_STOP': 83, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 110, 'TIMEOUT': 65} |
| STRUCT_LIQUIDITY_RUN_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.091701 | -0.141701 | -44.383078 | -68.583078 | 0.475207 | 0.297521 | 76 | {'LOCK_STOP': 135, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 208, 'TIMEOUT': 141} |
| STRUCT_LIQUIDITY_RUN_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.539766 | 0.489766 | 172.185336 | 156.235336 | 0.695925 | 0.56875 | 24 | {'LOCK_STOP': 146, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 89, 'TIMEOUT': 85} |
| STRUCT_LIQUIDITY_RUN_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.500149 | 0.450149 | 238.070706 | 214.270706 | 0.586134 | 0.361345 | 59 | {'LOCK_STOP': 140, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 168, 'TIMEOUT': 162, 'TP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 455 | 0.264581 | 0.214581 | 120.384315 | 97.634315 | 0.8 | 0.8 | 26 | {'LOCK_STOP': 352, 'NO_ENTRY': 730, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 1530, 'SL': 66, 'TIMEOUT': 37} |
| STRUCT_COMPOSITE_ANY_V2 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 715 | -0.146347 | -0.196347 | -104.63843 | -140.38843 | 0.516084 | 0.515363 | 24 | {'LOCK_STOP': 363, 'NO_ENTRY': 893, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 252, 'SL': 314, 'TIMEOUT': 39} |
| STRUCT_COMPOSITE_ANY_V2 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 761 | 0.219039 | 0.169039 | 166.688334 | 128.638334 | 0.600526 | 0.587776 | 133 | {'LOCK_STOP': 423, 'NO_ENTRY': 1115, 'SAME_BAR': 133, 'SETUP_NOT_REFINABLE': 1425, 'SL': 287, 'TIMEOUT': 53, 'TP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 311 | 0.183328 | 0.133328 | 57.014854 | 41.464854 | 0.546624 | 0.530351 | 83 | {'LOCK_STOP': 155, 'NO_DATA': 1, 'NO_ENTRY': 808, 'SAME_BAR': 83, 'SETUP_NOT_REFINABLE': 110, 'SL': 141, 'TIMEOUT': 17} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 159 | 0.472132 | 0.422132 | 75.068936 | 67.118936 | 0.81761 | 0.81761 | 16 | {'LOCK_STOP': 128, 'NO_ENTRY': 324, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 619, 'SL': 27, 'TIMEOUT': 4} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|london\|bullish\|D1 | negative_control | 362 | 0.025856 | -0.024144 | 9.359851 | -8.740149 | 0.632597 | 0.626374 | 71 | {'LOCK_STOP': 218, 'NO_ENTRY': 511, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 1635, 'SL': 130, 'TIMEOUT': 16} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 231 | 0.521823 | 0.471823 | 120.541111 | 108.991111 | 0.805195 | 0.805195 | 22 | {'LOCK_STOP': 186, 'NO_ENTRY': 365, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 727, 'SL': 45} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 257 | 0.205474 | 0.155474 | 52.806838 | 39.956838 | 0.719844 | 0.693798 | 9 | {'LOCK_STOP': 161, 'NO_ENTRY': 329, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 94, 'SL': 67, 'TIMEOUT': 30} |
| STRUCT_COMPOSITE_ANY_V2 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 484 | -0.007497 | -0.057497 | -3.628444 | -27.828444 | 0.588843 | 0.582645 | 76 | {'LOCK_STOP': 282, 'NO_ENTRY': 630, 'SAME_BAR': 76, 'SETUP_NOT_REFINABLE': 1949, 'SL': 180, 'TIMEOUT': 22} |
| STRUCT_COMPOSITE_ANY_V2 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 319 | 0.494335 | 0.444335 | 157.692778 | 141.742778 | 0.749216 | 0.74375 | 24 | {'LOCK_STOP': 227, 'NO_ENTRY': 873, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 1111, 'SL': 74, 'TIMEOUT': 19} |
| STRUCT_COMPOSITE_ANY_V2 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 476 | 0.267002 | 0.217002 | 127.092943 | 103.292943 | 0.787815 | 0.787815 | 59 | {'LOCK_STOP': 371, 'NO_ENTRY': 1164, 'SAME_BAR': 59, 'SETUP_NOT_REFINABLE': 1200, 'SL': 99, 'TIMEOUT': 6} |

## Selector Fire Summary

| variant_id | selector_id | family | selected_timeframe | side | symbol | session | role | fires | resolved_n | gross_mean_r | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | NAS100 | ny | dominance_watchlist | 457 | 457 | 1.649492 | {'LOCK_STOP': 297, 'TIMEOUT': 112, 'TP': 48} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | NAS100 | ny | dominance_watchlist | 428 | 428 | 1.381791 | {'LOCK_STOP': 389, 'TP': 39} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | XAUUSD | ny | dominance_watchlist | 413 | 413 | 1.154289 | {'LOCK_STOP': 311, 'TIMEOUT': 90, 'TP': 12} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | NAS100 | ny | dominance_watchlist | 345 | 345 | 1.025451 | {'LOCK_STOP': 333, 'TIMEOUT': 9, 'TP': 3} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | XAUUSD | ny | dominance_watchlist | 298 | 298 | 0.948179 | {'LOCK_STOP': 247, 'TIMEOUT': 51} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | GBPUSD | london | negative_control | 295 | 295 | 1.380914 | {'LOCK_STOP': 169, 'TIMEOUT': 106, 'TP': 20} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | GBPUSD | london | negative_control | 292 | 292 | 1.136024 | {'LOCK_STOP': 253, 'TIMEOUT': 39} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | XAUUSD | ny | dominance_watchlist | 266 | 266 | 0.826378 | {'LOCK_STOP': 206, 'TIMEOUT': 59, 'TP': 1} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | NAS100 | ny | dominance_watchlist | 260 | 260 | 1.812088 | {'LOCK_STOP': 189, 'TIMEOUT': 40, 'TP': 31} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | NAS100 | ny | dominance_watchlist | 254 | 254 | 1.934631 | {'LOCK_STOP': 217, 'TP': 37} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 228 | 228 | 0.97971 | {'LOCK_STOP': 228} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 228 | 228 | 1.637177 | {'LOCK_STOP': 228} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | XAUUSD | ny | dominance_watchlist | 227 | 227 | 1.487471 | {'LOCK_STOP': 166, 'TIMEOUT': 52, 'TP': 9} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | NAS100 | ny | dominance_watchlist | 208 | 208 | 0.855651 | {'LOCK_STOP': 208} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 206 | 206 | 1.454131 | {'LOCK_STOP': 145, 'TIMEOUT': 61} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | USDJPY | tokyo | negative_control | 186 | 186 | 1.223743 | {'LOCK_STOP': 186} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 185 | 185 | 2.355279 | {'LOCK_STOP': 131, 'TIMEOUT': 1, 'TP': 53} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | USDJPY | tokyo | negative_control | 182 | 182 | 0.884666 | {'LOCK_STOP': 182} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 182 | 182 | 1.465217 | {'LOCK_STOP': 182} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 178 | 178 | 2.988871 | {'LOCK_STOP': 144, 'TIMEOUT': 19, 'TP': 15} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 178 | 178 | 0.684449 | {'LOCK_STOP': 178} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | XAUUSD | ny | dominance_watchlist | 175 | 175 | 1.474236 | {'LOCK_STOP': 149, 'TIMEOUT': 9, 'TP': 17} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 174 | 174 | 1.599837 | {'LOCK_STOP': 174} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | NAS100 | ny | dominance_watchlist | 169 | 169 | 2.616329 | {'LOCK_STOP': 97, 'TIMEOUT': 72} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 164 | 164 | 1.37317 | {'LOCK_STOP': 147, 'TIMEOUT': 17} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | US30_cash | ny | dominance_watchlist | 164 | 164 | 2.144012 | {'LOCK_STOP': 164} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | USDJPY | tokyo | negative_control | 163 | 163 | 1.085913 | {'LOCK_STOP': 151, 'TIMEOUT': 12} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | GBPUSD | london | negative_control | 162 | 162 | 1.369651 | {'LOCK_STOP': 121, 'TIMEOUT': 21, 'TP': 20} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 155 | 155 | 0.748262 | {'LOCK_STOP': 152, 'TIMEOUT': 3} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 154 | 154 | 0.929075 | {'LOCK_STOP': 149, 'TIMEOUT': 5} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | US30_cash | ny | dominance_watchlist | 149 | 149 | 1.969643 | {'LOCK_STOP': 149} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 149 | 149 | 1.066987 | {'LOCK_STOP': 137, 'TIMEOUT': 12} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 148 | 148 | 2.317553 | {'LOCK_STOP': 72, 'TIMEOUT': 76} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 145 | 145 | 0.943764 | {'LOCK_STOP': 112, 'TIMEOUT': 33} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 144 | 144 | 0.640476 | {'LOCK_STOP': 144} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | USDJPY | london | negative_control | 142 | 142 | 1.029171 | {'LOCK_STOP': 89, 'TIMEOUT': 53} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 140 | 140 | 2.242805 | {'LOCK_STOP': 81, 'TIMEOUT': 59} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 138 | 138 | 1.857686 | {'LOCK_STOP': 138} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | SHORT | GBPUSD | london | negative_control | 138 | 138 | 0.329739 | {'LOCK_STOP': 138} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 136 | 136 | 1.495712 | {'LOCK_STOP': 119, 'TIMEOUT': 17} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | GBPUSD | london | negative_control | 135 | 135 | 1.477097 | {'LOCK_STOP': 82, 'TIMEOUT': 53} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | USDJPY | london | negative_control | 135 | 135 | 1.006624 | {'LOCK_STOP': 123, 'TIMEOUT': 12} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | USDJPY | london | negative_control | 135 | 135 | 0.752623 | {'LOCK_STOP': 135} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 134 | 134 | 1.648683 | {'LOCK_STOP': 48, 'TIMEOUT': 86} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 133 | 133 | 1.5698 | {'LOCK_STOP': 105, 'TIMEOUT': 28} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | XAUUSD | ny | dominance_watchlist | 132 | 132 | 0.711176 | {'LOCK_STOP': 132} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 132 | 132 | 1.96514 | {'LOCK_STOP': 132} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 131 | 131 | 1.063401 | {'LOCK_STOP': 62, 'TIMEOUT': 69} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | USDJPY | tokyo | negative_control | 127 | 127 | 0.737423 | {'LOCK_STOP': 127} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 127 | 127 | 0.638342 | {'LOCK_STOP': 84, 'TIMEOUT': 43} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | US30_cash | ny | dominance_watchlist | 127 | 127 | 1.565809 | {'LOCK_STOP': 127} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 126 | 126 | 2.455671 | {'LOCK_STOP': 77, 'TIMEOUT': 15, 'TP': 34} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | GBPUSD | london | negative_control | 122 | 122 | 0.747471 | {'LOCK_STOP': 117, 'TIMEOUT': 5} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 118 | 118 | 0.708905 | {'LOCK_STOP': 118} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | SHORT | GBPUSD | london | negative_control | 118 | 118 | 0.513287 | {'LOCK_STOP': 118} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 118 | 118 | 1.170593 | {'LOCK_STOP': 118} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | NAS100 | ny | dominance_watchlist | 114 | 114 | 1.88669 | {'LOCK_STOP': 83, 'TIMEOUT': 30, 'TP': 1} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | SHORT | GBPUSD | london | negative_control | 114 | 114 | 0.613124 | {'LOCK_STOP': 114} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 109 | 109 | 1.485048 | {'LOCK_STOP': 97, 'TIMEOUT': 12} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | USDJPY | tokyo | negative_control | 109 | 109 | 0.886061 | {'LOCK_STOP': 109} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | USDJPY | tokyo | negative_control | 109 | 109 | 0.494546 | {'LOCK_STOP': 89, 'TIMEOUT': 20} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 107 | 107 | 1.97564 | {'LOCK_STOP': 51, 'TIMEOUT': 56} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | XAUUSD | ny | dominance_watchlist | 105 | 105 | 0.625999 | {'LOCK_STOP': 105} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 105 | 105 | 1.605933 | {'LOCK_STOP': 82, 'TIMEOUT': 23} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 105 | 105 | 0.974536 | {'LOCK_STOP': 105} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | XAUUSD | ny | dominance_watchlist | 104 | 104 | 0.544601 | {'LOCK_STOP': 104} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | USDJPY | london | negative_control | 103 | 103 | 0.6188 | {'LOCK_STOP': 103} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 102 | 102 | 0.870359 | {'LOCK_STOP': 102} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAUUSD | ny | dominance_watchlist | 100 | 100 | 0.560833 | {'LOCK_STOP': 100} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | SHORT | GBPUSD | london | negative_control | 100 | 100 | 0.411673 | {'LOCK_STOP': 100} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 100 | 100 | 0.497421 | {'LOCK_STOP': 100} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | NAS100 | ny | dominance_watchlist | 98 | 98 | 1.002509 | {'LOCK_STOP': 98} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | NAS100 | ny | dominance_watchlist | 96 | 96 | 0.855621 | {'LOCK_STOP': 93, 'TP': 3} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | USDJPY | london | negative_control | 96 | 96 | 0.831905 | {'LOCK_STOP': 96} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 95 | 95 | 0.841922 | {'LOCK_STOP': 62, 'TIMEOUT': 33} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 94 | 94 | 1.08514 | {'LOCK_STOP': 94} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | XAUUSD | ny | dominance_watchlist | 93 | 93 | 2.572933 | {'LOCK_STOP': 55, 'TIMEOUT': 38} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | USDJPY | tokyo | negative_control | 92 | 92 | 1.408856 | {'LOCK_STOP': 42, 'TIMEOUT': 50} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | USDJPY | london | negative_control | 90 | 90 | 0.998632 | {'LOCK_STOP': 80, 'TIMEOUT': 10} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | NAS100 | ny | dominance_watchlist | 90 | 90 | 1.704162 | {'LOCK_STOP': 78, 'TIMEOUT': 11, 'TP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | NAS100 | ny | dominance_watchlist | 90 | 90 | 0.906663 | {'LOCK_STOP': 83, 'TP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | GBPUSD | london | negative_control | 90 | 90 | 0.38447 | {'LOCK_STOP': 89, 'TIMEOUT': 1} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 90 | 90 | 0.600802 | {'LOCK_STOP': 90} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 90 | 90 | 1.333853 | {'LOCK_STOP': 90} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | NAS100 | ny | dominance_watchlist | 89 | 89 | 1.815611 | {'LOCK_STOP': 75, 'TIMEOUT': 14} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | USDJPY | tokyo | negative_control | 85 | 85 | 0.651454 | {'LOCK_STOP': 85} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 85 | 85 | 1.286658 | {'LOCK_STOP': 60, 'TIMEOUT': 25} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 85 | 85 | 1.563594 | {'LOCK_STOP': 36, 'TIMEOUT': 49} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 84 | 84 | 0.345505 | {'LOCK_STOP': 84} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | USDJPY | tokyo | negative_control | 83 | 83 | 0.691838 | {'LOCK_STOP': 83} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 82 | 82 | 1.295131 | {'LOCK_STOP': 67, 'TIMEOUT': 15} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | XAUUSD | ny | dominance_watchlist | 81 | 81 | 2.249463 | {'LOCK_STOP': 81} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | SHORT | GBPUSD | london | negative_control | 80 | 80 | 0.310773 | {'LOCK_STOP': 80} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | USDJPY | london | negative_control | 79 | 79 | 0.650624 | {'LOCK_STOP': 79} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | GBPUSD | london | negative_control | 78 | 78 | 1.882446 | {'LOCK_STOP': 60, 'TIMEOUT': 18} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | SHORT | GBPUSD | london | negative_control | 78 | 78 | 1.873752 | {'LOCK_STOP': 4, 'TIMEOUT': 65, 'TP': 9} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | USDJPY | london | negative_control | 77 | 77 | 0.652799 | {'LOCK_STOP': 77} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | USDJPY | london | negative_control | 77 | 77 | 0.731842 | {'LOCK_STOP': 77} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 76 | 76 | 1.073603 | {'LOCK_STOP': 66, 'TIMEOUT': 10} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 75 | 75 | 0.877665 | {'LOCK_STOP': 75} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | USDJPY | london | negative_control | 75 | 75 | 0.815724 | {'LOCK_STOP': 35, 'TIMEOUT': 40} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | US30_cash | ny | dominance_watchlist | 75 | 75 | 1.587172 | {'LOCK_STOP': 27, 'TIMEOUT': 48} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | GBPUSD | london | negative_control | 74 | 74 | 0.339105 | {'LOCK_STOP': 74} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 74 | 74 | 0.657092 | {'LOCK_STOP': 74} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 73 | 73 | 1.605213 | {'LOCK_STOP': 59, 'TIMEOUT': 14} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 71 | 71 | 0.93841 | {'LOCK_STOP': 71} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 71 | 71 | 0.851429 | {'LOCK_STOP': 71} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | NAS100 | ny | dominance_watchlist | 71 | 71 | 2.261558 | {'LOCK_STOP': 37, 'TIMEOUT': 33, 'TP': 1} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 71 | 71 | 1.715024 | {'LOCK_STOP': 35, 'TIMEOUT': 36} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | XAUUSD | ny | dominance_watchlist | 70 | 70 | 2.233493 | {'LOCK_STOP': 54, 'TIMEOUT': 16} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 69 | 69 | 0.584161 | {'LOCK_STOP': 69} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | US30_cash | ny | dominance_watchlist | 69 | 69 | 1.333604 | {'LOCK_STOP': 69} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 69 | 69 | 1.125732 | {'LOCK_STOP': 49, 'TIMEOUT': 20} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 68 | 68 | 0.731803 | {'LOCK_STOP': 68} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | US30_cash | ny | dominance_watchlist | 68 | 68 | 1.707806 | {'LOCK_STOP': 57, 'TIMEOUT': 6, 'TP': 5} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | USDJPY | tokyo | negative_control | 68 | 68 | 0.344696 | {'LOCK_STOP': 68} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 67 | 67 | 0.827013 | {'LOCK_STOP': 67} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | tokyo | negative_control | 66 | 66 | 0.845392 | {'LOCK_STOP': 66} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 65 | 65 | 1.235728 | {'LOCK_STOP': 65} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | US30_cash | ny | dominance_watchlist | 65 | 65 | 1.732007 | {'LOCK_STOP': 54, 'TIMEOUT': 11} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | USDJPY | tokyo | negative_control | 65 | 65 | 0.193956 | {'LOCK_STOP': 65} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 64 | 64 | 0.47343 | {'LOCK_STOP': 52, 'TIMEOUT': 12} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | US30_cash | ny | dominance_watchlist | 62 | 62 | 1.771895 | {'LOCK_STOP': 62} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | NAS100 | ny | dominance_watchlist | 62 | 62 | 1.945485 | {'LOCK_STOP': 55, 'TP': 7} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 62 | 62 | 3.082364 | {'LOCK_STOP': 62} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | GBPUSD | london | negative_control | 61 | 61 | 0.739181 | {'LOCK_STOP': 61} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | SHORT | GBPUSD | london | negative_control | 61 | 61 | 0.597715 | {'LOCK_STOP': 61} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | XAUUSD | ny | dominance_watchlist | 61 | 61 | 1.031412 | {'LOCK_STOP': 31, 'TIMEOUT': 30} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | US30_cash | ny | dominance_watchlist | 61 | 61 | 1.973306 | {'LOCK_STOP': 59, 'TIMEOUT': 2} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | USDJPY | tokyo | negative_control | 61 | 61 | 0.50647 | {'LOCK_STOP': 61} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | SHORT | GBPUSD | london | negative_control | 60 | 60 | 0.530821 | {'LOCK_STOP': 60} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 60 | 60 | 0.746814 | {'LOCK_STOP': 60} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 60 | 60 | 1.031758 | {'LOCK_STOP': 51, 'TIMEOUT': 9} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 59 | 59 | 0.717919 | {'LOCK_STOP': 59} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | USDJPY | london | negative_control | 58 | 58 | 1.188475 | {'LOCK_STOP': 46, 'TIMEOUT': 12} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 58 | 58 | 1.461397 | {'LOCK_STOP': 58} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | SHORT | GBPUSD | london | negative_control | 58 | 58 | 0.668348 | {'LOCK_STOP': 58} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 57 | 57 | 1.516293 | {'LOCK_STOP': 55, 'TIMEOUT': 2} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 57 | 57 | 1.501495 | {'LOCK_STOP': 57} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 56 | 56 | 1.345287 | {'LOCK_STOP': 14, 'TIMEOUT': 42} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | GBPUSD | london | negative_control | 56 | 56 | 0.927745 | {'LOCK_STOP': 45, 'TIMEOUT': 11} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 55 | 55 | 2.214301 | {'LOCK_STOP': 26, 'TIMEOUT': 29} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 55 | 55 | 0.493102 | {'LOCK_STOP': 55} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 55 | 55 | 1.415559 | {'LOCK_STOP': 43, 'TIMEOUT': 12} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | XAUUSD | ny | dominance_watchlist | 54 | 54 | 1.888846 | {'LOCK_STOP': 54} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | USDJPY | tokyo | negative_control | 54 | 54 | 0.652359 | {'LOCK_STOP': 31, 'TIMEOUT': 23} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | USDJPY | tokyo | negative_control | 53 | 53 | 0.686208 | {'LOCK_STOP': 53} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 53 | 53 | 1.302889 | {'LOCK_STOP': 10, 'TIMEOUT': 43} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 52 | 52 | 1.926602 | {'LOCK_STOP': 52} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAUUSD | ny | dominance_watchlist | 52 | 52 | 0.360295 | {'LOCK_STOP': 52} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | USDJPY | london | negative_control | 52 | 52 | 1.178164 | {'LOCK_STOP': 42, 'TIMEOUT': 10} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | USDJPY | tokyo | negative_control | 52 | 52 | 0.243027 | {'LOCK_STOP': 52} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | US30_cash | ny | dominance_watchlist | 51 | 51 | 0.983097 | {'LOCK_STOP': 51} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | USDJPY | london | negative_control | 51 | 51 | 1.15886 | {'LOCK_STOP': 51} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 51 | 51 | 0.862737 | {'LOCK_STOP': 15, 'TIMEOUT': 36} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 50 | 50 | 0.985648 | {'LOCK_STOP': 46, 'TIMEOUT': 4} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 50 | 50 | 0.740713 | {'LOCK_STOP': 26, 'TIMEOUT': 24} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | XAUUSD | ny | dominance_watchlist | 50 | 50 | 0.76114 | {'LOCK_STOP': 34, 'TIMEOUT': 16} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 50 | 50 | 0.45951 | {'LOCK_STOP': 38, 'TIMEOUT': 12} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | NAS100 | ny | dominance_watchlist | 49 | 49 | 2.922713 | {'LOCK_STOP': 45, 'TIMEOUT': 4} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 49 | 49 | 1.927173 | {'LOCK_STOP': 49} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | USDJPY | london | negative_control | 48 | 48 | 0.729796 | {'LOCK_STOP': 38, 'TIMEOUT': 10} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | NAS100 | ny | dominance_watchlist | 47 | 47 | 2.28186 | {'LOCK_STOP': 42, 'TP': 5} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | GBPUSD | london | negative_control | 47 | 47 | 0.936416 | {'LOCK_STOP': 47} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | US30_cash | ny | dominance_watchlist | 47 | 47 | 1.926008 | {'LOCK_STOP': 47} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | XAUUSD | ny | dominance_watchlist | 46 | 46 | 2.687366 | {'LOCK_STOP': 24, 'TIMEOUT': 22} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 45 | 45 | 1.316684 | {'LOCK_STOP': 27, 'TIMEOUT': 18} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 45 | 45 | 0.93008 | {'LOCK_STOP': 45} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 45 | 45 | 2.130774 | {'LOCK_STOP': 45} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | XAUUSD | ny | dominance_watchlist | 44 | 44 | 1.382005 | {'LOCK_STOP': 36, 'TIMEOUT': 8} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | US30_cash | ny | dominance_watchlist | 44 | 44 | 1.653569 | {'LOCK_STOP': 30, 'TIMEOUT': 14} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | XAUUSD | ny | dominance_watchlist | 44 | 44 | 2.768576 | {'LOCK_STOP': 20, 'TIMEOUT': 24} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | tokyo | negative_control | 43 | 43 | 1.523306 | {'LOCK_STOP': 34, 'TIMEOUT': 9} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 43 | 43 | 0.474777 | {'LOCK_STOP': 43} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | london | negative_control | 42 | 42 | 1.040094 | {'LOCK_STOP': 26, 'TIMEOUT': 16} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 42 | 42 | 1.753006 | {'LOCK_STOP': 35, 'TIMEOUT': 7} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 42 | 42 | 1.063105 | {'LOCK_STOP': 42} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | NAS100 | ny | dominance_watchlist | 42 | 42 | 2.670199 | {'LOCK_STOP': 38, 'TIMEOUT': 4} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | USDJPY | london | negative_control | 42 | 42 | 0.969228 | {'LOCK_STOP': 40, 'TIMEOUT': 2} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 41 | 41 | 0.729565 | {'LOCK_STOP': 41} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | USDJPY | london | negative_control | 41 | 41 | 1.726759 | {'LOCK_STOP': 2, 'TIMEOUT': 39} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | USDJPY | tokyo | negative_control | 41 | 41 | 0.211942 | {'LOCK_STOP': 41} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | USDJPY | tokyo | negative_control | 40 | 40 | 0.759767 | {'LOCK_STOP': 40} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 40 | 40 | 1.193469 | {'LOCK_STOP': 40} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | USDJPY | tokyo | negative_control | 40 | 40 | 1.53523 | {'LOCK_STOP': 40} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 39 | 39 | 0.884347 | {'LOCK_STOP': 39} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 38 | 38 | 0.602815 | {'LOCK_STOP': 36, 'TIMEOUT': 2} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | USDJPY | london | negative_control | 38 | 38 | 0.446331 | {'LOCK_STOP': 38} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | XAUUSD | ny | dominance_watchlist | 37 | 37 | 1.98557 | {'LOCK_STOP': 32, 'TIMEOUT': 5} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | LONG | US30_cash | ny | dominance_watchlist | 37 | 37 | 1.335295 | {'LOCK_STOP': 26, 'TIMEOUT': 11} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 37 | 37 | 0.942643 | {'LOCK_STOP': 37} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | US30_cash | ny | dominance_watchlist | 37 | 37 | 1.56501 | {'LOCK_STOP': 37} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 37 | 37 | 0.681468 | {'LOCK_STOP': 37} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | USDJPY | tokyo | negative_control | 36 | 36 | 0.679279 | {'LOCK_STOP': 36} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | USDJPY | tokyo | negative_control | 36 | 36 | 0.472805 | {'LOCK_STOP': 36} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | US30_cash | ny | dominance_watchlist | 36 | 36 | 1.87162 | {'LOCK_STOP': 36} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 35 | 35 | 1.209757 | {'LOCK_STOP': 35} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 35 | 35 | 1.693686 | {'LOCK_STOP': 23, 'TIMEOUT': 12} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | NAS100 | ny | dominance_watchlist | 35 | 35 | 3.859821 | {'LOCK_STOP': 2, 'TIMEOUT': 33} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 34 | 34 | 0.870389 | {'LOCK_STOP': 30, 'TIMEOUT': 4} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 34 | 34 | 0.407649 | {'LOCK_STOP': 34} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 34 | 34 | 1.458845 | {'LOCK_STOP': 34} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 34 | 34 | 0.407649 | {'LOCK_STOP': 34} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | USDJPY | tokyo | negative_control | 33 | 33 | 1.14513 | {'LOCK_STOP': 33} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 33 | 33 | 0.405648 | {'LOCK_STOP': 33} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | USDJPY | london | negative_control | 33 | 33 | 0.220049 | {'LOCK_STOP': 33} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | GBPUSD | london | negative_control | 32 | 32 | 1.834401 | {'LOCK_STOP': 29, 'TIMEOUT': 3} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 32 | 32 | 0.930396 | {'TIMEOUT': 32} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | US30_cash | ny | dominance_watchlist | 31 | 31 | 1.782876 | {'LOCK_STOP': 31} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 31 | 31 | 0.40068 | {'LOCK_STOP': 31} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | US30_cash | ny | dominance_watchlist | 30 | 30 | 2.913555 | {'LOCK_STOP': 30} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 30 | 30 | 1.063693 | {'LOCK_STOP': 28, 'TIMEOUT': 2} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | USDJPY | tokyo | negative_control | 30 | 30 | 0.220638 | {'LOCK_STOP': 30} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | USDJPY | london | negative_control | 28 | 28 | 1.563254 | {'LOCK_STOP': 28} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | XAUUSD | ny | dominance_watchlist | 28 | 28 | 0.738016 | {'LOCK_STOP': 28} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | LONG | USDJPY | tokyo | negative_control | 28 | 28 | 0.911835 | {'LOCK_STOP': 28} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 28 | 28 | 0.220802 | {'LOCK_STOP': 28} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | GBPUSD | london | negative_control | 28 | 28 | 0.630345 | {'LOCK_STOP': 12, 'TIMEOUT': 16} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | tokyo | negative_control | 27 | 27 | 1.91577 | {'LOCK_STOP': 27} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 27 | 27 | 0.533353 | {'LOCK_STOP': 27} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 27 | 27 | 0.680476 | {'LOCK_STOP': 27} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 26 | 26 | 0.609395 | {'LOCK_STOP': 14, 'TIMEOUT': 12} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 26 | 26 | 0.188555 | {'LOCK_STOP': 26} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | london | negative_control | 26 | 26 | 2.198568 | {'LOCK_STOP': 26} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | GBPUSD | london | negative_control | 25 | 25 | 1.573025 | {'LOCK_STOP': 18, 'TIMEOUT': 7} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | london | negative_control | 25 | 25 | 0.8944 | {'LOCK_STOP': 15, 'TIMEOUT': 10} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 25 | 25 | 1.932495 | {'LOCK_STOP': 25} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | NAS100 | ny | dominance_watchlist | 25 | 25 | 2.111365 | {'LOCK_STOP': 25} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | NAS100 | ny | dominance_watchlist | 25 | 25 | 0.709768 | {'LOCK_STOP': 24, 'TIMEOUT': 1} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | LONG | USDJPY | london | negative_control | 25 | 25 | 0.763356 | {'LOCK_STOP': 25} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 25 | 25 | 1.972283 | {'LOCK_STOP': 4, 'TIMEOUT': 21} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | GBPUSD | london | negative_control | 25 | 25 | 0.2133 | {'LOCK_STOP': 24, 'TIMEOUT': 1} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 24 | 24 | 0.888207 | {'LOCK_STOP': 24} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 24 | 24 | 0.935431 | {'LOCK_STOP': 24} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 23 | 23 | 0.505385 | {'LOCK_STOP': 23} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M15 | LONG | XAUUSD | ny | dominance_watchlist | 23 | 23 | 0.283657 | {'LOCK_STOP': 23} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 22 | 22 | 0.396572 | {'LOCK_STOP': 22} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 22 | 22 | 0.831049 | {'LOCK_STOP': 22} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | US30_cash | ny | dominance_watchlist | 22 | 22 | 1.574068 | {'LOCK_STOP': 20, 'TIMEOUT': 2} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | XAUUSD | ny | dominance_watchlist | 22 | 22 | 1.416467 | {'TIMEOUT': 22} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 21 | 21 | 1.09599 | {'LOCK_STOP': 21} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | NAS100 | ny | dominance_watchlist | 21 | 21 | 1.040778 | {'LOCK_STOP': 21} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | GBPUSD | london | negative_control | 21 | 21 | 0.609413 | {'LOCK_STOP': 21} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | USDJPY | london | negative_control | 20 | 20 | 1.312043 | {'LOCK_STOP': 10, 'TIMEOUT': 10} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | GBPUSD | london | negative_control | 20 | 20 | 0.856512 | {'LOCK_STOP': 20} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 20 | 20 | 0.484943 | {'LOCK_STOP': 20} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | XAUUSD | ny | dominance_watchlist | 20 | 20 | 2.049731 | {'LOCK_STOP': 16, 'TIMEOUT': 4} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | US30_cash | ny | dominance_watchlist | 20 | 20 | 1.58408 | {'LOCK_STOP': 18, 'TIMEOUT': 2} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 20 | 20 | 0.691278 | {'LOCK_STOP': 20} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | london | negative_control | 20 | 20 | 1.502086 | {'LOCK_STOP': 20} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 20 | 20 | 0.793421 | {'LOCK_STOP': 20} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | tokyo | negative_control | 20 | 20 | 1.080455 | {'LOCK_STOP': 20} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 20 | 20 | 1.027051 | {'LOCK_STOP': 6, 'TIMEOUT': 14} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | USDJPY | tokyo | negative_control | 20 | 20 | 1.734548 | {'TIMEOUT': 20} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | LONG | US30_cash | ny | dominance_watchlist | 20 | 20 | 1.855167 | {'LOCK_STOP': 16, 'TIMEOUT': 4} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 20 | 20 | 0.526298 | {'LOCK_STOP': 20} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | SHORT | GBPUSD | london | negative_control | 19 | 19 | 0.164709 | {'LOCK_STOP': 19} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | USDJPY | london | negative_control | 19 | 19 | 0.376675 | {'LOCK_STOP': 19} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 19 | 19 | 1.995284 | {'LOCK_STOP': 14, 'TIMEOUT': 5} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | NAS100 | ny | dominance_watchlist | 19 | 19 | 1.710408 | {'LOCK_STOP': 18, 'TP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 19 | 19 | 0.236446 | {'LOCK_STOP': 19} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | US30_cash | ny | dominance_watchlist | 19 | 19 | 0.344631 | {'LOCK_STOP': 19} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | SHORT | GBPUSD | london | negative_control | 19 | 19 | 0.768166 | {'LOCK_STOP': 18, 'TIMEOUT': 1} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | US30_cash | ny | dominance_watchlist | 19 | 19 | 0.242991 | {'LOCK_STOP': 19} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 18 | 18 | 0.561802 | {'LOCK_STOP': 18} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | LONG | USDJPY | london | negative_control | 18 | 18 | 0.344337 | {'LOCK_STOP': 18} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | US30_cash | ny | dominance_watchlist | 18 | 18 | 1.509173 | {'LOCK_STOP': 18} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | GBPUSD | london | negative_control | 18 | 18 | 0.064798 | {'LOCK_STOP': 18} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | US30_cash | ny | dominance_watchlist | 18 | 18 | 0.475298 | {'LOCK_STOP': 18} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | tokyo | negative_control | 18 | 18 | 1.331942 | {'LOCK_STOP': 18} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | NAS100 | ny | dominance_watchlist | 17 | 17 | 0.06851 | {'LOCK_STOP': 17} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 17 | 17 | 0.379159 | {'LOCK_STOP': 17} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 17 | 17 | 3.262469 | {'LOCK_STOP': 17} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | US30_cash | ny | dominance_watchlist | 17 | 17 | 2.763952 | {'LOCK_STOP': 17} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 17 | 17 | 2.291148 | {'LOCK_STOP': 17} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | NAS100 | ny | dominance_watchlist | 16 | 16 | 0.053503 | {'LOCK_STOP': 16} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 16 | 16 | 0.427578 | {'LOCK_STOP': 16} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | USDJPY | london | negative_control | 16 | 16 | 1.72715 | {'LOCK_STOP': 16} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | GBPJPY | tokyo | primary_controlled_child | 16 | 16 | 1.287286 | {'LOCK_STOP': 16} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 16 | 16 | 0.092612 | {'LOCK_STOP': 16} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | US30_cash | ny | dominance_watchlist | 16 | 16 | 0.403822 | {'LOCK_STOP': 16} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | tokyo | negative_control | 15 | 15 | 0.931702 | {'LOCK_STOP': 15} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | tokyo | negative_control | 15 | 15 | 1.005734 | {'LOCK_STOP': 15} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 15 | 15 | 2.814863 | {'LOCK_STOP': 8, 'TIMEOUT': 7} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 14 | 14 | 0.983355 | {'LOCK_STOP': 14} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 14 | 14 | 2.00319 | {'TIMEOUT': 14} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 14 | 14 | 2.033848 | {'LOCK_STOP': 14} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | US30_cash | ny | dominance_watchlist | 14 | 14 | 0.420229 | {'LOCK_STOP': 14} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | primary_controlled_child | 14 | 14 | 0.800281 | {'LOCK_STOP': 14} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | london | negative_control | 14 | 14 | 1.856355 | {'LOCK_STOP': 14} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | XAGUSD | london | cleared_non_primary_strong_lead | 13 | 13 | 1.046727 | {'LOCK_STOP': 13} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | USDJPY | tokyo | negative_control | 13 | 13 | 0.084782 | {'LOCK_STOP': 13} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | XAUUSD | ny | dominance_watchlist | 13 | 13 | 2.15275 | {'LOCK_STOP': 13} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 12 | 12 | 0.823742 | {'LOCK_STOP': 12} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | XAUUSD | ny | dominance_watchlist | 12 | 12 | 0.664188 | {'LOCK_STOP': 12} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 12 | 12 | 0.210744 | {'LOCK_STOP': 12} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | USDJPY | tokyo | negative_control | 12 | 12 | 0.18158 | {'LOCK_STOP': 12} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 12 | 12 | 0.044488 | {'LOCK_STOP': 12} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 12 | 12 | 1.114105 | {'LOCK_STOP': 11, 'TIMEOUT': 1} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 11 | 11 | 2.260511 | {'LOCK_STOP': 11} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 11 | 11 | 2.260511 | {'LOCK_STOP': 11} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | USDJPY | london | negative_control | 10 | 10 | 0.411286 | {'LOCK_STOP': 10} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | US30_cash | ny | dominance_watchlist | 9 | 9 | 0.275728 | {'LOCK_STOP': 9} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | LONG | USDJPY | london | negative_control | 9 | 9 | 2.435708 | {'LOCK_STOP': 9} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 9 | 9 | 1.445947 | {'LOCK_STOP': 9} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | US30_cash | ny | dominance_watchlist | 9 | 9 | 0.288697 | {'LOCK_STOP': 9} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M15 | SHORT | USDJPY | tokyo | cleared_non_primary_strong_lead | 9 | 9 | 4.571113 | {'TIMEOUT': 9} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | NAS100 | ny | dominance_watchlist | 7 | 7 | 0.66391 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | USDJPY | tokyo | negative_control | 7 | 7 | 1.324106 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 7 | 7 | 0.543204 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | GBPJPY | tokyo | primary_controlled_child | 7 | 7 | 0.353684 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M5 | SHORT | GBPUSD | london | negative_control | 7 | 7 | 1.25239 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 7 | 7 | 1.029659 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | USDJPY | tokyo | negative_control | 7 | 7 | 1.536884 | {'LOCK_STOP': 7} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 7 | 7 | 0.825745 | {'LOCK_STOP': 7} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | GBPUSD | london | negative_control | 6 | 6 | 0.623781 | {'LOCK_STOP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 6 | 6 | 0.772027 | {'LOCK_STOP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | XAUUSD | ny | dominance_watchlist | 6 | 6 | 0.746657 | {'LOCK_STOP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | LONG | GBPJPY | tokyo | primary_controlled_child | 6 | 6 | 2.291148 | {'LOCK_STOP': 6} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M1 | LONG | XAUUSD | ny | dominance_watchlist | 6 | 6 | 1.604373 | {'LOCK_STOP': 6} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 5 | 5 | 0.840662 | {'LOCK_STOP': 5} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | US30_cash | ny | dominance_watchlist | 4 | 4 | 0.989554 | {'LOCK_STOP': 4} |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | SHORT | GBPUSD | london | negative_control | 4 | 4 | 2.318182 | {'LOCK_STOP': 4} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | XAUUSD | ny | dominance_watchlist | 3 | 3 | 3.514805 | {'LOCK_STOP': 2, 'TIMEOUT': 1} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | LONG | US30_cash | ny | dominance_watchlist | 3 | 3 | 0.664321 | {'LOCK_STOP': 3} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | LONG | US30_cash | ny | dominance_watchlist | 3 | 3 | 1.509129 | {'LOCK_STOP': 3} |
| STRUCT_COMPOSITE_ANY_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M5 | SHORT | GBPUSD | london | negative_control | 3 | 3 | 0.154505 | {'LOCK_STOP': 3} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | LONG | USDJPY | london | negative_control | 3 | 3 | 0.986769 | {'LOCK_STOP': 3} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M5 | LONG | USDJPY | london | negative_control | 3 | 3 | 1.106239 | {'LOCK_STOP': 3} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M15 | LONG | US30_cash | ny | dominance_watchlist | 2 | 2 | 0.175222 | {'LOCK_STOP': 2} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M5 | SHORT | USDJPY | tokyo | primary_controlled_child | 2 | 2 | 0.222368 | {'LOCK_STOP': 2} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | SHORT | GBPUSD | london | negative_control | 2 | 2 | 0.020039 | {'LOCK_STOP': 2} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | US30_cash | ny | dominance_watchlist | 2 | 2 | 0.61611 | {'LOCK_STOP': 2} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 2 | 2 | 0.456482 | {'LOCK_STOP': 2} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 2 | 2 | 0.035833 | {'LOCK_STOP': 2} |
| STRUCT_BOS_LEVEL_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.394164 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | BOS_BROKEN_LEVEL | swing_structure | M1 | LONG | USDJPY | london | negative_control | 1 | 1 | 0.065461 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.090731 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.187734 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | FVG_MIDPOINT | poi_boundary | M5 | SHORT | GBPUSD | london | negative_control | 1 | 1 | 2.454545 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | PATH_HIGH_LOW_RUN | liquidity | M5 | SHORT | USDJPY | london | cleared_non_primary_strong_lead | 1 | 1 | 0.637544 | {'LOCK_STOP': 1} |
| STRUCT_COMPOSITE_ANY_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.187734 | {'LOCK_STOP': 1} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.090731 | {'LOCK_STOP': 1} |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | DISPLACEMENT_HALFBACK | volatility_displacement | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.187734 | {'LOCK_STOP': 1} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.165984 | {'LOCK_STOP': 1} |
| STRUCT_FVG_MID_EDGE_V2 | FVG_MIDPOINT | poi_boundary | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.105941 | {'LOCK_STOP': 1} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M15 | LONG | XAUUSD | ny | dominance_watchlist | 1 | 1 | 1.379514 | {'TIMEOUT': 1} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.185801 | {'LOCK_STOP': 1} |
| STRUCT_LIQUIDITY_RUN_V2 | EQUAL_HIGH_LOW_RUN | liquidity | M1 | SHORT | USDJPY | tokyo | primary_controlled_child | 1 | 1 | 0.16826 | {'LOCK_STOP': 1} |
| STRUCT_OB_BOUNDARY_V2 | OB_PROTECTIVE_BOUNDARY | poi_boundary | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.165472 | {'LOCK_STOP': 1} |
| STRUCT_SWING_PROTECTED_V2 | PROTECTED_CONFIRMED_SWING | swing_structure | M1 | LONG | NAS100 | ny | dominance_watchlist | 1 | 1 | 0.120713 | {'LOCK_STOP': 1} |

## Structural Event Census

| selected_timeframe | side | selector_id | family | candidate_count |
| --- | --- | --- | --- | --- |
| M1 | LONG | BOS_BROKEN_LEVEL | swing_structure | 66190 |
| M1 | LONG | DISPLACEMENT_HALFBACK | volatility_displacement | 58041 |
| M1 | LONG | EQUAL_HIGH_LOW_RUN | liquidity | 498391 |
| M1 | LONG | FVG_MIDPOINT | poi_boundary | 77375 |
| M1 | LONG | FVG_PROTECTIVE_EDGE | poi_boundary | 77139 |
| M1 | LONG | OB_PROTECTIVE_BOUNDARY | poi_boundary | 64035 |
| M1 | LONG | PATH_HIGH_LOW_RUN | liquidity | 9415 |
| M1 | LONG | PROTECTED_CONFIRMED_SWING | swing_structure | 578891 |
| M1 | SHORT | BOS_BROKEN_LEVEL | swing_structure | 20176 |
| M1 | SHORT | DISPLACEMENT_HALFBACK | volatility_displacement | 18250 |
| M1 | SHORT | EQUAL_HIGH_LOW_RUN | liquidity | 173606 |
| M1 | SHORT | FVG_MIDPOINT | poi_boundary | 25393 |
| M1 | SHORT | FVG_PROTECTIVE_EDGE | poi_boundary | 25312 |
| M1 | SHORT | OB_PROTECTIVE_BOUNDARY | poi_boundary | 18990 |
| M1 | SHORT | PATH_HIGH_LOW_RUN | liquidity | 3682 |
| M1 | SHORT | PROTECTED_CONFIRMED_SWING | swing_structure | 187118 |
| M15 | LONG | BOS_BROKEN_LEVEL | swing_structure | 28611 |
| M15 | LONG | DISPLACEMENT_HALFBACK | volatility_displacement | 34492 |
| M15 | LONG | EQUAL_HIGH_LOW_RUN | liquidity | 141455 |
| M15 | LONG | FVG_MIDPOINT | poi_boundary | 42942 |
| M15 | LONG | FVG_PROTECTIVE_EDGE | poi_boundary | 42700 |
| M15 | LONG | OB_PROTECTIVE_BOUNDARY | poi_boundary | 27055 |
| M15 | LONG | PATH_HIGH_LOW_RUN | liquidity | 24149 |
| M15 | LONG | PROTECTED_CONFIRMED_SWING | swing_structure | 300215 |
| M15 | SHORT | BOS_BROKEN_LEVEL | swing_structure | 12311 |
| M15 | SHORT | DISPLACEMENT_HALFBACK | volatility_displacement | 15255 |
| M15 | SHORT | EQUAL_HIGH_LOW_RUN | liquidity | 59736 |
| M15 | SHORT | FVG_MIDPOINT | poi_boundary | 16590 |
| M15 | SHORT | FVG_PROTECTIVE_EDGE | poi_boundary | 16370 |
| M15 | SHORT | OB_PROTECTIVE_BOUNDARY | poi_boundary | 11443 |
| M15 | SHORT | PATH_HIGH_LOW_RUN | liquidity | 7272 |
| M15 | SHORT | PROTECTED_CONFIRMED_SWING | swing_structure | 130650 |
| M5 | LONG | BOS_BROKEN_LEVEL | swing_structure | 83116 |
| M5 | LONG | DISPLACEMENT_HALFBACK | volatility_displacement | 74269 |
| M5 | LONG | EQUAL_HIGH_LOW_RUN | liquidity | 543284 |
| M5 | LONG | FVG_MIDPOINT | poi_boundary | 97751 |
| M5 | LONG | FVG_PROTECTIVE_EDGE | poi_boundary | 97333 |
| M5 | LONG | OB_PROTECTIVE_BOUNDARY | poi_boundary | 79710 |
| M5 | LONG | PATH_HIGH_LOW_RUN | liquidity | 31380 |
| M5 | LONG | PROTECTED_CONFIRMED_SWING | swing_structure | 774433 |
| M5 | SHORT | BOS_BROKEN_LEVEL | swing_structure | 20882 |
| M5 | SHORT | DISPLACEMENT_HALFBACK | volatility_displacement | 22170 |
| M5 | SHORT | EQUAL_HIGH_LOW_RUN | liquidity | 156911 |
| M5 | SHORT | FVG_MIDPOINT | poi_boundary | 26320 |
| M5 | SHORT | FVG_PROTECTIVE_EDGE | poi_boundary | 26191 |
| M5 | SHORT | OB_PROTECTIVE_BOUNDARY | poi_boundary | 20358 |
| M5 | SHORT | PATH_HIGH_LOW_RUN | liquidity | 6700 |
| M5 | SHORT | PROTECTED_CONFIRMED_SWING | swing_structure | 209504 |

## Structural Diagnostic Census

| selected_timeframe | diagnostic_event | count |
| --- | --- | --- |
| M1 | CHOCH_AGAINST_TRADE | 107223 |
| M1 | CONFIRMED_SWING_HIGH | 121161 |
| M1 | CONFIRMED_SWING_LOW | 124910 |
| M1 | FAILED_BREAK_RECLAIM_HIGH | 12252 |
| M1 | FAILED_BREAK_RECLAIM_LOW | 11558 |
| M1 | SWEEP_AND_RECLAIM | 23810 |
| M15 | CHOCH_AGAINST_TRADE | 42755 |
| M15 | CONFIRMED_SWING_HIGH | 76689 |
| M15 | CONFIRMED_SWING_LOW | 77084 |
| M15 | FAILED_BREAK_RECLAIM_HIGH | 30618 |
| M15 | FAILED_BREAK_RECLAIM_LOW | 25042 |
| M15 | SWEEP_AND_RECLAIM | 55660 |
| M5 | CHOCH_AGAINST_TRADE | 111917 |
| M5 | CONFIRMED_SWING_HIGH | 153090 |
| M5 | CONFIRMED_SWING_LOW | 154602 |
| M5 | FAILED_BREAK_RECLAIM_HIGH | 37772 |
| M5 | FAILED_BREAK_RECLAIM_LOW | 28551 |
| M5 | SWEEP_AND_RECLAIM | 66323 |

## Pairwise Versus J46

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.222595 | 0.022727 | 99.863803 | 0.176832 | 0.176604 | 777 | 776 | 2841 | 2043 | 2329 | 2034 | 2056 | 1627 | 0.370278 | 753 | 532.688734 | 0.121231 | 296 | 295 | 9 |
| STRUCT_COMPOSITE_ANY_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.157415 | -0.042453 | -186.53636 | 0.33614 | 0.314065 | 1477 | 1380 | 1537 | 2043 | 2923 | 2043 | 1471 | 2904 | 0.660901 | 1364 | 1471.473712 | 0.334883 | 881 | 880 | 0 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.161287 | -0.03858 | -169.521266 | 0.262403 | 0.258079 | 1153 | 1134 | 2107 | 2043 | 2666 | 2036 | 1721 | 2398 | 0.545744 | 1116 | 1151.977482 | 0.262171 | 631 | 630 | 7 |
| STRUCT_FVG_MID_EDGE_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.233159 | 0.033292 | 146.285141 | 0.244197 | 0.239873 | 1073 | 1054 | 2267 | 2043 | 2609 | 2036 | 1778 | 2392 | 0.544379 | 1038 | 793.07971 | 0.180492 | 574 | 573 | 7 |
| STRUCT_LIQUIDITY_RUN_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.209902 | 0.010034 | 44.09129 | 0.177742 | 0.162039 | 781 | 712 | 2901 | 2043 | 2349 | 2034 | 2036 | 1550 | 0.352754 | 696 | 587.180533 | 0.133632 | 316 | 315 | 9 |
| STRUCT_OB_BOUNDARY_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.223928 | 0.024061 | 105.724281 | 0.09513 | 0.106054 | 418 | 466 | 3510 | 2043 | 2245 | 2034 | 2140 | 1286 | 0.292672 | 443 | 257.611975 | 0.058628 | 212 | 211 | 9 |
| STRUCT_SWING_PROTECTED_V2 | J46_J49_ONLY | 4394 | 0.199867 | 0.224381 | 0.024514 | 107.714286 | 0.238052 | 0.18366 | 1046 | 807 | 2541 | 2043 | 2672 | 2041 | 1720 | 2191 | 0.498635 | 784 | 768.847276 | 0.174977 | 632 | 631 | 2 |

## Pairwise Versus Fixed-R Control

| candidate_variant | baseline_variant | paired_resolved_n | baseline_mean_r | candidate_mean_r | mean_delta_candidate_minus_baseline | sum_delta_candidate_minus_baseline | candidate_better_rate | baseline_better_rate | candidate_better_n | baseline_better_n | tie_n | baseline_positive_n | candidate_positive_n | both_positive_n | both_nonpositive_n | candidate_lock_triggered_n | candidate_lock_triggered_rate | truncation_n | truncation_lost_r | truncation_lost_r_per_pair | rescued_baseline_nonpositive_n | rescued_to_positive_n | candidate_made_positive_nonpositive_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_BOS_LEVEL_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.197643 | 0.016532 | 63.152332 | 0.22801 | 0.215707 | 871 | 824 | 2125 | 2030 | 2082 | 1890 | 1598 | 1486 | 0.389005 | 808 | 642.111217 | 0.168092 | 193 | 192 | 140 |
| STRUCT_COMPOSITE_ANY_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.136898 | -0.044212 | -168.890862 | 0.34555 | 0.331414 | 1320 | 1266 | 1234 | 2030 | 2634 | 2024 | 1180 | 2621 | 0.686126 | 1250 | 987.956176 | 0.258627 | 611 | 610 | 6 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.142209 | -0.038901 | -148.602384 | 0.282199 | 0.279581 | 1078 | 1068 | 1674 | 2030 | 2380 | 1982 | 1392 | 2174 | 0.56911 | 1052 | 771.076144 | 0.201852 | 399 | 398 | 48 |
| STRUCT_FVG_MID_EDGE_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.190631 | 0.00952 | 36.36821 | 0.278272 | 0.253403 | 1063 | 968 | 1789 | 2030 | 2340 | 1967 | 1417 | 2152 | 0.563351 | 952 | 615.778297 | 0.161199 | 374 | 373 | 63 |
| STRUCT_LIQUIDITY_RUN_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.175947 | -0.005163 | -19.723946 | 0.218586 | 0.203403 | 835 | 777 | 2208 | 2030 | 2084 | 1902 | 1608 | 1426 | 0.373298 | 761 | 613.530143 | 0.16061 | 183 | 182 | 128 |
| STRUCT_OB_BOUNDARY_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.211943 | 0.030833 | 117.781146 | 0.154712 | 0.165183 | 591 | 631 | 2598 | 2030 | 1998 | 1886 | 1678 | 1179 | 0.308639 | 615 | 415.667447 | 0.108813 | 113 | 112 | 144 |
| STRUCT_SWING_PROTECTED_V2 | PATH_LOCK_HALF_GAIN_V0 | 3820 | 0.18111 | 0.192476 | 0.011366 | 43.417309 | 0.256021 | 0.23089 | 978 | 882 | 1960 | 2030 | 2405 | 2000 | 1385 | 1982 | 0.518848 | 866 | 589.561393 | 0.154335 | 406 | 405 | 30 |

## Methodology Diagnostics

| exit_policy_pbo | pbo_status | pbo_promotion_usable | exit_policy_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- |
| 0.583333 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | False | 1.699111 | False |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Cost model | SENSITIVITY_NOT_MEASURED_COST | Historical OHLC does not contain reliable commission/spread/slippage; report uses R-cost sensitivity. |
| Lower-timeframe coverage | QUANTIFIED | M1 windows=774, M5 windows=5512, M15 fallback windows=7319. |
| Post-decision lower-TF start | PASS | Lower-timeframe rows with close_time <= setup decision clock: 0. |
| Remaining same-bar ambiguity | QUANTIFIED | Total SAME_BAR rows across all variants=10416; all-enabled pessimistic best structural minus J46=0.05872. |
| Future-swing leakage | RULED_OUT_BY_SELECTOR_RULE | Confirmed swings are unavailable until two later selected-timeframe bars close; tests cover this. |
| Unimplemented structural catalog | EXPLICITLY_SCOPED | Breaker, round-number, higher-timeframe composite, and reentry require fresh registered hypotheses. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical raw-OHLC structural-level exit-policy ablation. |

## Opened Questions

| question | status | detail |
| --- | --- | --- |
| Does structural path scaling beat J46 on the registered global metric? | ANSWERED | Headline all-enabled best structural minus J46=0.024511. |
| Does the same result survive pessimistic same-bar treatment? | ANSWERED | Pessimistic all-enabled best structural minus J46=0.05872. |
| Does structural selection reduce V1's fixed-R truncation problem? | ANSWERED | Best pairwise structural candidate=STRUCT_FVG_MID_EDGE_V2 truncation_lost_r=793.07971, rescued_to_positive_n=573. |
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
