# Phase 3 Truth-Layer Cohort Stability Follow-Up

**Created UTC:** 2026-05-01T07:27:52.291243+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Cohort spec:** `research\phase_3_external_feed_validation\TRUTH_LAYER_FOLLOWUP_COHORTS_V1.json`
**Rows scanned:** 205197

## Interpretation Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- No AI/API calls are made. `ai_attempted_rows` and `ai_call_count_sum` must remain zero.
- These cohorts were selected after seeing the diagnostic report, so this is stability and invalidation work, not out-of-sample proof.
- `CLEAN_*` scopes exclude same-bar and lower-timeframe gappy outcomes. Selected-source lower-timeframe gap counts remain visible as diagnostics, not hard exclusions.
- `RESOLUTION_SAFE_*` scopes additionally exclude selected-source gaps before or at the mechanical resolution point.
- `ZERO_GAP_*` scopes additionally require zero selected-source lower-timeframe gap counts in the tested horizon.
- DSR-corrected p, PBO, and true effective_N are not computed here; the report only checks whether a cohort is worth a deeper controlled research run.

## Data Integrity

| rows_scanned | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum | selection_status |
| --- | --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 | post_diagnostic_followup_v1 |

## Follow-Up Priority

| cohort_key | role | recommended_treatment | priority_score | clean_high_n | clean_high_mean_r | clean_high_win_rate | clean_valid_years | clean_positive_years | clean_worst_year | clean_worst_year_mean_r | high_only_n | high_only_mean_r | high_only_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|tokyo\|bearish\|D1 | primary_followup | PRIMARY_CONTROLLED_RESEARCH | 0.883181 | 212 | 0.630181 | 0.65566 | 3 | 3 | 2025 | 0.464286 | 212 | 0.630181 | 0.65566 |
| XAUUSD\|ny\|bullish\|D1 | primary_followup | CONTROLLED_RESEARCH_WATCHLIST | 0.846365 | 311 | 0.570303 | 0.62701 | 3 | 3 | 2023 | 0.081081 | 311 | 0.570303 | 0.62701 |
| GBPJPY\|tokyo\|bullish\|D1 | primary_followup | PRIMARY_CONTROLLED_RESEARCH | 0.800524 | 430 | 0.493024 | 0.609302 | 4 | 4 | 2024 | 0.241674 | 430 | 0.493024 | 0.609302 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | ambiguity_watchlist | CONTROLLED_RESEARCH_WATCHLIST | 0.785523 | 320 | 0.508648 | 0.590625 | 3 | 3 | 2024 | 0.503445 | 320 | 0.508648 | 0.590625 |
| NAS100\|ny\|bullish\|D1 | primary_followup | CONTROLLED_RESEARCH_WATCHLIST | 0.665728 | 631 | 0.373786 | 0.545166 | 3 | 3 | 2024 | 0.062339 | 631 | 0.373786 | 0.545166 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | secondary_followup | CONTROLLED_RESEARCH_WATCHLIST | 0.637938 | 509 | 0.350688 | 0.540275 | 5 | 4 | 2022 | -0.032258 | 509 | 0.350688 | 0.540275 |

## Cohort Scope Summary

| cohort_key | scope | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop_rate_sl | no_entry_rate_setup | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | HIGH_ONLY | 956 | 430 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.550209 | 0.0 | 0.224895 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | HIGH_MEDIUM | 1140 | 445 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.609649 | 0.0 | 0.188596 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | CLEAN_HIGH | 956 | 430 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.550209 | 0.0 | 0.224895 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | CLEAN_HIGH_MEDIUM | 1140 | 445 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.609649 | 0.0 | 0.188596 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 956 | 430 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.550209 | 0.0 | 0.224895 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | RESOLUTION_SAFE_HIGH_MEDIUM | 1140 | 445 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 0.031447 | 0.609649 | 0.0 | 0.188596 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | ZERO_GAP_HIGH | 741 | 215 | 0.683023 | 0.697674 | 121 | 56 | 38 | 526 | 0 | 0 | 0 | 0 | 0 | 0 | 0.071429 | 0.709852 | 0.0 | 0.0 | 0.0 |
| GBPJPY\|tokyo\|bullish\|D1 | ZERO_GAP_HIGH_MEDIUM | 925 | 230 | 0.688573 | 0.717391 | 125 | 56 | 49 | 695 | 0 | 0 | 0 | 0 | 0 | 0 | 0.071429 | 0.751351 | 0.0 | 0.0 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | HIGH_ONLY | 311 | 311 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 0.068966 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | HIGH_MEDIUM | 1574 | 490 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 0.043956 | 0.688691 | 0.0 | 0.197586 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | CLEAN_HIGH | 311 | 311 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 0.068966 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | CLEAN_HIGH_MEDIUM | 1574 | 490 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 0.043956 | 0.688691 | 0.0 | 0.197586 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 311 | 311 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 0.068966 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH_MEDIUM | 1574 | 490 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 0.043956 | 0.688691 | 0.0 | 0.197586 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | ZERO_GAP_HIGH | 0 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| XAUUSD\|ny\|bullish\|D1 | ZERO_GAP_HIGH_MEDIUM | 1263 | 179 | 0.480503 | 0.597765 | 90 | 66 | 23 | 1084 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.858274 | 0.0 | 0.0 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | HIGH_ONLY | 508 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.582677 | 0.0 | 0.32874 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | HIGH_MEDIUM | 566 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.625442 | 0.0 | 0.295053 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | CLEAN_HIGH | 508 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.582677 | 0.0 | 0.32874 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | CLEAN_HIGH_MEDIUM | 566 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.625442 | 0.0 | 0.295053 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | RESOLUTION_SAFE_HIGH | 508 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.582677 | 0.0 | 0.32874 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | RESOLUTION_SAFE_HIGH_MEDIUM | 566 | 212 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 0.013699 | 0.625442 | 0.0 | 0.295053 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | ZERO_GAP_HIGH | 341 | 45 | 0.679962 | 0.688889 | 29 | 14 | 2 | 296 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.868035 | 0.0 | 0.0 | 0.0 |
| USDJPY\|tokyo\|bearish\|D1 | ZERO_GAP_HIGH_MEDIUM | 399 | 45 | 0.679962 | 0.688889 | 29 | 14 | 2 | 354 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.887218 | 0.0 | 0.0 | 0.0 |
| NAS100\|ny\|bullish\|D1 | HIGH_ONLY | 631 | 631 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 0.101045 | 0.0 | 0.0 | 1.0 | 0.0 |
| NAS100\|ny\|bullish\|D1 | HIGH_MEDIUM | 1874 | 830 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 0.094972 | 0.557097 | 0.0 | 0.336713 | 0.0 |
| NAS100\|ny\|bullish\|D1 | CLEAN_HIGH | 631 | 631 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 0.101045 | 0.0 | 0.0 | 1.0 | 0.0 |
| NAS100\|ny\|bullish\|D1 | CLEAN_HIGH_MEDIUM | 1874 | 830 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 0.094972 | 0.557097 | 0.0 | 0.336713 | 0.0 |
| NAS100\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 631 | 631 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 0.101045 | 0.0 | 0.0 | 1.0 | 0.0 |
| NAS100\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH_MEDIUM | 1874 | 830 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 0.094972 | 0.557097 | 0.0 | 0.336713 | 0.0 |
| NAS100\|ny\|bullish\|D1 | ZERO_GAP_HIGH | 0 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| NAS100\|ny\|bullish\|D1 | ZERO_GAP_HIGH_MEDIUM | 1243 | 199 | 0.431944 | 0.623116 | 85 | 71 | 43 | 1044 | 0 | 0 | 0 | 0 | 0 | 0 | 0.070423 | 0.839903 | 0.0 | 0.0 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | HIGH_ONLY | 320 | 320 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 0.229008 | 0.0 | 0.0 | 1.0 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | HIGH_MEDIUM | 1116 | 341 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 0.244604 | 0.694444 | 0.0 | 0.286738 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 320 | 320 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 0.229008 | 0.0 | 0.0 | 1.0 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH_MEDIUM | 1116 | 341 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 0.244604 | 0.694444 | 0.0 | 0.286738 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH | 320 | 320 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 0.229008 | 0.0 | 0.0 | 1.0 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH_MEDIUM | 1116 | 341 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 0.244604 | 0.694444 | 0.0 | 0.286738 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH | 0 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH_MEDIUM | 796 | 21 | 0.196281 | 0.47619 | 8 | 8 | 5 | 775 | 0 | 0 | 0 | 0 | 0 | 0 | 0.5 | 0.973618 | 0.0 | 0.0 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | HIGH_ONLY | 509 | 509 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 0.029915 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | HIGH_MEDIUM | 2833 | 728 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 0.072607 | 0.743029 | 0.0 | 0.179668 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 509 | 509 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 0.029915 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH_MEDIUM | 2833 | 728 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 0.072607 | 0.743029 | 0.0 | 0.179668 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH | 509 | 509 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 0.029915 | 0.0 | 0.0 | 1.0 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH_MEDIUM | 2833 | 728 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 0.072607 | 0.743029 | 0.0 | 0.179668 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH | 0 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH_MEDIUM | 2324 | 219 | 0.597444 | 0.666667 | 121 | 69 | 29 | 2105 | 0 | 0 | 0 | 0 | 0 | 0 | 0.217391 | 0.905766 | 0.0 | 0.0 | 0.0 |

## Clean High Year Stability

| cohort_key | scope | valid_years | positive_years | positive_year_rate | worst_year | worst_year_mean_r | best_year | best_year_mean_r | min_valid_year_resolved_n | max_year_resolved_share | underpowered_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | CLEAN_HIGH | 4 | 4 | 1.0 | 2024 | 0.241674 | 2023 | 0.742826 | 51 | 0.413953 | 1 |
| XAUUSD\|ny\|bullish\|D1 | CLEAN_HIGH | 3 | 3 | 1.0 | 2023 | 0.081081 | 2026 | 1.0 | 37 | 0.453376 | 2 |
| USDJPY\|tokyo\|bearish\|D1 | CLEAN_HIGH | 3 | 3 | 1.0 | 2025 | 0.464286 | 2024 | 0.981132 | 53 | 0.330189 | 1 |
| NAS100\|ny\|bullish\|D1 | CLEAN_HIGH | 3 | 3 | 1.0 | 2024 | 0.062339 | 2023 | 0.504772 | 99 | 0.581616 | 1 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 3 | 3 | 1.0 | 2024 | 0.503445 | 2025 | 0.952834 | 58 | 0.45625 | 1 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 5 | 4 | 0.8 | 2022 | -0.032258 | 2023 | 0.835938 | 64 | 0.243615 | 0 |

## Resolution-Safe High Stability

| cohort_key | scope | valid_years | positive_years | positive_year_rate | worst_year | worst_year_mean_r | best_year | best_year_mean_r | min_valid_year_resolved_n | max_year_resolved_share | underpowered_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 4 | 4 | 1.0 | 2024 | 0.241674 | 2023 | 0.742826 | 51 | 0.413953 | 1 |
| XAUUSD\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 3 | 3 | 1.0 | 2023 | 0.081081 | 2026 | 1.0 | 37 | 0.453376 | 2 |
| USDJPY\|tokyo\|bearish\|D1 | RESOLUTION_SAFE_HIGH | 3 | 3 | 1.0 | 2025 | 0.464286 | 2024 | 0.981132 | 53 | 0.330189 | 1 |
| NAS100\|ny\|bullish\|D1 | RESOLUTION_SAFE_HIGH | 3 | 3 | 1.0 | 2024 | 0.062339 | 2023 | 0.504772 | 99 | 0.581616 | 1 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH | 3 | 3 | 1.0 | 2024 | 0.503445 | 2025 | 0.952834 | 58 | 0.45625 | 1 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | RESOLUTION_SAFE_HIGH | 5 | 4 | 0.8 | 2022 | -0.032258 | 2023 | 0.835938 | 64 | 0.243615 | 0 |

## High-Only Year Stability

| cohort_key | scope | valid_years | positive_years | positive_year_rate | worst_year | worst_year_mean_r | best_year | best_year_mean_r | min_valid_year_resolved_n | max_year_resolved_share | underpowered_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | HIGH_ONLY | 4 | 4 | 1.0 | 2024 | 0.241674 | 2023 | 0.742826 | 51 | 0.413953 | 1 |
| XAUUSD\|ny\|bullish\|D1 | HIGH_ONLY | 3 | 3 | 1.0 | 2023 | 0.081081 | 2026 | 1.0 | 37 | 0.453376 | 2 |
| USDJPY\|tokyo\|bearish\|D1 | HIGH_ONLY | 3 | 3 | 1.0 | 2025 | 0.464286 | 2024 | 0.981132 | 53 | 0.330189 | 1 |
| NAS100\|ny\|bullish\|D1 | HIGH_ONLY | 3 | 3 | 1.0 | 2024 | 0.062339 | 2023 | 0.504772 | 99 | 0.581616 | 1 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | HIGH_ONLY | 3 | 3 | 1.0 | 2024 | 0.503445 | 2025 | 0.952834 | 58 | 0.45625 | 1 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | HIGH_ONLY | 5 | 4 | 0.8 | 2022 | -0.032258 | 2023 | 0.835938 | 64 | 0.243615 | 0 |

## Zero-Gap High Sensitivity

| cohort_key | scope | valid_years | positive_years | positive_year_rate | worst_year | worst_year_mean_r | best_year | best_year_mean_r | min_valid_year_resolved_n | max_year_resolved_share | underpowered_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | ZERO_GAP_HIGH | 3 | 3 | 1.0 | 2024 | 0.031675 | 2023 | 0.99136 | 40 | 0.432558 | 2 |
| XAUUSD\|ny\|bullish\|D1 | ZERO_GAP_HIGH | 0 | 0 | 0.0 |  |  |  |  | 0 | 0.0 | 0 |
| USDJPY\|tokyo\|bearish\|D1 | ZERO_GAP_HIGH | 0 | 0 | 0.0 |  |  |  |  | 0 | 0.0 | 4 |
| NAS100\|ny\|bullish\|D1 | ZERO_GAP_HIGH | 0 | 0 | 0.0 |  |  |  |  | 0 | 0.0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH | 0 | 0 | 0.0 |  |  |  |  | 0 | 0.0 | 0 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | ZERO_GAP_HIGH | 0 | 0 | 0.0 |  |  |  |  | 0 | 0.0 | 0 |

## Early vs Recent Split

| cohort_key | scope | period | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | CLEAN_HIGH | 2022_2023 | 129 | 0.590671 | 0.658915 | 75 | 44 | 10 | 219 | 0 | 0 | 32 | 0 | 32 |
| GBPJPY\|tokyo\|bullish\|D1 | CLEAN_HIGH | 2024_2026_partial | 301 | 0.451175 | 0.58804 | 158 | 115 | 28 | 307 | 0 | 0 | 183 | 0 | 183 |
| XAUUSD\|ny\|bullish\|D1 | CLEAN_HIGH | 2022_2023 | 64 | 0.263503 | 0.5 | 32 | 32 | 0 | 0 | 0 | 0 | 64 | 0 | 64 |
| XAUUSD\|ny\|bullish\|D1 | CLEAN_HIGH | 2024_2026_partial | 247 | 0.649798 | 0.659919 | 163 | 84 | 0 | 0 | 0 | 0 | 247 | 0 | 247 |
| USDJPY\|tokyo\|bearish\|D1 | CLEAN_HIGH | 2022_2023 | 89 | 0.551666 | 0.629213 | 54 | 33 | 2 | 89 | 0 | 0 | 79 | 0 | 79 |
| USDJPY\|tokyo\|bearish\|D1 | CLEAN_HIGH | 2024_2026_partial | 123 | 0.686992 | 0.674797 | 83 | 40 | 0 | 207 | 0 | 0 | 88 | 0 | 88 |
| NAS100\|ny\|bullish\|D1 | CLEAN_HIGH | 2022_2023 | 144 | 0.504772 | 0.583333 | 84 | 60 | 0 | 0 | 0 | 0 | 144 | 0 | 144 |
| NAS100\|ny\|bullish\|D1 | CLEAN_HIGH | 2024_2026_partial | 487 | 0.335055 | 0.533881 | 260 | 227 | 0 | 0 | 0 | 0 | 487 | 0 | 487 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 2022_2023 | 91 | 0.620879 | 0.648352 | 59 | 32 | 0 | 0 | 0 | 0 | 91 | 0 | 91 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 2024_2026_partial | 229 | 0.464049 | 0.567686 | 130 | 99 | 0 | 0 | 0 | 0 | 229 | 0 | 229 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 2022_2023 | 157 | 0.321656 | 0.528662 | 83 | 74 | 0 | 0 | 0 | 0 | 157 | 0 | 157 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | CLEAN_HIGH | 2024_2026_partial | 352 | 0.363636 | 0.545455 | 192 | 160 | 0 | 0 | 0 | 0 | 352 | 0 | 352 |

## Cohort Details

### GBPJPY|tokyo|bullish|D1

- Role: `primary_followup`
- Treatment: `PRIMARY_CONTROLLED_RESEARCH`
- Selection reason: Top high-confidence diagnostic score with low lower-timeframe gap burden and strong pooled mean R.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 956 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.550209 | 0.369767 | 0.0 | 0.224895 | 0.0 |
| HIGH_MEDIUM | 1140 | 1140 | 445 | 223.5221 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.609649 | 0.357303 | 0.0 | 0.188596 | 0.0 |
| CLEAN_HIGH | 956 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.550209 | 0.369767 | 0.0 | 0.224895 | 0.0 |
| CLEAN_HIGH_MEDIUM | 1140 | 1140 | 445 | 223.5221 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.609649 | 0.357303 | 0.0 | 0.188596 | 0.0 |
| RESOLUTION_SAFE_HIGH | 956 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | 233 | 159 | 38 | 526 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.550209 | 0.369767 | 0.0 | 0.224895 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 1140 | 1140 | 445 | 223.5221 | 0.502297 | 0.622472 | 237 | 159 | 49 | 695 | 0 | 0 | 215 | 0 | 215 | 0 | 5 | 0.031447 | 0.609649 | 0.357303 | 0.0 | 0.188596 | 0.0 |
| ZERO_GAP_HIGH | 741 | 741 | 215 | 146.85 | 0.683023 | 0.697674 | 121 | 56 | 38 | 526 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0.071429 | 0.709852 | 0.260465 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 925 | 925 | 230 | 158.3719 | 0.688573 | 0.717391 | 125 | 56 | 49 | 695 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0.071429 | 0.751351 | 0.243478 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 57 | 57 | 17 | -7.0 | -0.411765 | 0.235294 | 4 | 13 | 0 | 40 | 0 | 0 | 13 | 0 | 13 | 0 | 4 | 0.307692 | 0.701754 | 0.764706 | 0.0 | 0.22807 | 0.0 |
| 2023 | 291 | 291 | 112 | 83.1965 | 0.742826 | 0.723214 | 71 | 31 | 10 | 179 | 0 | 0 | 19 | 0 | 19 | 0 | 1 | 0.032258 | 0.61512 | 0.276786 | 0.0 | 0.065292 | 0.0 |
| 2024 | 169 | 169 | 72 | 17.4005 | 0.241674 | 0.555556 | 29 | 31 | 12 | 97 | 0 | 0 | 12 | 0 | 12 | 0 | 0 | 0.0 | 0.573964 | 0.430556 | 0.0 | 0.071006 | 0.0 |
| 2025 | 340 | 340 | 178 | 93.016 | 0.522562 | 0.589888 | 101 | 65 | 12 | 162 | 0 | 0 | 138 | 0 | 138 | 0 | 0 | 0.0 | 0.476471 | 0.365169 | 0.0 | 0.405882 | 0.0 |
| 2026 | 99 | 99 | 51 | 25.3872 | 0.497788 | 0.627451 | 28 | 19 | 4 | 48 | 0 | 0 | 33 | 0 | 33 | 0 | 0 | 0.0 | 0.484848 | 0.372549 | 0.0 | 0.333333 | 0.0 |

Treatment reasons:

- CLEAN_HIGH clears sample, >=3 yearly folds, all valid years positive, and no single-year dominance flag.

### XAUUSD|ny|bullish|D1

- Role: `primary_followup`
- Treatment: `CONTROLLED_RESEARCH_WATCHLIST`
- Selection reason: Strong high-confidence and high+medium pooled diagnostics on the main production symbol/session.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 311 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.068966 | 0.0 | 0.37299 | 0.0 | 1.0 | 0.0 |
| HIGH_MEDIUM | 1574 | 1574 | 490 | 263.3742 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.043956 | 0.688691 | 0.371429 | 0.0 | 0.197586 | 0.0 |
| CLEAN_HIGH | 311 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.068966 | 0.0 | 0.37299 | 0.0 | 1.0 | 0.0 |
| CLEAN_HIGH_MEDIUM | 1574 | 1574 | 490 | 263.3742 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.043956 | 0.688691 | 0.371429 | 0.0 | 0.197586 | 0.0 |
| RESOLUTION_SAFE_HIGH | 311 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | 195 | 116 | 0 | 0 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.068966 | 0.0 | 0.37299 | 0.0 | 1.0 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 1574 | 1574 | 490 | 263.3742 | 0.537498 | 0.616327 | 285 | 182 | 23 | 1084 | 0 | 0 | 311 | 0 | 311 | 0 | 8 | 0.043956 | 0.688691 | 0.371429 | 0.0 | 0.197586 | 0.0 |
| ZERO_GAP_HIGH | 0 | 0 | 0 | 0.0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 1263 | 1263 | 179 | 86.01 | 0.480503 | 0.597765 | 90 | 66 | 23 | 1084 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.858274 | 0.368715 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 27 | 27 | 27 | 13.8642 | 0.513489 | 0.592593 | 16 | 11 | 0 | 0 | 0 | 0 | 27 | 0 | 27 | 0 | 0 | 0.0 | 0.0 | 0.407407 | 0.0 | 1.0 | 0.0 |
| 2023 | 37 | 37 | 37 | 3.0 | 0.081081 | 0.432432 | 16 | 21 | 0 | 0 | 0 | 0 | 37 | 0 | 37 | 0 | 6 | 0.285714 | 0.0 | 0.567568 | 0.0 | 1.0 | 0.0 |
| 2024 | 26 | 26 | 26 | 9.0 | 0.346154 | 0.538462 | 14 | 12 | 0 | 0 | 0 | 0 | 26 | 0 | 26 | 0 | 0 | 0.0 | 0.0 | 0.461538 | 0.0 | 1.0 | 0.0 |
| 2025 | 141 | 141 | 141 | 71.5 | 0.507092 | 0.602837 | 85 | 56 | 0 | 0 | 0 | 0 | 141 | 0 | 141 | 0 | 1 | 0.017857 | 0.0 | 0.397163 | 0.0 | 1.0 | 0.0 |
| 2026 | 80 | 80 | 80 | 80.0 | 1.0 | 0.8 | 64 | 16 | 0 | 0 | 0 | 0 | 80 | 0 | 80 | 0 | 1 | 0.0625 | 0.0 | 0.2 | 0.0 | 1.0 | 0.0 |

Treatment reasons:

- CLEAN_HIGH has enough sample and mostly positive yearly folds, but at least one stability or dominance caution remains.

### USDJPY|tokyo|bearish|D1

- Role: `primary_followup`
- Treatment: `PRIMARY_CONTROLLED_RESEARCH`
- Selection reason: High pooled mean R and win rate with low immediate-stop burden, but smaller sample than the top cohorts.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 508 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.582677 | 0.34434 | 0.0 | 0.32874 | 0.0 |
| HIGH_MEDIUM | 566 | 566 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.625442 | 0.34434 | 0.0 | 0.295053 | 0.0 |
| CLEAN_HIGH | 508 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.582677 | 0.34434 | 0.0 | 0.32874 | 0.0 |
| CLEAN_HIGH_MEDIUM | 566 | 566 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.625442 | 0.34434 | 0.0 | 0.295053 | 0.0 |
| RESOLUTION_SAFE_HIGH | 508 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 296 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.582677 | 0.34434 | 0.0 | 0.32874 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 566 | 566 | 212 | 133.5983 | 0.630181 | 0.65566 | 137 | 73 | 2 | 354 | 0 | 0 | 167 | 0 | 167 | 0 | 1 | 0.013699 | 0.625442 | 0.34434 | 0.0 | 0.295053 | 0.0 |
| ZERO_GAP_HIGH | 341 | 341 | 45 | 30.5983 | 0.679962 | 0.688889 | 29 | 14 | 2 | 296 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.868035 | 0.311111 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 399 | 399 | 45 | 30.5983 | 0.679962 | 0.688889 | 29 | 14 | 2 | 354 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.887218 | 0.311111 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 135 | 135 | 65 | 43.0983 | 0.663051 | 0.676923 | 42 | 21 | 2 | 70 | 0 | 0 | 57 | 0 | 57 | 0 | 1 | 0.047619 | 0.518519 | 0.323077 | 0.0 | 0.422222 | 0.0 |
| 2023 | 43 | 43 | 24 | 6.0 | 0.25 | 0.5 | 12 | 12 | 0 | 19 | 0 | 0 | 22 | 0 | 22 | 0 | 0 | 0.0 | 0.44186 | 0.5 | 0.0 | 0.511628 | 0.0 |
| 2024 | 116 | 116 | 53 | 52.0 | 0.981132 | 0.792453 | 42 | 11 | 0 | 63 | 0 | 0 | 37 | 0 | 37 | 0 | 0 | 0.0 | 0.543103 | 0.207547 | 0.0 | 0.318966 | 0.0 |
| 2025 | 214 | 214 | 70 | 32.5 | 0.464286 | 0.585714 | 41 | 29 | 0 | 144 | 0 | 0 | 51 | 0 | 51 | 0 | 0 | 0.0 | 0.672897 | 0.414286 | 0.0 | 0.238318 | 0.0 |

Treatment reasons:

- CLEAN_HIGH clears sample, >=3 yearly folds, all valid years positive, and no single-year dominance flag.

### NAS100|ny|bullish|D1

- Role: `primary_followup`
- Treatment: `CONTROLLED_RESEARCH_WATCHLIST`
- Selection reason: Large sample and positive pooled diagnostics in a key index cohort, with meaningful gappy/same-bar ambiguity to test.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 631 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 29 | 0.101045 | 0.0 | 0.454834 | 0.0 | 1.0 | 0.0 |
| HIGH_MEDIUM | 1874 | 1874 | 830 | 321.8157 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 34 | 0.094972 | 0.557097 | 0.431325 | 0.0 | 0.336713 | 0.0 |
| CLEAN_HIGH | 631 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 29 | 0.101045 | 0.0 | 0.454834 | 0.0 | 1.0 | 0.0 |
| CLEAN_HIGH_MEDIUM | 1874 | 1874 | 830 | 321.8157 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 34 | 0.094972 | 0.557097 | 0.431325 | 0.0 | 0.336713 | 0.0 |
| RESOLUTION_SAFE_HIGH | 631 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | 344 | 287 | 0 | 0 | 0 | 0 | 631 | 0 | 631 | 0 | 29 | 0.101045 | 0.0 | 0.454834 | 0.0 | 1.0 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 1874 | 1874 | 830 | 321.8157 | 0.38773 | 0.563855 | 429 | 358 | 43 | 1044 | 0 | 0 | 631 | 0 | 631 | 0 | 34 | 0.094972 | 0.557097 | 0.431325 | 0.0 | 0.336713 | 0.0 |
| ZERO_GAP_HIGH | 0 | 0 | 0 | 0.0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 1243 | 1243 | 199 | 85.9569 | 0.431944 | 0.623116 | 85 | 71 | 43 | 1044 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0.070423 | 0.839903 | 0.356784 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 144 | 144 | 144 | 72.6872 | 0.504772 | 0.583333 | 84 | 60 | 0 | 0 | 0 | 0 | 144 | 0 | 144 | 0 | 0 | 0.0 | 0.0 | 0.416667 | 0.0 | 1.0 | 0.0 |
| 2024 | 99 | 99 | 99 | 6.1716 | 0.062339 | 0.0 | 42 | 57 | 0 | 0 | 0 | 0 | 99 | 0 | 99 | 0 | 22 | 0.385965 | 0.0 | 0.575758 | 0.0 | 1.0 | 0.0 |
| 2025 | 367 | 367 | 367 | 175.5 | 0.478202 | 0.591281 | 217 | 150 | 0 | 0 | 0 | 0 | 367 | 0 | 367 | 0 | 7 | 0.046667 | 0.0 | 0.408719 | 0.0 | 1.0 | 0.0 |
| 2026 | 21 | 21 | 21 | -18.5 | -0.880952 | 0.047619 | 1 | 20 | 0 | 0 | 0 | 0 | 21 | 0 | 21 | 0 | 0 | 0.0 | 0.0 | 0.952381 | 0.0 | 1.0 | 0.0 |

Treatment reasons:

- CLEAN_HIGH has enough sample and mostly positive yearly folds, but at least one stability or dominance caution remains.

### US30_cash|ny|bullish|H4+H1_consensus

- Role: `ambiguity_watchlist`
- Treatment: `CONTROLLED_RESEARCH_WATCHLIST`
- Selection reason: High pooled mean R but elevated immediate-stop and same-bar/gappy burden; needs anatomy before any deeper work.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 320 | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 30 | 0.229008 | 0.0 | 0.409375 | 0.0 | 1.0 | 0.0 |
| HIGH_MEDIUM | 1116 | 1116 | 341 | 166.8892 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 34 | 0.244604 | 0.694444 | 0.407625 | 0.0 | 0.286738 | 0.0 |
| CLEAN_HIGH | 320 | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 30 | 0.229008 | 0.0 | 0.409375 | 0.0 | 1.0 | 0.0 |
| CLEAN_HIGH_MEDIUM | 1116 | 1116 | 341 | 166.8892 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 34 | 0.244604 | 0.694444 | 0.407625 | 0.0 | 0.286738 | 0.0 |
| RESOLUTION_SAFE_HIGH | 320 | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | 189 | 131 | 0 | 0 | 0 | 0 | 320 | 0 | 320 | 0 | 30 | 0.229008 | 0.0 | 0.409375 | 0.0 | 1.0 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 1116 | 1116 | 341 | 166.8892 | 0.489411 | 0.583578 | 197 | 139 | 5 | 775 | 0 | 0 | 320 | 0 | 320 | 0 | 34 | 0.244604 | 0.694444 | 0.407625 | 0.0 | 0.286738 | 0.0 |
| ZERO_GAP_HIGH | 0 | 0 | 0 | 0.0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 796 | 796 | 21 | 4.1219 | 0.196281 | 0.47619 | 8 | 8 | 5 | 775 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0.5 | 0.973618 | 0.380952 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023 | 91 | 91 | 91 | 56.5 | 0.620879 | 0.648352 | 59 | 32 | 0 | 0 | 0 | 0 | 91 | 0 | 91 | 0 | 11 | 0.34375 | 0.0 | 0.351648 | 0.0 | 1.0 | 0.0 |
| 2024 | 146 | 146 | 146 | 73.5029 | 0.503445 | 0.575342 | 84 | 62 | 0 | 0 | 0 | 0 | 146 | 0 | 146 | 0 | 19 | 0.306452 | 0.0 | 0.424658 | 0.0 | 1.0 | 0.0 |
| 2025 | 58 | 58 | 58 | 55.2644 | 0.952834 | 0.775862 | 45 | 13 | 0 | 0 | 0 | 0 | 58 | 0 | 58 | 0 | 0 | 0.0 | 0.0 | 0.224138 | 0.0 | 1.0 | 0.0 |
| 2026 | 25 | 25 | 25 | -22.5 | -0.9 | 0.04 | 1 | 24 | 0 | 0 | 0 | 0 | 25 | 0 | 25 | 0 | 0 | 0.0 | 0.0 | 0.96 | 0.0 | 1.0 | 0.0 |

Treatment reasons:

- CLEAN_HIGH has enough sample and mostly positive yearly folds, but at least one stability or dominance caution remains.

### XAGUSD|ny|bullish|H4+H1_consensus

- Role: `secondary_followup`
- Treatment: `CONTROLLED_RESEARCH_WATCHLIST`
- Selection reason: Strong high+medium diagnostic lead and large sample; high-only result was weaker, so confidence-scope sensitivity is the question.

Scope rows:

| scope | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HIGH_ONLY | 509 | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 7 | 0.029915 | 0.0 | 0.459725 | 0.0 | 1.0 | 0.0 |
| HIGH_MEDIUM | 2833 | 2833 | 728 | 309.3403 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 22 | 0.072607 | 0.743029 | 0.416209 | 0.0 | 0.179668 | 0.0 |
| CLEAN_HIGH | 509 | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 7 | 0.029915 | 0.0 | 0.459725 | 0.0 | 1.0 | 0.0 |
| CLEAN_HIGH_MEDIUM | 2833 | 2833 | 728 | 309.3403 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 22 | 0.072607 | 0.743029 | 0.416209 | 0.0 | 0.179668 | 0.0 |
| RESOLUTION_SAFE_HIGH | 509 | 509 | 509 | 178.5 | 0.350688 | 0.540275 | 275 | 234 | 0 | 0 | 0 | 0 | 509 | 0 | 509 | 0 | 7 | 0.029915 | 0.0 | 0.459725 | 0.0 | 1.0 | 0.0 |
| RESOLUTION_SAFE_HIGH_MEDIUM | 2833 | 2833 | 728 | 309.3403 | 0.424918 | 0.578297 | 396 | 303 | 29 | 2105 | 0 | 0 | 509 | 0 | 509 | 0 | 22 | 0.072607 | 0.743029 | 0.416209 | 0.0 | 0.179668 | 0.0 |
| ZERO_GAP_HIGH | 0 | 0 | 0 | 0.0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ZERO_GAP_HIGH_MEDIUM | 2324 | 2324 | 219 | 130.8403 | 0.597444 | 0.666667 | 121 | 69 | 29 | 2105 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0.217391 | 0.905766 | 0.315068 | 0.0 | 0.0 | 0.0 |

Clean high yearly rows:

| year | setup_rows | rows | resolved_r_n | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | gap_rows | gap_before_resolution | gap_after_resolution | gap_timing_unknown | immediate_stop | immediate_stop_rate_sl | no_entry_rate_setup | sl_rate_filled | ambiguity_rate_setup | gap_row_rate_setup | gap_before_resolution_rate_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 93 | 93 | 93 | -3.0 | -0.032258 | 0.387097 | 36 | 57 | 0 | 0 | 0 | 0 | 93 | 0 | 93 | 0 | 1 | 0.017544 | 0.0 | 0.612903 | 0.0 | 1.0 | 0.0 |
| 2023 | 64 | 64 | 64 | 53.5 | 0.835938 | 0.734375 | 47 | 17 | 0 | 0 | 0 | 0 | 64 | 0 | 64 | 0 | 0 | 0.0 | 0.0 | 0.265625 | 0.0 | 1.0 | 0.0 |
| 2024 | 116 | 116 | 116 | 44.0 | 0.37931 | 0.551724 | 64 | 52 | 0 | 0 | 0 | 0 | 116 | 0 | 116 | 0 | 1 | 0.019231 | 0.0 | 0.448276 | 0.0 | 1.0 | 0.0 |
| 2025 | 124 | 124 | 124 | 78.5 | 0.633065 | 0.653226 | 81 | 43 | 0 | 0 | 0 | 0 | 124 | 0 | 124 | 0 | 1 | 0.023256 | 0.0 | 0.346774 | 0.0 | 1.0 | 0.0 |
| 2026 | 112 | 112 | 112 | 5.5 | 0.049107 | 0.419643 | 47 | 65 | 0 | 0 | 0 | 0 | 112 | 0 | 112 | 0 | 4 | 0.061538 | 0.0 | 0.580357 | 0.0 | 1.0 | 0.0 |

Treatment reasons:

- CLEAN_HIGH has enough sample and mostly positive yearly folds, but at least one stability or dominance caution remains.

## Synthesis

- This pass narrows the diagnostics from global anatomy to explicit follow-up cohorts and year/period stability checks.
- It does not answer promotion. The correct use is to decide which cohorts deserve a pre-declared controlled research run with DSR/PBO/effective_N accounting.
- Highest follow-up priority by the stability score is `USDJPY|tokyo|bearish|D1` with CLEAN_HIGH n=212, mean R=+0.6302, valid years=3, positive years=3.
- Treatment split: primary=2, watchlist/split-required=4, other=0.
- Remaining open tasks are actual realized-R enrichment, forward external-feed accumulation, and a true pre-declared validation pass; this artifact should not be used to tune entry offsets.
