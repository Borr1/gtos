# Phase 3 Path Scaling V1 MTF Path Resolution

**Created UTC:** 2026-05-01T20:21:45.323577+00:00
**Replay spec:** `research\phase_3_external_feed_validation\RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`
**V1 spec:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_SPEC_V1.json`
**V1 protocol:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_PROTOCOL_2026-05-02.md`
**V0 comparison report:** `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- V1 uses the same raw-OHLC no-leak candidate reconstruction and frozen V0 exit policies.
- Outcomes are attached only after the cohort decision is locked.
- M1/M5 rows are used only for post-decision path ordering, never for level selection.
- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.
- Reentry and L2-on/off attribution remain intentionally blocked.

## Run Scope

| source_scope | rows_replayed | take_rows_seen | setup_ok_rows | include_blocked_controls | first_take_clock | last_take_clock |
| --- | --- | --- | --- | --- | --- | --- |
| FULL_AVAILABLE_CORPUS | 205197 | 23483 | 12831 | True | 2022-02-07T13:30:00+00:00 | 2026-04-30T17:00:00+00:00 |

## MTF Resolution Policy

| decision_clock | path_timeframe_hierarchy | lower_tf_start_rule | level_selection | time_stop_unit | fallback |
| --- | --- | --- | --- | --- | --- |
| M15 candle close UTC | ['M1', 'M5', 'M15'] | strictly greater than setup candle close | frozen V0 exit-policy R levels only; no lower-timeframe level selection | registered M15 bars converted to elapsed UTC time for M1/M5 path rows | M1 if available in the post-decision path window, else M5, else M15 |

## Coverage Diagnostics

| setup_windows | m1_available_windows | m1_available_rows | m5_available_windows | m5_available_rows | m15_available_windows | m15_available_rows | m15_fallback_windows | selected_timeframes | lower_tf_start_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12831 | 774 | 1005608 | 5512 | 1408564 | 12830 | 1092041 | 7319 | {'M1': 774, 'M15': 7319, 'M5': 4738} | 0 |

## Cost Model

| unit | cost_scenarios_r | actual_commission_spread_source | reentry_cost_note |
| --- | --- | --- | --- |
| R per completed round turn | [0.0, 0.02, 0.05, 0.1] | not reliably available in historical OHLC; reported as sensitivity, not measured cost | V1 has no reentries; future reentry variants must charge one additional round turn per reentry. |

## Policies

| variant_id | family | description | final_target_r | time_stop_bars | pending_expiry_bars | use_setup_tp | lock_steps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | Current raw mechanical fixed TP/SL with 96 M15-bar max hold. |  | 96 | 96 | True | [] |
| J46_J49_ONLY | j46_j49 | 0% partial, 3R trigger to BE, 6R final target, 12 M15-bar time stop after fill. | 6.0 | 12 | 96 | False | [{'trigger_r': 3.0, 'floor_r': 0.0}] |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | Lock-only ladder: 1.5R->0R, 2R->0.5R, 3R->1R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.5, 'floor_r': 0.0}, {'trigger_r': 2.0, 'floor_r': 0.5}, {'trigger_r': 3.0, 'floor_r': 1.0}] |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | Lock-only ladder: 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.5, 'floor_r': 0.5}, {'trigger_r': 2.0, 'floor_r': 1.0}, {'trigger_r': 3.0, 'floor_r': 1.5}] |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | Lock-only ladder: 1R->0R, 1.5R->0.5R, 2R->1R, 3R->1.5R, 6R final target. | 6.0 | 12 | 96 | False | [{'trigger_r': 1.0, 'floor_r': 0.0}, {'trigger_r': 1.5, 'floor_r': 0.5}, {'trigger_r': 2.0, 'floor_r': 1.0}, {'trigger_r': 3.0, 'floor_r': 1.5}] |

## Direct Answers

| question | answer |
| --- | --- |
| Which V1 variant leads on gross mean R? | J46_J49_ONLY with gross_mean_r=0.213894. |
| Which V1 variant leads after a 0.05R round-turn cost sensitivity? | J46_J49_ONLY with net_mean_r_cost_0.05=0.163894. |
| Did lock-only V1 beat J46-J49 globally? | Best lock-only net-minus-J46 at 0.05R cost = -0.022329. This remains same-dataset diagnostic evidence only. |
| How much did MTF path resolution reduce same-bar ambiguity? | Across policy-event rows, V0 same-bar count=9104, V1 same-bar count=6615, and V0 same-bars resolved by MTF=2258. |
| Where did lock-only look most interesting under V1? | Target-family best-lock minus J46 at 0.05R cost = 0.063597; primary-family delta = 0.028002; cleared-non-primary delta = 0.162248. |
| Did MTF resolution change any group/cohort conclusion flags? | 5 group/cohort best-variant or lock-vs-J46 sign changes were detected. See the Conclusion Changes table before moving to V2. |
| Does this promote an exit policy? | No. This is same-dataset historical MTF path-resolution research and remains NO_PROMOTION_VERDICT. |

## V1 Variant Summary

| variant_id | family | actions_seen | setup_ok | entries_filled | resolved_n | gross_sum_r | gross_mean_r | gross_median_r | gross_win_rate | avg_bars_in_trade | lock_trigger_rate | lock_then_stop_rate | direct_3r_available_rate | direct_6r_available_rate | mfe_p50 | mfe_p75 | mfe_p90 | mae_p10 | outcomes | same_dataset_dsr_p_gross | net_mean_r_cost_0 | net_sum_r_cost_0 | net_max_drawdown_r_cost_0 | net_mean_r_cost_0.02 | net_sum_r_cost_0.02 | net_max_drawdown_r_cost_0.02 | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | net_max_drawdown_r_cost_0.05 | net_mean_r_cost_0.1 | net_sum_r_cost_0.1 | net_max_drawdown_r_cost_0.1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | 23483 | 12831 | 3905 | 3898 | 805.111736 | 0.206545 | -0.091581 | 0.491534 | 11.584915 | 0.0 | 0.0 | 0.00744 | 0.0 | 1.193556 | 1.609821 | 1.870665 | -1.529894 | {'NO_ENTRY': 7631, 'SAME_BAR': 1295, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1888, 'TIMEOUT': 301, 'TP': 1716} | 0.0 | 0.206545 | 805.111736 | -88.887538 | 0.186545 | 727.151736 | -91.147538 | 0.156545 | 610.211736 | -94.537538 | 0.106545 | 415.311736 | -100.187538 |
| J46_J49_ONLY | j46_j49 | 23483 | 12831 | 4487 | 4477 | 957.601655 | 0.213894 | -0.108364 | 0.466384 | 8.200581 | 0.098507 | 0.00624 | 0.101407 | 0.019433 | 1.029804 | 1.861024 | 3.014877 | -1.548182 | {'BE_STOP': 28, 'NO_ENTRY': 7631, 'SAME_BAR': 713, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1953, 'TIMEOUT': 2419, 'TP': 87} | 0.0 | 0.213894 | 957.601655 | -121.921318 | 0.193894 | 868.061655 | -125.561318 | 0.163894 | 733.751655 | -131.021318 | 0.113894 | 509.901655 | -142.224131 |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 23483 | 12831 | 3891 | 3884 | 731.530537 | 0.188345 | 0.0 | 0.476313 | 8.147528 | 0.318941 | 0.112824 | 0.07415 | 0.013903 | 0.975389 | 1.755434 | 2.64587 | -1.482079 | {'BE_STOP': 216, 'LOCK_STOP': 223, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1965, 'TP': 41} | 3e-12 | 0.188345 | 731.530537 | -139.052438 | 0.168345 | 653.850537 | -148.512438 | 0.138345 | 537.330537 | -162.702438 | 0.088345 | 343.130537 | -188.443787 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 23483 | 12831 | 3891 | 3884 | 744.039507 | 0.191565 | 0.164554 | 0.531926 | 7.734809 | 0.318941 | 0.177846 | 0.066684 | 0.009784 | 0.975389 | 1.695892 | 2.498677 | -1.477386 | {'LOCK_STOP': 692, 'NO_ENTRY': 7631, 'SAME_BAR': 1309, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1446, 'TIMEOUT': 1722, 'TP': 31} | 0.0 | 0.191565 | 744.039507 | -109.271251 | 0.171565 | 666.359507 | -119.531251 | 0.141565 | 549.839507 | -134.921251 | 0.091565 | 355.639507 | -160.571251 |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 23483 | 12831 | 3211 | 3206 | 466.501659 | 0.145509 | 0.0 | 0.482533 | 7.678104 | 0.47493 | 0.246652 | 0.056145 | 0.00811 | 0.901665 | 1.553687 | 2.279789 | -1.336221 | {'BE_STOP': 322, 'LOCK_STOP': 470, 'NO_ENTRY': 7631, 'SAME_BAR': 1989, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1057, 'TIMEOUT': 1343, 'TP': 19} | 5.8589e-07 | 0.145509 | 466.501659 | -86.781514 | 0.125509 | 402.381659 | -95.741514 | 0.095509 | 306.201659 | -109.181514 | 0.045509 | 145.901659 | -139.347879 |

## V0 M15 Variant Summary

| variant_id | family | actions_seen | setup_ok | entries_filled | resolved_n | gross_sum_r | gross_mean_r | gross_median_r | gross_win_rate | avg_bars_in_trade | lock_trigger_rate | lock_then_stop_rate | direct_3r_available_rate | direct_6r_available_rate | mfe_p50 | mfe_p75 | mfe_p90 | mae_p10 | outcomes | same_dataset_dsr_p_gross | net_mean_r_cost_0 | net_sum_r_cost_0 | net_max_drawdown_r_cost_0 | net_mean_r_cost_0.02 | net_sum_r_cost_0.02 | net_max_drawdown_r_cost_0.02 | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | net_max_drawdown_r_cost_0.05 | net_mean_r_cost_0.1 | net_sum_r_cost_0.1 | net_max_drawdown_r_cost_0.1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | 23483 | 12831 | 3499 | 3488 | 790.801045 | 0.22672 | 0.151992 | 0.503727 | 12.884461 | 0.0 | 0.0 | 0.008314 | 0.0 | 1.249367 | 1.657477 | 1.944544 | -1.675201 | {'NO_ENTRY': 7527, 'SAME_BAR': 1805, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1680, 'TIMEOUT': 262, 'TP': 1557} | 0.0 | 0.22672 | 790.801045 | -88.887538 | 0.20672 | 721.041045 | -91.147538 | 0.17672 | 616.401045 | -94.537538 | 0.12672 | 442.001045 | -100.187538 |
| J46_J49_ONLY | j46_j49 | 23483 | 12831 | 4259 | 4244 | 1019.104108 | 0.240128 | -0.01494 | 0.494581 | 8.540528 | 0.099554 | 0.003287 | 0.102733 | 0.014844 | 1.048405 | 1.864453 | 3.021435 | -1.686341 | {'BE_STOP': 14, 'NO_ENTRY': 7527, 'SAME_BAR': 1045, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1724, 'TIMEOUT': 2458, 'TP': 63} | 0.0 | 0.240128 | 1019.104108 | -95.711412 | 0.220128 | 934.224108 | -98.351412 | 0.190128 | 806.904108 | -112.974131 | 0.140128 | 594.704108 | -142.224131 |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 23483 | 12831 | 3476 | 3465 | 688.844097 | 0.198801 | 0.001589 | 0.500433 | 8.57518 | 0.313867 | 0.093211 | 0.078211 | 0.013276 | 0.960927 | 1.700397 | 2.607266 | -1.536606 | {'BE_STOP': 155, 'LOCK_STOP': 169, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1893, 'TP': 33} | 0.0 | 0.198801 | 688.844097 | -94.571897 | 0.178801 | 619.544097 | -102.451897 | 0.148801 | 515.594097 | -114.271897 | 0.098801 | 342.344097 | -133.971897 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 23483 | 12831 | 3476 | 3465 | 763.580802 | 0.22037 | 0.2123 | 0.545166 | 8.249062 | 0.313867 | 0.158228 | 0.077056 | 0.009524 | 0.960927 | 1.693573 | 2.569652 | -1.529412 | {'LOCK_STOP': 550, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1674, 'TP': 26} | 0.0 | 0.22037 | 763.580802 | -77.528686 | 0.20037 | 694.280802 | -85.408686 | 0.17037 | 590.330802 | -97.228686 | 0.12037 | 417.080802 | -116.928686 |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 23483 | 12831 | 2706 | 2697 | 435.557502 | 0.161497 | 0.0 | 0.497961 | 8.341861 | 0.447894 | 0.195861 | 0.056359 | 0.007786 | 0.776888 | 1.462752 | 2.290085 | -1.377804 | {'BE_STOP': 222, 'LOCK_STOP': 308, 'NO_ENTRY': 7527, 'SAME_BAR': 2598, 'SETUP_NOT_REFINABLE': 10652, 'SL': 860, 'TIMEOUT': 1302, 'TP': 14} | 1.29522e-07 | 0.161497 | 435.557502 | -83.376398 | 0.141497 | 381.617502 | -93.176398 | 0.111497 | 300.707502 | -107.876398 | 0.061497 | 165.857502 | -139.347879 |

## V0 Versus V1 Comparison

| variant_id | actions_seen | v0_resolved_n | v1_resolved_n | both_resolved_n | v0_same_bar | v1_same_bar | same_bar_resolved_by_mtf | same_bar_still_unresolved | v1_new_same_bar | same_bar_delta | outcome_changed | paired_gross_mean_delta_r | paired_gross_sum_delta_r | selected_timeframes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | 23483 | 3488 | 3898 | 3429 | 1805 | 1295 | 469 | 1295 | 0 | -510 | 686 | 0.00653 | 22.391901 | {'M1': 774, 'M15': 17971, 'M5': 4738} |
| J46_J49_ONLY | 23483 | 4244 | 4477 | 4178 | 1045 | 713 | 299 | 713 | 0 | -332 | 1237 | 0.014509 | 60.619075 | {'M1': 774, 'M15': 17971, 'M5': 4738} |
| PATH_LOCK_CONSERVATIVE_V0 | 23483 | 3465 | 3884 | 3406 | 1828 | 1309 | 478 | 1309 | 0 | -519 | 1250 | 0.009171 | 31.236823 | {'M1': 774, 'M15': 17971, 'M5': 4738} |
| PATH_LOCK_HALF_GAIN_V0 | 23483 | 3465 | 3884 | 3406 | 1828 | 1309 | 478 | 1309 | 0 | -519 | 1162 | 0.01089 | 37.089984 | {'M1': 774, 'M15': 17971, 'M5': 4738} |
| PATH_LOCK_EARLY_BE_V0 | 23483 | 2697 | 3206 | 2672 | 2598 | 1989 | 534 | 1989 | 0 | -609 | 1085 | -0.004349 | -11.619705 | {'M1': 774, 'M15': 17971, 'M5': 4738} |

## V1 Group Summary

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

## Group Delta Summary

| variant_id | group | v0_resolved_n | v1_resolved_n | resolved_n_delta | v0_net_mean_r_cost_0.05 | v1_net_mean_r_cost_0.05 | net_mean_delta_cost_0.05 | v0_same_bar | v1_same_bar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | all_enabled | 3488 | 3898 | 410 | 0.17672 | 0.156545 | -0.020175 | 1805 | 1295 |
| BASE_RAW_FIXED_TP | all_excluding_gbpusd_control | 2900 | 3228 | 328 | 0.246748 | 0.230789 | -0.015959 | 1641 | 1213 |
| BASE_RAW_FIXED_TP | target_cohorts | 1222 | 1270 | 48 | 0.358979 | 0.35674 | -0.002239 | 333 | 260 |
| BASE_RAW_FIXED_TP | primary_controlled_family | 576 | 596 | 20 | 0.327031 | 0.343097 | 0.016066 | 168 | 138 |
| BASE_RAW_FIXED_TP | cleared_non_primary_targets | 646 | 674 | 28 | 0.387465 | 0.368804 | -0.018661 | 165 | 122 |
| BASE_RAW_FIXED_TP | negative_controls | 1274 | 1426 | 152 | -0.115199 | -0.152844 | -0.037645 | 471 | 319 |
| BASE_RAW_FIXED_TP | blocked_dominance_controls | 992 | 1202 | 210 | 0.327109 | 0.31207 | -0.015039 | 1001 | 716 |
| J46_J49_ONLY | all_enabled | 4244 | 4477 | 233 | 0.190128 | 0.163894 | -0.026234 | 1045 | 713 |
| J46_J49_ONLY | all_excluding_gbpusd_control | 3591 | 3762 | 171 | 0.243152 | 0.229402 | -0.01375 | 946 | 676 |
| J46_J49_ONLY | target_cohorts | 1398 | 1406 | 8 | 0.454167 | 0.409292 | -0.044875 | 156 | 123 |
| J46_J49_ONLY | primary_controlled_family | 670 | 674 | 4 | 0.420624 | 0.395481 | -0.025143 | 74 | 60 |
| J46_J49_ONLY | cleared_non_primary_targets | 728 | 732 | 4 | 0.485039 | 0.422008 | -0.063031 | 82 | 63 |
| J46_J49_ONLY | negative_controls | 1428 | 1518 | 90 | -0.117349 | -0.150354 | -0.033005 | 317 | 227 |
| J46_J49_ONLY | blocked_dominance_controls | 1418 | 1553 | 135 | 0.239459 | 0.248889 | 0.00943 | 572 | 363 |
| PATH_LOCK_CONSERVATIVE_V0 | all_enabled | 3465 | 3884 | 419 | 0.148801 | 0.138345 | -0.010456 | 1828 | 1309 |
| PATH_LOCK_CONSERVATIVE_V0 | all_excluding_gbpusd_control | 2877 | 3214 | 337 | 0.202192 | 0.205819 | 0.003627 | 1664 | 1227 |
| PATH_LOCK_CONSERVATIVE_V0 | target_cohorts | 1222 | 1270 | 48 | 0.448671 | 0.472889 | 0.024218 | 333 | 260 |
| PATH_LOCK_CONSERVATIVE_V0 | primary_controlled_family | 576 | 596 | 20 | 0.36712 | 0.423483 | 0.056363 | 168 | 138 |
| PATH_LOCK_CONSERVATIVE_V0 | cleared_non_primary_targets | 646 | 674 | 28 | 0.521385 | 0.516576 | -0.004809 | 165 | 122 |
| PATH_LOCK_CONSERVATIVE_V0 | negative_controls | 1274 | 1426 | 152 | -0.108947 | -0.169888 | -0.060941 | 471 | 319 |
| PATH_LOCK_CONSERVATIVE_V0 | blocked_dominance_controls | 969 | 1188 | 219 | 0.109512 | 0.150692 | 0.04118 | 1024 | 730 |
| PATH_LOCK_HALF_GAIN_V0 | all_enabled | 3465 | 3884 | 419 | 0.17037 | 0.141565 | -0.028805 | 1828 | 1309 |
| PATH_LOCK_HALF_GAIN_V0 | all_excluding_gbpusd_control | 2877 | 3214 | 337 | 0.225625 | 0.203533 | -0.022092 | 1664 | 1227 |
| PATH_LOCK_HALF_GAIN_V0 | target_cohorts | 1222 | 1270 | 48 | 0.463278 | 0.439021 | -0.024257 | 333 | 260 |
| PATH_LOCK_HALF_GAIN_V0 | primary_controlled_family | 576 | 596 | 20 | 0.320715 | 0.32881 | 0.008095 | 168 | 138 |
| PATH_LOCK_HALF_GAIN_V0 | cleared_non_primary_targets | 646 | 674 | 28 | 0.590393 | 0.536477 | -0.053916 | 165 | 122 |
| PATH_LOCK_HALF_GAIN_V0 | negative_controls | 1274 | 1426 | 152 | -0.112927 | -0.16443 | -0.051503 | 471 | 319 |
| PATH_LOCK_HALF_GAIN_V0 | blocked_dominance_controls | 969 | 1188 | 219 | 0.173452 | 0.190875 | 0.017423 | 1024 | 730 |
| PATH_LOCK_EARLY_BE_V0 | all_enabled | 2697 | 3206 | 509 | 0.111497 | 0.095509 | -0.015988 | 2598 | 1989 |
| PATH_LOCK_EARLY_BE_V0 | all_excluding_gbpusd_control | 2170 | 2627 | 457 | 0.205237 | 0.19171 | -0.013527 | 2373 | 1816 |
| PATH_LOCK_EARLY_BE_V0 | target_cohorts | 981 | 1113 | 132 | 0.487573 | 0.427437 | -0.060136 | 574 | 417 |
| PATH_LOCK_EARLY_BE_V0 | primary_controlled_family | 459 | 537 | 78 | 0.297256 | 0.259229 | -0.038027 | 285 | 197 |
| PATH_LOCK_EARLY_BE_V0 | cleared_non_primary_targets | 522 | 576 | 54 | 0.65492 | 0.584256 | -0.070664 | 289 | 220 |
| PATH_LOCK_EARLY_BE_V0 | negative_controls | 1076 | 1229 | 153 | -0.179204 | -0.236156 | -0.056952 | 670 | 517 |
| PATH_LOCK_EARLY_BE_V0 | blocked_dominance_controls | 640 | 864 | 224 | 0.023785 | 0.1397 | 0.115915 | 1354 | 1055 |

## V1 Cohort Summary

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

## Cohort Delta Summary

| variant_id | cohort_key | role | v0_resolved_n | v1_resolved_n | resolved_n_delta | v0_net_mean_r_cost_0.05 | v1_net_mean_r_cost_0.05 | net_mean_delta_cost_0.05 | v0_same_bar | v1_same_bar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 394 | 8 | 0.3507 | 0.340319 | -0.010381 | 105 | 87 |
| BASE_RAW_FIXED_TP | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | 670 | 82 | -0.168655 | -0.201155 | -0.0325 | 164 | 82 |
| BASE_RAW_FIXED_TP | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 468 | 575 | 107 | 0.224765 | 0.280513 | 0.055748 | 494 | 368 |
| BASE_RAW_FIXED_TP | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 138 | 179 | 41 | 0.412074 | 0.216851 | -0.195223 | 289 | 248 |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 139 | 10 | 0.461628 | 0.532734 | 0.071106 | 46 | 36 |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bullish\|D1 | negative_control | 306 | 332 | 26 | -0.055699 | -0.033792 | 0.021907 | 127 | 101 |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 202 | 12 | 0.278947 | 0.348515 | 0.069568 | 63 | 51 |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 231 | 19 | 0.422689 | 0.340185 | -0.082504 | 55 | 36 |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | 424 | 44 | -0.080396 | -0.169724 | -0.089328 | 180 | 136 |
| BASE_RAW_FIXED_TP | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 304 | -1 | 0.331615 | 0.315595 | -0.01602 | 64 | 50 |
| BASE_RAW_FIXED_TP | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 386 | 448 | 62 | 0.420817 | 0.390617 | -0.0302 | 218 | 100 |
| J46_J49_ONLY | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 451 | 455 | 4 | 0.142789 | 0.114197 | -0.028592 | 40 | 26 |
| J46_J49_ONLY | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 653 | 715 | 62 | -0.101461 | -0.180781 | -0.07932 | 99 | 37 |
| J46_J49_ONLY | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 708 | 775 | 67 | 0.270838 | 0.29423 | 0.023392 | 252 | 166 |
| J46_J49_ONLY | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 259 | 298 | 39 | 0.215424 | 0.047095 | -0.168329 | 168 | 129 |
| J46_J49_ONLY | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 149 | 149 | 0 | 1.063312 | 1.058757 | -0.004555 | 26 | 26 |
| J46_J49_ONLY | USDJPY\|london\|bullish\|D1 | negative_control | 330 | 346 | 16 | -0.071896 | -0.013785 | 0.058111 | 103 | 87 |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 219 | 219 | 0 | 0.992785 | 0.979884 | -0.012901 | 34 | 34 |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 240 | 257 | 17 | 0.055966 | -0.013233 | -0.069199 | 26 | 9 |
| J46_J49_ONLY | USDJPY\|tokyo\|bullish\|D1 | negative_control | 445 | 457 | 12 | -0.17437 | -0.206147 | -0.031777 | 115 | 103 |
| J46_J49_ONLY | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 339 | 326 | -13 | 0.534639 | 0.4741 | -0.060539 | 30 | 28 |
| J46_J49_ONLY | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 451 | 480 | 29 | 0.204001 | 0.300963 | 0.096962 | 152 | 68 |
| PATH_LOCK_CONSERVATIVE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 394 | 8 | 0.228654 | 0.224052 | -0.004602 | 105 | 87 |
| PATH_LOCK_CONSERVATIVE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | 670 | 82 | -0.112436 | -0.18533 | -0.072894 | 164 | 82 |
| PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 464 | 571 | 107 | -0.077941 | 0.026533 | 0.104474 | 498 | 372 |
| PATH_LOCK_CONSERVATIVE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 128 | 169 | 41 | 0.256899 | 0.033788 | -0.223111 | 299 | 258 |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 139 | 10 | 0.455046 | 0.695596 | 0.24055 | 46 | 36 |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 306 | 332 | 26 | -0.067801 | -0.055567 | 0.012234 | 127 | 101 |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 202 | 12 | 0.648424 | 0.812474 | 0.16405 | 63 | 51 |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 231 | 19 | 0.336628 | 0.273121 | -0.063507 | 55 | 36 |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | 424 | 44 | -0.136681 | -0.235002 | -0.098321 | 180 | 136 |
| PATH_LOCK_CONSERVATIVE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 304 | -1 | 0.677864 | 0.619715 | -0.058149 | 64 | 50 |
| PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 377 | 448 | 71 | 0.290182 | 0.35304 | 0.062858 | 227 | 100 |
| PATH_LOCK_HALF_GAIN_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 394 | 8 | 0.241138 | 0.258233 | 0.017095 | 105 | 87 |
| PATH_LOCK_HALF_GAIN_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | 670 | 82 | -0.099988 | -0.155693 | -0.055705 | 164 | 82 |
| PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 464 | 571 | 107 | -0.000576 | 0.059613 | 0.060189 | 498 | 372 |
| PATH_LOCK_HALF_GAIN_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 128 | 169 | 41 | 0.297655 | 0.069986 | -0.227669 | 299 | 258 |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 139 | 10 | 0.607412 | 0.591204 | -0.016208 | 46 | 36 |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 306 | 332 | 26 | -0.058927 | -0.055241 | 0.003686 | 127 | 101 |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 202 | 12 | 0.482383 | 0.466471 | -0.015912 | 63 | 51 |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 231 | 19 | 0.454982 | 0.38174 | -0.073242 | 55 | 36 |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | 424 | 44 | -0.176434 | -0.263731 | -0.087297 | 180 | 136 |
| PATH_LOCK_HALF_GAIN_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 304 | -1 | 0.677316 | 0.629033 | -0.048283 | 64 | 50 |
| PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 377 | 448 | 71 | 0.345471 | 0.403779 | 0.058308 | 227 | 100 |
| PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 287 | 347 | 60 | 0.177249 | 0.153132 | -0.024117 | 204 | 134 |
| PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 527 | 579 | 52 | -0.27449 | -0.340967 | -0.066477 | 225 | 173 |
| PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 302 | 423 | 121 | -0.144432 | -0.035405 | 0.109027 | 660 | 520 |
| PATH_LOCK_EARLY_BE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 94 | 133 | 39 | -0.060764 | 0.068855 | 0.129619 | 333 | 294 |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 114 | 124 | 10 | 0.636896 | 0.61635 | -0.020546 | 61 | 51 |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 238 | 280 | 42 | -0.057794 | -0.063847 | -0.006053 | 196 | 154 |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 172 | 190 | 18 | 0.497499 | 0.452995 | -0.044504 | 81 | 63 |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 157 | 174 | 17 | 0.492519 | 0.410609 | -0.08191 | 110 | 93 |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 311 | 370 | 59 | -0.110651 | -0.202539 | -0.091888 | 249 | 190 |
| PATH_LOCK_EARLY_BE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 251 | 278 | 27 | 0.764688 | 0.678626 | -0.086062 | 118 | 76 |
| PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 244 | 308 | 64 | 0.264559 | 0.410777 | 0.146218 | 361 | 241 |

## Conclusion Changes

| scope | v0_best_variant | v0_best_net_mean_r_cost_0.05 | v1_best_variant | v1_best_net_mean_r_cost_0.05 | lock_vs_j46_sign_changed | group | cohort_key | role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group | PATH_LOCK_CONSERVATIVE_V0 | -0.108947 | J46_J49_ONLY | -0.150354 | True | negative_controls |  |  |
| group | J46_J49_ONLY | 0.420624 | PATH_LOCK_CONSERVATIVE_V0 | 0.423483 | True | primary_controlled_family |  |  |
| group | PATH_LOCK_EARLY_BE_V0 | 0.487573 | PATH_LOCK_CONSERVATIVE_V0 | 0.472889 | False | target_cohorts |  |  |
| cohort | BASE_RAW_FIXED_TP | -0.055699 | J46_J49_ONLY | -0.013785 | True |  | USDJPY\|london\|bullish\|D1 | negative_control |
| cohort | BASE_RAW_FIXED_TP | 0.420817 | PATH_LOCK_EARLY_BE_V0 | 0.410777 | False |  | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist |

## Methodology Diagnostics

| exit_policy_pbo | pbo_status | pbo_promotion_usable | exit_policy_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- |
| 0.358974 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | False | 1.501323 | False |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Cost model | SENSITIVITY_NOT_MEASURED_COST | Historical OHLC does not contain reliable commission/spread/slippage. Report uses R-cost sensitivity. |
| Lower-timeframe coverage | QUANTIFIED | M1 windows=774, M5 windows=5512, M15 fallback windows=7319. |
| Post-decision lower-TF start | PASS | Lower-timeframe rows with close_time <= setup decision clock: 0. |
| Remaining same-bar ambiguity | REMAINS_QUANTIFIED | V1 same-bar unresolved policy-event rows: 6615. These are inside the selected M1/M5/M15 bar. |
| Reentry | INTENTIONALLY_BLOCKED | No reentry is tested in V1. Risk-budgeted reentry remains V3-only. |
| L2 attribution | NOT_IMPLEMENTED_IN_V1 | V1 preserves V0's raw cohort stream and does not reconstruct deterministic L2. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical raw-OHLC MTF path-resolution ablation. |

## Opened Questions

| question | status | detail |
| --- | --- | --- |
| Are remaining same-bar cases material enough to block V2? | OPEN | Remaining V1 same-bar policy-event rows: 6615. |
| Does lower-timeframe coverage create a cohort comparability problem? | OPEN | Selected timeframe mix: {'M1': 774, 'M15': 7319, 'M5': 4738}. Any V2 structural-level run must preserve this coverage ledger. |
| Did MTF resolution change the interpretation of any cohort? | OPEN | Conclusion change rows detected: 5. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Review remaining same-bar rows from the V1 event log | V2 should not start if unresolved ordering is concentrated in a decision-critical cohort or variant. |
| 2 | Review conclusion-change rows | Any cohort where MTF changes the best variant or lock-vs-J46 sign needs explicit synthesis before V2. |
| 3 | Only then decide whether V1 ambiguity is cleared for V2 structural levels | The next layer should inherit a stable path-resolution measurement layer, not fix V1 retroactively. |

## Synthesis

- V1 is a path-ordering measurement layer, not a new strategy or promotion dossier.
- The decision stream and exit levels are inherited from V0; lower timeframes only resolve post-decision path order where available.
- V2 should not begin until the ambiguity ledger and conclusion-change rows are reviewed.
