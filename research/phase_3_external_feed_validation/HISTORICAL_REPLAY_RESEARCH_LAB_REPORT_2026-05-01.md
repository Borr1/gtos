# Phase 3 Historical Replay Research Lab Report

**Created UTC:** 2026-05-01T09:12:08.207745+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Lab spec:** `research\phase_3_external_feed_validation\HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json`
**Strategy spec:** `research\phase_3_external_feed_validation\HISTORICAL_REPLAY_STRATEGY_PRIMARY_COHORTS_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- Replay is prequential: observation first, strategy decision second, scorer-only outcome third.
- This run is historical same-dataset evidence unless paired with a predeclared untouched split or prospective rows.
- DSR, PBO, and effective_N are not computed here.

## Reproducibility

| input_sha256 | lab_spec_sha256 | strategy_spec_sha256 | code_commit | run_mode | evidence_class |
| --- | --- | --- | --- | --- | --- |
| 0530a49f1eafcaa46bf94b9c9267670d815803ed3c067ecd5501a5a9888455ae | 6c95fbe15aa70f05715291e77ba8ea57e325cf1fafec02396d63add64556f091 | 290b961df9e2f58a96df56d656b193cc47064a36ad15a7710e6b1a71b901d224 | 98820c1+dirty | LOCKED_HISTORICAL_REPLAY | same_dataset_historical_diagnostic |

## Guardrails

| rows_loaded | rows_replayed | duplicate_opportunity_keys | invalid_clock_rows | forbidden_exposure_violations | external_asof_violations | ai_attempted_rows | ai_call_count_sum | integrity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 201135 | 4062 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 4062 | 1464 | 642 | 345.5985 | 0.538315 | 0.624611 |

## Action Outcomes

| NO_ENTRY | PRE_AI_POI_REJECT | SAME_BAR | SETUP_NOT_REFINABLE | SL | TIMEOUT | TP |
| --- | --- | --- | --- | --- | --- | --- |
| 1049 | 354 | 77 | 1925 | 232 | 51 | 374 |

## Scoring Exclusions

| not_resolution_safe | not_setup_row | truth_confidence_not_allowed | truth_outcome_excluded |
| --- | --- | --- | --- |
| 77 | 2279 | 2598 | 77 |

## Cohort Scores

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | 2753 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | {'NO_ENTRY': 695, 'PRE_AI_POI_REJECT': 235, 'SAME_BAR': 52, 'SETUP_NOT_REFINABLE': 1326, 'SL': 159, 'TIMEOUT': 49, 'TP': 237} |
| USDJPY\|tokyo\|bearish\|D1 | 1309 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | {'NO_ENTRY': 354, 'PRE_AI_POI_REJECT': 119, 'SAME_BAR': 25, 'SETUP_NOT_REFINABLE': 599, 'SL': 73, 'TIMEOUT': 2, 'TP': 137} |

## Period Scores

| period | actions_taken | resolved_r_n | sum_r | mean_r |
| --- | --- | --- | --- | --- |
| 2022-06 | 24 | 8 | -8.0 | -1.0 |
| 2022-08 | 96 | 5 | 2.5 | 0.5 |
| 2022-10 | 48 | 5 | 5.0 | 1.0 |
| 2022-11 | 180 | 43 | 42.5983 | 0.990658 |
| 2022-12 | 144 | 21 | -6.0 | -0.285714 |
| 2023-01 | 60 | 6 | 9.0 | 1.5 |
| 2023-02 | 72 | 19 | -1.5 | -0.078947 |
| 2023-03 | 60 | 13 | -13.0 | -1.0 |
| 2023-04 | 60 | 6 | 1.5 | 0.25 |
| 2023-05 | 96 | 12 | 18.0 | 1.5 |
| 2023-06 | 180 | 23 | 19.6965 | 0.85637 |
| 2023-07 | 60 | 7 | 10.5 | 1.5 |
| 2023-08 | 120 | 48 | 42.0 | 0.875 |
| 2023-11 | 132 | 0 | 0.0 |  |
| 2023-12 | 137 | 2 | 3.0 | 1.5 |
| 2024-01 | 96 | 28 | -5.5 | -0.196429 |
| 2024-02 | 24 | 0 | 0.0 |  |
| 2024-03 | 108 | 1 | 1.5 | 1.5 |
| 2024-05 | 84 | 5 | -5.0 | -1.0 |
| 2024-06 | 24 | 24 | 6.0 | 0.25 |
| 2024-07 | 32 | 0 | 0.0 |  |
| 2024-08 | 132 | 30 | 35.0 | 1.166667 |
| 2024-09 | 144 | 8 | 12.0 | 1.5 |
| 2024-10 | 72 | 4 | 1.0 | 0.25 |
| 2024-11 | 144 | 25 | 24.4005 | 0.97602 |
| 2025-02 | 180 | 58 | 14.5 | 0.25 |
| 2025-03 | 204 | 60 | 30.0 | 0.5 |
| 2025-04 | 72 | 0 | 0.0 |  |
| 2025-05 | 288 | 36 | 30.5664 | 0.849067 |
| 2025-06 | 216 | 35 | 31.8812 | 0.910891 |
| 2025-07 | 156 | 15 | -15.0 | -1.0 |
| 2025-09 | 72 | 13 | -13.0 | -1.0 |
| 2025-10 | 12 | 0 | 0.0 |  |
| 2025-12 | 180 | 31 | 46.5684 | 1.502206 |
| 2026-01 | 117 | 4 | 3.5 | 0.875 |
| 2026-02 | 105 | 31 | 1.5 | 0.048387 |
| 2026-03 | 71 | 16 | 20.3872 | 1.2742 |
| 2026-04 | 60 | 0 | 0.0 |  |

## Interpretation

- This validates the replay boundary: the strategy can select cohorts without receiving outcome/refinement fields.
- Positive historical replay results remain diagnostic because these cohorts were discovered from the same broad dataset.
- The same harness can now be used for broader controlled strategy experiments while preserving trial-budget language.
