# Raw-OHLC Path Scaling V1 Final Disposition

**Created UTC:** 2026-05-02T06:46:24.613916+00:00
**Event log:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\path_ablation_v1_mtf\raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl`
**Event log SHA256:** `cf3364825735c5858486b5c1e8678455748099250ee899b69a27379e469d38a0`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**V1 final verdict:** `REJECTED_FOR_EXIT_POLICY_PROMOTION`
**V1 completion status:** `CLOSED_NO_BLOCKING_AMBIGUITY`
**V2 gate:** `NOT_AUTO_PROMOTED_FROM_V1`

## Boundary

- Research/tooling only
- No live trading logic changes
- No prompt edits
- No parameter optimization
- No paid AI/API calls
- No V2/V3 implementation started

## Registered Residual Same-Bar Policy

| headline | decision_gate | coverage_subsets | do_not_do |
| --- | --- | --- | --- |
| Keep unresolved selected-row SAME_BAR outcomes excluded from mean-R headline metrics. | Use samebar_pessimistic (-1R) as the conservative stress treatment before considering any V1 exit-policy promotion. | M1/M5-only and M1-only views are diagnostic only, not final evidence, because lower-timeframe coverage is period-skewed. | Do not fabricate order inside M1/M5/M15 OHLC bars; do not silently drop same-bars without reporting counts; do not use M1/M5 coverage subset as final full-corpus evidence. |

## Direct Answers

| question | answer |
| --- | --- |
| Is V1 promoted as an exit-policy candidate? | No. V1 fixed-R lock-only is rejected for exit-policy promotion and remains NO_PROMOTION_VERDICT. |
| Is the V1 MTF path-resolution layer usable as diagnostic infrastructure? | Yes. It is accepted as diagnostic infrastructure with a registered residual same-bar policy, not as alpha. |
| What wins under the headline unresolved-exclusion treatment? | J46_J49_ONLY with net_mean_r_cost_0.05=0.163894. |
| What wins under conservative same-bar pessimistic stress? | J46_J49_ONLY with net_mean_r_cost_0.05=-0.002871. |
| Does the target-family lock-only advantage survive pessimistic stress? | No. Exclude-unresolved target best-lock-minus-J46=0.063597; samebar_pessimistic target best-lock-minus-J46=-0.077802. |
| Are residual same-bars still ambiguous? | They are no longer an unclassified ambiguity: they are registered as unresolved headline exclusions and -1R stress rows. Counts by selected timeframe are {'M1': 160, 'M15': 5038, 'M5': 1417}; V0 same-bars resolved by MTF are {'M1': 578, 'M5': 1680}. |
| Should V2 start automatically from V1? | No. V1 does not auto-promote to V2; a future V2 would need a fresh registered structural-level hypothesis. |

## Same-Bar Breakdown

| scope | key | v1_samebar_policy_rows | v1_samebar_unique_setups | v0_samebar_resolved_policy_rows | v0_samebar_resolved_unique_setups |
| --- | --- | --- | --- | --- | --- |
| timeframe | M1 | 160 | 64 | 578 | 204 |
| timeframe | M15 | 5038 | 1429 | 0 | 0 |
| timeframe | M5 | 1417 | 496 | 1680 | 601 |
| group | all_enabled | 6615 | 1989 |  |  |
| group | target_cohorts | 1320 | 417 |  |  |
| group | primary_controlled_family | 671 | 197 |  |  |
| group | cleared_non_primary_targets | 649 | 220 |  |  |
| group | negative_controls | 1701 | 517 |  |  |
| group | blocked_dominance_controls | 3594 | 1055 |  |  |

## Treatment Variant Summary

| treatment | variant_id | n | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | win_rate | is_best |
| --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | BASE_RAW_FIXED_TP | 3898 | 0.156545 | 610.211736 | 0.491534 | False |
| exclude_unresolved | J46_J49_ONLY | 4477 | 0.163894 | 733.751655 | 0.466384 | True |
| exclude_unresolved | PATH_LOCK_CONSERVATIVE_V0 | 3884 | 0.138345 | 537.330537 | 0.476313 | False |
| exclude_unresolved | PATH_LOCK_HALF_GAIN_V0 | 3884 | 0.141565 | 549.839507 | 0.531926 | False |
| exclude_unresolved | PATH_LOCK_EARLY_BE_V0 | 3206 | 0.095509 | 306.201659 | 0.482533 | False |
| samebar_breakeven | BASE_RAW_FIXED_TP | 5193 | 0.105038 | 545.461736 | 0.368958 | False |
| samebar_breakeven | J46_J49_ONLY | 5190 | 0.134509 | 698.101655 | 0.402312 | True |
| samebar_breakeven | PATH_LOCK_CONSERVATIVE_V0 | 5193 | 0.090869 | 471.880537 | 0.356249 | False |
| samebar_breakeven | PATH_LOCK_HALF_GAIN_V0 | 5193 | 0.093277 | 484.389507 | 0.397843 | False |
| samebar_breakeven | PATH_LOCK_EARLY_BE_V0 | 5195 | 0.039798 | 206.751659 | 0.297786 | False |
| samebar_pessimistic | BASE_RAW_FIXED_TP | 5193 | -0.144336 | -749.538264 | 0.368958 | False |
| samebar_pessimistic | J46_J49_ONLY | 5190 | -0.002871 | -14.898345 | 0.402312 | True |
| samebar_pessimistic | PATH_LOCK_CONSERVATIVE_V0 | 5193 | -0.161202 | -837.119463 | 0.356249 | False |
| samebar_pessimistic | PATH_LOCK_HALF_GAIN_V0 | 5193 | -0.158793 | -824.610493 | 0.397843 | False |
| samebar_pessimistic | PATH_LOCK_EARLY_BE_V0 | 5195 | -0.34307 | -1782.248341 | 0.297786 | False |

## Treatment Group Delta Summary

| treatment | group | j46_net_mean_r_cost_0.05 | best_lock_variant | best_lock_net_mean_r_cost_0.05 | best_lock_minus_j46 | j46_n | best_lock_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_unresolved | all_enabled | 0.163894 | PATH_LOCK_HALF_GAIN_V0 | 0.141565 | -0.022329 | 4477 | 3884 |
| exclude_unresolved | target_cohorts | 0.409292 | PATH_LOCK_CONSERVATIVE_V0 | 0.472889 | 0.063597 | 1406 | 1270 |
| exclude_unresolved | primary_controlled_family | 0.395481 | PATH_LOCK_CONSERVATIVE_V0 | 0.423483 | 0.028002 | 674 | 596 |
| exclude_unresolved | cleared_non_primary_targets | 0.422008 | PATH_LOCK_EARLY_BE_V0 | 0.584256 | 0.162248 | 732 | 576 |
| exclude_unresolved | negative_controls | -0.150354 | PATH_LOCK_HALF_GAIN_V0 | -0.16443 | -0.014076 | 1518 | 1426 |
| exclude_unresolved | blocked_dominance_controls | 0.248889 | PATH_LOCK_HALF_GAIN_V0 | 0.190875 | -0.058014 | 1553 | 1188 |
| samebar_breakeven | all_enabled | 0.134509 | PATH_LOCK_HALF_GAIN_V0 | 0.093277 | -0.041232 | 5190 | 5193 |
| samebar_breakeven | target_cohorts | 0.372344 | PATH_LOCK_CONSERVATIVE_V0 | 0.384032 | 0.011688 | 1529 | 1530 |
| samebar_breakeven | primary_controlled_family | 0.359065 | PATH_LOCK_CONSERVATIVE_V0 | 0.334463 | -0.024602 | 734 | 734 |
| samebar_breakeven | cleared_non_primary_targets | 0.384604 | PATH_LOCK_HALF_GAIN_V0 | 0.44659 | 0.061986 | 795 | 796 |
| samebar_breakeven | negative_controls | -0.137299 | PATH_LOCK_HALF_GAIN_V0 | -0.143511 | -0.006212 | 1745 | 1745 |
| samebar_breakeven | blocked_dominance_controls | 0.192262 | PATH_LOCK_HALF_GAIN_V0 | 0.099197 | -0.093065 | 1916 | 1918 |
| samebar_pessimistic | all_enabled | -0.002871 | PATH_LOCK_HALF_GAIN_V0 | -0.158793 | -0.155922 | 5190 | 5193 |
| samebar_pessimistic | target_cohorts | 0.291899 | PATH_LOCK_CONSERVATIVE_V0 | 0.214097 | -0.077802 | 1529 | 1530 |
| samebar_pessimistic | primary_controlled_family | 0.277322 | PATH_LOCK_CONSERVATIVE_V0 | 0.146452 | -0.13087 | 734 | 734 |
| samebar_pessimistic | cleared_non_primary_targets | 0.305359 | PATH_LOCK_HALF_GAIN_V0 | 0.293323 | -0.012036 | 795 | 796 |
| samebar_pessimistic | negative_controls | -0.267385 | PATH_LOCK_HALF_GAIN_V0 | -0.326319 | -0.058934 | 1745 | 1745 |
| samebar_pessimistic | blocked_dominance_controls | 0.002805 | PATH_LOCK_HALF_GAIN_V0 | -0.281408 | -0.284213 | 1916 | 1918 |

## Coverage Subset Variant Summary

| subset | variant_id | n | net_mean_r_cost_0.05 | net_sum_r_cost_0.05 | is_best |
| --- | --- | --- | --- | --- | --- |
| M1_M5_ONLY | BASE_RAW_FIXED_TP | 1847 | 0.18146 | 335.15601 | True |
| M1_M5_ONLY | J46_J49_ONLY | 2045 | 0.166268 | 340.018308 | False |
| M1_M5_ONLY | PATH_LOCK_CONSERVATIVE_V0 | 1837 | 0.168927 | 310.319645 | False |
| M1_M5_ONLY | PATH_LOCK_HALF_GAIN_V0 | 1837 | 0.166163 | 305.241209 | False |
| M1_M5_ONLY | PATH_LOCK_EARLY_BE_V0 | 1586 | 0.142044 | 225.281234 | False |
| M1_ONLY | BASE_RAW_FIXED_TP | 390 | 0.20005 | 78.019678 | True |
| M1_ONLY | J46_J49_ONLY | 402 | -0.101465 | -40.788752 | False |
| M1_ONLY | PATH_LOCK_CONSERVATIVE_V0 | 390 | 0.079565 | 31.030318 | False |
| M1_ONLY | PATH_LOCK_HALF_GAIN_V0 | 390 | 0.141599 | 55.223526 | False |
| M1_ONLY | PATH_LOCK_EARLY_BE_V0 | 353 | 0.028003 | 9.885202 | False |
| M5_ONLY | BASE_RAW_FIXED_TP | 1457 | 0.176483 | 257.136332 | False |
| M5_ONLY | J46_J49_ONLY | 1643 | 0.231775 | 380.80706 | True |
| M5_ONLY | PATH_LOCK_CONSERVATIVE_V0 | 1447 | 0.193013 | 279.289327 | False |
| M5_ONLY | PATH_LOCK_HALF_GAIN_V0 | 1447 | 0.172783 | 250.017683 | False |
| M5_ONLY | PATH_LOCK_EARLY_BE_V0 | 1233 | 0.174693 | 215.396032 | False |
| M15_ONLY | BASE_RAW_FIXED_TP | 2051 | 0.134108 | 275.055726 | False |
| M15_ONLY | J46_J49_ONLY | 2432 | 0.161897 | 393.733347 | True |
| M15_ONLY | PATH_LOCK_CONSERVATIVE_V0 | 2047 | 0.110899 | 227.010892 | False |
| M15_ONLY | PATH_LOCK_HALF_GAIN_V0 | 2047 | 0.119491 | 244.598298 | False |
| M15_ONLY | PATH_LOCK_EARLY_BE_V0 | 1620 | 0.049951 | 80.920425 | False |

## Coverage Subset Group Delta Summary

| subset | group | j46_net_mean_r_cost_0.05 | best_lock_variant | best_lock_net_mean_r_cost_0.05 | best_lock_minus_j46 | j46_n | best_lock_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1_M5_ONLY | all_enabled | 0.166268 | PATH_LOCK_CONSERVATIVE_V0 | 0.168927 | 0.002659 | 2045 | 1837 |
| M1_M5_ONLY | target_cohorts | 0.597028 | PATH_LOCK_CONSERVATIVE_V0 | 0.762543 | 0.165515 | 564 | 513 |
| M1_M5_ONLY | primary_controlled_family | 0.342833 | PATH_LOCK_CONSERVATIVE_V0 | 0.506029 | 0.163196 | 320 | 283 |
| M1_M5_ONLY | cleared_non_primary_targets | 0.930399 | PATH_LOCK_CONSERVATIVE_V0 | 1.078167 | 0.147768 | 244 | 230 |
| M1_M5_ONLY | negative_controls | -0.330591 | PATH_LOCK_HALF_GAIN_V0 | -0.369544 | -0.038953 | 573 | 551 |
| M1_M5_ONLY | blocked_dominance_controls | 0.21225 | PATH_LOCK_EARLY_BE_V0 | 0.273695 | 0.061445 | 908 | 582 |
| M1_ONLY | all_enabled | -0.101465 | PATH_LOCK_HALF_GAIN_V0 | 0.141599 | 0.243064 | 402 | 390 |
| M1_ONLY | target_cohorts | -0.732634 | PATH_LOCK_HALF_GAIN_V0 | 0.352783 | 1.085417 | 80 | 68 |
| M1_ONLY | primary_controlled_family | -0.812783 | PATH_LOCK_HALF_GAIN_V0 | 0.121521 | 0.934304 | 60 | 48 |
| M1_ONLY | cleared_non_primary_targets | -0.492186 | PATH_LOCK_HALF_GAIN_V0 | 0.907814 | 1.4 | 20 | 20 |
| M1_ONLY | negative_controls | -0.040247 | PATH_LOCK_CONSERVATIVE_V0 | -0.053663 | -0.013416 | 209 | 209 |
| M1_ONLY | blocked_dominance_controls | 0.232156 | PATH_LOCK_EARLY_BE_V0 | 0.405224 | 0.173068 | 113 | 104 |
| M5_ONLY | all_enabled | 0.231775 | PATH_LOCK_CONSERVATIVE_V0 | 0.193013 | -0.038762 | 1643 | 1447 |
| M5_ONLY | target_cohorts | 0.816807 | PATH_LOCK_CONSERVATIVE_V0 | 0.867855 | 0.051048 | 484 | 445 |
| M5_ONLY | primary_controlled_family | 0.609514 | PATH_LOCK_CONSERVATIVE_V0 | 0.635631 | 0.026117 | 260 | 235 |
| M5_ONLY | cleared_non_primary_targets | 1.057415 | PATH_LOCK_CONSERVATIVE_V0 | 1.127724 | 0.070309 | 224 | 210 |
| M5_ONLY | negative_controls | -0.497299 | PATH_LOCK_HALF_GAIN_V0 | -0.557516 | -0.060217 | 364 | 342 |
| M5_ONLY | blocked_dominance_controls | 0.20942 | PATH_LOCK_EARLY_BE_V0 | 0.245078 | 0.035658 | 795 | 478 |
| M15_ONLY | all_enabled | 0.161897 | PATH_LOCK_HALF_GAIN_V0 | 0.119491 | -0.042406 | 2432 | 2047 |
| M15_ONLY | target_cohorts | 0.28354 | PATH_LOCK_EARLY_BE_V0 | 0.295685 | 0.012145 | 842 | 616 |
| M15_ONLY | primary_controlled_family | 0.443072 | PATH_LOCK_CONSERVATIVE_V0 | 0.348849 | -0.094223 | 354 | 313 |
| M15_ONLY | cleared_non_primary_targets | 0.167813 | PATH_LOCK_EARLY_BE_V0 | 0.36751 | 0.199697 | 488 | 348 |
| M15_ONLY | negative_controls | -0.041067 | PATH_LOCK_CONSERVATIVE_V0 | -0.033432 | 0.007635 | 945 | 875 |
| M15_ONLY | blocked_dominance_controls | 0.300468 | PATH_LOCK_HALF_GAIN_V0 | 0.142346 | -0.158122 | 645 | 415 |

## Cohort Best Summary

| treatment | cohort_key | role | best_variant | best_net_mean_r_cost_0.05 | n |
| --- | --- | --- | --- | --- | --- |
| exclude_unresolved | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | BASE_RAW_FIXED_TP | 0.34032 | 394 |
| exclude_unresolved | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | PATH_LOCK_HALF_GAIN_V0 | -0.155693 | 670 |
| exclude_unresolved | NAS100\|ny\|bullish\|D1 | dominance_watchlist | J46_J49_ONLY | 0.29423 | 775 |
| exclude_unresolved | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | BASE_RAW_FIXED_TP | 0.216851 | 179 |
| exclude_unresolved | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | J46_J49_ONLY | 1.058757 | 149 |
| exclude_unresolved | USDJPY\|london\|bullish\|D1 | negative_control | J46_J49_ONLY | -0.013785 | 346 |
| exclude_unresolved | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | J46_J49_ONLY | 0.979884 | 219 |
| exclude_unresolved | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | PATH_LOCK_EARLY_BE_V0 | 0.410609 | 174 |
| exclude_unresolved | USDJPY\|tokyo\|bullish\|D1 | negative_control | BASE_RAW_FIXED_TP | -0.169724 | 424 |
| exclude_unresolved | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | PATH_LOCK_EARLY_BE_V0 | 0.678626 | 278 |
| exclude_unresolved | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | PATH_LOCK_EARLY_BE_V0 | 0.410777 | 308 |
| samebar_pessimistic | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | BASE_RAW_FIXED_TP | 0.088848 | 481 |
| samebar_pessimistic | GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | J46_J49_ONLY | -0.223548 | 752 |
| samebar_pessimistic | NAS100\|ny\|bullish\|D1 | dominance_watchlist | J46_J49_ONLY | 0.057097 | 941 |
| samebar_pessimistic | US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | J46_J49_ONLY | -0.284346 | 427 |
| samebar_pessimistic | USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | J46_J49_ONLY | 0.745456 | 175 |
| samebar_pessimistic | USDJPY\|london\|bullish\|D1 | negative_control | J46_J49_ONLY | -0.221986 | 433 |
| samebar_pessimistic | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | J46_J49_ONLY | 0.707093 | 253 |
| samebar_pessimistic | USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | PATH_LOCK_HALF_GAIN_V0 | 0.188696 | 267 |
| samebar_pessimistic | USDJPY\|tokyo\|bullish\|D1 | negative_control | J46_J49_ONLY | -0.361356 | 560 |
| samebar_pessimistic | XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | PATH_LOCK_HALF_GAIN_V0 | 0.391882 | 354 |
| samebar_pessimistic | XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | PATH_LOCK_HALF_GAIN_V0 | 0.138491 | 548 |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| Residual same-bar handling | CLOSED_BY_REGISTERED_POLICY | Headline metrics keep SAME_BAR unresolved; decision-gate stress scores them as -1R. Counts by selected timeframe: {'M1': 160, 'M15': 5038, 'M5': 1417}. |
| M15 fallback coverage | CLOSED_AS_DATA_LIMITATION | M15 fallback rows are not resolved or fabricated. They remain unresolved in headline metrics and pessimistic in stress metrics. |
| M5 without M1 coverage | CLOSED_AS_DATA_LIMITATION | M5 same-bars are not accepted as ordered. They use the same unresolved/stress treatment. |
| M1 same-bars | CLOSED_AS_OHLC_GRANULARITY_LIMIT | M1 OHLC cannot order intra-minute events. V1 does not fabricate tick order. |
| Coverage subset temptation | CLOSED_DIAGNOSTIC_ONLY | M1/M5-only subsets are reported but not used as final evidence because coverage is period-skewed. |
| Promotion | REJECTED_FOR_EXIT_POLICY_PROMOTION | J46-J49 remains best globally; target-family lock advantage does not survive samebar_pessimistic stress. |

## Closed Questions

| question | answer | status |
| --- | --- | --- |
| Should V2 proceed with M15 fallback same-bars carried as resolved? | No. Carry them only as unresolved headline exclusions and pessimistic stress rows. | CLOSED |
| Should M5 same-bars be accepted where M1 coverage is absent? | No. M5 same-bars remain unresolved/stressed; M5 does not establish intra-bar order. | CLOSED |
| Should M1 same-bars be dropped, pessimistically scored, or retained as unresolved? | Retain as unresolved in headline metrics and score as -1R in stress metrics. Do not silently drop them. | CLOSED |
| Should V2 be limited to M1/M5-covered windows? | No for final evidence. M1/M5-only is diagnostic because it sacrifices full-corpus comparability and is period-skewed. | CLOSED |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Stop V1 fixed-R lock-only promotion work. | It does not beat J46-J49 globally and the target-family lock edge fails conservative same-bar stress. |
| 2 | Do not start V2 automatically from V1. | A future V2 must be registered as a new structural-level hypothesis, not as a promoted V1 continuation. |
| 3 | If V2 is later approved, inherit V1's residual same-bar policy. | This prevents structural levels from repairing V1 ambiguity post hoc. |

## Synthesis

- V1 is closed. The MTF resolver is useful diagnostic infrastructure, but fixed-R lock-only V1 is rejected for exit-policy promotion.
- The ambiguity is no longer open-ended: residual selected-row SAME_BAR cases have a registered treatment, and coverage subsets are explicitly diagnostic-only.
- The decisive result is robustness failure. Under headline unresolved-exclusion, J46-J49 remains the best global variant; under samebar_pessimistic stress, J46-J49 still leads globally and the target-family lock-only advantage flips negative.
- V1 therefore does not auto-promote to V2. Any V2 work must be a separately registered structural-level hypothesis.
