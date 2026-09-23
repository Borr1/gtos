# Phase 3 Historical Opportunity Truth Layer v2

**Created UTC:** 2026-05-01T06:20:25.699418+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z.jsonl`
**Output JSONL:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Rows classified:** 205197
**Lower timeframe priority:** M1, M5

## Interpretation Boundary

- Research/tooling only; no live trading logic, prompt, or config behavior is changed.
- No paid AI/API replay is performed; AI-attempted rows and AI call counts must remain zero.
- Truth labels are mechanical diagnostic labels, not production trade outcomes.
- `truth_failure_bucket` includes success, failure, ambiguity, setup-reject, and data-quality anatomy buckets.

## Data Integrity

| rows | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum |
| --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 |

## Truth Outcome Distribution

| truth_outcome | rows |
| --- | --- |
| SETUP_NOT_REFINABLE | 61112 |
| PRE_SCREEN_REJECT | 56834 |
| NO_ENTRY | 44098 |
| SL | 14024 |
| PRE_AI_POI_REJECT | 12209 |
| TP | 11124 |
| SAME_BAR | 1907 |
| TIMEOUT | 1662 |
| LOWER_TF_GAPPY | 1135 |
| SKIP_FIRST_NY_CANDLE | 1092 |

## Failure And Success Anatomy

| truth_failure_bucket | rows |
| --- | --- |
| SETUP_MISSING_OR_LOW_QUALITY_POI | 62273 |
| SETUP_HTF_NO_DIRECTION | 45457 |
| FAIL_NO_FILL | 44098 |
| FAIL_STOP_FIRST | 13204 |
| SETUP_HTF_CONFLICT | 11377 |
| SUCCESS_TP_FIRST | 11124 |
| SETUP_POI_ALREADY_MITIGATED | 11048 |
| AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 1907 |
| DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 1135 |
| MIXED_TIMEOUT_POSITIVE | 1126 |
| SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| FAIL_IMMEDIATE_STOP_AFTER_FILL | 820 |
| FAIL_TIMEOUT_NEGATIVE | 536 |

## Ambiguity And Confidence

### Ambiguity Buckets

| truth_ambiguity_bucket | rows |
| --- | --- |
| NOT_REFINABLE_PRE_AI_REJECT | 70135 |
| NOT_REFINABLE_MECHANICAL_SETUP | 61112 |
| LOWER_TF_RESOLVED | 37713 |
| M15_ONLY_LOWER_TF_UNAVAILABLE | 33195 |
| LOWER_TF_SAME_BAR_REMAINS | 1671 |
| LOWER_TF_GAPPY | 1135 |
| M15_SAME_BAR_NO_LOCAL_LOWER_TF | 236 |

### Confidence

| truth_confidence | rows |
| --- | --- |
| NONE | 131247 |
| HIGH | 37713 |
| MEDIUM | 32888 |
| LOW | 3349 |

### Selected Truth Timeframe

| truth_source_timeframe | rows |
| --- | --- |
| NONE | 131247 |
| M15 | 33431 |
| M1 | 30421 |
| M5 | 10098 |

## Lower-Timeframe Coverage

| timeframe | tp | sl | timeout | no_entry | same_bar | no_full_horizon | attempted | local_coverage | local_coverage_rate | horizon_complete | horizon_complete_rate | gappy | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | 11411 | 14663 | 1708 | 43829 | 1756 | 20 | 73950 | 73387 | 0.992387 | 11836 | 0.160054 | 61509 | 30421 |
| M5 | 10575 | 12896 | 1702 | 43869 | 4339 | 20 | 73950 | 73401 | 0.992576 | 25349 | 0.342786 | 48010 | 10098 |

## M15 Outcome To Truth Outcome

| truth_outcome | m15_outcome | rows |
| --- | --- | --- |
| SETUP_NOT_REFINABLE | NOT_EVALUATED | 61112 |
| PRE_SCREEN_REJECT | NOT_EVALUATED | 56834 |
| NO_ENTRY | NO_ENTRY | 44098 |
| PRE_AI_POI_REJECT | NOT_EVALUATED | 12209 |
| SL | SL | 10472 |
| TP | TP | 9021 |
| SL | SAME_BAR | 3552 |
| TP | SAME_BAR | 2071 |
| SAME_BAR | SAME_BAR | 1907 |
| TIMEOUT | TIMEOUT | 1641 |
| LOWER_TF_GAPPY | SAME_BAR | 1135 |
| SKIP_FIRST_NY_CANDLE | NOT_EVALUATED | 1092 |
| TP | SL | 32 |
| TIMEOUT | SAME_BAR | 21 |

## Cohort Diagnostics

### Symbol

| symbol | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 33471 | 4161 | 0.198142 | 0.489065 | 1810 | 2003 | 348 | 6665 | 307 | 0 | 39 | 9115 | 1701 | 356 | 22299 |
| GBPUSD | 31410 | 4179 | 0.055283 | 0.433597 | 1601 | 2249 | 329 | 6173 | 227 | 0 | 91 | 8556 | 1792 | 322 | 20740 |
| NAS100 | 24454 | 3866 | 0.082611 | 0.440766 | 1547 | 2116 | 203 | 5521 | 286 | 0 | 148 | 3146 | 6230 | 445 | 14633 |
| US30_cash | 16257 | 2037 | 0.034706 | 0.405989 | 801 | 1164 | 72 | 3009 | 235 | 0 | 125 | 1856 | 3149 | 401 | 10851 |
| USDJPY | 33481 | 4256 | 0.137312 | 0.466165 | 1788 | 2216 | 252 | 6871 | 547 | 0 | 52 | 9166 | 1948 | 612 | 21755 |
| XAGUSD | 33364 | 3704 | 0.240003 | 0.49784 | 1770 | 1831 | 103 | 8150 | 119 | 0 | 377 | 2512 | 9195 | 643 | 21014 |
| XAUUSD | 32760 | 4607 | 0.087072 | 0.443673 | 1807 | 2445 | 355 | 7709 | 186 | 0 | 303 | 3362 | 8873 | 570 | 19955 |

### Session

| session | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| london | 92373 | 12754 | 0.083186 | 0.439 | 5133 | 6923 | 698 | 19771 | 816 | 0 | 348 | 17713 | 14672 | 1304 | 58684 |
| ny | 87762 | 10737 | 0.135677 | 0.462885 | 4478 | 5529 | 730 | 19439 | 756 | 0 | 775 | 12996 | 17013 | 1698 | 56055 |
| tokyo | 25062 | 3319 | 0.241748 | 0.506478 | 1513 | 1572 | 234 | 4888 | 335 | 0 | 12 | 7004 | 1203 | 347 | 16508 |

### Year

| year | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 32814 | 4224 | 0.129599 | 0.458807 | 1782 | 2201 | 241 | 6788 | 286 | 0 | 139 | 6041 | 4664 | 732 | 21377 |
| 2023 | 49858 | 6966 | 0.120701 | 0.457651 | 2858 | 3642 | 466 | 11158 | 536 | 0 | 194 | 9597 | 8527 | 730 | 31004 |
| 2024 | 52578 | 6772 | 0.128618 | 0.458358 | 2802 | 3529 | 441 | 10837 | 584 | 0 | 313 | 10187 | 7422 | 897 | 34072 |
| 2025 | 52691 | 6518 | 0.097877 | 0.442927 | 2665 | 3507 | 346 | 11726 | 356 | 0 | 357 | 8873 | 9371 | 713 | 33734 |
| 2026 | 17256 | 2330 | 0.181495 | 0.486266 | 1017 | 1145 | 168 | 3589 | 145 | 0 | 132 | 3015 | 2904 | 277 | 11060 |

### Framework

| framework | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ob_retest | 205197 | 26810 | 0.123837 | 0.456919 | 11124 | 14024 | 1662 | 44098 | 1907 | 0 | 1135 | 37713 | 32888 | 3349 | 131247 |

### Regime

| regime | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bearish\|D1 | 21222 | 3395 | 0.103695 | 0.448601 | 1397 | 1806 | 192 | 4345 | 180 | 0 | 61 | 5069 | 2671 | 241 | 13241 |
| bearish\|H4+H1_consensus | 15845 | 5058 | 0.021235 | 0.417556 | 1866 | 2784 | 408 | 8611 | 211 | 0 | 188 | 6832 | 6822 | 414 | 1777 |
| bearish\|H4_primary | 15063 | 535 | 0.196448 | 0.471028 | 241 | 262 | 32 | 380 | 30 | 0 | 19 | 618 | 297 | 49 | 14099 |
| bullish\|D1 | 41347 | 6941 | 0.168824 | 0.475868 | 2985 | 3508 | 448 | 10843 | 528 | 0 | 347 | 9237 | 8476 | 946 | 22688 |
| bullish\|H4+H1_consensus | 35494 | 10071 | 0.142341 | 0.464403 | 4269 | 5248 | 554 | 19472 | 914 | 0 | 509 | 15055 | 14280 | 1631 | 4528 |
| bullish\|H4_primary | 18300 | 810 | 0.185438 | 0.47284 | 366 | 416 | 28 | 447 | 44 | 0 | 11 | 902 | 342 | 68 | 16988 |
| none\|none | 57926 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 57926 |

### Symbol x Session

| symbol_session | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london | 10470 | 1346 | 0.191849 | 0.475483 | 598 | 670 | 78 | 2073 | 91 | 0 | 15 | 2909 | 510 | 106 | 6945 |
| GBPJPY\|ny | 10480 | 1235 | 0.105204 | 0.466397 | 464 | 614 | 157 | 2118 | 68 | 0 | 24 | 2715 | 628 | 102 | 7035 |
| GBPJPY\|tokyo | 12521 | 1580 | 0.276148 | 0.518354 | 748 | 719 | 113 | 2474 | 148 | 0 | 0 | 3491 | 563 | 148 | 8319 |
| GBPUSD\|london | 20940 | 3029 | 0.075216 | 0.44239 | 1195 | 1626 | 208 | 4000 | 165 | 0 | 60 | 5920 | 1109 | 225 | 13686 |
| GBPUSD\|ny | 10470 | 1150 | 0.002781 | 0.410435 | 406 | 623 | 121 | 2173 | 62 | 0 | 31 | 2636 | 683 | 97 | 7054 |
| NAS100\|london | 11444 | 1841 | 0.044695 | 0.427485 | 719 | 1046 | 76 | 2574 | 148 | 0 | 48 | 1603 | 2803 | 205 | 6833 |
| NAS100\|ny | 13010 | 2025 | 0.117083 | 0.45284 | 828 | 1070 | 127 | 2947 | 138 | 0 | 100 | 1543 | 3427 | 240 | 7800 |
| US30_cash\|london | 8189 | 1009 | 0.008346 | 0.391477 | 385 | 585 | 39 | 1531 | 128 | 0 | 37 | 947 | 1569 | 189 | 5484 |
| US30_cash\|ny | 8068 | 1028 | 0.06058 | 0.420233 | 416 | 579 | 33 | 1478 | 107 | 0 | 88 | 909 | 1580 | 212 | 5367 |
| USDJPY\|london | 10470 | 1365 | 0.060874 | 0.430037 | 552 | 766 | 47 | 2180 | 155 | 0 | 20 | 2967 | 575 | 178 | 6750 |
| USDJPY\|ny | 10470 | 1152 | 0.11741 | 0.46441 | 471 | 597 | 84 | 2277 | 205 | 0 | 20 | 2686 | 733 | 235 | 6816 |
| USDJPY\|tokyo | 12541 | 1739 | 0.210493 | 0.495687 | 765 | 853 | 121 | 2414 | 187 | 0 | 12 | 3513 | 640 | 199 | 8189 |
| XAGUSD\|london | 15572 | 1814 | 0.157194 | 0.464168 | 818 | 953 | 43 | 3772 | 49 | 0 | 113 | 1433 | 4091 | 224 | 9824 |
| XAGUSD\|ny | 17792 | 1890 | 0.319483 | 0.530159 | 952 | 878 | 60 | 4378 | 70 | 0 | 264 | 1079 | 5104 | 419 | 11190 |
| XAUUSD\|london | 15288 | 2350 | 0.049339 | 0.428936 | 866 | 1277 | 207 | 3641 | 80 | 0 | 55 | 1934 | 4015 | 177 | 9162 |
| XAUUSD\|ny | 17472 | 2257 | 0.12636 | 0.459016 | 941 | 1168 | 148 | 4068 | 106 | 0 | 248 | 1428 | 4858 | 393 | 10793 |

## Top Failure Buckets By Cohort

### Symbol

| symbol | truth_failure_bucket | rows |
| --- | --- | --- |
| GBPUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 11033 |
| USDJPY | SETUP_MISSING_OR_LOW_QUALITY_POI | 10693 |
| GBPJPY | SETUP_MISSING_OR_LOW_QUALITY_POI | 9717 |
| XAGUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 9321 |
| XAGUSD | SETUP_HTF_NO_DIRECTION | 8819 |
| XAUUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 8596 |
| XAGUSD | FAIL_NO_FILL | 8150 |
| GBPJPY | SETUP_HTF_NO_DIRECTION | 7927 |
| XAUUSD | FAIL_NO_FILL | 7709 |
| NAS100 | SETUP_MISSING_OR_LOW_QUALITY_POI | 7427 |
| XAUUSD | SETUP_HTF_NO_DIRECTION | 7404 |
| USDJPY | SETUP_HTF_NO_DIRECTION | 7367 |
| USDJPY | FAIL_NO_FILL | 6871 |
| GBPJPY | FAIL_NO_FILL | 6665 |
| GBPUSD | SETUP_HTF_NO_DIRECTION | 6510 |
| GBPUSD | FAIL_NO_FILL | 6173 |
| NAS100 | FAIL_NO_FILL | 5521 |
| US30_cash | SETUP_MISSING_OR_LOW_QUALITY_POI | 5486 |
| NAS100 | SETUP_HTF_NO_DIRECTION | 4119 |
| US30_cash | SETUP_HTF_NO_DIRECTION | 3311 |
| US30_cash | FAIL_NO_FILL | 3009 |
| GBPJPY | SETUP_HTF_CONFLICT | 2608 |
| XAUUSD | FAIL_STOP_FIRST | 2259 |
| GBPUSD | FAIL_STOP_FIRST | 2218 |
| USDJPY | FAIL_STOP_FIRST | 2099 |
| USDJPY | SETUP_POI_ALREADY_MITIGATED | 2049 |
| GBPJPY | SETUP_POI_ALREADY_MITIGATED | 2047 |
| GBPJPY | FAIL_STOP_FIRST | 1960 |
| NAS100 | FAIL_STOP_FIRST | 1907 |
| GBPUSD | SETUP_POI_ALREADY_MITIGATED | 1864 |

### Session

| session | truth_failure_bucket | rows |
| --- | --- | --- |
| london | SETUP_MISSING_OR_LOW_QUALITY_POI | 28450 |
| ny | SETUP_MISSING_OR_LOW_QUALITY_POI | 26141 |
| london | SETUP_HTF_NO_DIRECTION | 20231 |
| london | FAIL_NO_FILL | 19771 |
| ny | SETUP_HTF_NO_DIRECTION | 19497 |
| ny | FAIL_NO_FILL | 19439 |
| tokyo | SETUP_MISSING_OR_LOW_QUALITY_POI | 7682 |
| london | FAIL_STOP_FIRST | 6576 |
| tokyo | SETUP_HTF_NO_DIRECTION | 5729 |
| london | SUCCESS_TP_FIRST | 5133 |
| ny | FAIL_STOP_FIRST | 5115 |
| london | SETUP_POI_ALREADY_MITIGATED | 5027 |
| london | SETUP_HTF_CONFLICT | 4976 |
| tokyo | FAIL_NO_FILL | 4888 |
| ny | SETUP_HTF_CONFLICT | 4818 |
| ny | SETUP_POI_ALREADY_MITIGATED | 4507 |
| ny | SUCCESS_TP_FIRST | 4478 |
| tokyo | SETUP_HTF_CONFLICT | 1583 |
| tokyo | SETUP_POI_ALREADY_MITIGATED | 1514 |
| tokyo | FAIL_STOP_FIRST | 1513 |
| tokyo | SUCCESS_TP_FIRST | 1513 |
| ny | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| london | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 816 |
| ny | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 775 |
| ny | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 756 |
| ny | MIXED_TIMEOUT_POSITIVE | 492 |
| london | MIXED_TIMEOUT_POSITIVE | 466 |
| ny | FAIL_IMMEDIATE_STOP_AFTER_FILL | 414 |
| london | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 348 |
| london | FAIL_IMMEDIATE_STOP_AFTER_FILL | 347 |

### Year

| year | truth_failure_bucket | rows |
| --- | --- | --- |
| 2024 | SETUP_MISSING_OR_LOW_QUALITY_POI | 16641 |
| 2023 | SETUP_MISSING_OR_LOW_QUALITY_POI | 15744 |
| 2025 | SETUP_MISSING_OR_LOW_QUALITY_POI | 15087 |
| 2025 | SETUP_HTF_NO_DIRECTION | 12466 |
| 2024 | SETUP_HTF_NO_DIRECTION | 11811 |
| 2025 | FAIL_NO_FILL | 11726 |
| 2023 | FAIL_NO_FILL | 11158 |
| 2024 | FAIL_NO_FILL | 10837 |
| 2022 | SETUP_MISSING_OR_LOW_QUALITY_POI | 9835 |
| 2023 | SETUP_HTF_NO_DIRECTION | 9235 |
| 2022 | SETUP_HTF_NO_DIRECTION | 8474 |
| 2022 | FAIL_NO_FILL | 6788 |
| 2026 | SETUP_MISSING_OR_LOW_QUALITY_POI | 4966 |
| 2026 | FAIL_NO_FILL | 3589 |
| 2026 | SETUP_HTF_NO_DIRECTION | 3471 |
| 2025 | FAIL_STOP_FIRST | 3398 |
| 2023 | FAIL_STOP_FIRST | 3367 |
| 2024 | FAIL_STOP_FIRST | 3260 |
| 2025 | SETUP_HTF_CONFLICT | 3207 |
| 2023 | SETUP_POI_ALREADY_MITIGATED | 2960 |
| 2023 | SUCCESS_TP_FIRST | 2858 |
| 2024 | SETUP_POI_ALREADY_MITIGATED | 2833 |
| 2023 | SETUP_HTF_CONFLICT | 2808 |
| 2024 | SUCCESS_TP_FIRST | 2802 |
| 2025 | SETUP_POI_ALREADY_MITIGATED | 2716 |
| 2025 | SUCCESS_TP_FIRST | 2665 |
| 2024 | SETUP_HTF_CONFLICT | 2528 |
| 2022 | FAIL_STOP_FIRST | 2127 |
| 2022 | SUCCESS_TP_FIRST | 1782 |
| 2022 | SETUP_HTF_CONFLICT | 1730 |

### Framework

| framework | truth_failure_bucket | rows |
| --- | --- | --- |
| ob_retest | SETUP_MISSING_OR_LOW_QUALITY_POI | 62273 |
| ob_retest | SETUP_HTF_NO_DIRECTION | 45457 |
| ob_retest | FAIL_NO_FILL | 44098 |
| ob_retest | FAIL_STOP_FIRST | 13204 |
| ob_retest | SETUP_HTF_CONFLICT | 11377 |
| ob_retest | SUCCESS_TP_FIRST | 11124 |
| ob_retest | SETUP_POI_ALREADY_MITIGATED | 11048 |
| ob_retest | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 1907 |
| ob_retest | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 1135 |
| ob_retest | MIXED_TIMEOUT_POSITIVE | 1126 |
| ob_retest | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| ob_retest | FAIL_IMMEDIATE_STOP_AFTER_FILL | 820 |
| ob_retest | FAIL_TIMEOUT_NEGATIVE | 536 |

### Regime

| regime | truth_failure_bucket | rows |
| --- | --- | --- |
| none\|none | SETUP_HTF_NO_DIRECTION | 45457 |
| bullish\|H4+H1_consensus | FAIL_NO_FILL | 19472 |
| bullish\|D1 | SETUP_MISSING_OR_LOW_QUALITY_POI | 18618 |
| bullish\|H4_primary | SETUP_MISSING_OR_LOW_QUALITY_POI | 16570 |
| bearish\|H4_primary | SETUP_MISSING_OR_LOW_QUALITY_POI | 13757 |
| bearish\|D1 | SETUP_MISSING_OR_LOW_QUALITY_POI | 11931 |
| none\|none | SETUP_HTF_CONFLICT | 11377 |
| bullish\|D1 | FAIL_NO_FILL | 10843 |
| bearish\|H4+H1_consensus | FAIL_NO_FILL | 8611 |
| bullish\|H4+H1_consensus | FAIL_STOP_FIRST | 4918 |
| bearish\|D1 | FAIL_NO_FILL | 4345 |
| bullish\|H4+H1_consensus | SUCCESS_TP_FIRST | 4269 |
| bullish\|D1 | SETUP_POI_ALREADY_MITIGATED | 4070 |
| bullish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 3573 |
| bullish\|D1 | FAIL_STOP_FIRST | 3214 |
| bullish\|D1 | SUCCESS_TP_FIRST | 2985 |
| bearish\|H4+H1_consensus | FAIL_STOP_FIRST | 2622 |
| bearish\|H4+H1_consensus | SUCCESS_TP_FIRST | 1866 |
| bearish\|D1 | FAIL_STOP_FIRST | 1775 |
| bearish\|D1 | SUCCESS_TP_FIRST | 1397 |
| bearish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 1335 |
| bearish\|D1 | SETUP_POI_ALREADY_MITIGATED | 1310 |
| none\|none | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| bullish\|H4+H1_consensus | SETUP_MISSING_OR_LOW_QUALITY_POI | 955 |
| bullish\|H4+H1_consensus | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 914 |
| bullish\|D1 | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 528 |
| bullish\|H4+H1_consensus | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 509 |
| bullish\|H4_primary | FAIL_NO_FILL | 447 |
| bearish\|H4+H1_consensus | SETUP_MISSING_OR_LOW_QUALITY_POI | 442 |
| bullish\|H4_primary | SETUP_POI_ALREADY_MITIGATED | 418 |

## Synthesis

- Classified 205,197 opportunity rows with 205,197 unique keys and 0 AI calls.
- The truth layer separates setup rejects, no-fill outcomes, resolved TP/SL paths, same-bar ambiguity, lower-timeframe gaps, and incomplete lower-timeframe horizons before any parameter sweep.
- Core truth outcomes: TP=11,124, SL=14,024, TIMEOUT=1,662, NO_ENTRY=44,098, SAME_BAR=1,907.
- Selected truth source counts: M1=30,421, M15=33,431, M5=10,098, NONE=131,247.
- Confidence mix: HIGH=37,713, LOW=3,349, MEDIUM=32,888, NONE=131,247. Low/none-confidence rows should be excluded or sensitivity-tested before optimization.
- This report is a label-quality audit only. It does not justify live trading changes, prompt changes, or buffer/offset tuning by itself.
