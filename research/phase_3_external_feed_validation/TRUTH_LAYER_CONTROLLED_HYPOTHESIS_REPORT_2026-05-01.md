# Phase 3 Controlled Truth-Layer Hypothesis Report

**Created UTC:** 2026-05-01T08:27:47.407332+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Spec:** `research\phase_3_external_feed_validation\TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
**Verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- The cohorts were selected after same-dataset diagnostics, so this report is stability and invalidation evidence only.
- DSR-corrected p, PBO, and true effective_N are not computed here.
- This evaluator must not be used as alpha promotion proof.

## Data Integrity

| rows_scanned | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum | promotion_verdict_allowed | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 | False | NO_PROMOTION_VERDICT |

## Family Preconditions

| promotion_verdict_allowed | data_integrity_ok | primary_child_count | necessary_research_preconditions_met | promotion_blocked_reason |
| --- | --- | --- | --- | --- |
| False | True | 2 | True | DSR_PBO_EFFECTIVE_N_NOT_COMPUTED_AND_SAME_DATASET_SELECTION |

## Hypothesis Summary

| hypothesis_id | cohort_key | role | matching_setup_rows | population_rows | resolved_r_n | mean_r | win_rate | no_entry | no_entry_rate_population | valid_year_folds | positive_valid_year_folds | max_year_resolved_share | promotion_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | primary | 591 | 508 | 212 | 0.630181 | 0.65566 | 296 | 0.582677 | 3 | 3 | 0.330189 | NOT_ALLOWED_SAME_DATASET_AND_DSR_PBO_EFFECTIVE_N_NOT_COMPUTED |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | primary | 1192 | 956 | 430 | 0.493024 | 0.609302 | 526 | 0.550209 | 4 | 4 | 0.413953 | NOT_ALLOWED_SAME_DATASET_AND_DSR_PBO_EFFECTIVE_N_NOT_COMPUTED |

## Year Folds

| hypothesis_id | cohort_key | population_rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | no_entry_rate_population | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | immediate_stop | immediate_stop_rate_sl | max_year_resolved_share | year | gap_timing_unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 135 | 65 | 43.0983 | 0.663051 | 0.676923 | 42 | 21 | 2 | 70 | 0.518519 | 0 | 0 | 57 | 0 | 57 | 1 | 0.047619 |  | 2022 | 0 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 43 | 24 | 6.0 | 0.25 | 0.5 | 12 | 12 | 0 | 19 | 0.44186 | 0 | 0 | 22 | 0 | 22 | 0 | 0.0 |  | 2023 | 0 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 116 | 53 | 52.0 | 0.981132 | 0.792453 | 42 | 11 | 0 | 63 | 0.543103 | 0 | 0 | 37 | 0 | 37 | 0 | 0.0 |  | 2024 | 0 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 214 | 70 | 32.5 | 0.464286 | 0.585714 | 41 | 29 | 0 | 144 | 0.672897 | 0 | 0 | 51 | 0 | 51 | 0 | 0.0 |  | 2025 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 57 | 17 | -7.0 | -0.411765 | 0.235294 | 4 | 13 | 0 | 40 | 0.701754 | 0 | 0 | 13 | 0 | 13 | 4 | 0.307692 |  | 2022 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 291 | 112 | 83.1965 | 0.742826 | 0.723214 | 71 | 31 | 10 | 179 | 0.61512 | 0 | 0 | 19 | 0 | 19 | 1 | 0.032258 |  | 2023 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 169 | 72 | 17.4005 | 0.241674 | 0.555556 | 29 | 31 | 12 | 97 | 0.573964 | 0 | 0 | 12 | 0 | 12 | 0 | 0.0 |  | 2024 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 340 | 178 | 93.016 | 0.522562 | 0.589888 | 101 | 65 | 12 | 162 | 0.476471 | 0 | 0 | 138 | 0 | 138 | 0 | 0.0 |  | 2025 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 99 | 51 | 25.3872 | 0.497788 | 0.627451 | 28 | 19 | 4 | 48 | 0.484848 | 0 | 0 | 33 | 0 | 33 | 0 | 0.0 |  | 2026 | 0 |

## Early vs Recent

| hypothesis_id | cohort_key | population_rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | no_entry_rate_population | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | immediate_stop | immediate_stop_rate_sl | max_year_resolved_share | period | gap_timing_unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 178 | 89 | 49.0983 | 0.551666 | 0.629213 | 54 | 33 | 2 | 89 | 0.5 | 0 | 0 | 79 | 0 | 79 | 1 | 0.030303 |  | 2022_2023 | 0 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 330 | 123 | 84.5 | 0.686992 | 0.674797 | 83 | 40 | 0 | 207 | 0.627273 | 0 | 0 | 88 | 0 | 88 | 0 | 0.0 |  | 2024_2026_partial | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 348 | 129 | 76.1965 | 0.590671 | 0.658915 | 75 | 44 | 10 | 219 | 0.62931 | 0 | 0 | 32 | 0 | 32 | 5 | 0.113636 |  | 2022_2023 | 0 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 608 | 301 | 135.8037 | 0.451175 | 0.58804 | 158 | 115 | 28 | 307 | 0.504934 | 0 | 0 | 183 | 0 | 183 | 0 | 0.0 |  | 2024_2026_partial | 0 |

## Exclusions

| hypothesis_id | cohort_key | reason | rows |
| --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | not_resolution_safe | 25 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | not_setup_row | 718 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | truth_confidence_not_allowed | 801 |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | truth_outcome_excluded | 25 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | not_resolution_safe | 52 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | not_setup_row | 1561 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | truth_confidence_not_allowed | 1797 |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | truth_outcome_excluded | 52 |

## Synthesis

- The locked populations can be audited with this report.
- A positive diagnostic result here is not out-of-sample validation because selection already used this truth-layer dataset.
- Promotion remains blocked until a separate evaluator computes DSR, PBO, effective_N, and validates on untouched future or prospective data.
