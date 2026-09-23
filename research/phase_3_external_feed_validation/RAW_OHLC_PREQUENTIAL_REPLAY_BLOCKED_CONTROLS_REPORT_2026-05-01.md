# Phase 3 Raw-OHLC Prequential Replay Report

**Created UTC:** 2026-05-01T13:00:42.497133+00:00
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
| ac19f0e227eafa5cba7b7328c835faa67ff7110d23191ee3330244caf133ee1e | 412d378+dirty | LOCKED_HISTORICAL_RAW_OHLC_REPLAY | same_dataset_historical_raw_ohlc_diagnostic | 1fa926622392298715c5bf56909d95893734b7a5efa9e249758cb3caf1edfaec |

## Run Scope

| source_scope | start | end | max_candles_per_symbol | max_events | include_blocked_controls | symbols | rows_replayed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FULL_AVAILABLE_CORPUS |  |  |  |  | True | GBPJPY,GBPUSD,NAS100,US30_cash,USDJPY,XAGUSD,XAUUSD | 205197 |

## Data Inventory

| symbol | timeframe | status | path | rows | first | last | gap_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPJPY_M15.csv | 100012 | 2022-04-14 11:15:00 | 2026-04-30 23:45:00 | 238 |
| GBPJPY | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M5.csv | 99941 | 2024-12-26 11:25:00 | 2026-04-30 23:55:00 | 111 |
| GBPJPY | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M1.csv | 99711 | 2026-01-23 08:54:00 | 2026-04-30 23:59:00 | 106 |
| GBPJPY | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_H1.csv | 26764 | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 238 |
| GBPJPY | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_H1.csv |  | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 238 |
| GBPJPY | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_D1.csv | 1124 | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 230 |
| GBPUSD | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPUSD_M15.csv | 100012 | 2022-04-14 19:00:00 | 2026-04-30 23:45:00 | 225 |
| GBPUSD | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M5.csv | 99941 | 2024-12-26 16:50:00 | 2026-04-30 23:55:00 | 127 |
| GBPUSD | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M1.csv | 99722 | 2026-01-23 09:15:00 | 2026-04-30 23:59:00 | 266 |
| GBPUSD | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_H1.csv | 26766 | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 237 |
| GBPUSD | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_H1.csv |  | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 237 |
| GBPUSD | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_D1.csv | 1124 | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 230 |
| NAS100 | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\NAS100_M15.csv | 72862 | 2022-10-20 11:00:00 | 2026-04-30 23:45:00 | 3558 |
| NAS100 | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_M5.csv | 99953 | 2024-11-28 06:30:00 | 2026-04-30 23:55:00 | 377 |
| NAS100 | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_M1.csv | 99768 | 2026-01-20 05:27:00 | 2026-04-30 23:59:00 | 73 |
| NAS100 | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_H1.csv | 20310 | 2022-10-20 11:00:00 | 2026-04-30 23:00:00 | 913 |
| NAS100 | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_H1.csv |  | 2022-10-20 11:00:00 | 2026-04-30 23:00:00 | 913 |
| NAS100 | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_D1.csv | 910 | 2022-10-20 00:00:00 | 2026-04-30 00:00:00 | 189 |
| US30_cash | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\US30_cash_M15.csv | 72847 | 2022-10-20 11:00:00 | 2026-04-30 23:45:00 | 3554 |
| US30_cash | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_M5.csv | 99953 | 2024-11-28 06:10:00 | 2026-04-30 23:55:00 | 370 |
| US30_cash | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_M1.csv | 99769 | 2026-01-20 02:01:00 | 2026-04-30 23:58:00 | 88 |
| US30_cash | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_H1.csv | 20304 | 2022-10-20 11:00:00 | 2026-04-30 23:00:00 | 912 |
| US30_cash | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_H1.csv |  | 2022-10-20 11:00:00 | 2026-04-30 23:00:00 | 912 |
| US30_cash | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_D1.csv | 910 | 2022-10-20 00:00:00 | 2026-04-30 00:00:00 | 189 |
| USDJPY | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\USDJPY_M15.csv | 100012 | 2022-04-14 19:00:00 | 2026-04-30 23:45:00 | 228 |
| USDJPY | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M5.csv | 99941 | 2024-12-26 17:30:00 | 2026-04-30 23:55:00 | 116 |
| USDJPY | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M1.csv | 99718 | 2026-01-23 08:58:00 | 2026-04-30 23:59:00 | 262 |
| USDJPY | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_H1.csv | 26768 | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 238 |
| USDJPY | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_H1.csv |  | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 238 |
| USDJPY | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_D1.csv | 1124 | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 230 |
| XAGUSD | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\XAGUSD_M15.csv | 99195 | 2022-01-03 01:00:00 | 2026-04-30 23:45:00 | 1122 |
| XAGUSD | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M5.csv | 99953 | 2024-11-29 03:20:00 | 2026-04-30 23:55:00 | 384 |
| XAGUSD | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M1.csv | 99768 | 2026-01-19 11:39:00 | 2026-04-30 23:59:00 | 78 |
| XAGUSD | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_H1.csv | 24847 | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | 1113 |
| XAGUSD | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_H1.csv |  | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | 1113 |
| XAGUSD | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_D1.csv | 1113 | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 230 |
| XAUUSD | M15 | AVAILABLE | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\XAUUSD_M15.csv | 100012 | 2022-02-01 21:30:00 | 2026-04-30 23:45:00 | 1104 |
| XAUUSD | M5 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_M5.csv | 99953 | 2024-11-29 06:40:00 | 2026-04-30 23:55:00 | 376 |
| XAUUSD | M1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_M1.csv | 99768 | 2026-01-19 11:59:00 | 2026-04-30 23:59:00 | 74 |
| XAUUSD | H1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_H1.csv | 25550 | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | 1116 |
| XAUUSD | H4 | DERIVED_FROM_H1 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_H1.csv |  | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | 1116 |
| XAUUSD | D1 | AVAILABLE | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_D1.csv | 1116 | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 229 |

## Active Cohorts

| cohort_key | role | status | source |
| --- | --- | --- | --- |
| USDJPY\|tokyo\|bearish\|D1 | primary_controlled_child | enabled | TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1 |
| GBPJPY\|tokyo\|bullish\|D1 | primary_controlled_child | enabled | TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1 |
| USDJPY\|london\|bearish\|D1 | cleared_non_primary_strong_lead | enabled | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | cleared_non_primary_strong_lead | enabled | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |
| XAGUSD\|london\|bullish\|D1 | cleared_non_primary_strong_lead | enabled | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |
| USDJPY\|tokyo\|bullish\|D1 | negative_control | enabled | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 |
| USDJPY\|london\|bullish\|D1 | negative_control | enabled | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 |
| GBPUSD\|london\|bearish\|H4+H1_consensus | negative_control | enabled | HISTORICAL_REPLAY_REGISTERED_MATRIX_REPORT_2026-05-01 |
| NAS100\|ny\|bullish\|D1 | dominance_watchlist | blocked_control | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | dominance_watchlist | blocked_control | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |
| XAUUSD\|ny\|bullish\|D1 | dominance_watchlist | blocked_control | TRUTH_LAYER_MATRIX_DOMINANCE_AUDIT_2026-05-01 |

## Guardrails

| rows_replayed | duplicate_event_keys | invalid_clock_rows | future_candle_exposure_violations | htf_asof_violations | forbidden_observation_violations | ai_attempted_rows | ai_call_count_sum | integrity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 205197 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 181714 | 23483 |

## Pre-AI Gate Counts

| PRE_AI_POI_REJECT | PRE_SCREEN_REJECT | SKIP_FIRST_NY_CANDLE | WOULD_SEND_AI |
| --- | --- | --- | --- |
| 12282 | 56704 | 1092 | 135119 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 23483 | 11026 | 3499 | 792.4424 | 0.226477 | 0.503858 |

## Action Outcomes

| NO_ENTRY | PRE_AI_POI_REJECT | SAME_BAR | SETUP_NOT_REFINABLE | SL | TIMEOUT | TP |
| --- | --- | --- | --- | --- | --- | --- |
| 7527 | 1630 | 1805 | 9022 | 1680 | 262 | 1557 |

## Scoring Exclusions

| mechanical_outcome_excluded | not_setup_row | not_would_send_ai |
| --- | --- | --- |
| 1805 | 10652 | 1630 |

## Cohort Scores

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | 2741 | 1106 | 387 | 155.0845 | 0.400735 | 0.583979 | {'NO_ENTRY': 719, 'PRE_AI_POI_REJECT': 226, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 1304, 'SL': 152, 'TIMEOUT': 48, 'TP': 187} |
| GBPUSD\|london\|bearish\|H4+H1_consensus | 1885 | 1469 | 589 | -69.2339 | -0.117545 | 0.375212 | {'NO_ENTRY': 880, 'PRE_AI_POI_REJECT': 68, 'SAME_BAR': 164, 'SETUP_NOT_REFINABLE': 184, 'SL': 353, 'TIMEOUT': 58, 'TP': 178} |
| NAS100\|ny\|bullish\|D1 | 3442 | 1523 | 470 | 128.6635 | 0.273752 | 0.52766 | {'NO_ENTRY': 1053, 'PRE_AI_POI_REJECT': 158, 'SAME_BAR': 494, 'SETUP_NOT_REFINABLE': 1267, 'SL': 219, 'TIMEOUT': 39, 'TP': 212} |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 1315 | 916 | 139 | 63.9979 | 0.460417 | 0.568345 | {'NO_ENTRY': 777, 'PRE_AI_POI_REJECT': 26, 'SAME_BAR': 289, 'SETUP_NOT_REFINABLE': 84, 'SL': 57, 'TIMEOUT': 7, 'TP': 75} |
| USDJPY\|london\|bearish\|D1 | 1118 | 453 | 129 | 66.0 | 0.511628 | 0.604651 | {'NO_ENTRY': 324, 'PRE_AI_POI_REJECT': 92, 'SAME_BAR': 46, 'SETUP_NOT_REFINABLE': 527, 'SL': 51, 'TP': 78} |
| USDJPY\|london\|bullish\|D1 | 2581 | 819 | 308 | -1.5765 | -0.005119 | 0.399351 | {'NO_ENTRY': 511, 'PRE_AI_POI_REJECT': 168, 'SAME_BAR': 127, 'SETUP_NOT_REFINABLE': 1467, 'SL': 178, 'TIMEOUT': 13, 'TP': 117} |
| USDJPY\|tokyo\|bearish\|D1 | 1345 | 555 | 190 | 62.5 | 0.328947 | 0.531579 | {'NO_ENTRY': 365, 'PRE_AI_POI_REJECT': 113, 'SAME_BAR': 63, 'SETUP_NOT_REFINABLE': 614, 'SL': 89, 'TP': 101} |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 690 | 541 | 212 | 100.2102 | 0.47269 | 0.603774 | {'NO_ENTRY': 329, 'PRE_AI_POI_REJECT': 12, 'SAME_BAR': 55, 'SETUP_NOT_REFINABLE': 82, 'SL': 78, 'TIMEOUT': 20, 'TP': 114} |
| USDJPY\|tokyo\|bullish\|D1 | 3139 | 1010 | 380 | -11.5502 | -0.030395 | 0.418421 | {'NO_ENTRY': 630, 'PRE_AI_POI_REJECT': 225, 'SAME_BAR': 180, 'SETUP_NOT_REFINABLE': 1724, 'SL': 221, 'TIMEOUT': 33, 'TP': 126} |
| XAGUSD\|london\|bullish\|D1 | 2328 | 1153 | 306 | 116.2419 | 0.379875 | 0.558824 | {'NO_ENTRY': 847, 'PRE_AI_POI_REJECT': 274, 'SAME_BAR': 64, 'SETUP_NOT_REFINABLE': 837, 'SL': 131, 'TIMEOUT': 17, 'TP': 158} |
| XAUUSD\|ny\|bullish\|D1 | 2899 | 1481 | 389 | 182.105 | 0.468136 | 0.588689 | {'NO_ENTRY': 1092, 'PRE_AI_POI_REJECT': 268, 'SAME_BAR': 218, 'SETUP_NOT_REFINABLE': 932, 'SL': 151, 'TIMEOUT': 27, 'TP': 211} |

## Period Scores

| period | actions_taken | resolved_r_n | sum_r | mean_r |
| --- | --- | --- | --- | --- |
| 2022-02 | 210 | 24 | 17.3339 | 0.722246 |
| 2022-03 | 143 | 14 | 21.0 | 1.5 |
| 2022-04 | 60 | 20 | 4.9983 | 0.249915 |
| 2022-05 | 236 | 53 | -18.374 | -0.346679 |
| 2022-06 | 180 | 58 | 17.6066 | 0.303562 |
| 2022-07 | 352 | 14 | -14.0 | -1.0 |
| 2022-08 | 368 | 68 | -30.4996 | -0.448524 |
| 2022-09 | 56 | 8 | 12.0 | 1.5 |
| 2022-10 | 153 | 7 | -7.0 | -1.0 |
| 2022-11 | 382 | 104 | 61.0 | 0.586538 |
| 2022-12 | 657 | 84 | -14.0937 | -0.167782 |
| 2023-01 | 307 | 26 | 26.501 | 1.019269 |
| 2023-02 | 319 | 87 | -19.4994 | -0.224131 |
| 2023-03 | 380 | 59 | -37.3875 | -0.633686 |
| 2023-04 | 601 | 75 | 43.8819 | 0.585092 |
| 2023-05 | 697 | 94 | 11.0 | 0.117021 |
| 2023-06 | 748 | 67 | -1.8188 | -0.027146 |
| 2023-07 | 434 | 79 | 98.0255 | 1.240829 |
| 2023-08 | 642 | 153 | -1.8158 | -0.011868 |
| 2023-09 | 262 | 46 | 19.121 | 0.415674 |
| 2023-10 | 431 | 81 | -30.8394 | -0.380733 |
| 2023-11 | 750 | 88 | 74.5 | 0.846591 |
| 2023-12 | 656 | 106 | -58.8081 | -0.554793 |
| 2024-01 | 274 | 35 | -12.5 | -0.357143 |
| 2024-02 | 160 | 41 | 28.6412 | 0.698566 |
| 2024-03 | 683 | 54 | 15.9083 | 0.294598 |
| 2024-04 | 185 | 27 | 18.0 | 0.666667 |
| 2024-05 | 331 | 62 | -14.5 | -0.233871 |
| 2024-06 | 388 | 54 | 11.0 | 0.203704 |
| 2024-07 | 290 | 75 | 71.2651 | 0.950201 |
| 2024-08 | 581 | 73 | 37.1442 | 0.508825 |
| 2024-09 | 347 | 28 | 8.1639 | 0.291568 |
| 2024-10 | 708 | 92 | 40.633 | 0.441663 |
| 2024-11 | 623 | 72 | 1.9129 | 0.026568 |
| 2024-12 | 152 | 45 | 25.0 | 0.555556 |
| 2025-01 | 843 | 108 | 78.7163 | 0.728855 |
| 2025-02 | 1089 | 183 | 36.0213 | 0.196838 |
| 2025-03 | 359 | 55 | 22.5 | 0.409091 |
| 2025-04 | 284 | 5 | -5.0 | -1.0 |
| 2025-05 | 712 | 124 | 7.5938 | 0.06124 |
| 2025-06 | 905 | 128 | 73.1208 | 0.571256 |
| 2025-07 | 834 | 142 | -5.7664 | -0.040608 |
| 2025-08 | 402 | 26 | -23.5 | -0.903846 |
| 2025-09 | 680 | 107 | 73.1716 | 0.683847 |
| 2025-10 | 768 | 113 | 45.1426 | 0.399492 |
| 2025-11 | 322 | 47 | 0.5 | 0.010638 |
| 2025-12 | 421 | 60 | 63.339 | 1.05565 |
| 2026-01 | 698 | 64 | -10.3237 | -0.161308 |
| 2026-02 | 318 | 76 | -13.0818 | -0.172129 |
| 2026-03 | 609 | 120 | 22.0084 | 0.183403 |
| 2026-04 | 493 | 68 | 24.5 | 0.360294 |

## Interpretation

- This is a raw-candle replay adapter validation, not a promotion dossier.
- The result can prioritize future research and catch leakage or data-coverage issues.
- Same-dataset historical positives or negatives cannot be called live alpha proof.
