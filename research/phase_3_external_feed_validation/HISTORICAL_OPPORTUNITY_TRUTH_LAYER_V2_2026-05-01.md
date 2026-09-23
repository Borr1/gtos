# Phase 3 Historical Opportunity Truth Layer v2

**Created UTC:** 2026-05-01T05:21:15.786112+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z.jsonl`
**Output JSONL:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T051951Z.jsonl`
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
| PRE_AI_POI_REJECT | 12209 |
| SL | 11516 |
| TP | 9549 |
| SAME_BAR | 6624 |
| TIMEOUT | 1645 |
| SKIP_FIRST_NY_CANDLE | 1092 |
| LOWER_TF_GAPPY | 518 |

## Failure And Success Anatomy

| truth_failure_bucket | rows |
| --- | --- |
| SETUP_MISSING_OR_LOW_QUALITY_POI | 62273 |
| SETUP_HTF_NO_DIRECTION | 45457 |
| FAIL_NO_FILL | 44098 |
| SETUP_HTF_CONFLICT | 11377 |
| SETUP_POI_ALREADY_MITIGATED | 11048 |
| SUCCESS_TP_FIRST | 9549 |
| FAIL_STOP_FIRST | 9456 |
| AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 6624 |
| FAIL_IMMEDIATE_STOP_AFTER_FILL | 2060 |
| MIXED_TIMEOUT_POSITIVE | 1111 |
| SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| FAIL_TIMEOUT_NEGATIVE | 534 |
| DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 518 |

## Ambiguity And Confidence

### Ambiguity Buckets

| truth_ambiguity_bucket | rows |
| --- | --- |
| NOT_REFINABLE_PRE_AI_REJECT | 70135 |
| NOT_REFINABLE_MECHANICAL_SETUP | 61112 |
| M15_ONLY_LOWER_TF_UNAVAILABLE | 55210 |
| LOWER_TF_RESOLVED | 11598 |
| M15_SAME_BAR_NO_LOCAL_LOWER_TF | 5533 |
| LOWER_TF_SAME_BAR_REMAINS | 1091 |
| LOWER_TF_GAPPY | 518 |

### Confidence

| truth_confidence | rows |
| --- | --- |
| NONE | 131247 |
| MEDIUM | 54667 |
| HIGH | 11598 |
| LOW | 7685 |

### Selected Truth Timeframe

| truth_source_timeframe | rows |
| --- | --- |
| NONE | 131247 |
| M15 | 60743 |
| M5 | 11217 |
| M1 | 1990 |

## Lower-Timeframe Coverage

| timeframe | tp | sl | timeout | no_entry | same_bar | no_full_horizon | attempted | local_coverage | local_coverage_rate | horizon_complete | horizon_complete_rate | gappy | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | 869 | 1080 | 108 | 3029 | 152 | 20 | 73950 | 5258 | 0.071102 | 279 | 0.003773 | 4937 | 1990 |
| M5 | 3559 | 4484 | 545 | 15783 | 1624 | 20 | 73950 | 26015 | 0.351792 | 7251 | 0.098053 | 18722 | 11217 |

## M15 Outcome To Truth Outcome

| truth_outcome | m15_outcome | rows |
| --- | --- | --- |
| SETUP_NOT_REFINABLE | NOT_EVALUATED | 61112 |
| PRE_SCREEN_REJECT | NOT_EVALUATED | 56834 |
| NO_ENTRY | NO_ENTRY | 44098 |
| PRE_AI_POI_REJECT | NOT_EVALUATED | 12209 |
| SL | SL | 10489 |
| TP | TP | 9021 |
| SAME_BAR | SAME_BAR | 6624 |
| TIMEOUT | TIMEOUT | 1641 |
| SKIP_FIRST_NY_CANDLE | NOT_EVALUATED | 1092 |
| SL | SAME_BAR | 1027 |
| LOWER_TF_GAPPY | SAME_BAR | 518 |
| TP | SAME_BAR | 513 |
| TP | SL | 15 |
| TIMEOUT | SAME_BAR | 4 |

## Cohort Diagnostics

### Symbol

| symbol | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 33471 | 3785 | 0.238149 | 0.505945 | 1692 | 1749 | 344 | 6665 | 701 | 0 | 21 | 2661 | 7641 | 870 | 22299 |
| GBPUSD | 31410 | 3790 | 0.076868 | 0.44248 | 1477 | 1995 | 318 | 6173 | 658 | 0 | 49 | 2845 | 7046 | 779 | 20740 |
| NAS100 | 24454 | 3038 | 0.083059 | 0.4447 | 1194 | 1641 | 203 | 5521 | 1175 | 0 | 87 | 1454 | 7094 | 1273 | 14633 |
| US30_cash | 16257 | 1498 | 0.028516 | 0.401202 | 575 | 851 | 72 | 3009 | 852 | 0 | 47 | 612 | 3854 | 940 | 10851 |
| USDJPY | 33481 | 3698 | 0.214116 | 0.498378 | 1649 | 1799 | 250 | 6871 | 1125 | 0 | 32 | 2370 | 8178 | 1178 | 21755 |
| XAGUSD | 33364 | 3188 | 0.258532 | 0.505646 | 1538 | 1547 | 103 | 8150 | 844 | 0 | 168 | 716 | 10455 | 1179 | 21014 |
| XAUUSD | 32760 | 3713 | 0.090797 | 0.447347 | 1424 | 1934 | 355 | 7709 | 1269 | 0 | 114 | 940 | 10399 | 1466 | 19955 |

### Session

| session | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| london | 92373 | 10810 | 0.105421 | 0.448751 | 4393 | 5727 | 690 | 19771 | 2926 | 0 | 182 | 5569 | 24755 | 3365 | 58684 |
| ny | 87762 | 8960 | 0.156041 | 0.473214 | 3753 | 4484 | 723 | 19439 | 2984 | 0 | 324 | 4118 | 24047 | 3542 | 56055 |
| tokyo | 25062 | 2940 | 0.307203 | 0.533673 | 1403 | 1305 | 232 | 4888 | 714 | 0 | 12 | 1911 | 5865 | 778 | 16508 |

### Year

| year | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 32814 | 3544 | 0.179921 | 0.479966 | 1549 | 1760 | 235 | 6788 | 1105 | 0 | 0 | 0 | 9789 | 1648 | 21377 |
| 2023 | 49858 | 5579 | 0.180134 | 0.483599 | 2371 | 2745 | 463 | 11158 | 2117 | 0 | 0 | 0 | 16737 | 2117 | 31004 |
| 2024 | 52578 | 5320 | 0.13749 | 0.464474 | 2177 | 2710 | 433 | 10837 | 2320 | 0 | 29 | 291 | 15866 | 2349 | 34072 |
| 2025 | 52691 | 5937 | 0.108466 | 0.447532 | 2435 | 3156 | 346 | 11726 | 937 | 0 | 357 | 8292 | 9371 | 1294 | 33734 |
| 2026 | 17256 | 2330 | 0.181495 | 0.486266 | 1017 | 1145 | 168 | 3589 | 145 | 0 | 132 | 3015 | 2904 | 277 | 11060 |

### Framework

| framework | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ob_retest | 205197 | 22710 | 0.151515 | 0.469397 | 9549 | 11516 | 1645 | 44098 | 6624 | 0 | 518 | 11598 | 54667 | 7685 | 131247 |

### Regime

| regime | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bearish\|D1 | 21222 | 2974 | 0.117293 | 0.456624 | 1234 | 1550 | 190 | 4345 | 648 | 0 | 14 | 1558 | 5761 | 662 | 13241 |
| bearish\|H4+H1_consensus | 15845 | 4376 | 0.020653 | 0.41819 | 1592 | 2384 | 400 | 8611 | 1004 | 0 | 77 | 1772 | 11118 | 1178 | 1777 |
| bearish\|H4_primary | 15063 | 505 | 0.163565 | 0.457426 | 220 | 253 | 32 | 380 | 79 | 0 | 0 | 285 | 600 | 79 | 14099 |
| bullish\|D1 | 41347 | 5878 | 0.221841 | 0.498469 | 2615 | 2818 | 445 | 10843 | 1723 | 0 | 215 | 3693 | 12956 | 2010 | 22688 |
| bullish\|H4+H1_consensus | 35494 | 8295 | 0.173312 | 0.47836 | 3562 | 4183 | 550 | 19472 | 2998 | 0 | 201 | 4010 | 23397 | 3559 | 4528 |
| bullish\|H4_primary | 18300 | 682 | 0.260249 | 0.502933 | 326 | 328 | 28 | 447 | 172 | 0 | 11 | 280 | 835 | 197 | 16988 |
| none\|none | 57926 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 57926 |

### Symbol x Session

| symbol_session | rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | no_full_horizon | lower_tf_gappy | high_confidence | medium_confidence | low_confidence | none_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london | 10470 | 1204 | 0.24313 | 0.495847 | 555 | 571 | 78 | 2073 | 241 | 0 | 7 | 871 | 2366 | 288 | 6945 |
| GBPJPY\|ny | 10480 | 1147 | 0.129851 | 0.477768 | 438 | 556 | 153 | 2118 | 166 | 0 | 14 | 783 | 2422 | 240 | 7035 |
| GBPJPY\|tokyo | 12521 | 1434 | 0.32059 | 0.53696 | 699 | 622 | 113 | 2474 | 294 | 0 | 0 | 1007 | 2853 | 342 | 8319 |
| GBPUSD\|london | 20940 | 2757 | 0.096189 | 0.451215 | 1107 | 1450 | 200 | 4000 | 469 | 0 | 28 | 1983 | 4716 | 555 | 13686 |
| GBPUSD\|ny | 10470 | 1033 | 0.025302 | 0.419167 | 370 | 545 | 118 | 2173 | 189 | 0 | 21 | 862 | 2330 | 224 | 7054 |
| NAS100\|london | 11444 | 1461 | 0.028941 | 0.423682 | 551 | 834 | 76 | 2574 | 545 | 0 | 31 | 768 | 3258 | 585 | 6833 |
| NAS100\|ny | 13010 | 1577 | 0.133197 | 0.464172 | 643 | 807 | 127 | 2947 | 630 | 0 | 56 | 686 | 3836 | 688 | 7800 |
| US30_cash\|london | 8189 | 781 | -0.001642 | 0.384123 | 290 | 452 | 39 | 1531 | 373 | 0 | 20 | 331 | 1957 | 417 | 5484 |
| US30_cash\|ny | 8068 | 717 | 0.061367 | 0.419805 | 285 | 399 | 33 | 1478 | 479 | 0 | 27 | 281 | 1897 | 523 | 5367 |
| USDJPY\|london | 10470 | 1209 | 0.139862 | 0.462366 | 524 | 638 | 47 | 2180 | 321 | 0 | 10 | 783 | 2599 | 338 | 6750 |
| USDJPY\|ny | 10470 | 983 | 0.182357 | 0.493388 | 421 | 478 | 84 | 2277 | 384 | 0 | 10 | 683 | 2567 | 404 | 6816 |
| USDJPY\|tokyo | 12541 | 1506 | 0.294455 | 0.530544 | 704 | 683 | 119 | 2414 | 420 | 0 | 12 | 904 | 3012 | 436 | 8189 |
| XAGUSD\|london | 15572 | 1536 | 0.166438 | 0.468099 | 695 | 798 | 43 | 3772 | 382 | 0 | 58 | 351 | 4881 | 516 | 9824 |
| XAGUSD\|ny | 17792 | 1652 | 0.344158 | 0.540557 | 843 | 749 | 60 | 4378 | 462 | 0 | 110 | 365 | 5574 | 663 | 11190 |
| XAUUSD\|london | 15288 | 1862 | 0.062263 | 0.436627 | 671 | 984 | 207 | 3641 | 595 | 0 | 28 | 482 | 4978 | 666 | 9162 |
| XAUUSD\|ny | 17472 | 1851 | 0.1195 | 0.458131 | 753 | 950 | 148 | 4068 | 674 | 0 | 86 | 458 | 5421 | 800 | 10793 |

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
| USDJPY | SETUP_POI_ALREADY_MITIGATED | 2049 |
| GBPJPY | SETUP_POI_ALREADY_MITIGATED | 2047 |
| GBPUSD | SETUP_POI_ALREADY_MITIGATED | 1864 |
| XAGUSD | SETUP_HTF_CONFLICT | 1692 |
| GBPJPY | SUCCESS_TP_FIRST | 1692 |
| GBPUSD | FAIL_STOP_FIRST | 1691 |
| USDJPY | SUCCESS_TP_FIRST | 1649 |
| USDJPY | SETUP_HTF_CONFLICT | 1646 |

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
| tokyo | SETUP_HTF_NO_DIRECTION | 5729 |
| london | SETUP_POI_ALREADY_MITIGATED | 5027 |
| london | SETUP_HTF_CONFLICT | 4976 |
| tokyo | FAIL_NO_FILL | 4888 |
| ny | SETUP_HTF_CONFLICT | 4818 |
| london | FAIL_STOP_FIRST | 4706 |
| ny | SETUP_POI_ALREADY_MITIGATED | 4507 |
| london | SUCCESS_TP_FIRST | 4393 |
| ny | SUCCESS_TP_FIRST | 3753 |
| ny | FAIL_STOP_FIRST | 3616 |
| ny | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 2984 |
| london | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 2926 |
| tokyo | SETUP_HTF_CONFLICT | 1583 |
| tokyo | SETUP_POI_ALREADY_MITIGATED | 1514 |
| tokyo | SUCCESS_TP_FIRST | 1403 |
| tokyo | FAIL_STOP_FIRST | 1134 |
| ny | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| london | FAIL_IMMEDIATE_STOP_AFTER_FILL | 1021 |
| ny | FAIL_IMMEDIATE_STOP_AFTER_FILL | 868 |
| tokyo | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 714 |
| ny | MIXED_TIMEOUT_POSITIVE | 487 |
| london | MIXED_TIMEOUT_POSITIVE | 458 |
| ny | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 324 |

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
| 2025 | SETUP_HTF_CONFLICT | 3207 |
| 2023 | SETUP_POI_ALREADY_MITIGATED | 2960 |
| 2025 | FAIL_STOP_FIRST | 2840 |
| 2024 | SETUP_POI_ALREADY_MITIGATED | 2833 |
| 2023 | SETUP_HTF_CONFLICT | 2808 |
| 2025 | SETUP_POI_ALREADY_MITIGATED | 2716 |
| 2024 | SETUP_HTF_CONFLICT | 2528 |
| 2025 | SUCCESS_TP_FIRST | 2435 |
| 2023 | SUCCESS_TP_FIRST | 2371 |
| 2024 | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 2320 |
| 2023 | FAIL_STOP_FIRST | 2192 |
| 2024 | SUCCESS_TP_FIRST | 2177 |
| 2023 | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 2117 |
| 2024 | FAIL_STOP_FIRST | 1998 |
| 2022 | SETUP_HTF_CONFLICT | 1730 |

### Framework

| framework | truth_failure_bucket | rows |
| --- | --- | --- |
| ob_retest | SETUP_MISSING_OR_LOW_QUALITY_POI | 62273 |
| ob_retest | SETUP_HTF_NO_DIRECTION | 45457 |
| ob_retest | FAIL_NO_FILL | 44098 |
| ob_retest | SETUP_HTF_CONFLICT | 11377 |
| ob_retest | SETUP_POI_ALREADY_MITIGATED | 11048 |
| ob_retest | SUCCESS_TP_FIRST | 9549 |
| ob_retest | FAIL_STOP_FIRST | 9456 |
| ob_retest | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 6624 |
| ob_retest | FAIL_IMMEDIATE_STOP_AFTER_FILL | 2060 |
| ob_retest | MIXED_TIMEOUT_POSITIVE | 1111 |
| ob_retest | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| ob_retest | FAIL_TIMEOUT_NEGATIVE | 534 |
| ob_retest | DATA_LOWER_TF_GAP_BEFORE_RESOLUTION | 518 |

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
| bearish\|D1 | FAIL_NO_FILL | 4345 |
| bullish\|D1 | SETUP_POI_ALREADY_MITIGATED | 4070 |
| bullish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 3573 |
| bullish\|H4+H1_consensus | SUCCESS_TP_FIRST | 3562 |
| bullish\|H4+H1_consensus | FAIL_STOP_FIRST | 3339 |
| bullish\|H4+H1_consensus | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 2998 |
| bullish\|D1 | SUCCESS_TP_FIRST | 2615 |
| bullish\|D1 | FAIL_STOP_FIRST | 2397 |
| bearish\|H4+H1_consensus | FAIL_STOP_FIRST | 1844 |
| bullish\|D1 | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 1723 |
| bearish\|H4+H1_consensus | SUCCESS_TP_FIRST | 1592 |
| bearish\|D1 | FAIL_STOP_FIRST | 1356 |
| bearish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 1335 |
| bearish\|D1 | SETUP_POI_ALREADY_MITIGATED | 1310 |
| bearish\|D1 | SUCCESS_TP_FIRST | 1234 |
| none\|none | SETUP_SKIP_FIRST_NY_CANDLE | 1092 |
| bearish\|H4+H1_consensus | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 1004 |
| bullish\|H4+H1_consensus | SETUP_MISSING_OR_LOW_QUALITY_POI | 955 |
| bullish\|H4+H1_consensus | FAIL_IMMEDIATE_STOP_AFTER_FILL | 844 |
| bearish\|D1 | AMBIGUOUS_FILL_AND_EXIT_SAME_BAR | 648 |
| bearish\|H4+H1_consensus | FAIL_IMMEDIATE_STOP_AFTER_FILL | 540 |

## Synthesis

- Classified 205,197 opportunity rows with 205,197 unique keys and 0 AI calls.
- The truth layer separates setup rejects, no-fill outcomes, resolved TP/SL paths, same-bar ambiguity, lower-timeframe gaps, and incomplete lower-timeframe horizons before any parameter sweep.
- Core truth outcomes: TP=9,549, SL=11,516, TIMEOUT=1,645, NO_ENTRY=44,098, SAME_BAR=6,624.
- Selected truth source counts: M1=1,990, M15=60,743, M5=11,217, NONE=131,247.
- Confidence mix: HIGH=11,598, LOW=7,685, MEDIUM=54,667, NONE=131,247. Low/none-confidence rows should be excluded or sensitivity-tested before optimization.
- This report is a label-quality audit only. It does not justify live trading changes, prompt changes, or buffer/offset tuning by itself.
