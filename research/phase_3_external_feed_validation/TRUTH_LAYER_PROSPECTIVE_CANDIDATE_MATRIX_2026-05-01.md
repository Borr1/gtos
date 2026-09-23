# Phase 3 Truth-Layer Prospective Candidate Matrix

**Created UTC:** 2026-05-01T08:27:48.073516+00:00
**Status:** `registered_future_prospective_matrix`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- This freezes the broad candidate matrix before future prospective rows arrive.
- The historical candidate universe was identified after diagnostics, so historical results remain post-hoc.
- Future PBO/effective_N work must keep every registered candidate in the matrix.

## Source And Rules

| candidate_count | primary_candidate_count | watchlist_candidate_count | prospective_cutoff_utc | candidate_unit | periodization | missing_period_policy | truth_layer_jsonl | truth_layer_sha256 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 44 | 2 | 4 | 2026-04-30T17:00:00+00:00 | symbol\|session\|truth_regime | calendar_month | zero_return_no_resolved_trade | data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl | 0530a49f1eafcaa46bf94b9c9267670d815803ed3c067ecd5501a5a9888455ae |

## Historical PBO Reference

| status | promotion_usable | pbo | period_count | candidate_universe_n | eligible_universe_n | pbo_diagnostics |
| --- | --- | --- | --- | --- | --- | --- |
| POSTHOC_DIAGNOSTIC_ONLY | False | 0.5553613053613053 | 52 | 95 | 44 | {"combination_count": 3432, "logit_max": 3.784189633918261, "logit_mean": -0.25177560760802903, "logit_min": -3.784189633918261, "period_count": 52, "periods_used": 52, "sample_records": [{"below_median": true, "is_best_oos_rank": 17, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 6]}, {"below_median": false, "is_best_oos_rank": 30, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 7]}, {"below_median": false, "is_best_oos_rank": 34, "is_best_strategy_index": 37, "is_subperiods": [0, 1, 2, 3, 4, 5, 8]}, {"below_median": true, "is_best_oos_rank": 11, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 9]}, {"below_median": false, "is_best_oos_rank": 34, "is_best_strategy_index": 18, "is_subperiods": [0, 1, 2, 3, 4, 5, 10]}, {"below_median": false, "is_best_oos_rank": 28, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 11]}, {"below_median": true, "is_best_oos_rank": 17, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 12]}, {"below_median": false, "is_best_oos_rank": 25, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 5, 13]}, {"below_median": true, "is_best_oos_rank": 19, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 7]}, {"below_median": true, "is_best_oos_rank": 16, "is_best_strategy_index": 2, "is_subperiods": [0, 1, 2, 3, 4, 6, 8]}, {"below_median": true, "is_best_oos_rank": 8, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 9]}, {"below_median": true, "is_best_oos_rank": 17, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 10]}, {"below_median": true, "is_best_oos_rank": 16, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 11]}, {"below_median": true, "is_best_oos_rank": 9, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 12]}, {"below_median": true, "is_best_oos_rank": 17, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 6, 13]}, {"below_median": false, "is_best_oos_rank": 41, "is_best_strategy_index": 6, "is_subperiods": [0, 1, 2, 3, 4, 7, 8]}, {"below_median": true, "is_best_oos_rank": 16, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 7, 9]}, {"below_median": false, "is_best_oos_rank": 39, "is_best_strategy_index": 18, "is_subperiods": [0, 1, 2, 3, 4, 7, 10]}, {"below_median": false, "is_best_oos_rank": 30, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 7, 11]}, {"below_median": true, "is_best_oos_rank": 22, "is_best_strategy_index": 8, "is_subperiods": [0, 1, 2, 3, 4, 7, 12]}], "status": "COMPUTED_POSTHOC_DIAGNOSTIC_ONLY", "strategy_count": 44, "subperiod_count": 14, "subperiod_policy": "balanced_contiguous_all_periods", "subperiod_sizes": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3]} |

## Primary Candidates

| candidate_id | cohort_key | role | historical_population_rows | historical_resolved_r_n | historical_sum_r | historical_mean_r | historical_win_rate | historical_valid_year_folds | historical_positive_valid_year_folds | historical_max_year_resolved_share | historical_active_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-007 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 4 | 4 | 0.413953 | 26 |
| P3-TL-MATRIX-030 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 3 | 3 | 0.330189 | 11 |

## Registered Candidate Matrix

| candidate_id | cohort_key | role | historical_population_rows | historical_resolved_r_n | historical_sum_r | historical_mean_r | historical_win_rate | historical_valid_year_folds | historical_positive_valid_year_folds | historical_max_year_resolved_share | historical_active_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-001 | GBPJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 512 | 203 | 10.9683 | 0.054031 | 0.433498 | 4 | 1 | 0.325123 | 13 |
| P3-TL-MATRIX-002 | GBPJPY\|london\|bullish\|D1 | registered_matrix_candidate | 792 | 318 | 51.6575 | 0.162445 | 0.459119 | 4 | 2 | 0.342767 | 23 |
| P3-TL-MATRIX-003 | GBPJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1292 | 530 | 161.2745 | 0.304292 | 0.516981 | 4 | 3 | 0.456604 | 27 |
| P3-TL-MATRIX-004 | GBPJPY\|ny\|bullish\|D1 | registered_matrix_candidate | 728 | 261 | 15.5737 | 0.059669 | 0.455939 | 4 | 2 | 0.298851 | 20 |
| P3-TL-MATRIX-005 | GBPJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1201 | 449 | 79.2424 | 0.176486 | 0.492205 | 5 | 2 | 0.438753 | 28 |
| P3-TL-MATRIX-006 | GBPJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | 644 | 270 | 9.1669 | 0.033951 | 0.425926 | 4 | 1 | 0.411111 | 17 |
| P3-TL-MATRIX-007 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 4 | 4 | 0.413953 | 26 |
| P3-TL-MATRIX-008 | GBPJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1552 | 657 | 150.0429 | 0.228376 | 0.493151 | 4 | 3 | 0.461187 | 28 |
| P3-TL-MATRIX-009 | GBPUSD\|london\|bearish\|D1 | registered_matrix_candidate | 1396 | 727 | 179.6955 | 0.247174 | 0.503439 | 5 | 4 | 0.264099 | 21 |
| P3-TL-MATRIX-010 | GBPUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 1337 | 671 | -93.5818 | -0.139466 | 0.359165 | 5 | 2 | 0.295082 | 25 |
| P3-TL-MATRIX-011 | GBPUSD\|london\|bullish\|D1 | registered_matrix_candidate | 1126 | 614 | -18.589 | -0.030275 | 0.405537 | 5 | 2 | 0.397394 | 21 |
| P3-TL-MATRIX-012 | GBPUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1768 | 658 | 40.0797 | 0.060911 | 0.420973 | 4 | 4 | 0.398176 | 27 |
| P3-TL-MATRIX-013 | GBPUSD\|ny\|bearish\|D1 | registered_matrix_candidate | 620 | 298 | -30.7401 | -0.103155 | 0.379195 | 4 | 2 | 0.295302 | 18 |
| P3-TL-MATRIX-014 | GBPUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 573 | 214 | -28.0417 | -0.131036 | 0.359813 | 3 | 2 | 0.280374 | 17 |
| P3-TL-MATRIX-015 | GBPUSD\|ny\|bullish\|D1 | registered_matrix_candidate | 462 | 175 | 0.868 | 0.00496 | 0.428571 | 3 | 1 | 0.377143 | 16 |
| P3-TL-MATRIX-016 | GBPUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 880 | 264 | 29.2658 | 0.110855 | 0.443182 | 3 | 2 | 0.44697 | 22 |
| P3-TL-MATRIX-017 | NAS100\|london\|bullish\|D1 | registered_matrix_candidate | 591 | 591 | 16.8921 | 0.028582 | 0.411168 | 3 | 2 | 0.624365 | 19 |
| P3-TL-MATRIX-018 | NAS100\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 662 | 662 | 53.685 | 0.081095 | 0.429003 | 4 | 3 | 0.321752 | 24 |
| P3-TL-MATRIX-019 | NAS100\|ny\|bullish\|D1 | watchlist_from_controlled_spec | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 3 | 3 | 0.581616 | 21 |
| P3-TL-MATRIX-020 | NAS100\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 640 | 640 | -25.0 | -0.039062 | 0.384375 | 4 | 1 | 0.315625 | 24 |
| P3-TL-MATRIX-021 | US30_cash\|london\|bearish\|D1 | registered_matrix_candidate | 173 | 173 | 49.5 | 0.286127 | 0.514451 | 3 | 2 | 0.393064 | 9 |
| P3-TL-MATRIX-022 | US30_cash\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 355 | 355 | 18.2344 | 0.051365 | 0.411268 | 3 | 2 | 0.507042 | 20 |
| P3-TL-MATRIX-023 | US30_cash\|ny\|bullish\|D1 | registered_matrix_candidate | 230 | 230 | -2.6284 | -0.011428 | 0.391304 | 3 | 1 | 0.452174 | 17 |
| P3-TL-MATRIX-024 | US30_cash\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 3 | 3 | 0.45625 | 18 |
| P3-TL-MATRIX-025 | USDJPY\|london\|bearish\|D1 | registered_matrix_candidate | 404 | 154 | 66.0 | 0.428571 | 0.571429 | 3 | 3 | 0.337662 | 10 |
| P3-TL-MATRIX-026 | USDJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 425 | 181 | 49.2944 | 0.272345 | 0.524862 | 3 | 1 | 0.392265 | 11 |
| P3-TL-MATRIX-027 | USDJPY\|london\|bullish\|D1 | registered_matrix_candidate | 776 | 404 | -2.3875 | -0.00591 | 0.398515 | 4 | 2 | 0.425743 | 19 |
| P3-TL-MATRIX-028 | USDJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1243 | 522 | -18.5586 | -0.035553 | 0.388889 | 5 | 2 | 0.348659 | 29 |
| P3-TL-MATRIX-029 | USDJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1168 | 447 | -60.9654 | -0.136388 | 0.348993 | 5 | 1 | 0.340045 | 29 |
| P3-TL-MATRIX-030 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 3 | 3 | 0.330189 | 11 |
| P3-TL-MATRIX-031 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | 458 | 252 | 97.5805 | 0.387224 | 0.563492 | 4 | 4 | 0.34127 | 15 |
| P3-TL-MATRIX-032 | USDJPY\|tokyo\|bullish\|D1 | registered_matrix_candidate | 924 | 482 | -11.3247 | -0.023495 | 0.394191 | 4 | 3 | 0.446058 | 24 |
| P3-TL-MATRIX-033 | USDJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | 1476 | 655 | 135.492 | 0.206858 | 0.485496 | 5 | 4 | 0.300763 | 29 |
| P3-TL-MATRIX-034 | XAGUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 482 | 482 | 41.1849 | 0.085446 | 0.43361 | 3 | 2 | 0.383817 | 21 |
| P3-TL-MATRIX-035 | XAGUSD\|london\|bullish\|D1 | registered_matrix_candidate | 249 | 249 | 100.5655 | 0.403878 | 0.558233 | 3 | 3 | 0.35743 | 15 |
| P3-TL-MATRIX-036 | XAGUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 584 | 584 | 118.5 | 0.202911 | 0.481164 | 5 | 3 | 0.241438 | 26 |
| P3-TL-MATRIX-037 | XAGUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 285 | 285 | 67.1006 | 0.235441 | 0.491228 | 3 | 2 | 0.378947 | 19 |
| P3-TL-MATRIX-038 | XAGUSD\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 5 | 4 | 0.243615 | 31 |
| P3-TL-MATRIX-039 | XAUUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 388 | 388 | 52.0 | 0.134021 | 0.453608 | 4 | 1 | 0.332474 | 22 |
| P3-TL-MATRIX-040 | XAUUSD\|london\|bullish\|D1 | registered_matrix_candidate | 395 | 395 | 71.6689 | 0.18144 | 0.470886 | 5 | 4 | 0.41519 | 19 |
| P3-TL-MATRIX-041 | XAUUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 786 | 786 | -119.3763 | -0.151878 | 0.333333 | 5 | 1 | 0.290076 | 35 |
| P3-TL-MATRIX-042 | XAUUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 283 | 283 | -2.2946 | -0.008108 | 0.39576 | 4 | 2 | 0.392226 | 19 |
| P3-TL-MATRIX-043 | XAUUSD\|ny\|bullish\|D1 | watchlist_from_controlled_spec | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 3 | 3 | 0.453376 | 20 |
| P3-TL-MATRIX-044 | XAUUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 619 | 619 | 31.4874 | 0.050868 | 0.420032 | 4 | 3 | 0.332795 | 34 |

## Synthesis

- The two JPY Tokyo cohorts remain the primary controlled family.
- The wider instrument universe remains registered for prospective PBO/effective_N accounting.
- This prevents accidental narrowing to only the historical winners.
