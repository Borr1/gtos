# Phase 3 Truth-Layer Effective-N Diagnostic

**Created UTC:** 2026-05-01T08:27:58.425567+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Matrix:** `research\phase_3_external_feed_validation\TRUTH_LAYER_PROSPECTIVE_CANDIDATE_MATRIX_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- Historical effective_N is diagnostic-only because the matrix was registered after historical discovery.
- Future promotion use requires prospective rows, frozen matrix membership, DSR, PBO, and effective_N together.

## Method

| primary | formula | promotion_threshold |
| --- | --- | --- |
| correlation_eigenvalue_participation_ratio | (sum(lambda)^2) / sum(lambda^2) on the candidate return correlation matrix | 3 |

## Matrix Effective-N

| status | period_count | candidate_count | active_candidate_count | effective_n | threshold_effective_n_gte_3_met | average_pairwise_correlation | average_abs_pairwise_correlation | path_start | path_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMPUTED_DIAGNOSTIC_ONLY | 52 | 44 | 44 | 20.575922 | True | 0.015728 | 0.117954 | 2022-01 | 2026-04 |

## Primary Children Effective-N

| status | period_count | candidate_count | active_candidate_count | effective_n | threshold_effective_n_gte_3_met | average_pairwise_correlation | average_abs_pairwise_correlation | path_start | path_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMPUTED_DIAGNOSTIC_ONLY | 52 | 2 | 2 | 1.97964 | False | -0.101414 | 0.101414 | 2022-01 | 2026-04 |

## Candidate Activity

| cohort_key | role | active_periods | resolved_r_n | sum_r | mean_period_sum_r | std_period_sum_r |
| --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 13 | 203 | 10.9683 | 0.210929 | 7.814716 |
| GBPJPY\|london\|bullish\|D1 | registered_matrix_candidate | 23 | 318 | 51.6575 | 0.993413 | 6.423056 |
| GBPJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 27 | 530 | 161.2745 | 3.101433 | 11.389412 |
| GBPJPY\|ny\|bullish\|D1 | registered_matrix_candidate | 20 | 261 | 15.5737 | 0.299494 | 7.995906 |
| GBPJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 28 | 449 | 79.2424 | 1.523892 | 11.31684 |
| GBPJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | 17 | 270 | 9.1669 | 0.176287 | 6.696896 |
| GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | 26 | 430 | 212.0002 | 4.076927 | 12.455211 |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | 28 | 657 | 150.0429 | 2.88544 | 13.745292 |
| GBPUSD\|london\|bearish\|D1 | registered_matrix_candidate | 21 | 727 | 179.6955 | 3.455683 | 16.201817 |
| GBPUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 25 | 671 | -93.5818 | -1.79965 | 15.086894 |
| GBPUSD\|london\|bullish\|D1 | registered_matrix_candidate | 21 | 614 | -18.589 | -0.357481 | 13.264508 |
| GBPUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 27 | 658 | 40.0797 | 0.770763 | 11.913265 |
| GBPUSD\|ny\|bearish\|D1 | registered_matrix_candidate | 18 | 298 | -30.7401 | -0.591156 | 7.43203 |
| GBPUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 17 | 214 | -28.0417 | -0.539263 | 6.361712 |
| GBPUSD\|ny\|bullish\|D1 | registered_matrix_candidate | 16 | 175 | 0.868 | 0.016692 | 4.986907 |
| GBPUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 22 | 264 | 29.2658 | 0.562804 | 7.523265 |
| NAS100\|london\|bullish\|D1 | registered_matrix_candidate | 19 | 591 | 16.8921 | 0.324848 | 17.836922 |
| NAS100\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 24 | 662 | 53.685 | 1.032404 | 15.876527 |
| NAS100\|ny\|bullish\|D1 | watchlist_from_controlled_spec | 21 | 631 | 235.8588 | 4.535746 | 17.641158 |
| NAS100\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 24 | 640 | -25.0 | -0.480769 | 13.512507 |
| US30_cash\|london\|bearish\|D1 | registered_matrix_candidate | 9 | 173 | 49.5 | 0.951923 | 5.575911 |
| US30_cash\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 20 | 355 | 18.2344 | 0.350662 | 4.932954 |
| US30_cash\|ny\|bullish\|D1 | registered_matrix_candidate | 17 | 230 | -2.6284 | -0.050546 | 6.793306 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | 18 | 320 | 162.7673 | 3.13014 | 10.784075 |
| USDJPY\|london\|bearish\|D1 | registered_matrix_candidate | 10 | 154 | 66.0 | 1.269231 | 6.943371 |
| USDJPY\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 11 | 181 | 49.2944 | 0.947969 | 7.420624 |
| USDJPY\|london\|bullish\|D1 | registered_matrix_candidate | 19 | 404 | -2.3875 | -0.045913 | 10.117275 |
| USDJPY\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 29 | 522 | -18.5586 | -0.356896 | 10.001216 |
| USDJPY\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 28 | 447 | -60.9654 | -1.172412 | 7.16834 |
| USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | 11 | 212 | 133.5983 | 2.569198 | 8.647408 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | registered_matrix_candidate | 15 | 252 | 97.5805 | 1.876548 | 7.939328 |
| USDJPY\|tokyo\|bullish\|D1 | registered_matrix_candidate | 24 | 482 | -11.3247 | -0.217783 | 7.914084 |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | registered_matrix_candidate | 29 | 655 | 135.492 | 2.605615 | 14.405523 |
| XAGUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 21 | 482 | 41.1849 | 0.792017 | 10.786762 |
| XAGUSD\|london\|bullish\|D1 | registered_matrix_candidate | 15 | 249 | 100.5655 | 1.933952 | 6.449602 |
| XAGUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 26 | 584 | 118.5 | 2.278846 | 14.386273 |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 19 | 285 | 67.1006 | 1.290396 | 9.816101 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | watchlist_from_controlled_spec | 31 | 509 | 178.5 | 3.432692 | 9.90545 |
| XAUUSD\|london\|bearish\|H4+H1_consensus | registered_matrix_candidate | 22 | 388 | 52.0 | 1.0 | 13.611198 |
| XAUUSD\|london\|bullish\|D1 | registered_matrix_candidate | 18 | 395 | 71.6689 | 1.378248 | 10.218147 |
| XAUUSD\|london\|bullish\|H4+H1_consensus | registered_matrix_candidate | 34 | 786 | -119.3763 | -2.295698 | 13.489 |
| XAUUSD\|ny\|bearish\|H4+H1_consensus | registered_matrix_candidate | 19 | 283 | -2.2946 | -0.044127 | 7.579092 |
| XAUUSD\|ny\|bullish\|D1 | watchlist_from_controlled_spec | 20 | 311 | 177.3642 | 3.41085 | 10.076232 |
| XAUUSD\|ny\|bullish\|H4+H1_consensus | registered_matrix_candidate | 34 | 619 | 31.4874 | 0.605527 | 13.33468 |

## Synthesis

- The matrix-level effective_N tells us whether the broader instrument universe carries independent validation paths.
- The primary-child effective_N is expected to be small because it contains only two selected cohorts.
- This diagnostic fills the infrastructure gap; it does not rescue historical evidence into promotion proof.
