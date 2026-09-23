# Phase 3 Historical Opportunity Synthesis

**Created UTC:** 2026-05-01T04:51:02.605853+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z.jsonl`
**Rows scanned:** 205197
**Would send AI:** 135062 (65.82%)

## Interpretation Boundary

- This is a research synthesis over deterministic pre-AI opportunity rows, not a paid AI replay.
- `WOULD_SEND_AI` means deterministic pre-AI gates pass; it is not an AI CANDIDATE, L2 pass, or trade.
- Mechanical R is diagnostic OB-retest behavior and is not a substitute for production-faithful AI outcome data.
- External feature tables are exploratory screens; they are not DSR/PBO-cleared alpha claims.

## Data Integrity

| rows | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum |
| --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 |

## Pre-AI Gate Shape

| pre_ai_gate_reason | rows |
| --- | --- |
| passed_deterministic_pre_ai_gates | 135062 |
| L1_no_direction_d1_transitional_h4_transitional | 43194 |
| no_bullish_pois_for_ob_retest+fvg_fill+breaker_re_entry | 6832 |
| L2_h4_conflict_bearish_vs_d1_bullish | 6558 |
| no_bearish_pois_for_ob_retest+fvg_fill+breaker_re_entry | 5377 |
| L2_h4_conflict_bullish_vs_d1_bearish | 4819 |
| L1_no_direction_d1_insufficient_data_h4_transitional | 2171 |
| skip_first_ny_candle | 1092 |
| L1_no_direction_d1_insufficient_data_h4_insufficient_data | 92 |

## Symbol Diagnostics

| symbol | rows | would_send_ai | would_send_ai_rate | complete_rate | mechanical_realized_n | mechanical_mean_r_realized | mechanical_win_rate_realized | m15_tp | m15_sl | m15_timeout | m15_same_bar | m15_no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 33471 | 21005 | 0.627558 | 0.993965 | 3597 | 0.250274 | 0.511259 | 1618 | 1639 | 340 | 910 | 6665 |
| GBPUSD | 31410 | 21540 | 0.685769 | 0.994269 | 3583 | 0.104194 | 0.454089 | 1427 | 1838 | 318 | 914 | 6173 |
| NAS100 | 24454 | 17743 | 0.725566 | 0.991004 | 2644 | 0.063856 | 0.438729 | 1003 | 1438 | 203 | 1656 | 5521 |
| US30_cash | 16257 | 10839 | 0.666728 | 0.991573 | 1346 | 0.103802 | 0.430163 | 553 | 721 | 72 | 1051 | 3009 |
| USDJPY | 33481 | 22877 | 0.683283 | 0.993907 | 3509 | 0.233239 | 0.507267 | 1586 | 1673 | 250 | 1346 | 6871 |
| XAGUSD | 33364 | 20322 | 0.6091 | 0.976622 | 3049 | 0.278189 | 0.513611 | 1492 | 1454 | 103 | 1151 | 8150 |
| XAUUSD | 32760 | 20736 | 0.632967 | 0.994078 | 3438 | 0.11842 | 0.459279 | 1342 | 1741 | 355 | 1658 | 7709 |

## Year Diagnostics

| year | rows | would_send_ai | would_send_ai_rate | complete_rate | mechanical_realized_n | mechanical_mean_r_realized | mechanical_win_rate_realized | m15_tp | m15_sl | m15_timeout | m15_same_bar | m15_no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 32814 | 20419 | 0.622265 | 0.94158 | 3544 | 0.179921 | 0.479966 | 1549 | 1760 | 235 | 1105 | 6788 |
| 2023 | 49858 | 34280 | 0.687553 | 1.0 | 5579 | 0.180134 | 0.483599 | 2371 | 2745 | 463 | 2117 | 11158 |
| 2024 | 52578 | 34693 | 0.659839 | 1.0 | 5250 | 0.137895 | 0.464762 | 2146 | 2671 | 433 | 2419 | 10837 |
| 2025 | 52691 | 33893 | 0.643241 | 1.0 | 5096 | 0.141936 | 0.461538 | 2132 | 2622 | 342 | 2135 | 11726 |
| 2026 | 17256 | 11777 | 0.682487 | 1.0 | 1697 | 0.333541 | 0.553329 | 823 | 706 | 168 | 910 | 3589 |

## Session Diagnostics

| session | rows | would_send_ai | would_send_ai_rate | complete_rate | mechanical_realized_n | mechanical_mean_r_realized | mechanical_win_rate_realized | m15_tp | m15_sl | m15_timeout | m15_same_bar | m15_no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| london | 92373 | 61682 | 0.667749 | 0.990354 | 10056 | 0.136111 | 0.461714 | 4185 | 5181 | 690 | 3862 | 19771 |
| ny | 87762 | 56839 | 0.647649 | 0.990087 | 8315 | 0.162834 | 0.476729 | 3479 | 4117 | 719 | 3953 | 19439 |
| tokyo | 25062 | 16541 | 0.660003 | 0.993775 | 2795 | 0.333874 | 0.544902 | 1357 | 1206 | 232 | 871 | 4888 |

## Symbol x Session Diagnostics

| symbol_session | rows | would_send_ai | would_send_ai_rate | complete_rate | mechanical_realized_n | mechanical_mean_r_realized | mechanical_win_rate_realized | m15_tp | m15_sl | m15_timeout | m15_same_bar | m15_no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london | 10470 | 6641 | 0.634288 | 0.994269 | 1141 | 0.25042 | 0.498685 | 527 | 536 | 78 | 311 | 2073 |
| GBPJPY\|ny | 10480 | 6350 | 0.605916 | 0.993321 | 1082 | 0.147671 | 0.486137 | 418 | 515 | 149 | 245 | 2118 |
| GBPJPY\|tokyo | 12521 | 8014 | 0.640045 | 0.99425 | 1374 | 0.330951 | 0.541485 | 673 | 588 | 113 | 354 | 2474 |
| GBPUSD\|london | 20940 | 14424 | 0.688825 | 0.994269 | 2582 | 0.12885 | 0.465143 | 1064 | 1318 | 200 | 672 | 4000 |
| GBPUSD\|ny | 10470 | 7116 | 0.679656 | 0.994269 | 1001 | 0.040596 | 0.425574 | 363 | 520 | 118 | 242 | 2173 |
| NAS100\|london | 11444 | 8393 | 0.733397 | 0.990563 | 1292 | 0.028083 | 0.424923 | 481 | 735 | 76 | 745 | 2574 |
| NAS100\|ny | 13010 | 9350 | 0.718678 | 0.991391 | 1352 | 0.098041 | 0.451923 | 522 | 703 | 127 | 911 | 2947 |
| US30_cash\|london | 8189 | 5485 | 0.669801 | 0.990109 | 711 | 0.086101 | 0.417722 | 287 | 385 | 39 | 463 | 1531 |
| US30_cash\|ny | 8068 | 5354 | 0.663609 | 0.993059 | 635 | 0.123622 | 0.444094 | 266 | 336 | 33 | 588 | 1478 |
| USDJPY\|london | 10470 | 7224 | 0.689971 | 0.994269 | 1139 | 0.139798 | 0.464442 | 494 | 598 | 47 | 401 | 2180 |
| USDJPY\|ny | 10470 | 7126 | 0.680611 | 0.994269 | 949 | 0.190471 | 0.497366 | 408 | 457 | 84 | 428 | 2277 |
| USDJPY\|tokyo | 12541 | 8527 | 0.67993 | 0.993302 | 1421 | 0.336699 | 0.548205 | 684 | 618 | 119 | 517 | 2414 |
| XAGUSD\|london | 15572 | 9470 | 0.608143 | 0.976625 | 1454 | 0.202991 | 0.482806 | 678 | 733 | 43 | 522 | 3772 |
| XAGUSD\|ny | 17792 | 10852 | 0.609937 | 0.976619 | 1595 | 0.34674 | 0.541693 | 814 | 721 | 60 | 629 | 4378 |
| XAUUSD\|london | 15288 | 10045 | 0.657051 | 0.99359 | 1737 | 0.114239 | 0.458261 | 654 | 876 | 207 | 748 | 3641 |
| XAUUSD\|ny | 17472 | 10691 | 0.611893 | 0.994505 | 1701 | 0.122689 | 0.460317 | 688 | 865 | 148 | 910 | 4068 |

## Symbol x Year Diagnostics

| symbol_year | rows | would_send_ai | would_send_ai_rate | complete_rate | mechanical_realized_n | mechanical_mean_r_realized | mechanical_win_rate_realized | m15_tp | m15_sl | m15_timeout | m15_same_bar | m15_no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|2022 | 5946 | 3455 | 0.581063 | 0.966028 | 654 | -0.082385 | 0.373089 | 214 | 380 | 60 | 130 | 1127 |
| GBPJPY\|2023 | 8288 | 5374 | 0.648407 | 1.0 | 851 | 0.367229 | 0.558167 | 428 | 352 | 71 | 131 | 1425 |
| GBPJPY\|2024 | 8248 | 5570 | 0.675315 | 1.0 | 1054 | 0.353803 | 0.555977 | 519 | 445 | 90 | 296 | 2102 |
| GBPJPY\|2025 | 8287 | 4949 | 0.5972 | 1.0 | 843 | 0.183576 | 0.479241 | 343 | 399 | 101 | 191 | 1621 |
| GBPJPY\|2026 | 2702 | 1657 | 0.613249 | 1.0 | 195 | 0.584316 | 0.666667 | 114 | 63 | 18 | 162 | 390 |
| GBPUSD\|2022 | 5576 | 3788 | 0.67934 | 0.967719 | 671 | 0.116583 | 0.448584 | 279 | 359 | 33 | 110 | 1135 |
| GBPUSD\|2023 | 7770 | 5390 | 0.693694 | 1.0 | 992 | 0.122016 | 0.467742 | 392 | 503 | 97 | 190 | 1351 |
| GBPUSD\|2024 | 7744 | 5075 | 0.655346 | 1.0 | 806 | 0.24722 | 0.523573 | 354 | 355 | 97 | 309 | 1410 |
| GBPUSD\|2025 | 7770 | 5500 | 0.707851 | 1.0 | 856 | -0.00016 | 0.399533 | 332 | 497 | 27 | 201 | 1736 |
| GBPUSD\|2026 | 2550 | 1787 | 0.700784 | 1.0 | 258 | -0.097134 | 0.379845 | 70 | 124 | 64 | 104 | 541 |
| NAS100\|2022 | 404 | 141 | 0.34901 | 0.455446 | 19 | -0.736842 | 0.105263 | 2 | 17 | 0 | 30 | 6 |
| NAS100\|2023 | 6067 | 4673 | 0.770232 | 1.0 | 708 | 0.13714 | 0.471751 | 285 | 362 | 61 | 443 | 1417 |
| NAS100\|2024 | 7714 | 5315 | 0.689007 | 1.0 | 688 | 0.104243 | 0.454942 | 274 | 360 | 54 | 399 | 1524 |
| NAS100\|2025 | 7721 | 5792 | 0.750162 | 1.0 | 950 | -0.013015 | 0.403158 | 332 | 556 | 62 | 678 | 2109 |
| NAS100\|2026 | 2548 | 1822 | 0.715071 | 1.0 | 279 | 0.094566 | 0.458781 | 110 | 143 | 26 | 106 | 465 |
| US30_cash\|2022 | 252 | 182 | 0.722222 | 0.456349 | 12 | -0.166667 | 0.333333 | 4 | 8 | 0 | 42 | 35 |
| US30_cash\|2023 | 4020 | 2818 | 0.700995 | 1.0 | 428 | 0.151005 | 0.462617 | 184 | 221 | 23 | 280 | 818 |
| US30_cash\|2024 | 5140 | 3597 | 0.699805 | 1.0 | 429 | 0.015982 | 0.375291 | 158 | 248 | 23 | 388 | 923 |
| US30_cash\|2025 | 5145 | 3251 | 0.631876 | 1.0 | 359 | 0.090192 | 0.426184 | 148 | 191 | 20 | 253 | 916 |
| US30_cash\|2026 | 1700 | 991 | 0.582941 | 1.0 | 118 | 0.320783 | 0.533898 | 59 | 53 | 6 | 88 | 317 |
| USDJPY\|2022 | 5936 | 3844 | 0.647574 | 0.965633 | 602 | 0.351305 | 0.553156 | 302 | 265 | 35 | 223 | 951 |
| USDJPY\|2023 | 8293 | 6342 | 0.764741 | 1.0 | 1040 | 0.190101 | 0.495192 | 444 | 499 | 97 | 410 | 1985 |
| USDJPY\|2024 | 8248 | 5774 | 0.700048 | 1.0 | 901 | 0.17696 | 0.482797 | 394 | 450 | 57 | 367 | 2163 |
| USDJPY\|2025 | 8288 | 4895 | 0.590613 | 1.0 | 635 | 0.236679 | 0.502362 | 287 | 310 | 38 | 268 | 1282 |
| USDJPY\|2026 | 2716 | 2022 | 0.744477 | 1.0 | 331 | 0.300646 | 0.537764 | 159 | 149 | 23 | 78 | 490 |
| XAGUSD\|2022 | 7680 | 4592 | 0.597917 | 0.898438 | 819 | 0.330233 | 0.538462 | 416 | 357 | 46 | 264 | 1806 |
| XAGUSD\|2023 | 7710 | 4641 | 0.601946 | 1.0 | 698 | 0.319159 | 0.524355 | 345 | 331 | 22 | 261 | 2143 |
| XAGUSD\|2024 | 7714 | 4731 | 0.6133 | 1.0 | 623 | 0.019726 | 0.4061 | 245 | 364 | 14 | 263 | 1284 |
| XAGUSD\|2025 | 7740 | 4536 | 0.586047 | 1.0 | 620 | 0.332793 | 0.540323 | 317 | 284 | 19 | 178 | 2084 |
| XAGUSD\|2026 | 2520 | 1822 | 0.723016 | 1.0 | 289 | 0.47178 | 0.591696 | 169 | 118 | 2 | 185 | 833 |
| XAUUSD\|2022 | 7020 | 4417 | 0.629202 | 0.972365 | 767 | 0.192107 | 0.490222 | 332 | 374 | 61 | 306 | 1728 |
| XAUUSD\|2023 | 7710 | 5042 | 0.653956 | 1.0 | 862 | -0.012514 | 0.401392 | 293 | 477 | 92 | 402 | 2019 |
| XAUUSD\|2024 | 7770 | 4631 | 0.59601 | 1.0 | 749 | -0.13154 | 0.360481 | 202 | 449 | 98 | 397 | 1431 |
| XAUUSD\|2025 | 7740 | 4970 | 0.642119 | 1.0 | 833 | 0.230551 | 0.4994 | 373 | 385 | 75 | 366 | 1978 |
| XAUUSD\|2026 | 2520 | 1676 | 0.665079 | 1.0 | 227 | 0.77993 | 0.753304 | 142 | 56 | 29 | 187 | 553 |

## HTF Sensitivity

| rows | would_send_ai | would_send_ai_rate | htf_policy | pre_screen_reject | pre_ai_poi_reject | skip_first_ny |
| --- | --- | --- | --- | --- | --- | --- |
| 205197 | 135062 | 0.6582 | partial_htf | 56834 | 12209 | 1092 |
| 205197 | 133853 | 0.6523 | closed_only | 57699 | 12553 | 1092 |

## Lower-Timeframe Mechanical Refinement

### M1

| timeframe | attempted | local_coverage | local_coverage_rate | resolved_r_n | mean_r_realized |
| --- | --- | --- | --- | --- | --- |
| M1 | 73950 | 5258 | 0.071102 | 2057 | 0.120164 |

| refined_outcome | rows |
| --- | --- |
| NO_ENTRY | 3029 |
| NO_FULL_HORIZON | 20 |
| NO_LOCAL_OHLCV | 68692 |
| SAME_BAR | 152 |
| SL | 1080 |
| TIMEOUT | 108 |
| TP | 869 |

M15 outcome -> refined outcome:

| m15_outcome | refined_outcome | rows |
| --- | --- | --- |
| NO_ENTRY | NO_ENTRY | 3029 |
| NO_ENTRY | NO_FULL_HORIZON | 20 |
| NO_ENTRY | NO_LOCAL_OHLCV | 41047 |
| NO_ENTRY | TIMEOUT | 2 |
| SAME_BAR | NO_LOCAL_OHLCV | 7886 |
| SAME_BAR | SAME_BAR | 152 |
| SAME_BAR | SL | 466 |
| SAME_BAR | TIMEOUT | 9 |
| SAME_BAR | TP | 173 |
| SL | NO_LOCAL_OHLCV | 9877 |
| SL | SL | 612 |
| SL | TP | 15 |
| TIMEOUT | NO_LOCAL_OHLCV | 1542 |
| TIMEOUT | SL | 2 |
| TIMEOUT | TIMEOUT | 97 |
| TP | NO_LOCAL_OHLCV | 8340 |
| TP | TP | 681 |

Symbol -> refined outcome:

| symbol | refined_outcome | rows |
| --- | --- | --- |
| GBPJPY | NO_ENTRY | 305 |
| GBPJPY | NO_LOCAL_OHLCV | 10571 |
| GBPJPY | SAME_BAR | 28 |
| GBPJPY | SL | 85 |
| GBPJPY | TIMEOUT | 18 |
| GBPJPY | TP | 165 |
| GBPUSD | NO_ENTRY | 503 |
| GBPUSD | NO_LOCAL_OHLCV | 9861 |
| GBPUSD | SAME_BAR | 11 |
| GBPUSD | SL | 163 |
| GBPUSD | TIMEOUT | 34 |
| GBPUSD | TP | 98 |
| NAS100 | NO_ENTRY | 439 |
| NAS100 | NO_LOCAL_OHLCV | 9004 |
| NAS100 | SAME_BAR | 14 |
| NAS100 | SL | 191 |
| NAS100 | TIMEOUT | 27 |
| NAS100 | TP | 146 |
| US30_cash | NO_ENTRY | 302 |
| US30_cash | NO_FULL_HORIZON | 10 |
| US30_cash | NO_LOCAL_OHLCV | 4911 |
| US30_cash | SAME_BAR | 30 |
| US30_cash | SL | 84 |
| US30_cash | TIMEOUT | 7 |
| US30_cash | TP | 62 |
| USDJPY | NO_ENTRY | 451 |
| USDJPY | NO_FULL_HORIZON | 10 |
| USDJPY | NO_LOCAL_OHLCV | 10926 |
| USDJPY | SAME_BAR | 7 |
| USDJPY | SL | 175 |
| USDJPY | TIMEOUT | 13 |
| USDJPY | TP | 144 |
| XAGUSD | NO_ENTRY | 618 |
| XAGUSD | NO_LOCAL_OHLCV | 11342 |
| XAGUSD | SAME_BAR | 3 |
| XAGUSD | SL | 249 |
| XAGUSD | TIMEOUT | 1 |
| XAGUSD | TP | 137 |
| XAUUSD | NO_ENTRY | 411 |
| XAUUSD | NO_LOCAL_OHLCV | 12077 |
| XAUUSD | SAME_BAR | 59 |
| XAUUSD | SL | 133 |
| XAUUSD | TIMEOUT | 8 |
| XAUUSD | TP | 117 |

### M5

| timeframe | attempted | local_coverage | local_coverage_rate | resolved_r_n | mean_r_realized |
| --- | --- | --- | --- | --- | --- |
| M5 | 73950 | 26015 | 0.351792 | 8588 | 0.122421 |

| refined_outcome | rows |
| --- | --- |
| NO_ENTRY | 15783 |
| NO_FULL_HORIZON | 20 |
| NO_LOCAL_OHLCV | 47935 |
| SAME_BAR | 1624 |
| SL | 4484 |
| TIMEOUT | 545 |
| TP | 3559 |

M15 outcome -> refined outcome:

| m15_outcome | refined_outcome | rows |
| --- | --- | --- |
| NO_ENTRY | NO_ENTRY | 15783 |
| NO_ENTRY | NO_FULL_HORIZON | 20 |
| NO_ENTRY | NO_LOCAL_OHLCV | 28290 |
| NO_ENTRY | SAME_BAR | 2 |
| NO_ENTRY | TIMEOUT | 2 |
| NO_ENTRY | TP | 1 |
| SAME_BAR | NO_LOCAL_OHLCV | 5533 |
| SAME_BAR | SAME_BAR | 1622 |
| SAME_BAR | SL | 982 |
| SAME_BAR | TIMEOUT | 21 |
| SAME_BAR | TP | 528 |
| SL | NO_LOCAL_OHLCV | 6987 |
| SL | SL | 3502 |
| SL | TP | 15 |
| TIMEOUT | NO_LOCAL_OHLCV | 1119 |
| TIMEOUT | TIMEOUT | 522 |
| TP | NO_LOCAL_OHLCV | 6006 |
| TP | TP | 3015 |

Symbol -> refined outcome:

| symbol | refined_outcome | rows |
| --- | --- | --- |
| GBPJPY | NO_ENTRY | 2023 |
| GBPJPY | NO_LOCAL_OHLCV | 7724 |
| GBPJPY | SAME_BAR | 194 |
| GBPJPY | SL | 573 |
| GBPJPY | TIMEOUT | 124 |
| GBPJPY | TP | 534 |
| GBPUSD | NO_ENTRY | 2288 |
| GBPUSD | NO_LOCAL_OHLCV | 6947 |
| GBPUSD | SAME_BAR | 154 |
| GBPUSD | SL | 763 |
| GBPUSD | TIMEOUT | 93 |
| GBPUSD | TP | 425 |
| NAS100 | NO_ENTRY | 2759 |
| NAS100 | NO_LOCAL_OHLCV | 4955 |
| NAS100 | SAME_BAR | 426 |
| NAS100 | SL | 938 |
| NAS100 | TIMEOUT | 89 |
| NAS100 | TP | 654 |
| US30_cash | NO_ENTRY | 1380 |
| US30_cash | NO_FULL_HORIZON | 10 |
| US30_cash | NO_LOCAL_OHLCV | 3130 |
| US30_cash | SAME_BAR | 189 |
| US30_cash | SL | 428 |
| US30_cash | TIMEOUT | 30 |
| US30_cash | TP | 239 |
| USDJPY | NO_ENTRY | 1794 |
| USDJPY | NO_FULL_HORIZON | 10 |
| USDJPY | NO_LOCAL_OHLCV | 8576 |
| USDJPY | SAME_BAR | 153 |
| USDJPY | SL | 588 |
| USDJPY | TIMEOUT | 61 |
| USDJPY | TP | 544 |
| XAGUSD | NO_ENTRY | 2992 |
| XAGUSD | NO_LOCAL_OHLCV | 8051 |
| XAGUSD | SAME_BAR | 180 |
| XAGUSD | SL | 539 |
| XAGUSD | TIMEOUT | 23 |
| XAGUSD | TP | 565 |
| XAUUSD | NO_ENTRY | 2547 |
| XAUUSD | NO_LOCAL_OHLCV | 8552 |
| XAUUSD | SAME_BAR | 328 |
| XAUUSD | SL | 655 |
| XAUUSD | TIMEOUT | 125 |
| XAUUSD | TP | 598 |

## External Feature Coverage

### All Opportunity Rows

| source | available_rows | missing_rows | available_rate |
| --- | --- | --- | --- |
| cftc_cot | 28800 | 176397 | 0.140353 |
| flashalpha_gex | 0 | 205197 | 0.0 |
| fred | 205167 | 30 | 0.999854 |
| lbma_calendar | 9217 | 195980 | 0.044918 |
| wgc | 0 | 205197 | 0.0 |

### `WOULD_SEND_AI` Rows

| source | available_rows | missing_rows | available_rate |
| --- | --- | --- | --- |
| cftc_cot | 18416 | 116646 | 0.136352 |
| flashalpha_gex | 0 | 135062 | 0.0 |
| fred | 135062 | 0 | 1.0 |
| lbma_calendar | 6326 | 128736 | 0.046838 |
| wgc | 0 | 135062 | 0.0 |

## Exploratory External Feature Separation

| feature | quintile | n | min | max | mean_r | q5_minus_q1_mean_r |
| --- | --- | --- | --- | --- | --- | --- |
| lbma_calendar__minutes_to_next_fix | 1 | 204 | 15.0 | 90.0 | 0.3635 | 0.3777 |
| lbma_calendar__minutes_to_next_fix | 2 | 205 | 90.0 | 210.0 | 0.4476 | 0.3777 |
| lbma_calendar__minutes_to_next_fix | 3 | 205 | 210.0 | 1125.0 | 0.514 | 0.3777 |
| lbma_calendar__minutes_to_next_fix | 4 | 205 | 1125.0 | 1260.0 | 0.3618 | 0.3777 |
| lbma_calendar__minutes_to_next_fix | 5 | 205 | 1260.0 | 10080.0 | 0.7412 | 0.3777 |
| cftc_cot__disagg_combined__managed_money_long | 1 | 603 | 78540.0 | 124021.0 | 0.2048 | -0.2409 |
| cftc_cot__disagg_combined__managed_money_long | 2 | 603 | 124021.0 | 146318.0 | 0.2139 | -0.2409 |
| cftc_cot__disagg_combined__managed_money_long | 3 | 604 | 146318.0 | 179464.0 | -0.0893 | -0.2409 |
| cftc_cot__disagg_combined__managed_money_long | 4 | 603 | 179464.0 | 210131.0 | 0.3025 | -0.2409 |
| cftc_cot__disagg_combined__managed_money_long | 5 | 604 | 210131.0 | 282912.0 | -0.0361 | -0.2409 |
| lbma_calendar__minutes_since_previous_fix | 1 | 196 | 0.0 | 90.0 | 0.6092 | -0.1747 |
| lbma_calendar__minutes_since_previous_fix | 2 | 196 | 90.0 | 210.0 | 0.3104 | -0.1747 |
| lbma_calendar__minutes_since_previous_fix | 3 | 196 | 210.0 | 330.0 | 0.4571 | -0.1747 |
| lbma_calendar__minutes_since_previous_fix | 4 | 196 | 330.0 | 1215.0 | 0.4363 | -0.1747 |
| lbma_calendar__minutes_since_previous_fix | 5 | 197 | 1215.0 | 4125.0 | 0.4345 | -0.1747 |
| cftc_cot__disagg_combined__managed_money_net | 1 | 603 | -41300.0 | 71976.0 | 0.2059 | -0.1385 |
| cftc_cot__disagg_combined__managed_money_net | 2 | 603 | 71976.0 | 107976.0 | 0.0849 | -0.1385 |
| cftc_cot__disagg_combined__managed_money_net | 3 | 604 | 107976.0 | 146626.0 | 0.0086 | -0.1385 |
| cftc_cot__disagg_combined__managed_money_net | 4 | 603 | 146626.0 | 190324.0 | 0.2286 | -0.1385 |
| cftc_cot__disagg_combined__managed_money_net | 5 | 604 | 190324.0 | 254841.0 | 0.0674 | -0.1385 |

## Synthesis

- The historical pre-AI population is broad: 135,062/205,197 rows (65.82%) pass deterministic gates. That is enough substrate for downstream selection research, but it is not a trade signal.
- Data-integrity checks are clean for this artifact: 205,197 unique keys, 0 duplicates, 0 AI-attempted rows, and 0 summed AI calls.
- M15 mechanical OB-retest diagnostics remain positive but ambiguous: 21,166 resolved outcomes average +0.1727R, while 8,686 same-bar and 44,098 no-entry rows can distort fill/exit interpretation without lower-timeframe confirmation.
- HTF replay sensitivity is small at the population level: closed-only HTF context changes `WOULD_SEND_AI` by -1,209 rows (-0.59%). Exact row-level studies should still pin one HTF policy because individual gates can flip near boundaries.
- M5 refinement has limited local coverage (26,015/73,950, 35.18%) and 8,588 resolved R outcomes averaging +0.1224R. The positive sign is useful as a diagnostic, but historical lower-timeframe depth is not yet sufficient for threshold or pip-offset optimization.
- M1 refinement has limited local coverage (5,258/73,950, 7.11%) and 2,057 resolved R outcomes averaging +0.1202R. The positive sign is useful as a diagnostic, but historical lower-timeframe depth is not yet sufficient for threshold or pip-offset optimization.
- External-feed interpretation is currently coverage-limited: FRED covers 100.00% of `WOULD_SEND_AI` rows, CFTC 13.64%, LBMA 4.68%, FlashAlpha 0.00%, and WGC 0.00%. The current substrate can screen macro/regime features, but it cannot yet prove multi-feed confluence.
- The strongest next hypotheses are session/symbol/year conditioning, lower-timeframe entry realization, and DSR-controlled external-feature screens. Tokyo strength and 2026 strength should be treated as composition-confounded until split by symbol and deeper intraday coverage.
- Parameter sweeps on buffers, offsets, or percentage levels should wait until the measurement layer is pinned: fixed HTF policy, enough M1/M5 history, explicit same-bar handling, and DSR/PBO accounting for all tested variants.
