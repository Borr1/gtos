# Phase 3 Registered Matrix Historical Replay Report

**Created UTC:** 2026-05-01T09:34:32.570359+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Matrix:** `research\phase_3_external_feed_validation\TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`
**Strategy spec:** `research\phase_3_external_feed_validation\HISTORICAL_REPLAY_STRATEGY_REGISTERED_MATRIX_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- This uses the same prequential replay boundary as the primary-cohort report.
- The full registered matrix is evaluated so we do not narrow to only the historical winners.
- Results are discovery/stress-map evidence because the matrix was registered after historical diagnostics.

## Replay Guardrails

| rows_replayed | candidate_count | duplicate_opportunity_keys | invalid_clock_rows | forbidden_exposure_violations | external_asof_violations | ai_attempted_rows | ai_call_count_sum | integrity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 205197 | 44 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Matrix Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 91407 | 31714 | 18541 | 2383.6216 | 0.128559 | 0.454237 |

## Methodology Context

| historical_pbo | pbo_status | matrix_effective_n | matrix_effective_n_status | primary_children_effective_n | promotion_usable |
| --- | --- | --- | --- | --- | --- |
| 0.5553613053613053 | POSTHOC_DIAGNOSTIC_ONLY | 20.575922 | COMPUTED_DIAGNOSTIC_ONLY | 1.97964 | False |

## Research Buckets

| research_bucket | candidate_count |
| --- | --- |
| MARGINAL_POSITIVE | 1 |
| NEGATIVE_OR_FLAT | 12 |
| POSITIVE_BUT_DOMINATED | 3 |
| POSITIVE_BUT_UNSTABLE | 23 |
| STRONG_DISCOVERY_LEAD | 5 |

## Bucket Rules

| research_bucket | rule |
| --- | --- |
| STRONG_DISCOVERY_LEAD | resolved_r_n >= 150, mean_r >= 0.25, win_rate >= 0.50, all valid years positive, max year share <= 0.45 |
| POSITIVE_BUT_UNSTABLE | mean_r > 0 but at least one valid year is non-positive |
| POSITIVE_BUT_DOMINATED | mean_r > 0, all valid years positive, but max year share > 0.45 |
| MARGINAL_POSITIVE | mean_r > 0 but below strong-lead thresholds |
| NEGATIVE_OR_FLAT | mean_r <= 0 |
| UNDERPOWERED | resolved_r_n < 150 |

## Follow-Up Lanes

| lane | candidate_count | resolved_r_n | mean_r | cohort_keys | next_action |
| --- | --- | --- | --- | --- | --- |
| lane_1_primary_controlled_family | 2 | 642 | 0.538315 | GBPJPY\|tokyo\|bullish\|D1, USDJPY\|tokyo\|bearish\|D1 | continue controlled reporting separately; do not mix with broader discovery ranking |
| lane_2_non_primary_strong_leads | 3 | 655 | 0.403276 | USDJPY\|london\|bearish\|D1, USDJPY\|tokyo\|bearish\|H4+H1_consensus, XAGUSD\|london\|bullish\|D1 | pre-register a new family before any deeper same-dataset replay or raw-OHLC adapter work |
| lane_3_dominance_watchlist | 3 | 1262 | 0.456411 | NAS100\|ny\|bullish\|D1, US30_cash\|ny\|bullish\|H4+H1_consensus, XAUUSD\|ny\|bullish\|D1 | run dominance/year concentration audit before treating as a candidate family |
| lane_4_high_mean_unstable | 4 | 1393 | 0.314838 | GBPJPY\|london\|bullish\|H4+H1_consensus, US30_cash\|london\|bearish\|D1, USDJPY\|london\|bearish\|H4+H1_consensus, XAGUSD\|ny\|bullish\|H4+H1_consensus | inspect fold/month failure anatomy; only then decide whether to register a family |
| lane_5_negative_controls | 12 | 5591 | -0.073956 | GBPUSD\|london\|bearish\|H4+H1_consensus, GBPUSD\|london\|bullish\|D1, GBPUSD\|ny\|bearish\|D1, GBPUSD\|ny\|bearish\|H4+H1_consensus, NAS100\|ny\|bullish\|H4+H1_consensus, US30_cash\|ny\|bullish\|D1, USDJPY\|london\|bullish\|D1, USDJPY\|london\|bullish\|H4+H1_consensus | use as controls for new replay infrastructure and avoid pooled headline claims |

## Instrument Summary

| symbol | candidate_count | replay_actions | population_actions | resolved_r_n | sum_r | mean_r | win_rate_estimate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAGUSD | 5 | 12314 | 2109 | 2109 | 505.851 | 0.239853 | 0.495021 |
| GBPJPY | 8 | 14706 | 7677 | 3118 | 689.9264 | 0.221272 | 0.496793 |
| US30_cash | 4 | 5338 | 1078 | 1078 | 227.8733 | 0.211385 | 0.476809 |
| USDJPY | 9 | 15115 | 7382 | 3309 | 388.729 | 0.117476 | 0.450891 |
| NAS100 | 4 | 11180 | 2524 | 2524 | 281.4359 | 0.111504 | 0.442552 |
| XAUUSD | 6 | 14792 | 2782 | 2782 | 210.8496 | 0.075791 | 0.428109 |
| GBPUSD | 8 | 17962 | 8162 | 3621 | 78.9564 | 0.021805 | 0.418393 |

## Session Summary

| session | candidate_count | replay_actions | population_actions | resolved_r_n | sum_r | mean_r | win_rate_estimate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tokyo | 7 | 13007 | 6518 | 2958 | 726.5561 | 0.245624 | 0.503719 |
| ny | 16 | 33874 | 9460 | 5936 | 828.358 | 0.139548 | 0.459737 |
| london | 21 | 44526 | 15736 | 9647 | 828.7075 | 0.085903 | 0.435679 |

## Role Summary

| role | candidate_count | replay_actions | population_actions | resolved_r_n | sum_r | mean_r | win_rate_estimate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary_controlled_child | 2 | 4062 | 1464 | 642 | 345.5985 | 0.538315 | 0.62461 |
| watchlist_from_controlled_spec | 4 | 11043 | 1771 | 1771 | 754.4903 | 0.426025 | 0.566347 |
| registered_matrix_candidate | 38 | 76302 | 28479 | 16128 | 1283.5328 | 0.079584 | 0.435144 |

## Strong Discovery Leads

| candidate_id | cohort_key | role | research_bucket | resolved_r_n | mean_r | win_rate | population_actions | historical_positive_valid_year_folds | historical_valid_year_folds | historical_max_year_resolved_share | followup_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-030 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | STRONG_DISCOVERY_LEAD | 212 | 0.630181 | 0.65566 | 508 | 3 | 3 | 0.330189 | primary family; keep controlled reporting separate from broader matrix ranking |
| P3-TL-MATRIX-007 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | STRONG_DISCOVERY_LEAD | 430 | 0.493024 | 0.609302 | 956 | 4 | 4 | 0.413953 | primary family; keep controlled reporting separate from broader matrix ranking |
| P3-TL-MATRIX-025 | USDJPY\|london\|bearish\|D1 | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 154 | 0.428571 | 0.571429 | 404 | 3 | 3 | 0.337662 | candidate for pre-registered family or raw-OHLC replay adapter |
| P3-TL-MATRIX-035 | XAGUSD\|london\|bullish\|D1 | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 249 | 0.403878 | 0.558233 | 249 | 3 | 3 | 0.35743 | candidate for pre-registered family or raw-OHLC replay adapter |
| P3-TL-MATRIX-031 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 252 | 0.387224 | 0.563492 | 458 | 4 | 4 | 0.34127 | candidate for pre-registered family or raw-OHLC replay adapter |

## Positive But Unstable

| candidate_id | cohort_key | role | research_bucket | resolved_r_n | mean_r | win_rate | population_actions | historical_positive_valid_year_folds | historical_valid_year_folds | historical_max_year_resolved_share | followup_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-038 | XAGUSD\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | POSITIVE_BUT_UNSTABLE | 509 | 0.350688 | 0.540275 | 509 | 4 | 5 | 0.243615 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-003 | GBPJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 530 | 0.304292 | 0.516981 | 1292 | 3 | 4 | 0.456604 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-021 | US30_cash\|london\|bearish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 173 | 0.286127 | 0.514451 | 173 | 2 | 3 | 0.393064 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-026 | USDJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 181 | 0.272345 | 0.524862 | 425 | 1 | 3 | 0.392265 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-009 | GBPUSD\|london\|bearish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 727 | 0.247174 | 0.503439 | 1396 | 4 | 5 | 0.264099 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-037 | XAGUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 285 | 0.235441 | 0.491228 | 285 | 2 | 3 | 0.378947 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-008 | GBPJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 657 | 0.228376 | 0.493151 | 1552 | 3 | 4 | 0.461187 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-033 | USDJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 655 | 0.206858 | 0.485496 | 1476 | 4 | 5 | 0.300763 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-036 | XAGUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 584 | 0.202911 | 0.481164 | 584 | 3 | 5 | 0.241438 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-040 | XAUUSD\|london\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 395 | 0.18144 | 0.470886 | 395 | 4 | 5 | 0.41519 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-005 | GBPJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 449 | 0.176486 | 0.492205 | 1201 | 2 | 5 | 0.438753 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-002 | GBPJPY\|london\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 318 | 0.162445 | 0.459119 | 792 | 2 | 4 | 0.342767 | inspect year/month instability before any controlled follow-up |

## Negative Or Flat Controls

| candidate_id | cohort_key | role | research_bucket | resolved_r_n | mean_r | win_rate | population_actions | historical_positive_valid_year_folds | historical_valid_year_folds | historical_max_year_resolved_share | followup_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-041 | XAUUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 786 | -0.151878 | 0.333333 | 786 | 1 | 5 | 0.290076 | use as negative control or deprioritize |
| P3-TL-MATRIX-010 | GBPUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 671 | -0.139466 | 0.359165 | 1337 | 2 | 5 | 0.295082 | use as negative control or deprioritize |
| P3-TL-MATRIX-029 | USDJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 447 | -0.136388 | 0.348993 | 1168 | 1 | 5 | 0.340045 | use as negative control or deprioritize |
| P3-TL-MATRIX-014 | GBPUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 214 | -0.131036 | 0.359813 | 573 | 2 | 3 | 0.280374 | use as negative control or deprioritize |
| P3-TL-MATRIX-013 | GBPUSD\|ny\|bearish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 298 | -0.103155 | 0.379195 | 620 | 2 | 4 | 0.295302 | use as negative control or deprioritize |
| P3-TL-MATRIX-020 | NAS100\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 640 | -0.039062 | 0.384375 | 640 | 1 | 4 | 0.315625 | use as negative control or deprioritize |
| P3-TL-MATRIX-028 | USDJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 522 | -0.035553 | 0.388889 | 1243 | 2 | 5 | 0.348659 | use as negative control or deprioritize |
| P3-TL-MATRIX-011 | GBPUSD\|london\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 614 | -0.030275 | 0.405537 | 1126 | 2 | 5 | 0.397394 | use as negative control or deprioritize |
| P3-TL-MATRIX-032 | USDJPY\|tokyo\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 482 | -0.023495 | 0.394191 | 924 | 3 | 4 | 0.446058 | use as negative control or deprioritize |
| P3-TL-MATRIX-023 | US30_cash\|ny\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 230 | -0.011428 | 0.391304 | 230 | 1 | 3 | 0.452174 | use as negative control or deprioritize |
| P3-TL-MATRIX-042 | XAUUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 283 | -0.008108 | 0.39576 | 283 | 2 | 4 | 0.392226 | use as negative control or deprioritize |
| P3-TL-MATRIX-027 | USDJPY\|london\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 404 | -0.00591 | 0.398515 | 776 | 2 | 4 | 0.425743 | use as negative control or deprioritize |

## Full Candidate Matrix

| candidate_id | cohort_key | role | research_bucket | resolved_r_n | mean_r | win_rate | population_actions | historical_positive_valid_year_folds | historical_valid_year_folds | historical_max_year_resolved_share | followup_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P3-TL-MATRIX-001 | GBPJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 203 | 0.054031 | 0.433498 | 512 | 1 | 4 | 0.325123 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-002 | GBPJPY\|london\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 318 | 0.162445 | 0.459119 | 792 | 2 | 4 | 0.342767 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-003 | GBPJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 530 | 0.304292 | 0.516981 | 1292 | 3 | 4 | 0.456604 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-004 | GBPJPY\|ny\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 261 | 0.059669 | 0.455939 | 728 | 2 | 4 | 0.298851 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-005 | GBPJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 449 | 0.176486 | 0.492205 | 1201 | 2 | 5 | 0.438753 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-006 | GBPJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 270 | 0.033951 | 0.425926 | 644 | 1 | 4 | 0.411111 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-007 | GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | STRONG_DISCOVERY_LEAD | 430 | 0.493024 | 0.609302 | 956 | 4 | 4 | 0.413953 | primary family; keep controlled reporting separate from broader matrix ranking |
| P3-TL-MATRIX-008 | GBPJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 657 | 0.228376 | 0.493151 | 1552 | 3 | 4 | 0.461187 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-009 | GBPUSD\|london\|bearish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 727 | 0.247174 | 0.503439 | 1396 | 4 | 5 | 0.264099 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-010 | GBPUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 671 | -0.139466 | 0.359165 | 1337 | 2 | 5 | 0.295082 | use as negative control or deprioritize |
| P3-TL-MATRIX-011 | GBPUSD\|london\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 614 | -0.030275 | 0.405537 | 1126 | 2 | 5 | 0.397394 | use as negative control or deprioritize |
| P3-TL-MATRIX-012 | GBPUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | MARGINAL_POSITIVE | 658 | 0.060911 | 0.420973 | 1768 | 4 | 4 | 0.398176 | keep as low-priority matrix context |
| P3-TL-MATRIX-013 | GBPUSD\|ny\|bearish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 298 | -0.103155 | 0.379195 | 620 | 2 | 4 | 0.295302 | use as negative control or deprioritize |
| P3-TL-MATRIX-014 | GBPUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 214 | -0.131036 | 0.359813 | 573 | 2 | 3 | 0.280374 | use as negative control or deprioritize |
| P3-TL-MATRIX-015 | GBPUSD\|ny\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 175 | 0.00496 | 0.428571 | 462 | 1 | 3 | 0.377143 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-016 | GBPUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 264 | 0.110855 | 0.443182 | 880 | 2 | 3 | 0.44697 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-017 | NAS100\|london\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 591 | 0.028582 | 0.411168 | 591 | 2 | 3 | 0.624365 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-018 | NAS100\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 662 | 0.081095 | 0.429003 | 662 | 3 | 4 | 0.321752 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-019 | NAS100\|ny\|bullish\|D1 | watchlist_from_controlled_spec | POSITIVE_BUT_DOMINATED | 631 | 0.373786 | 0.545166 | 631 | 3 | 3 | 0.581616 | inspect dominance and data concentration before follow-up |
| P3-TL-MATRIX-020 | NAS100\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 640 | -0.039062 | 0.384375 | 640 | 1 | 4 | 0.315625 | use as negative control or deprioritize |
| P3-TL-MATRIX-021 | US30_cash\|london\|bearish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 173 | 0.286127 | 0.514451 | 173 | 2 | 3 | 0.393064 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-022 | US30_cash\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 355 | 0.051365 | 0.411268 | 355 | 2 | 3 | 0.507042 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-023 | US30_cash\|ny\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 230 | -0.011428 | 0.391304 | 230 | 1 | 3 | 0.452174 | use as negative control or deprioritize |
| P3-TL-MATRIX-024 | US30_cash\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | POSITIVE_BUT_DOMINATED | 320 | 0.508648 | 0.590625 | 320 | 3 | 3 | 0.45625 | inspect dominance and data concentration before follow-up |
| P3-TL-MATRIX-025 | USDJPY\|london\|bearish\|D1 | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 154 | 0.428571 | 0.571429 | 404 | 3 | 3 | 0.337662 | candidate for pre-registered family or raw-OHLC replay adapter |
| P3-TL-MATRIX-026 | USDJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 181 | 0.272345 | 0.524862 | 425 | 1 | 3 | 0.392265 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-027 | USDJPY\|london\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 404 | -0.00591 | 0.398515 | 776 | 2 | 4 | 0.425743 | use as negative control or deprioritize |
| P3-TL-MATRIX-028 | USDJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 522 | -0.035553 | 0.388889 | 1243 | 2 | 5 | 0.348659 | use as negative control or deprioritize |
| P3-TL-MATRIX-029 | USDJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 447 | -0.136388 | 0.348993 | 1168 | 1 | 5 | 0.340045 | use as negative control or deprioritize |
| P3-TL-MATRIX-030 | USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | STRONG_DISCOVERY_LEAD | 212 | 0.630181 | 0.65566 | 508 | 3 | 3 | 0.330189 | primary family; keep controlled reporting separate from broader matrix ranking |
| P3-TL-MATRIX-031 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 252 | 0.387224 | 0.563492 | 458 | 4 | 4 | 0.34127 | candidate for pre-registered family or raw-OHLC replay adapter |
| P3-TL-MATRIX-032 | USDJPY\|tokyo\|bullish\|D1 | registered_matrix_candidate | NEGATIVE_OR_FLAT | 482 | -0.023495 | 0.394191 | 924 | 3 | 4 | 0.446058 | use as negative control or deprioritize |
| P3-TL-MATRIX-033 | USDJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 655 | 0.206858 | 0.485496 | 1476 | 4 | 5 | 0.300763 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-034 | XAGUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 482 | 0.085446 | 0.43361 | 482 | 2 | 3 | 0.383817 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-035 | XAGUSD\|london\|bullish\|D1 | registered_matrix_candidate | STRONG_DISCOVERY_LEAD | 249 | 0.403878 | 0.558233 | 249 | 3 | 3 | 0.35743 | candidate for pre-registered family or raw-OHLC replay adapter |
| P3-TL-MATRIX-036 | XAGUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 584 | 0.202911 | 0.481164 | 584 | 3 | 5 | 0.241438 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-037 | XAGUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 285 | 0.235441 | 0.491228 | 285 | 2 | 3 | 0.378947 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-038 | XAGUSD\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | POSITIVE_BUT_UNSTABLE | 509 | 0.350688 | 0.540275 | 509 | 4 | 5 | 0.243615 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-039 | XAUUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 388 | 0.134021 | 0.453608 | 388 | 1 | 4 | 0.332474 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-040 | XAUUSD\|london\|bullish\|D1 | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 395 | 0.18144 | 0.470886 | 395 | 4 | 5 | 0.41519 | inspect year/month instability before any controlled follow-up |
| P3-TL-MATRIX-041 | XAUUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 786 | -0.151878 | 0.333333 | 786 | 1 | 5 | 0.290076 | use as negative control or deprioritize |
| P3-TL-MATRIX-042 | XAUUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | NEGATIVE_OR_FLAT | 283 | -0.008108 | 0.39576 | 283 | 2 | 4 | 0.392226 | use as negative control or deprioritize |
| P3-TL-MATRIX-043 | XAUUSD\|ny\|bullish\|D1 | watchlist_from_controlled_spec | POSITIVE_BUT_DOMINATED | 311 | 0.570303 | 0.62701 | 311 | 3 | 3 | 0.453376 | inspect dominance and data concentration before follow-up |
| P3-TL-MATRIX-044 | XAUUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | POSITIVE_BUT_UNSTABLE | 619 | 0.050868 | 0.420032 | 619 | 3 | 4 | 0.332795 | inspect year/month instability before any controlled follow-up |

## Synthesis

- Other instruments do add value now: they provide a broader discovery map under the same no-leak replay boundary.
- The JPY Tokyo primary family remains separate because it was already pre-registered as the controlled child family.
- Strong non-primary candidates should become new pre-registered families before deeper evaluation.
- Negative and unstable candidates are useful as controls and as warnings against pooling everything into one headline.
