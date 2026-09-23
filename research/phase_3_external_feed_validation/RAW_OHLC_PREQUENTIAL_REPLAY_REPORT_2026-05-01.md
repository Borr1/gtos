# Phase 3 Raw-OHLC Prequential Replay Report

**Created UTC:** 2026-05-01T11:17:37.028474+00:00
**Spec:** `research\phase_3_external_feed_validation\RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- Replay walks raw M15 candles in chronological order and reconstructs as-of observations from candle windows.
- HTF bars use the registered no-leak policy before a decision is locked.
- Mechanical outcomes are attached only after TAKE/SKIP is fixed.
- DSR, PBO, effective_N, and prospective confirmation are not computed here.

## Reproducibility

| spec_sha256 | code_commit | run_mode | evidence_class | event_log_sha256 |
| --- | --- | --- | --- | --- |
| ac19f0e227eafa5cba7b7328c835faa67ff7110d23191ee3330244caf133ee1e | 6dfb533+dirty | LOCKED_HISTORICAL_RAW_OHLC_REPLAY | same_dataset_historical_raw_ohlc_diagnostic | fa34977681f6b1cf775c21b01463a78b7e050a1d6d883ab1c96e78df1f9e29bb |

## Run Scope

| source_scope | start | end | max_candles_per_symbol | max_events | include_blocked_controls | symbols | rows_replayed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FULL_AVAILABLE_CORPUS |  |  |  |  | False | GBPJPY,GBPUSD,USDJPY,XAGUSD | 131726 |

## Data Inventory

| first | gap_count | last | path | rows | status | symbol | timeframe |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022-04-14 11:15:00 | 238 | 2026-04-30 23:45:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPJPY_M15.csv | 100012 | AVAILABLE | GBPJPY | M15 |
| 2024-12-26 11:25:00 | 111 | 2026-04-30 23:55:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M5.csv | 99941 | AVAILABLE | GBPJPY | M5 |
| 2026-01-23 08:54:00 | 106 | 2026-04-30 23:59:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M1.csv | 99711 | AVAILABLE | GBPJPY | M1 |
| 2022-01-03 00:00:00 | 238 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_H1.csv | 26764 | AVAILABLE | GBPJPY | H1 |
| 2022-01-03 00:00:00 | 238 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_H1.csv |  | DERIVED_FROM_H1 | GBPJPY | H4 |
| 2022-01-03 00:00:00 | 230 | 2026-04-30 00:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_D1.csv | 1124 | AVAILABLE | GBPJPY | D1 |
| 2022-04-14 19:00:00 | 225 | 2026-04-30 23:45:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPUSD_M15.csv | 100012 | AVAILABLE | GBPUSD | M15 |
| 2024-12-26 16:50:00 | 127 | 2026-04-30 23:55:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M5.csv | 99941 | AVAILABLE | GBPUSD | M5 |
| 2026-01-23 09:15:00 | 266 | 2026-04-30 23:59:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M1.csv | 99722 | AVAILABLE | GBPUSD | M1 |
| 2022-01-03 00:00:00 | 237 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_H1.csv | 26766 | AVAILABLE | GBPUSD | H1 |
| 2022-01-03 00:00:00 | 237 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_H1.csv |  | DERIVED_FROM_H1 | GBPUSD | H4 |
| 2022-01-03 00:00:00 | 230 | 2026-04-30 00:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_D1.csv | 1124 | AVAILABLE | GBPUSD | D1 |
| 2022-04-14 19:00:00 | 228 | 2026-04-30 23:45:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\USDJPY_M15.csv | 100012 | AVAILABLE | USDJPY | M15 |
| 2024-12-26 17:30:00 | 116 | 2026-04-30 23:55:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M5.csv | 99941 | AVAILABLE | USDJPY | M5 |
| 2026-01-23 08:58:00 | 262 | 2026-04-30 23:59:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M1.csv | 99718 | AVAILABLE | USDJPY | M1 |
| 2022-01-03 00:00:00 | 238 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_H1.csv | 26768 | AVAILABLE | USDJPY | H1 |
| 2022-01-03 00:00:00 | 238 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_H1.csv |  | DERIVED_FROM_H1 | USDJPY | H4 |
| 2022-01-03 00:00:00 | 230 | 2026-04-30 00:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_D1.csv | 1124 | AVAILABLE | USDJPY | D1 |
| 2022-01-03 01:00:00 | 1122 | 2026-04-30 23:45:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\XAGUSD_M15.csv | 99195 | AVAILABLE | XAGUSD | M15 |
| 2024-11-29 03:20:00 | 384 | 2026-04-30 23:55:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M5.csv | 99953 | AVAILABLE | XAGUSD | M5 |
| 2026-01-19 11:39:00 | 78 | 2026-04-30 23:59:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M1.csv | 99768 | AVAILABLE | XAGUSD | M1 |
| 2022-01-03 01:00:00 | 1113 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_H1.csv | 24847 | AVAILABLE | XAGUSD | H1 |
| 2022-01-03 01:00:00 | 1113 | 2026-04-30 23:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_H1.csv |  | DERIVED_FROM_H1 | XAGUSD | H4 |
| 2022-01-03 00:00:00 | 230 | 2026-04-30 00:00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_D1.csv | 1113 | AVAILABLE | XAGUSD | D1 |

## Active Cohorts

| cohort_key | role | source | status |
| --- | --- | --- | --- |
| USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1 | enabled |
| GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1 | enabled |
| USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 | enabled |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 | enabled |
| XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 | enabled |
| USDJPY\|tokyo\|bullish\|D1 | negative_control | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 | enabled |
| USDJPY\|london\|bullish\|D1 | negative_control | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 | enabled |
| GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 | enabled |

## Guardrails

| rows_replayed | duplicate_event_keys | invalid_clock_rows | future_candle_exposure_violations | htf_asof_violations | forbidden_observation_violations | ai_attempted_rows | ai_call_count_sum | integrity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 131726 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 115899 | 15827 |

## Pre-AI Gate Counts

| PRE_AI_POI_REJECT | PRE_SCREEN_REJECT | WOULD_SEND_AI |
| --- | --- | --- |
| 8142 | 37871 | 85713 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 15827 | 7106 | 2501 | 417.676 | 0.167004 | 0.482607 |

## Action Outcomes

| NO_ENTRY | PRE_AI_POI_REJECT | SAME_BAR | SETUP_NOT_REFINABLE | SL | TIMEOUT | TP |
| --- | --- | --- | --- | --- | --- | --- |
| 4605 | 1178 | 804 | 6739 | 1253 | 189 | 1059 |

## Scoring Exclusions

| mechanical_outcome_excluded | not_setup_row | not_would_send_ai |
| --- | --- | --- |
| 804 | 7917 | 1178 |

## Cohort Scores

| actions_taken | cohort_key | mean_r | outcomes | population_actions | resolved_r_n | sum_r | win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2741 | GBPJPY\|tokyo\|bullish\|D1 | 0.400735 | {'NO_ENTRY': 719, 'PRE_AI_POI_REJECT': 226, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 1304, 'SL': 152, 'TIMEOUT': 48, 'TP': 187} | 1106 | 387 | 155.0845 | 0.583979 |
| 1885 | GBPUSD\|london\|bearish\|H4+H1_consensus | -0.117545 | {'NO_ENTRY': 880, 'PRE_AI_POI_REJECT': 68, 'SAME_BAR': 164, 'SETUP_NOT_REFINABLE': 184, 'SL': 353, 'TIMEOUT': 58, 'TP': 178} | 1469 | 589 | -69.2339 | 0.375212 |
| 1118 | USDJPY\|london\|bearish\|D1 | 0.511628 | {'NO_ENTRY': 324, 'PRE_AI_POI_REJECT': 92, 'SAME_BAR': 46, 'SETUP_NOT_REFINABLE': 527, 'SL': 51, 'TP': 78} | 453 | 129 | 66.0 | 0.604651 |
| 2581 | USDJPY\|london\|bullish\|D1 | -0.005119 | {'NO_ENTRY': 511, 'PRE_AI_POI_REJECT': 168, 'SAME_BAR': 127, 'SETUP_NOT_REFINABLE': 1467, 'SL': 178, 'TIMEOUT': 13, 'TP': 117} | 819 | 308 | -1.5765 | 0.399351 |
| 1345 | USDJPY\|tokyo\|bearish\|D1 | 0.328947 | {'NO_ENTRY': 365, 'PRE_AI_POI_REJECT': 113, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 614, 'SL': 89, 'TP': 101} | 555 | 190 | 62.5 | 0.531579 |
| 690 | USDJPY\|tokyo\|bearish\|H4+H1_consensus | 0.47269 | {'NO_ENTRY': 329, 'PRE_AI_POI_REJECT': 12, 'SAME_BAR': 55, 'SETUP_NOT_REFINABLE': 82, 'SL': 78, 'TIMEOUT': 20, 'TP': 114} | 541 | 212 | 100.2102 | 0.603774 |
| 3139 | USDJPY\|tokyo\|bullish\|D1 | -0.030395 | {'NO_ENTRY': 630, 'PRE_AI_POI_REJECT': 225, 'SAME_BAR': 180, 'SETUP_NOT_REFINABLE': 1724, 'SL': 221, 'TIMEOUT': 33, 'TP': 126} | 1010 | 380 | -11.5502 | 0.418421 |
| 2328 | XAGUSD\|london\|bullish\|D1 | 0.379875 | {'NO_ENTRY': 847, 'PRE_AI_POI_REJECT': 274, 'SAME_BAR': 64, 'SETUP_NOT_REFINABLE': 837, 'SL': 131, 'TIMEOUT': 17, 'TP': 158} | 1153 | 306 | 116.2419 | 0.558824 |

## Period Scores

| actions_taken | mean_r | period | resolved_r_n | sum_r |
| --- | --- | --- | --- | --- |
| 98 | 1.5 | 2022-03 | 14 | 21.0 |
| 60 | 0.249915 | 2022-04 | 20 | 4.9983 |
| 236 | -0.346679 | 2022-05 | 53 | -18.374 |
| 180 | 0.303562 | 2022-06 | 58 | 17.6066 |
| 352 | -1.0 | 2022-07 | 14 | -14.0 |
| 368 | -0.448524 | 2022-08 | 68 | -30.4996 |
| 56 | 1.5 | 2022-09 | 8 | 12.0 |
| 152 | -1.0 | 2022-10 | 7 | -7.0 |
| 356 | 0.641414 | 2022-11 | 99 | 63.5 |
| 456 | -0.396673 | 2022-12 | 62 | -24.5937 |
| 224 | 1.25005 | 2023-01 | 20 | 25.001 |
| 210 | -0.176822 | 2023-02 | 82 | -14.4994 |
| 316 | -1.0 | 2023-03 | 26 | -26.0 |
| 360 | 0.328407 | 2023-04 | 58 | 19.0476 |
| 634 | 0.117021 | 2023-05 | 94 | 11.0 |
| 336 | 0.007248 | 2023-06 | 25 | 0.1812 |
| 250 | 1.363271 | 2023-07 | 34 | 46.3512 |
| 580 | 0.021515 | 2023-08 | 148 | 3.1842 |
| 166 | 0.366386 | 2023-09 | 44 | 16.121 |
| 420 | -0.380733 | 2023-10 | 81 | -30.8394 |
| 520 | 0.840278 | 2023-11 | 72 | 60.5 |
| 425 | -0.628272 | 2023-12 | 95 | -59.6858 |
| 242 | -0.357143 | 2024-01 | 35 | -12.5 |
| 112 | -1.0 | 2024-02 | 8 | -8.0 |
| 321 | 0.272642 | 2024-03 | 26 | 7.0887 |
| 140 | 0.666667 | 2024-04 | 27 | 18.0 |
| 106 | -1.0 | 2024-05 | 5 | -5.0 |
| 342 | 0.226415 | 2024-06 | 53 | 12.0 |
| 244 | 1.315821 | 2024-07 | 61 | 80.2651 |
| 365 | 0.538719 | 2024-08 | 43 | 23.1649 |
| 226 | 0.870217 | 2024-09 | 18 | 15.6639 |
| 339 | 0.625104 | 2024-10 | 77 | 48.133 |
| 562 | 0.026568 | 2024-11 | 72 | 1.9129 |
| 74 | 0.034483 | 2024-12 | 29 | 1.0 |
| 593 | 0.772489 | 2025-01 | 47 | 36.307 |
| 640 | 0.407563 | 2025-02 | 119 | 48.5 |
| 344 | 0.25 | 2025-03 | 48 | 12.0 |
| 224 | -1.0 | 2025-04 | 1 | -1.0 |
| 378 | 0.234376 | 2025-05 | 58 | 13.5938 |
| 384 | 0.356823 | 2025-06 | 69 | 24.6208 |
| 460 | -0.042532 | 2025-07 | 94 | -3.998 |
| 242 | -0.903846 | 2025-08 | 26 | -23.5 |
| 384 | 0.096145 | 2025-09 | 55 | 5.288 |
| 336 | -0.361749 | 2025-10 | 47 | -17.0022 |
| 262 | 0.388889 | 2025-11 | 27 | 10.5 |
| 268 | 1.210112 | 2025-12 | 34 | 41.1438 |
| 425 | -0.328813 | 2026-01 | 39 | -12.8237 |
| 237 | -0.083743 | 2026-02 | 56 | -4.6896 |
| 459 | 0.257223 | 2026-03 | 105 | 27.0084 |
| 363 | 0.125 | 2026-04 | 40 | 5.0 |

## Interpretation

- This is a raw-candle replay adapter validation, not a promotion dossier.
- The result can prioritize future research and catch leakage or data-coverage issues.
- Same-dataset historical positives or negatives cannot be called live alpha proof.
