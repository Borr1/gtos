# Phase 3 Raw-OHLC Architecture Ablation And Path-Scaling V0

**Created UTC:** 2026-05-01T16:01:50.384730+00:00
**Replay spec:** `research\phase_3_external_feed_validation\RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`
**Ablation spec:** `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_SPEC_V1.json`
**Ablation protocol:** `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_AND_PATH_SCALING_PROTOCOL_2026-05-01.md`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- V0 uses the same raw-OHLC no-leak candidate reconstruction as the prequential replay.
- Outcomes are attached only after the cohort decision is locked.
- Costs are reported as R-per-round-turn sensitivity because reliable historical commission/spread/slippage is not present in OHLC.
- Reentry and L2-on/off attribution are intentionally blocked in V0.

## Run Scope

| source_scope | rows_replayed | take_rows_seen | setup_ok_rows | path_timeframe | include_blocked_controls | first_take_clock | last_take_clock |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FULL_AVAILABLE_CORPUS | 205197 | 23483 | 12831 | M15 | True | 2022-02-07T13:30:00+00:00 | 2026-04-30T17:00:00+00:00 |

## Cost Model

| unit | cost_scenarios_r | actual_commission_spread_source | reentry_cost_note |
| --- | --- | --- | --- |
| R per completed round turn | [0.0, 0.02, 0.05, 0.1] | not reliably available in historical OHLC; reported as sensitivity, not measured cost | V0 has no reentries; future reentry variants must charge one additional round turn per reentry. |

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
| Which variant leads on gross mean R? | J46_J49_ONLY with gross_mean_r=0.240128. |
| Which variant leads after a 0.05R round-turn cost sensitivity? | J46_J49_ONLY with net_mean_r_cost_0.05=0.190128. |
| Did lock-only V0 beat J46-J49 in this diagnostic? | Best lock-only net-minus-J46 at 0.05R cost = -0.019758. This is same-dataset diagnostic evidence only. |
| What was the main tradeoff? | BASE_RAW_FIXED_TP had the shallowest reported 0.05R-cost max drawdown (-94.537538R), while J46-J49 kept the best mean R. The lock-only family improved some win-rate/median behavior but did not beat J46-J49 overall. |
| Where did lock-only look most interesting? | Target-family best-lock minus J46 at 0.05R cost = 0.033406; primary-family delta = -0.053504; cleared-non-primary delta = 0.169881. This suggests the lock ladder may be cohort-sensitive, not universally better. |
| What was the biggest unresolved measurement issue? | PATH_LOCK_EARLY_BE_V0 created the most same-bar unresolved cases (2598). That keeps lower-timeframe path refinement on the critical path before reentry is trusted. |
| Does this promote an exit policy? | No. This is same-dataset historical ablation and remains NO_PROMOTION_VERDICT. |

## Variant Summary

| variant_id | family | actions_seen | setup_ok | entries_filled | resolved_n | gross_sum_r | gross_mean_r | gross_median_r | gross_win_rate | avg_bars_in_trade | lock_trigger_rate | lock_then_stop_rate | direct_3r_available_rate | direct_6r_available_rate | mfe_p50 | mfe_p75 | mfe_p90 | mae_p10 | outcomes | same_dataset_dsr_p_gross | net_mean_r_cost_0 | net_sum_r_cost_0 | net_max_drawdown_r_cost_0 | net_mean_r_cost_0.02 | net_sum_r_cost_0.02 | net_max_drawdown_r_cost_0.02 | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | net_max_drawdown_r_cost_0.05 | net_mean_r_cost_0.1 | net_sum_r_cost_0.1 | net_max_drawdown_r_cost_0.1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | baseline | 23483 | 12831 | 3499 | 3488 | 790.801045 | 0.22672 | 0.151992 | 0.503727 | 12.884461 | 0.0 | 0.0 | 0.008314 | 0.0 | 1.249367 | 1.657477 | 1.944544 | -1.675201 | {'NO_ENTRY': 7527, 'SAME_BAR': 1805, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1680, 'TIMEOUT': 262, 'TP': 1557} | 0.0 | 0.22672 | 790.801045 | -88.887538 | 0.20672 | 721.041045 | -91.147538 | 0.17672 | 616.401045 | -94.537538 | 0.12672 | 442.001045 | -100.187538 |
| J46_J49_ONLY | j46_j49 | 23483 | 12831 | 4259 | 4244 | 1019.104108 | 0.240128 | -0.01494 | 0.494581 | 8.540528 | 0.099554 | 0.003287 | 0.102733 | 0.014844 | 1.048405 | 1.864453 | 3.021435 | -1.686341 | {'BE_STOP': 14, 'NO_ENTRY': 7527, 'SAME_BAR': 1045, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1724, 'TIMEOUT': 2458, 'TP': 63} | 0.0 | 0.240128 | 1019.104108 | -95.711412 | 0.220128 | 934.224108 | -98.351412 | 0.190128 | 806.904108 | -112.974131 | 0.140128 | 594.704108 | -142.224131 |
| PATH_LOCK_CONSERVATIVE_V0 | path_lock_only | 23483 | 12831 | 3476 | 3465 | 688.844097 | 0.198801 | 0.001589 | 0.500433 | 8.57518 | 0.313867 | 0.093211 | 0.078211 | 0.013276 | 0.960927 | 1.700397 | 2.607266 | -1.536606 | {'BE_STOP': 155, 'LOCK_STOP': 169, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1893, 'TP': 33} | 0.0 | 0.198801 | 688.844097 | -94.571897 | 0.178801 | 619.544097 | -102.451897 | 0.148801 | 515.594097 | -114.271897 | 0.098801 | 342.344097 | -133.971897 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 23483 | 12831 | 3476 | 3465 | 763.580802 | 0.22037 | 0.2123 | 0.545166 | 8.249062 | 0.313867 | 0.158228 | 0.077056 | 0.009524 | 0.960927 | 1.693573 | 2.569652 | -1.529412 | {'LOCK_STOP': 550, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1674, 'TP': 26} | 0.0 | 0.22037 | 763.580802 | -77.528686 | 0.20037 | 694.280802 | -85.408686 | 0.17037 | 590.330802 | -97.228686 | 0.12037 | 417.080802 | -116.928686 |
| PATH_LOCK_EARLY_BE_V0 | path_lock_only | 23483 | 12831 | 2706 | 2697 | 435.557502 | 0.161497 | 0.0 | 0.497961 | 8.341861 | 0.447894 | 0.195861 | 0.056359 | 0.007786 | 0.776888 | 1.462752 | 2.290085 | -1.377804 | {'BE_STOP': 222, 'LOCK_STOP': 308, 'NO_ENTRY': 7527, 'SAME_BAR': 2598, 'SETUP_NOT_REFINABLE': 10652, 'SL': 860, 'TIMEOUT': 1302, 'TP': 14} | 1.29522e-07 | 0.161497 | 435.557502 | -83.376398 | 0.141497 | 381.617502 | -93.176398 | 0.111497 | 300.707502 | -107.876398 | 0.061497 | 165.857502 | -139.347879 |

## Group Summary

| variant_id | group | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | all_enabled | 3488 | 0.22672 | 0.17672 | 790.801045 | 616.401045 | 0.503727 | 0.0 | {'NO_ENTRY': 7527, 'SAME_BAR': 1805, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1680, 'TIMEOUT': 262, 'TP': 1557} |
| BASE_RAW_FIXED_TP | all_excluding_gbpusd_control | 2900 | 0.296748 | 0.246748 | 860.569975 | 715.569975 | 0.53 | 0.0 | {'NO_ENTRY': 6647, 'SAME_BAR': 1641, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1327, 'TIMEOUT': 204, 'TP': 1379} |
| BASE_RAW_FIXED_TP | target_cohorts | 1222 | 0.408979 | 0.358979 | 499.772596 | 438.672596 | 0.575286 | 0.0 | {'NO_ENTRY': 2584, 'SAME_BAR': 333, 'SETUP_NOT_REFINABLE': 4081, 'SL': 501, 'TIMEOUT': 85, 'TP': 638} |
| BASE_RAW_FIXED_TP | primary_controlled_family | 576 | 0.377031 | 0.327031 | 217.170019 | 188.370019 | 0.565972 | 0.0 | {'NO_ENTRY': 1084, 'SAME_BAR': 168, 'SETUP_NOT_REFINABLE': 2257, 'SL': 241, 'TIMEOUT': 48, 'TP': 288} |
| BASE_RAW_FIXED_TP | cleared_non_primary_targets | 646 | 0.437465 | 0.387465 | 282.602577 | 250.302577 | 0.583591 | 0.0 | {'NO_ENTRY': 1500, 'SAME_BAR': 165, 'SETUP_NOT_REFINABLE': 1824, 'SL': 260, 'TIMEOUT': 37, 'TP': 350} |
| BASE_RAW_FIXED_TP | negative_controls | 1274 | -0.065199 | -0.115199 | -83.063184 | -146.763184 | 0.39325 | 0.0 | {'NO_ENTRY': 2021, 'SAME_BAR': 471, 'SETUP_NOT_REFINABLE': 3836, 'SL': 752, 'TIMEOUT': 104, 'TP': 421} |
| BASE_RAW_FIXED_TP | blocked_dominance_controls | 992 | 0.377109 | 0.327109 | 374.091633 | 324.491633 | 0.55746 | 0.0 | {'NO_ENTRY': 2922, 'SAME_BAR': 1001, 'SETUP_NOT_REFINABLE': 2735, 'SL': 427, 'TIMEOUT': 73, 'TP': 498} |
| J46_J49_ONLY | all_enabled | 4244 | 0.240128 | 0.190128 | 1019.104108 | 806.904108 | 0.494581 | 0.099554 | {'BE_STOP': 14, 'NO_ENTRY': 7527, 'SAME_BAR': 1045, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1724, 'TIMEOUT': 2458, 'TP': 63} |
| J46_J49_ONLY | all_excluding_gbpusd_control | 3591 | 0.293152 | 0.243152 | 1052.708174 | 873.158174 | 0.515177 | 0.108183 | {'BE_STOP': 7, 'NO_ENTRY': 6647, 'SAME_BAR': 946, 'SETUP_NOT_REFINABLE': 10400, 'SL': 1405, 'TIMEOUT': 2140, 'TP': 53} |
| J46_J49_ONLY | target_cohorts | 1398 | 0.504167 | 0.454167 | 704.826003 | 634.926003 | 0.583691 | 0.133476 | {'NO_ENTRY': 2584, 'SAME_BAR': 156, 'SETUP_NOT_REFINABLE': 4081, 'SL': 431, 'TIMEOUT': 936, 'TP': 34} |
| J46_J49_ONLY | primary_controlled_family | 670 | 0.470624 | 0.420624 | 315.317813 | 281.817813 | 0.620896 | 0.102832 | {'NO_ENTRY': 1084, 'SAME_BAR': 74, 'SETUP_NOT_REFINABLE': 2257, 'SL': 172, 'TIMEOUT': 489, 'TP': 10} |
| J46_J49_ONLY | cleared_non_primary_targets | 728 | 0.535039 | 0.485039 | 389.50819 | 353.10819 | 0.549451 | 0.161644 | {'NO_ENTRY': 1500, 'SAME_BAR': 82, 'SETUP_NOT_REFINABLE': 1824, 'SL': 259, 'TIMEOUT': 447, 'TP': 24} |
| J46_J49_ONLY | negative_controls | 1428 | -0.067349 | -0.117349 | -96.174692 | -167.574692 | 0.428571 | 0.02935 | {'BE_STOP': 7, 'NO_ENTRY': 2021, 'SAME_BAR': 317, 'SETUP_NOT_REFINABLE': 3836, 'SL': 661, 'TIMEOUT': 753, 'TP': 10} |
| J46_J49_ONLY | blocked_dominance_controls | 1418 | 0.289459 | 0.239459 | 410.452797 | 339.552797 | 0.473202 | 0.13665 | {'BE_STOP': 7, 'NO_ENTRY': 2922, 'SAME_BAR': 572, 'SETUP_NOT_REFINABLE': 2735, 'SL': 632, 'TIMEOUT': 769, 'TP': 19} |
| PATH_LOCK_CONSERVATIVE_V0 | all_enabled | 3465 | 0.198801 | 0.148801 | 688.844097 | 515.594097 | 0.500433 | 0.313867 | {'BE_STOP': 155, 'LOCK_STOP': 169, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1893, 'TP': 33} |
| PATH_LOCK_CONSERVATIVE_V0 | all_excluding_gbpusd_control | 2877 | 0.252192 | 0.202192 | 725.556702 | 581.706702 | 0.530414 | 0.339106 | {'BE_STOP': 151, 'LOCK_STOP': 162, 'NO_ENTRY': 6647, 'SAME_BAR': 1664, 'SETUP_NOT_REFINABLE': 10400, 'SL': 925, 'TIMEOUT': 1626, 'TP': 23} |
| PATH_LOCK_CONSERVATIVE_V0 | target_cohorts | 1222 | 0.498671 | 0.448671 | 609.37566 | 548.27566 | 0.599018 | 0.371732 | {'BE_STOP': 75, 'LOCK_STOP': 69, 'NO_ENTRY': 2584, 'SAME_BAR': 333, 'SETUP_NOT_REFINABLE': 4081, 'SL': 283, 'TIMEOUT': 776, 'TP': 21} |
| PATH_LOCK_CONSERVATIVE_V0 | primary_controlled_family | 576 | 0.41712 | 0.36712 | 240.261 | 211.461 | 0.616319 | 0.298094 | {'BE_STOP': 14, 'LOCK_STOP': 17, 'NO_ENTRY': 1084, 'SAME_BAR': 168, 'SETUP_NOT_REFINABLE': 2257, 'SL': 127, 'TIMEOUT': 412, 'TP': 7} |
| PATH_LOCK_CONSERVATIVE_V0 | cleared_non_primary_targets | 646 | 0.571385 | 0.521385 | 369.11466 | 336.81466 | 0.583591 | 0.437403 | {'BE_STOP': 61, 'LOCK_STOP': 52, 'NO_ENTRY': 1500, 'SAME_BAR': 165, 'SETUP_NOT_REFINABLE': 1824, 'SL': 156, 'TIMEOUT': 364, 'TP': 14} |
| PATH_LOCK_CONSERVATIVE_V0 | negative_controls | 1274 | -0.058947 | -0.108947 | -75.098427 | -138.798427 | 0.419152 | 0.20047 | {'BE_STOP': 21, 'LOCK_STOP': 14, 'NO_ENTRY': 2021, 'SAME_BAR': 471, 'SETUP_NOT_REFINABLE': 3836, 'SL': 580, 'TIMEOUT': 652, 'TP': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | blocked_dominance_controls | 969 | 0.159512 | 0.109512 | 154.566864 | 106.116864 | 0.482972 | 0.389744 | {'BE_STOP': 59, 'LOCK_STOP': 86, 'NO_ENTRY': 2922, 'SAME_BAR': 1024, 'SETUP_NOT_REFINABLE': 2735, 'SL': 363, 'TIMEOUT': 465, 'TP': 2} |
| PATH_LOCK_HALF_GAIN_V0 | all_enabled | 3465 | 0.22037 | 0.17037 | 763.580802 | 590.330802 | 0.545166 | 0.313867 | {'LOCK_STOP': 550, 'NO_ENTRY': 7527, 'SAME_BAR': 1828, 'SETUP_NOT_REFINABLE': 10652, 'SL': 1226, 'TIMEOUT': 1674, 'TP': 26} |
| PATH_LOCK_HALF_GAIN_V0 | all_excluding_gbpusd_control | 2877 | 0.275625 | 0.225625 | 792.973705 | 649.123705 | 0.582899 | 0.339106 | {'LOCK_STOP': 518, 'NO_ENTRY': 6647, 'SAME_BAR': 1664, 'SETUP_NOT_REFINABLE': 10400, 'SL': 925, 'TIMEOUT': 1428, 'TP': 16} |
| PATH_LOCK_HALF_GAIN_V0 | target_cohorts | 1222 | 0.513278 | 0.463278 | 627.22553 | 566.12553 | 0.660393 | 0.371732 | {'LOCK_STOP': 217, 'NO_ENTRY': 2584, 'SAME_BAR': 333, 'SETUP_NOT_REFINABLE': 4081, 'SL': 283, 'TIMEOUT': 710, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | primary_controlled_family | 576 | 0.370715 | 0.320715 | 213.531973 | 184.731973 | 0.640625 | 0.298094 | {'LOCK_STOP': 80, 'NO_ENTRY': 1084, 'SAME_BAR': 168, 'SETUP_NOT_REFINABLE': 2257, 'SL': 127, 'TIMEOUT': 370} |
| PATH_LOCK_HALF_GAIN_V0 | cleared_non_primary_targets | 646 | 0.640393 | 0.590393 | 413.693557 | 381.393557 | 0.678019 | 0.437403 | {'LOCK_STOP': 137, 'NO_ENTRY': 1500, 'SAME_BAR': 165, 'SETUP_NOT_REFINABLE': 1824, 'SL': 156, 'TIMEOUT': 340, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | negative_controls | 1274 | -0.062927 | -0.112927 | -80.169616 | -143.869616 | 0.435636 | 0.20047 | {'LOCK_STOP': 119, 'NO_ENTRY': 2021, 'SAME_BAR': 471, 'SETUP_NOT_REFINABLE': 3836, 'SL': 580, 'TIMEOUT': 568, 'TP': 10} |
| PATH_LOCK_HALF_GAIN_V0 | blocked_dominance_controls | 969 | 0.223452 | 0.173452 | 216.524888 | 168.074888 | 0.54386 | 0.389744 | {'LOCK_STOP': 214, 'NO_ENTRY': 2922, 'SAME_BAR': 1024, 'SETUP_NOT_REFINABLE': 2735, 'SL': 363, 'TIMEOUT': 396, 'TP': 2} |
| PATH_LOCK_EARLY_BE_V0 | all_enabled | 2697 | 0.161497 | 0.111497 | 435.557502 | 300.707502 | 0.497961 | 0.447894 | {'BE_STOP': 222, 'LOCK_STOP': 308, 'NO_ENTRY': 7527, 'SAME_BAR': 2598, 'SETUP_NOT_REFINABLE': 10652, 'SL': 860, 'TIMEOUT': 1302, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | all_excluding_gbpusd_control | 2170 | 0.255237 | 0.205237 | 553.863654 | 445.363654 | 0.540553 | 0.488522 | {'BE_STOP': 195, 'LOCK_STOP': 279, 'NO_ENTRY': 6647, 'SAME_BAR': 2373, 'SETUP_NOT_REFINABLE': 10400, 'SL': 584, 'TIMEOUT': 1106, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | target_cohorts | 981 | 0.537573 | 0.487573 | 527.358791 | 478.308791 | 0.658512 | 0.55646 | {'BE_STOP': 55, 'LOCK_STOP': 146, 'NO_ENTRY': 2584, 'SAME_BAR': 574, 'SETUP_NOT_REFINABLE': 4081, 'SL': 169, 'TIMEOUT': 599, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | primary_controlled_family | 459 | 0.347256 | 0.297256 | 159.390334 | 136.440334 | 0.638344 | 0.497826 | {'BE_STOP': 32, 'LOCK_STOP': 58, 'NO_ENTRY': 1084, 'SAME_BAR': 285, 'SETUP_NOT_REFINABLE': 2257, 'SL': 71, 'TIMEOUT': 299} |
| PATH_LOCK_EARLY_BE_V0 | cleared_non_primary_targets | 522 | 0.70492 | 0.65492 | 367.968457 | 341.868457 | 0.676245 | 0.608031 | {'BE_STOP': 23, 'LOCK_STOP': 88, 'NO_ENTRY': 1500, 'SAME_BAR': 289, 'SETUP_NOT_REFINABLE': 1824, 'SL': 98, 'TIMEOUT': 300, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | negative_controls | 1076 | -0.129204 | -0.179204 | -139.023419 | -192.823419 | 0.388476 | 0.326531 | {'BE_STOP': 79, 'LOCK_STOP': 63, 'NO_ENTRY': 2021, 'SAME_BAR': 670, 'SETUP_NOT_REFINABLE': 3836, 'SL': 468, 'TIMEOUT': 468} |
| PATH_LOCK_EARLY_BE_V0 | blocked_dominance_controls | 640 | 0.073785 | 0.023785 | 47.22213 | 15.22213 | 0.435937 | 0.485271 | {'BE_STOP': 88, 'LOCK_STOP': 99, 'NO_ENTRY': 2922, 'SAME_BAR': 1354, 'SETUP_NOT_REFINABLE': 2735, 'SL': 223, 'TIMEOUT': 235} |

## Cohort Summary

| variant_id | cohort_key | role | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_sum_r | net_sum_r_cost_0.05 | gross_win_rate | lock_trigger_rate | same_bar | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE_RAW_FIXED_TP | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 0.4007 | 0.3507 | 154.670019 | 135.370019 | 0.582902 | 0.0 | 105 | {'NO_ENTRY': 719, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 1530, 'SL': 152, 'TIMEOUT': 48, 'TP': 187} |
| BASE_RAW_FIXED_TP | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | -0.118655 | -0.168655 | -69.76893 | -99.16893 | 0.37415 | 0.0 | 164 | {'NO_ENTRY': 880, 'SAME_BAR': 164, 'SETUP_NOT_REFINABLE': 252, 'SL': 353, 'TIMEOUT': 58, 'TP': 178} |
| BASE_RAW_FIXED_TP | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 468 | 0.274765 | 0.224765 | 128.590034 | 105.190034 | 0.527778 | 0.0 | 494 | {'NO_ENTRY': 1053, 'SAME_BAR': 494, 'SETUP_NOT_REFINABLE': 1425, 'SL': 219, 'TIMEOUT': 39, 'TP': 212} |
| BASE_RAW_FIXED_TP | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 138 | 0.462074 | 0.412074 | 63.766274 | 56.866274 | 0.565217 | 0.0 | 289 | {'NO_ENTRY': 777, 'SAME_BAR': 289, 'SETUP_NOT_REFINABLE': 110, 'SL': 57, 'TIMEOUT': 7, 'TP': 75} |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 0.511628 | 0.461628 | 66.0 | 59.55 | 0.604651 | 0.0 | 46 | {'NO_ENTRY': 324, 'SAME_BAR': 46, 'SETUP_NOT_REFINABLE': 619, 'SL': 51, 'TP': 78} |
| BASE_RAW_FIXED_TP | USDJPY\|london\|bullish\|D1 | negative_control | 306 | -0.005699 | -0.055699 | -1.743903 | -17.043903 | 0.398693 | 0.0 | 127 | {'NO_ENTRY': 511, 'SAME_BAR': 127, 'SETUP_NOT_REFINABLE': 1635, 'SL': 178, 'TIMEOUT': 13, 'TP': 117} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 0.328947 | 0.278947 | 62.5 | 53.0 | 0.531579 | 0.0 | 63 | {'NO_ENTRY': 365, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 727, 'SL': 89, 'TP': 101} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 0.472689 | 0.422689 | 100.209971 | 89.609971 | 0.603774 | 0.0 | 55 | {'NO_ENTRY': 329, 'SAME_BAR': 55, 'SETUP_NOT_REFINABLE': 94, 'SL': 78, 'TIMEOUT': 20, 'TP': 114} |
| BASE_RAW_FIXED_TP | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | -0.030396 | -0.080396 | -11.550351 | -30.550351 | 0.418421 | 0.0 | 180 | {'NO_ENTRY': 630, 'SAME_BAR': 180, 'SETUP_NOT_REFINABLE': 1949, 'SL': 221, 'TIMEOUT': 33, 'TP': 126} |
| BASE_RAW_FIXED_TP | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 0.381615 | 0.331615 | 116.392606 | 101.142606 | 0.560656 | 0.0 | 64 | {'NO_ENTRY': 847, 'SAME_BAR': 64, 'SETUP_NOT_REFINABLE': 1111, 'SL': 131, 'TIMEOUT': 17, 'TP': 158} |
| BASE_RAW_FIXED_TP | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 386 | 0.470817 | 0.420817 | 181.735325 | 162.435325 | 0.590674 | 0.0 | 218 | {'NO_ENTRY': 1092, 'SAME_BAR': 218, 'SETUP_NOT_REFINABLE': 1200, 'SL': 151, 'TIMEOUT': 27, 'TP': 211} |
| J46_J49_ONLY | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 451 | 0.192789 | 0.142789 | 86.947812 | 64.397812 | 0.574279 | 0.035398 | 40 | {'NO_ENTRY': 719, 'SAME_BAR': 40, 'SETUP_NOT_REFINABLE': 1530, 'SL': 123, 'TIMEOUT': 329} |
| J46_J49_ONLY | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 653 | -0.051461 | -0.101461 | -33.604066 | -66.254066 | 0.381317 | 0.051988 | 99 | {'BE_STOP': 7, 'NO_ENTRY': 880, 'SAME_BAR': 99, 'SETUP_NOT_REFINABLE': 252, 'SL': 319, 'TIMEOUT': 318, 'TP': 10} |
| J46_J49_ONLY | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 708 | 0.320838 | 0.270838 | 227.153609 | 191.753609 | 0.44209 | 0.134831 | 252 | {'BE_STOP': 2, 'NO_ENTRY': 1053, 'SAME_BAR': 252, 'SETUP_NOT_REFINABLE': 1425, 'SL': 347, 'TIMEOUT': 346, 'TP': 17} |
| J46_J49_ONLY | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 259 | 0.265424 | 0.215424 | 68.744916 | 55.794916 | 0.413127 | 0.219231 | 168 | {'BE_STOP': 1, 'NO_ENTRY': 777, 'SAME_BAR': 168, 'SETUP_NOT_REFINABLE': 110, 'SL': 144, 'TIMEOUT': 113, 'TP': 2} |
| J46_J49_ONLY | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 149 | 1.113312 | 1.063312 | 165.88356 | 158.43356 | 0.657718 | 0.275168 | 26 | {'NO_ENTRY': 324, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 619, 'SL': 38, 'TIMEOUT': 101, 'TP': 10} |
| J46_J49_ONLY | USDJPY\|london\|bullish\|D1 | negative_control | 330 | -0.021896 | -0.071896 | -7.225821 | -23.725821 | 0.50303 | 0.012048 | 103 | {'NO_ENTRY': 511, 'SAME_BAR': 103, 'SETUP_NOT_REFINABLE': 1635, 'SL': 147, 'TIMEOUT': 185} |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 219 | 1.042785 | 0.992785 | 228.370001 | 217.420001 | 0.716895 | 0.242009 | 34 | {'NO_ENTRY': 365, 'SAME_BAR': 34, 'SETUP_NOT_REFINABLE': 727, 'SL': 49, 'TIMEOUT': 160, 'TP': 10} |
| J46_J49_ONLY | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 240 | 0.105966 | 0.055966 | 25.431901 | 13.431901 | 0.420833 | 0.112033 | 26 | {'NO_ENTRY': 329, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 94, 'SL': 107, 'TIMEOUT': 134} |
| J46_J49_ONLY | USDJPY\|tokyo\|bullish\|D1 | negative_control | 445 | -0.12437 | -0.17437 | -55.344805 | -77.594805 | 0.442697 | 0.008989 | 115 | {'NO_ENTRY': 630, 'SAME_BAR': 115, 'SETUP_NOT_REFINABLE': 1949, 'SL': 195, 'TIMEOUT': 250} |
| J46_J49_ONLY | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 339 | 0.584639 | 0.534639 | 198.192729 | 181.242729 | 0.59292 | 0.147059 | 30 | {'NO_ENTRY': 847, 'SAME_BAR': 30, 'SETUP_NOT_REFINABLE': 1111, 'SL': 114, 'TIMEOUT': 212, 'TP': 14} |
| J46_J49_ONLY | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 451 | 0.254001 | 0.204001 | 114.554272 | 92.004272 | 0.556541 | 0.092308 | 152 | {'BE_STOP': 4, 'NO_ENTRY': 1092, 'SAME_BAR': 152, 'SETUP_NOT_REFINABLE': 1200, 'SL': 141, 'TIMEOUT': 310} |
| PATH_LOCK_CONSERVATIVE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 0.278654 | 0.228654 | 107.560377 | 88.260377 | 0.606218 | 0.245478 | 105 | {'BE_STOP': 1, 'LOCK_STOP': 12, 'NO_ENTRY': 719, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 1530, 'SL': 84, 'TIMEOUT': 290} |
| PATH_LOCK_CONSERVATIVE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | -0.062436 | -0.112436 | -36.712605 | -66.112605 | 0.353741 | 0.190153 | 164 | {'BE_STOP': 4, 'LOCK_STOP': 7, 'NO_ENTRY': 880, 'SAME_BAR': 164, 'SETUP_NOT_REFINABLE': 252, 'SL': 301, 'TIMEOUT': 267, 'TP': 10} |
| PATH_LOCK_CONSERVATIVE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 464 | -0.027941 | -0.077941 | -12.964601 | -36.164601 | 0.383621 | 0.369099 | 498 | {'BE_STOP': 50, 'LOCK_STOP': 42, 'NO_ENTRY': 1053, 'SAME_BAR': 498, 'SETUP_NOT_REFINABLE': 1425, 'SL': 208, 'TIMEOUT': 166} |
| PATH_LOCK_CONSERVATIVE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 128 | 0.306899 | 0.256899 | 39.283027 | 32.883027 | 0.515625 | 0.550388 | 299 | {'BE_STOP': 7, 'LOCK_STOP': 7, 'NO_ENTRY': 777, 'SAME_BAR': 299, 'SETUP_NOT_REFINABLE': 110, 'SL': 53, 'TIMEOUT': 60, 'TP': 2} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 0.505046 | 0.455046 | 65.150964 | 58.700964 | 0.527132 | 0.550388 | 46 | {'BE_STOP': 20, 'LOCK_STOP': 21, 'NO_ENTRY': 324, 'SAME_BAR': 46, 'SETUP_NOT_REFINABLE': 619, 'SL': 28, 'TIMEOUT': 60} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 306 | -0.017801 | -0.067801 | -5.44706 | -20.74706 | 0.496732 | 0.256494 | 127 | {'BE_STOP': 9, 'NO_ENTRY': 511, 'SAME_BAR': 127, 'SETUP_NOT_REFINABLE': 1635, 'SL': 128, 'TIMEOUT': 171} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 0.698424 | 0.648424 | 132.700623 | 123.200623 | 0.636842 | 0.405263 | 63 | {'BE_STOP': 13, 'LOCK_STOP': 5, 'NO_ENTRY': 365, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 727, 'SL': 43, 'TIMEOUT': 122, 'TP': 7} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 0.386628 | 0.336628 | 81.965184 | 71.365184 | 0.495283 | 0.424528 | 55 | {'BE_STOP': 41, 'LOCK_STOP': 12, 'NO_ENTRY': 329, 'SAME_BAR': 55, 'SETUP_NOT_REFINABLE': 94, 'SL': 46, 'TIMEOUT': 113} |
| PATH_LOCK_CONSERVATIVE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | -0.086681 | -0.136681 | -32.938762 | -51.938762 | 0.457895 | 0.171053 | 180 | {'BE_STOP': 8, 'LOCK_STOP': 7, 'NO_ENTRY': 630, 'SAME_BAR': 180, 'SETUP_NOT_REFINABLE': 1949, 'SL': 151, 'TIMEOUT': 214} |
| PATH_LOCK_CONSERVATIVE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 0.727864 | 0.677864 | 221.998512 | 206.748512 | 0.668852 | 0.398693 | 64 | {'LOCK_STOP': 19, 'NO_ENTRY': 847, 'SAME_BAR': 64, 'SETUP_NOT_REFINABLE': 1111, 'SL': 82, 'TIMEOUT': 191, 'TP': 14} |
| PATH_LOCK_CONSERVATIVE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 377 | 0.340182 | 0.290182 | 128.248438 | 109.398438 | 0.594164 | 0.360526 | 227 | {'BE_STOP': 2, 'LOCK_STOP': 37, 'NO_ENTRY': 1092, 'SAME_BAR': 227, 'SETUP_NOT_REFINABLE': 1200, 'SL': 102, 'TIMEOUT': 239} |
| PATH_LOCK_HALF_GAIN_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 386 | 0.291138 | 0.241138 | 112.379291 | 93.079291 | 0.608808 | 0.245478 | 105 | {'LOCK_STOP': 37, 'NO_ENTRY': 719, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 1530, 'SL': 84, 'TIMEOUT': 266} |
| PATH_LOCK_HALF_GAIN_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 588 | -0.049988 | -0.099988 | -29.392903 | -58.792903 | 0.360544 | 0.190153 | 164 | {'LOCK_STOP': 32, 'NO_ENTRY': 880, 'SAME_BAR': 164, 'SETUP_NOT_REFINABLE': 252, 'SL': 301, 'TIMEOUT': 246, 'TP': 10} |
| PATH_LOCK_HALF_GAIN_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 464 | 0.049424 | -0.000576 | 22.932542 | -0.267458 | 0.491379 | 0.369099 | 498 | {'LOCK_STOP': 117, 'NO_ENTRY': 1053, 'SAME_BAR': 498, 'SETUP_NOT_REFINABLE': 1425, 'SL': 208, 'TIMEOUT': 141} |
| PATH_LOCK_HALF_GAIN_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 128 | 0.347655 | 0.297655 | 44.499805 | 38.099805 | 0.570312 | 0.550388 | 299 | {'LOCK_STOP': 45, 'NO_ENTRY': 777, 'SAME_BAR': 299, 'SETUP_NOT_REFINABLE': 110, 'SL': 53, 'TIMEOUT': 29, 'TP': 2} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 129 | 0.657412 | 0.607412 | 84.806182 | 78.356182 | 0.682171 | 0.550388 | 46 | {'LOCK_STOP': 42, 'NO_ENTRY': 324, 'SAME_BAR': 46, 'SETUP_NOT_REFINABLE': 619, 'SL': 28, 'TIMEOUT': 59} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 306 | -0.008927 | -0.058927 | -2.731756 | -18.031756 | 0.526144 | 0.256494 | 127 | {'LOCK_STOP': 42, 'NO_ENTRY': 511, 'SAME_BAR': 127, 'SETUP_NOT_REFINABLE': 1635, 'SL': 128, 'TIMEOUT': 138} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 190 | 0.532383 | 0.482383 | 101.152682 | 91.652682 | 0.705263 | 0.405263 | 63 | {'LOCK_STOP': 43, 'NO_ENTRY': 365, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 727, 'SL': 43, 'TIMEOUT': 104} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 212 | 0.504982 | 0.454982 | 107.056137 | 96.456137 | 0.688679 | 0.424528 | 55 | {'LOCK_STOP': 55, 'NO_ENTRY': 329, 'SAME_BAR': 55, 'SETUP_NOT_REFINABLE': 94, 'SL': 46, 'TIMEOUT': 111} |
| PATH_LOCK_HALF_GAIN_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 380 | -0.126434 | -0.176434 | -48.044957 | -67.044957 | 0.478947 | 0.171053 | 180 | {'LOCK_STOP': 45, 'NO_ENTRY': 630, 'SAME_BAR': 180, 'SETUP_NOT_REFINABLE': 1949, 'SL': 151, 'TIMEOUT': 184} |
| PATH_LOCK_HALF_GAIN_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 305 | 0.727316 | 0.677316 | 221.831238 | 206.581238 | 0.668852 | 0.398693 | 64 | {'LOCK_STOP': 40, 'NO_ENTRY': 847, 'SAME_BAR': 64, 'SETUP_NOT_REFINABLE': 1111, 'SL': 82, 'TIMEOUT': 170, 'TP': 14} |
| PATH_LOCK_HALF_GAIN_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 377 | 0.395471 | 0.345471 | 149.092541 | 130.242541 | 0.599469 | 0.360526 | 227 | {'LOCK_STOP': 52, 'NO_ENTRY': 1092, 'SAME_BAR': 227, 'SETUP_NOT_REFINABLE': 1200, 'SL': 102, 'TIMEOUT': 226} |
| PATH_LOCK_EARLY_BE_V0 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 287 | 0.227249 | 0.177249 | 65.220487 | 50.870487 | 0.595819 | 0.479167 | 204 | {'BE_STOP': 29, 'LOCK_STOP': 24, 'NO_ENTRY': 719, 'SAME_BAR': 204, 'SETUP_NOT_REFINABLE': 1530, 'SL': 36, 'TIMEOUT': 199} |
| PATH_LOCK_EARLY_BE_V0 | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | 527 | -0.22449 | -0.27449 | -118.306152 | -144.656152 | 0.322581 | 0.280303 | 225 | {'BE_STOP': 27, 'LOCK_STOP': 29, 'NO_ENTRY': 880, 'SAME_BAR': 225, 'SETUP_NOT_REFINABLE': 252, 'SL': 276, 'TIMEOUT': 196} |
| PATH_LOCK_EARLY_BE_V0 | NAS100\|ny\|bullish\|D1 | dominance_watchlist | 302 | -0.094432 | -0.144432 | -28.518392 | -43.618392 | 0.360927 | 0.450658 | 660 | {'BE_STOP': 45, 'LOCK_STOP': 38, 'NO_ENTRY': 1053, 'SAME_BAR': 660, 'SETUP_NOT_REFINABLE': 1425, 'SL': 122, 'TIMEOUT': 99} |
| PATH_LOCK_EARLY_BE_V0 | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | 94 | -0.010764 | -0.060764 | -1.011857 | -5.711857 | 0.382979 | 0.568421 | 333 | {'BE_STOP': 20, 'LOCK_STOP': 29, 'NO_ENTRY': 777, 'SAME_BAR': 333, 'SETUP_NOT_REFINABLE': 110, 'SL': 36, 'TIMEOUT': 10} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | 114 | 0.686896 | 0.636896 | 78.306182 | 72.606182 | 0.675439 | 0.692982 | 61 | {'BE_STOP': 6, 'LOCK_STOP': 31, 'NO_ENTRY': 324, 'SAME_BAR': 61, 'SETUP_NOT_REFINABLE': 619, 'SL': 18, 'TIMEOUT': 59} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|london\|bullish\|D1 | negative_control | 238 | -0.007794 | -0.057794 | -1.854915 | -13.754915 | 0.415966 | 0.389121 | 196 | {'BE_STOP': 32, 'LOCK_STOP': 7, 'NO_ENTRY': 511, 'SAME_BAR': 196, 'SETUP_NOT_REFINABLE': 1635, 'SL': 90, 'TIMEOUT': 110} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 172 | 0.547499 | 0.497499 | 94.169847 | 85.569847 | 0.709302 | 0.52907 | 81 | {'BE_STOP': 3, 'LOCK_STOP': 34, 'NO_ENTRY': 365, 'SAME_BAR': 81, 'SETUP_NOT_REFINABLE': 727, 'SL': 35, 'TIMEOUT': 100} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | 157 | 0.542519 | 0.492519 | 85.175508 | 77.325508 | 0.675159 | 0.477707 | 110 | {'BE_STOP': 1, 'LOCK_STOP': 19, 'NO_ENTRY': 329, 'SAME_BAR': 110, 'SETUP_NOT_REFINABLE': 94, 'SL': 34, 'TIMEOUT': 103} |
| PATH_LOCK_EARLY_BE_V0 | USDJPY\|tokyo\|bullish\|D1 | negative_control | 311 | -0.060651 | -0.110651 | -18.862352 | -34.412352 | 0.4791 | 0.356913 | 249 | {'BE_STOP': 20, 'LOCK_STOP': 27, 'NO_ENTRY': 630, 'SAME_BAR': 249, 'SETUP_NOT_REFINABLE': 1949, 'SL': 102, 'TIMEOUT': 162} |
| PATH_LOCK_EARLY_BE_V0 | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | 251 | 0.814688 | 0.764688 | 204.486767 | 191.936767 | 0.677291 | 0.650794 | 118 | {'BE_STOP': 16, 'LOCK_STOP': 38, 'NO_ENTRY': 847, 'SAME_BAR': 118, 'SETUP_NOT_REFINABLE': 1111, 'SL': 46, 'TIMEOUT': 138, 'TP': 14} |
| PATH_LOCK_EARLY_BE_V0 | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | 244 | 0.314559 | 0.264559 | 76.752379 | 64.552379 | 0.54918 | 0.495935 | 361 | {'BE_STOP': 23, 'LOCK_STOP': 32, 'NO_ENTRY': 1092, 'SAME_BAR': 361, 'SETUP_NOT_REFINABLE': 1200, 'SL': 65, 'TIMEOUT': 126} |

## Methodology Diagnostics

| exit_policy_pbo | pbo_status | pbo_promotion_usable | exit_policy_effective_N | effective_N_promotion_usable |
| --- | --- | --- | --- | --- |
| 0.117716 | COMPUTED_POSTHOC_DIAGNOSTIC_ONLY | False | 1.461255 | False |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Cost model | SENSITIVITY_NOT_MEASURED_COST | Historical OHLC does not contain reliable commission/spread/slippage. Report uses R-cost sensitivity. |
| Lower-timeframe execution | M15_V0_ONLY | Full-corpus V0 uses M15 for comparability; M1/M5 refinement is a later precision lane because coverage is incomplete before late 2024/2026. |
| Reentry | INTENTIONALLY_BLOCKED | No reentry is tested until lock-only proves value and incremental-risk accounting is implemented. |
| L2 attribution | NOT_IMPLEMENTED_IN_V0 | Requires deterministic L2 reconstruction on the pre-L2 candidate stream. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical raw-OHLC exit-policy ablation. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Inspect V0 lock-only result versus J46-J49 | Only continue to structural/liquidity or reentry policies if lock-only has a robust advantage or useful drawdown reduction. |
| 2 | Add M5/M1 refinement lane for post-coverage subsets | Lower-timeframe ordering is needed before reentry decisions are trusted. |
| 3 | Implement deterministic L2 reconstruction | Needed for with/without architecture attribution. |

## Synthesis

- This report is the first V0 measurement of J46-J49 versus lock-only path scaling on the same reconstructed raw-OHLC stream.
- The result should be read as an engineering diagnostic, not as a promotion verdict.
- If lock-only improves a specific cohort's return/drawdown/cost tradeoff, the next lane must pre-register that cohort-specific question before lower-timeframe refinement or risk-budgeted reentry.
