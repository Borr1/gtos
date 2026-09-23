# Phase 3 Historical Replay Research Lab Report

**Created UTC:** 2026-05-01T09:34:24.141210+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Lab spec:** `research\phase_3_external_feed_validation\HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json`
**Strategy spec:** `research\phase_3_external_feed_validation\HISTORICAL_REPLAY_STRATEGY_REGISTERED_MATRIX_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- Replay is prequential: observation first, strategy decision second, scorer-only outcome third.
- This run is historical same-dataset evidence unless paired with a predeclared untouched split or prospective rows.
- DSR, PBO, and effective_N are not computed here.

## Reproducibility

| input_sha256 | lab_spec_sha256 | strategy_spec_sha256 | code_commit | run_mode | evidence_class |
| --- | --- | --- | --- | --- | --- |
| 0530a49f1eafcaa46bf94b9c9267670d815803ed3c067ecd5501a5a9888455ae | 6c95fbe15aa70f05715291e77ba8ea57e325cf1fafec02396d63add64556f091 | 72ed271e35357ebfe1e1f8cf578a7c8eb3ecd5ada2a98f4d467424ee2cd38f60 | d88960e+dirty | REGISTERED_MATRIX_REPLAY | same_dataset_historical_diagnostic_matrix |

## Guardrails

| rows_loaded | rows_replayed | duplicate_opportunity_keys | invalid_clock_rows | forbidden_exposure_violations | external_asof_violations | ai_attempted_rows | ai_call_count_sum | integrity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 113790 | 91407 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 91407 | 31714 | 18541 | 2383.6216 | 0.128559 | 0.454237 |

## Action Outcomes

| LOWER_TF_GAPPY | NO_ENTRY | PRE_AI_POI_REJECT | SAME_BAR | SETUP_NOT_REFINABLE | SL | TIMEOUT | TP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 941 | 37276 | 5050 | 1629 | 24796 | 11189 | 1323 | 9203 |

## Scoring Exclusions

| not_resolution_safe | not_setup_row | truth_confidence_not_allowed | truth_outcome_excluded |
| --- | --- | --- | --- |
| 2570 | 29846 | 59693 | 2570 |

## Cohort Scores

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london\|bearish\|H4+H1_consensus | 701 | 512 | 203 | 10.9683 | 0.054031 | 0.433498 | {'NO_ENTRY': 418, 'PRE_AI_POI_REJECT': 6, 'SAME_BAR': 10, 'SETUP_NOT_REFINABLE': 34, 'SL': 137, 'TIMEOUT': 21, 'TP': 75} |
| GBPJPY\|london\|bullish\|D1 | 2289 | 792 | 318 | 51.6575 | 0.162445 | 0.459119 | {'LOWER_TF_GAPPY': 7, 'NO_ENTRY': 634, 'PRE_AI_POI_REJECT': 191, 'SAME_BAR': 39, 'SETUP_NOT_REFINABLE': 1058, 'SL': 168, 'TIMEOUT': 31, 'TP': 161} |
| GBPJPY\|london\|bullish\|H4+H1_consensus | 1845 | 1292 | 530 | 161.2745 | 0.304292 | 0.516981 | {'LOWER_TF_GAPPY': 8, 'NO_ENTRY': 855, 'PRE_AI_POI_REJECT': 83, 'SAME_BAR': 41, 'SETUP_NOT_REFINABLE': 318, 'SL': 258, 'TIMEOUT': 21, 'TP': 261} |
| GBPJPY\|ny\|bullish\|D1 | 2290 | 728 | 261 | 15.5737 | 0.059669 | 0.455939 | {'LOWER_TF_GAPPY': 14, 'NO_ENTRY': 642, 'PRE_AI_POI_REJECT': 249, 'SAME_BAR': 32, 'SETUP_NOT_REFINABLE': 1012, 'SL': 163, 'TIMEOUT': 50, 'TP': 128} |
| GBPJPY\|ny\|bullish\|H4+H1_consensus | 1784 | 1201 | 449 | 79.2424 | 0.176486 | 0.492205 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 888, 'PRE_AI_POI_REJECT': 98, 'SAME_BAR': 34, 'SETUP_NOT_REFINABLE': 253, 'SL': 249, 'TIMEOUT': 55, 'TP': 197} |
| GBPJPY\|tokyo\|bearish\|H4+H1_consensus | 886 | 644 | 270 | 9.1669 | 0.033951 | 0.425926 | {'NO_ENTRY': 532, 'PRE_AI_POI_REJECT': 9, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 27, 'SL': 149, 'TIMEOUT': 54, 'TP': 91} |
| GBPJPY\|tokyo\|bullish\|D1 | 2753 | 956 | 430 | 212.0002 | 0.493024 | 0.609302 | {'NO_ENTRY': 695, 'PRE_AI_POI_REJECT': 235, 'SAME_BAR': 52, 'SETUP_NOT_REFINABLE': 1326, 'SL': 159, 'TIMEOUT': 49, 'TP': 237} |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | 2158 | 1552 | 657 | 150.0429 | 0.228376 | 0.493151 | {'NO_ENTRY': 1023, 'PRE_AI_POI_REJECT': 62, 'SAME_BAR': 71, 'SETUP_NOT_REFINABLE': 345, 'SL': 331, 'TIMEOUT': 6, 'TP': 320} |
| GBPUSD\|london\|bearish\|D1 | 3889 | 1396 | 727 | 179.6955 | 0.247174 | 0.503439 | {'LOWER_TF_GAPPY': 11, 'NO_ENTRY': 866, 'PRE_AI_POI_REJECT': 444, 'SAME_BAR': 39, 'SETUP_NOT_REFINABLE': 1786, 'SL': 344, 'TIMEOUT': 53, 'TP': 346} |
| GBPUSD\|london\|bearish\|H4+H1_consensus | 1884 | 1337 | 671 | -93.5818 | -0.139466 | 0.359165 | {'LOWER_TF_GAPPY': 13, 'NO_ENTRY': 887, 'PRE_AI_POI_REJECT': 65, 'SAME_BAR': 13, 'SETUP_NOT_REFINABLE': 195, 'SL': 422, 'TIMEOUT': 67, 'TP': 222} |
| GBPUSD\|london\|bullish\|D1 | 3632 | 1126 | 614 | -18.589 | -0.030275 | 0.405537 | {'LOWER_TF_GAPPY': 8, 'NO_ENTRY': 673, 'PRE_AI_POI_REJECT': 314, 'SAME_BAR': 66, 'SETUP_NOT_REFINABLE': 1917, 'SL': 377, 'TIMEOUT': 62, 'TP': 215} |
| GBPUSD\|london\|bullish\|H4+H1_consensus | 2578 | 1768 | 658 | 40.0797 | 0.060911 | 0.420973 | {'LOWER_TF_GAPPY': 20, 'NO_ENTRY': 1451, 'PRE_AI_POI_REJECT': 63, 'SAME_BAR': 45, 'SETUP_NOT_REFINABLE': 273, 'SL': 383, 'TIMEOUT': 15, 'TP': 328} |
| GBPUSD\|ny\|bearish\|D1 | 1940 | 620 | 298 | -30.7401 | -0.103155 | 0.379195 | {'LOWER_TF_GAPPY': 1, 'NO_ENTRY': 450, 'PRE_AI_POI_REJECT': 238, 'SAME_BAR': 10, 'SETUP_NOT_REFINABLE': 939, 'SL': 185, 'TIMEOUT': 21, 'TP': 96} |
| GBPUSD\|ny\|bearish\|H4+H1_consensus | 972 | 573 | 214 | -28.0417 | -0.131036 | 0.359813 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 529, 'PRE_AI_POI_REJECT': 46, 'SAME_BAR': 22, 'SETUP_NOT_REFINABLE': 121, 'SL': 138, 'TIMEOUT': 32, 'TP': 74} |
| GBPUSD\|ny\|bullish\|D1 | 1810 | 462 | 175 | 0.868 | 0.00496 | 0.428571 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 370, 'PRE_AI_POI_REJECT': 152, 'SAME_BAR': 17, 'SETUP_NOT_REFINABLE': 1048, 'SL': 110, 'TIMEOUT': 45, 'TP': 58} |
| GBPUSD\|ny\|bullish\|H4+H1_consensus | 1257 | 880 | 264 | 29.2658 | 0.110855 | 0.443182 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 777, 'PRE_AI_POI_REJECT': 33, 'SAME_BAR': 13, 'SETUP_NOT_REFINABLE': 116, 'SL': 140, 'TIMEOUT': 23, 'TP': 145} |
| NAS100\|london\|bullish\|D1 | 3025 | 591 | 591 | 16.8921 | 0.028582 | 0.411168 | {'LOWER_TF_GAPPY': 42, 'NO_ENTRY': 900, 'PRE_AI_POI_REJECT': 121, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 1221, 'SL': 393, 'TIMEOUT': 17, 'TP': 280} |
| NAS100\|london\|bullish\|H4+H1_consensus | 2227 | 662 | 662 | 53.685 | 0.081095 | 0.429003 | {'LOWER_TF_GAPPY': 3, 'NO_ENTRY': 1089, 'PRE_AI_POI_REJECT': 43, 'SAME_BAR': 54, 'SETUP_NOT_REFINABLE': 297, 'SL': 405, 'TIMEOUT': 45, 'TP': 291} |
| NAS100\|ny\|bullish\|D1 | 3447 | 631 | 631 | 235.8588 | 0.373786 | 0.545166 | {'LOWER_TF_GAPPY': 64, 'NO_ENTRY': 1044, 'PRE_AI_POI_REJECT': 157, 'SAME_BAR': 51, 'SETUP_NOT_REFINABLE': 1301, 'SL': 358, 'TIMEOUT': 43, 'TP': 429} |
| NAS100\|ny\|bullish\|H4+H1_consensus | 2481 | 640 | 640 | -25.0 | -0.039062 | 0.384375 | {'LOWER_TF_GAPPY': 16, 'NO_ENTRY': 1178, 'PRE_AI_POI_REJECT': 69, 'SAME_BAR': 56, 'SETUP_NOT_REFINABLE': 374, 'SL': 448, 'TIMEOUT': 40, 'TP': 300} |
| US30_cash\|london\|bearish\|D1 | 879 | 173 | 173 | 49.5 | 0.286127 | 0.514451 | {'NO_ENTRY': 182, 'PRE_AI_POI_REJECT': 80, 'SAME_BAR': 29, 'SETUP_NOT_REFINABLE': 415, 'SL': 84, 'TP': 89} |
| US30_cash\|london\|bullish\|H4+H1_consensus | 1369 | 355 | 355 | 18.2344 | 0.051365 | 0.411268 | {'LOWER_TF_GAPPY': 17, 'NO_ENTRY': 801, 'PRE_AI_POI_REJECT': 25, 'SAME_BAR': 84, 'SETUP_NOT_REFINABLE': 72, 'SL': 210, 'TIMEOUT': 10, 'TP': 150} |
| US30_cash\|ny\|bullish\|D1 | 1737 | 230 | 230 | -2.6284 | -0.011428 | 0.391304 | {'LOWER_TF_GAPPY': 27, 'NO_ENTRY': 200, 'PRE_AI_POI_REJECT': 114, 'SAME_BAR': 17, 'SETUP_NOT_REFINABLE': 1107, 'SL': 166, 'TIMEOUT': 7, 'TP': 99} |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 1353 | 320 | 320 | 162.7673 | 0.508648 | 0.590625 | {'LOWER_TF_GAPPY': 37, 'NO_ENTRY': 785, 'PRE_AI_POI_REJECT': 25, 'SAME_BAR': 69, 'SETUP_NOT_REFINABLE': 91, 'SL': 143, 'TIMEOUT': 5, 'TP': 198} |
| USDJPY\|london\|bearish\|D1 | 1093 | 404 | 154 | 66.0 | 0.428571 | 0.571429 | {'NO_ENTRY': 310, 'PRE_AI_POI_REJECT': 91, 'SAME_BAR': 16, 'SETUP_NOT_REFINABLE': 517, 'SL': 71, 'TP': 88} |
| USDJPY\|london\|bearish\|H4+H1_consensus | 610 | 425 | 181 | 49.2944 | 0.272345 | 0.524862 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 350, 'PRE_AI_POI_REJECT': 13, 'SAME_BAR': 10, 'SETUP_NOT_REFINABLE': 46, 'SL': 86, 'TIMEOUT': 7, 'TP': 88} |
| USDJPY\|london\|bullish\|D1 | 2533 | 776 | 404 | -2.3875 | -0.00591 | 0.398515 | {'NO_ENTRY': 496, 'PRE_AI_POI_REJECT': 165, 'SAME_BAR': 43, 'SETUP_NOT_REFINABLE': 1415, 'SL': 246, 'TIMEOUT': 15, 'TP': 153} |
| USDJPY\|london\|bullish\|H4+H1_consensus | 1829 | 1243 | 522 | -18.5586 | -0.035553 | 0.388889 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 956, 'PRE_AI_POI_REJECT': 57, 'SAME_BAR': 86, 'SETUP_NOT_REFINABLE': 174, 'SL': 317, 'TIMEOUT': 25, 'TP': 204} |
| USDJPY\|ny\|bullish\|H4+H1_consensus | 1840 | 1168 | 447 | -60.9654 | -0.136388 | 0.348993 | {'LOWER_TF_GAPPY': 10, 'NO_ENTRY': 1016, 'PRE_AI_POI_REJECT': 57, 'SAME_BAR': 98, 'SETUP_NOT_REFINABLE': 180, 'SL': 302, 'TIMEOUT': 29, 'TP': 148} |
| USDJPY\|tokyo\|bearish\|D1 | 1309 | 508 | 212 | 133.5983 | 0.630181 | 0.65566 | {'NO_ENTRY': 354, 'PRE_AI_POI_REJECT': 119, 'SAME_BAR': 25, 'SETUP_NOT_REFINABLE': 599, 'SL': 73, 'TIMEOUT': 2, 'TP': 137} |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 674 | 458 | 252 | 97.5805 | 0.387224 | 0.563492 | {'LOWER_TF_GAPPY': 12, 'NO_ENTRY': 310, 'PRE_AI_POI_REJECT': 12, 'SAME_BAR': 17, 'SETUP_NOT_REFINABLE': 71, 'SL': 104, 'TIMEOUT': 19, 'TP': 129} |
| USDJPY\|tokyo\|bullish\|D1 | 3041 | 924 | 482 | -11.3247 | -0.023495 | 0.394191 | {'NO_ENTRY': 574, 'PRE_AI_POI_REJECT': 222, 'SAME_BAR': 38, 'SETUP_NOT_REFINABLE': 1702, 'SL': 294, 'TIMEOUT': 26, 'TP': 185} |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | 2186 | 1476 | 655 | 135.492 | 0.206858 | 0.485496 | {'NO_ENTRY': 1123, 'PRE_AI_POI_REJECT': 52, 'SAME_BAR': 105, 'SETUP_NOT_REFINABLE': 230, 'SL': 324, 'TIMEOUT': 74, 'TP': 278} |
| XAGUSD\|london\|bearish\|H4+H1_consensus | 1661 | 482 | 482 | 41.1849 | 0.085446 | 0.43361 | {'LOWER_TF_GAPPY': 15, 'NO_ENTRY': 791, 'PRE_AI_POI_REJECT': 98, 'SAME_BAR': 9, 'SETUP_NOT_REFINABLE': 147, 'SL': 329, 'TIMEOUT': 24, 'TP': 248} |
| XAGUSD\|london\|bullish\|D1 | 2285 | 249 | 249 | 100.5655 | 0.403878 | 0.558233 | {'LOWER_TF_GAPPY': 7, 'NO_ENTRY': 834, 'PRE_AI_POI_REJECT': 275, 'SETUP_NOT_REFINABLE': 817, 'SL': 153, 'TIMEOUT': 16, 'TP': 183} |
| XAGUSD\|london\|bullish\|H4+H1_consensus | 3017 | 584 | 584 | 118.5 | 0.202911 | 0.481164 | {'LOWER_TF_GAPPY': 80, 'NO_ENTRY': 1937, 'PRE_AI_POI_REJECT': 75, 'SAME_BAR': 37, 'SETUP_NOT_REFINABLE': 202, 'SL': 363, 'TIMEOUT': 3, 'TP': 320} |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | 1988 | 285 | 285 | 67.1006 | 0.235441 | 0.491228 | {'LOWER_TF_GAPPY': 25, 'NO_ENTRY': 1060, 'PRE_AI_POI_REJECT': 128, 'SAME_BAR': 7, 'SETUP_NOT_REFINABLE': 179, 'SL': 283, 'TIMEOUT': 17, 'TP': 289} |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | 3363 | 509 | 509 | 178.5 | 0.350688 | 0.540275 | {'LOWER_TF_GAPPY': 166, 'NO_ENTRY': 2167, 'PRE_AI_POI_REJECT': 69, 'SAME_BAR': 52, 'SETUP_NOT_REFINABLE': 169, 'SL': 315, 'TIMEOUT': 29, 'TP': 396} |
| XAUUSD\|london\|bearish\|H4+H1_consensus | 1452 | 388 | 388 | 52.0 | 0.134021 | 0.453608 | {'NO_ENTRY': 779, 'PRE_AI_POI_REJECT': 25, 'SAME_BAR': 14, 'SETUP_NOT_REFINABLE': 153, 'SL': 265, 'TIMEOUT': 26, 'TP': 190} |
| XAUUSD\|london\|bullish\|D1 | 2716 | 395 | 395 | 71.6689 | 0.18144 | 0.470886 | {'LOWER_TF_GAPPY': 23, 'NO_ENTRY': 1009, 'PRE_AI_POI_REJECT': 257, 'SAME_BAR': 14, 'SETUP_NOT_REFINABLE': 962, 'SL': 222, 'TIMEOUT': 13, 'TP': 216} |
| XAUUSD\|london\|bullish\|H4+H1_consensus | 3012 | 786 | 786 | -119.3763 | -0.151878 | 0.333333 | {'LOWER_TF_GAPPY': 32, 'NO_ENTRY': 1630, 'PRE_AI_POI_REJECT': 58, 'SAME_BAR': 33, 'SETUP_NOT_REFINABLE': 278, 'SL': 554, 'TIMEOUT': 100, 'TP': 327} |
| XAUUSD\|ny\|bearish\|H4+H1_consensus | 1537 | 283 | 283 | -2.2946 | -0.008108 | 0.39576 | {'LOWER_TF_GAPPY': 72, 'NO_ENTRY': 802, 'PRE_AI_POI_REJECT': 7, 'SAME_BAR': 24, 'SETUP_NOT_REFINABLE': 180, 'SL': 280, 'TIMEOUT': 29, 'TP': 143} |
| XAUUSD\|ny\|bullish\|D1 | 2880 | 311 | 311 | 177.3642 | 0.570303 | 0.62701 | {'LOWER_TF_GAPPY': 61, 'NO_ENTRY': 1113, 'PRE_AI_POI_REJECT': 262, 'SAME_BAR': 26, 'SETUP_NOT_REFINABLE': 928, 'SL': 182, 'TIMEOUT': 23, 'TP': 285} |
| XAUUSD\|ny\|bullish\|H4+H1_consensus | 3195 | 619 | 619 | 31.4874 | 0.050868 | 0.420032 | {'LOWER_TF_GAPPY': 90, 'NO_ENTRY': 1796, 'PRE_AI_POI_REJECT': 86, 'SAME_BAR': 36, 'SETUP_NOT_REFINABLE': 201, 'SL': 506, 'TIMEOUT': 74, 'TP': 406} |

## Period Scores

| period | actions_taken | resolved_r_n | sum_r | mean_r |
| --- | --- | --- | --- | --- |
| 2022-01 | 172 | 6 | -1.0 | -0.166667 |
| 2022-02 | 879 | 158 | -26.3897 | -0.167023 |
| 2022-03 | 588 | 79 | 63.5 | 0.803797 |
| 2022-04 | 770 | 161 | -67.8993 | -0.421735 |
| 2022-05 | 1448 | 302 | 110.0933 | 0.364547 |
| 2022-06 | 1207 | 405 | -97.2221 | -0.240055 |
| 2022-07 | 1145 | 126 | 104.3631 | 0.828279 |
| 2022-08 | 1450 | 374 | 26.33 | 0.070401 |
| 2022-09 | 1024 | 349 | -86.3821 | -0.247513 |
| 2022-10 | 1465 | 302 | 157.0614 | 0.520071 |
| 2022-11 | 1371 | 276 | 166.3462 | 0.602704 |
| 2022-12 | 1561 | 270 | -0.0028 | -1e-05 |
| 2023-01 | 1579 | 377 | 16.652 | 0.04417 |
| 2023-02 | 1491 | 245 | 26.4687 | 0.108036 |
| 2023-03 | 1570 | 275 | -52.5757 | -0.191184 |
| 2023-04 | 2155 | 338 | 66.0003 | 0.195267 |
| 2023-05 | 2747 | 496 | 87.5684 | 0.176549 |
| 2023-06 | 2203 | 391 | 134.0052 | 0.342724 |
| 2023-07 | 1837 | 450 | 239.6825 | 0.532628 |
| 2023-08 | 2249 | 532 | 63.2844 | 0.118956 |
| 2023-09 | 1451 | 259 | -21.0569 | -0.081301 |
| 2023-10 | 1747 | 348 | -65.9981 | -0.18965 |
| 2023-11 | 2509 | 501 | 185.5732 | 0.370406 |
| 2023-12 | 1982 | 498 | -39.9972 | -0.080316 |
| 2024-01 | 1601 | 327 | 220.7483 | 0.675071 |
| 2024-02 | 1135 | 270 | -8.7309 | -0.032337 |
| 2024-03 | 2071 | 289 | 30.8011 | 0.106578 |
| 2024-04 | 1820 | 317 | 42.1113 | 0.132843 |
| 2024-05 | 2637 | 618 | -33.6107 | -0.054386 |
| 2024-06 | 1774 | 367 | -2.441 | -0.006651 |
| 2024-07 | 1788 | 322 | 167.9376 | 0.521545 |
| 2024-08 | 1902 | 399 | 116.4255 | 0.291793 |
| 2024-09 | 2139 | 489 | 138.0661 | 0.282344 |
| 2024-10 | 2555 | 568 | 96.7542 | 0.170342 |
| 2024-11 | 2239 | 468 | -88.4098 | -0.18891 |
| 2024-12 | 1238 | 352 | 47.7996 | 0.135794 |
| 2025-01 | 2276 | 370 | 106.9782 | 0.28913 |
| 2025-02 | 2429 | 495 | 30.3623 | 0.061338 |
| 2025-03 | 1860 | 520 | 61.8843 | 0.119008 |
| 2025-04 | 1136 | 193 | -28.0006 | -0.145081 |
| 2025-05 | 1875 | 263 | -28.7025 | -0.109135 |
| 2025-06 | 2385 | 380 | 114.2806 | 0.300738 |
| 2025-07 | 1946 | 483 | -11.3408 | -0.02348 |
| 2025-08 | 1207 | 215 | -22.4946 | -0.104626 |
| 2025-09 | 2185 | 327 | 113.3117 | 0.346519 |
| 2025-10 | 2349 | 516 | -85.8342 | -0.166345 |
| 2025-11 | 1354 | 385 | 25.7425 | 0.066864 |
| 2025-12 | 2670 | 372 | 132.3459 | 0.355769 |
| 2026-01 | 2545 | 459 | 77.1262 | 0.168031 |
| 2026-02 | 1299 | 297 | 114.2725 | 0.384756 |
| 2026-03 | 2352 | 558 | 94.4456 | 0.169257 |
| 2026-04 | 2040 | 404 | -26.6116 | -0.06587 |

## Interpretation

- This validates the replay boundary: the strategy can select cohorts without receiving outcome/refinement fields.
- Positive historical replay results remain diagnostic because these cohorts were discovered from the same broad dataset.
- The same harness can now be used for broader controlled strategy experiments while preserving trial-budget language.
