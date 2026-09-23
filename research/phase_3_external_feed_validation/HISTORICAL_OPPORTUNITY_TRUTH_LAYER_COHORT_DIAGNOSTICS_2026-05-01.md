# Phase 3 Historical Opportunity Truth-Layer Cohort Diagnostics

**Created UTC:** 2026-05-01T07:03:18.426539+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Rows scanned:** 205197
**Path metrics:** `True`

## Interpretation Boundary

- Research/tooling only; no live trading logic, prompt, or config behavior is changed.
- No AI/API calls are made. `ai_attempted_rows` and `ai_call_count_sum` must stay zero.
- Rankings are diagnostic triage, not alpha validation or promotion evidence.
- No looser-entry or buffer simulation is included; that would be parameter optimization.
- Low-confidence, same-bar, and gappy cohorts should be excluded or sensitivity-tested before any sweep.

## Data Integrity

| rows | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum |
| --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 |

## Outcome Shape

### Truth Outcomes

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

### Failure And Success Buckets

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

### Confidence And Source

| truth_confidence | rows |
| --- | --- |
| NONE | 131247 |
| HIGH | 37713 |
| MEDIUM | 32888 |
| LOW | 3349 |

| truth_source_timeframe | rows |
| --- | --- |
| NONE | 131247 |
| M15 | 33431 |
| M1 | 30421 |
| M5 | 10098 |

## Candidate Cohort Triage

### High Confidence Only

| symbol_session_regime | confidence_scope | setup_rows | confidence_rows | resolved_r_n | mean_r | win_rate | same_bar | lower_tf_gappy | no_entry_rate_setup | immediate_stop_rate_sl | ambiguity_rate_setup | diagnostic_priority_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|tokyo\|bullish\|D1 | HIGH | 1192 | 956 | 430 | 0.493024 | 0.609302 | 52 | 0 | 0.583054 | 0.031447 | 0.087248 | 0.82309 |
| XAUUSD\|ny\|bullish\|D1 | HIGH | 1690 | 311 | 311 | 0.570303 | 0.62701 | 26 | 61 | 0.65858 | 0.043956 | 0.120118 | 0.794388 |
| USDJPY\|tokyo\|bearish\|D1 | HIGH | 591 | 508 | 212 | 0.630181 | 0.65566 | 25 | 0 | 0.598985 | 0.013699 | 0.084602 | 0.754872 |
| NAS100\|ny\|bullish\|D1 | HIGH | 1989 | 631 | 631 | 0.373786 | 0.545166 | 51 | 64 | 0.524887 | 0.094972 | 0.115636 | 0.708872 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | HIGH | 1237 | 320 | 320 | 0.508648 | 0.590625 | 69 | 37 | 0.6346 | 0.265734 | 0.183508 | 0.619897 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | HIGH | 3125 | 509 | 509 | 0.350688 | 0.540275 | 52 | 166 | 0.69344 | 0.069841 | 0.1632 | 0.569511 |
| GBPJPY\|london\|bullish\|H4+H1_consensus | HIGH | 1444 | 1292 | 530 | 0.304292 | 0.516981 | 41 | 8 | 0.592105 | 0.027132 | 0.067867 | 0.548011 |
| GBPUSD\|london\|bearish\|D1 | HIGH | 1659 | 1396 | 727 | 0.247174 | 0.503439 | 39 | 11 | 0.522001 | 0.002907 | 0.060277 | 0.526652 |
| XAGUSD\|london\|bullish\|D1 | HIGH | 1193 | 249 | 249 | 0.403878 | 0.558233 | 0 | 7 | 0.699078 | 0.124183 | 0.011735 | 0.510505 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | HIGH | 591 | 458 | 252 | 0.387224 | 0.563492 | 17 | 12 | 0.524535 | 0.0 | 0.098139 | 0.481203 |
| GBPJPY\|tokyo\|bearish\|D1 | HIGH | 349 | 293 | 155 | 0.433775 | 0.574194 | 1 | 0 | 0.544413 | 0.0 | 0.005731 | 0.469128 |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | HIGH | 1751 | 1552 | 657 | 0.228376 | 0.493151 | 71 | 0 | 0.584238 | 0.0 | 0.081097 | 0.448195 |
| USDJPY\|london\|bearish\|D1 | HIGH | 485 | 404 | 154 | 0.428571 | 0.571429 | 16 | 0 | 0.639175 | 0.0 | 0.065979 | 0.431615 |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | HIGH | 1904 | 1476 | 655 | 0.206858 | 0.485496 | 105 | 0 | 0.589811 | 0.037037 | 0.110294 | 0.37673 |
| XAGUSD\|london\|bullish\|H4+H1_consensus | HIGH | 2740 | 584 | 584 | 0.202911 | 0.481164 | 37 | 80 | 0.706934 | 0.046832 | 0.108029 | 0.342443 |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | HIGH | 1681 | 285 | 285 | 0.235441 | 0.491228 | 7 | 25 | 0.630577 | 0.116608 | 0.044616 | 0.28338 |
| GBPJPY\|ny\|bullish\|H4+H1_consensus | HIGH | 1433 | 1201 | 449 | 0.176486 | 0.492205 | 34 | 10 | 0.619679 | 0.040161 | 0.068388 | 0.27166 |
| USDJPY\|london\|bearish\|H4+H1_consensus | HIGH | 551 | 425 | 181 | 0.272345 | 0.524862 | 10 | 10 | 0.635209 | 0.116279 | 0.072595 | 0.252515 |
| XAUUSD\|london\|bullish\|D1 | HIGH | 1497 | 395 | 395 | 0.18144 | 0.470886 | 14 | 23 | 0.674015 | 0.126126 | 0.077488 | 0.229379 |
| GBPJPY\|london\|bullish\|D1 | HIGH | 1040 | 792 | 318 | 0.162445 | 0.459119 | 39 | 7 | 0.609615 | 0.017857 | 0.088462 | 0.190108 |
| XAUUSD\|london\|bearish\|H4+H1_consensus | HIGH | 1274 | 388 | 388 | 0.134021 | 0.453608 | 14 | 0 | 0.61146 | 0.067925 | 0.021978 | 0.188479 |
| XAGUSD\|london\|bearish\|H4+H1_consensus | HIGH | 1416 | 482 | 482 | 0.085446 | 0.43361 | 9 | 15 | 0.558616 | 0.0 | 0.033898 | 0.132122 |
| GBPUSD\|ny\|bullish\|H4+H1_consensus | HIGH | 1108 | 880 | 264 | 0.110855 | 0.443182 | 13 | 10 | 0.701264 | 0.0 | 0.041516 | 0.124603 |
| NAS100\|london\|bullish\|H4+H1_consensus | HIGH | 1887 | 662 | 662 | 0.081095 | 0.429003 | 54 | 3 | 0.577107 | 0.093827 | 0.065183 | 0.109066 |
| GBPUSD\|london\|bullish\|H4+H1_consensus | HIGH | 2242 | 1768 | 658 | 0.060911 | 0.420973 | 45 | 20 | 0.64719 | 0.0 | 0.057984 | 0.091326 |

### High + Medium Confidence

| symbol_session_regime | confidence_scope | setup_rows | confidence_rows | resolved_r_n | mean_r | win_rate | same_bar | lower_tf_gappy | no_entry_rate_setup | immediate_stop_rate_sl | ambiguity_rate_setup | diagnostic_priority_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|ny\|bullish\|D1 | HIGH+MEDIUM | 1690 | 1574 | 490 | 0.537498 | 0.616327 | 26 | 61 | 0.65858 | 0.043956 | 0.120118 | 0.942003 |
| XAGUSD\|ny\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 3125 | 2833 | 728 | 0.424918 | 0.578297 | 52 | 166 | 0.69344 | 0.069841 | 0.1632 | 0.86912 |
| NAS100\|ny\|bullish\|D1 | HIGH+MEDIUM | 1989 | 1874 | 830 | 0.38773 | 0.563855 | 51 | 64 | 0.524887 | 0.094972 | 0.115636 | 0.858962 |
| GBPJPY\|tokyo\|bullish\|D1 | HIGH+MEDIUM | 1192 | 1140 | 445 | 0.502297 | 0.622472 | 52 | 0 | 0.583054 | 0.031447 | 0.087248 | 0.856789 |
| USDJPY\|tokyo\|bearish\|D1 | HIGH+MEDIUM | 591 | 566 | 212 | 0.630181 | 0.65566 | 25 | 0 | 0.598985 | 0.013699 | 0.084602 | 0.754872 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 1237 | 1116 | 341 | 0.489411 | 0.583578 | 69 | 37 | 0.6346 | 0.265734 | 0.183508 | 0.61312 |
| XAGUSD\|london\|bullish\|D1 | HIGH+MEDIUM | 1193 | 1186 | 352 | 0.36735 | 0.551136 | 0 | 7 | 0.699078 | 0.124183 | 0.011735 | 0.551108 |
| GBPUSD\|london\|bearish\|D1 | HIGH+MEDIUM | 1659 | 1609 | 743 | 0.253725 | 0.51144 | 39 | 11 | 0.522001 | 0.002907 | 0.060277 | 0.549187 |
| XAGUSD\|ny\|bearish\|H4+H1_consensus | HIGH+MEDIUM | 1681 | 1638 | 589 | 0.28827 | 0.517827 | 7 | 25 | 0.630577 | 0.116608 | 0.044616 | 0.536727 |
| GBPJPY\|london\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 1444 | 1395 | 540 | 0.280138 | 0.507407 | 41 | 8 | 0.592105 | 0.027132 | 0.067867 | 0.50516 |
| USDJPY\|ny\|bearish\|H4+H1_consensus | HIGH+MEDIUM | 539 | 520 | 151 | 0.532695 | 0.655629 | 9 | 10 | 0.684601 | 0.192308 | 0.070501 | 0.502547 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | HIGH+MEDIUM | 591 | 562 | 252 | 0.387224 | 0.563492 | 17 | 12 | 0.524535 | 0.0 | 0.098139 | 0.481203 |
| GBPJPY\|tokyo\|bearish\|D1 | HIGH+MEDIUM | 349 | 348 | 158 | 0.416275 | 0.563291 | 1 | 0 | 0.544413 | 0.0 | 0.005731 | 0.452689 |
| GBPJPY\|tokyo\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 1751 | 1680 | 657 | 0.228376 | 0.493151 | 71 | 0 | 0.584238 | 0.0 | 0.081097 | 0.448195 |
| XAGUSD\|london\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 2740 | 2561 | 658 | 0.224182 | 0.490881 | 37 | 80 | 0.706934 | 0.046832 | 0.108029 | 0.414033 |
| XAGUSD\|ny\|bullish\|D1 | HIGH+MEDIUM | 1261 | 1194 | 317 | 0.343521 | 0.526814 | 3 | 64 | 0.69548 | 0.253333 | 0.106265 | 0.402125 |
| XAUUSD\|london\|bullish\|D1 | HIGH+MEDIUM | 1497 | 1418 | 451 | 0.262469 | 0.507761 | 14 | 23 | 0.674015 | 0.126126 | 0.077488 | 0.399279 |
| USDJPY\|tokyo\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 1904 | 1799 | 676 | 0.209886 | 0.494083 | 105 | 0 | 0.589811 | 0.037037 | 0.110294 | 0.39218 |
| USDJPY\|london\|bearish\|D1 | HIGH+MEDIUM | 485 | 469 | 159 | 0.383648 | 0.553459 | 16 | 0 | 0.639175 | 0.0 | 0.065979 | 0.387865 |
| GBPUSD\|ny\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 1108 | 1085 | 308 | 0.24689 | 0.493506 | 13 | 10 | 0.701264 | 0.0 | 0.041516 | 0.343898 |
| GBPUSD\|london\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 2242 | 2177 | 726 | 0.166562 | 0.469697 | 45 | 20 | 0.64719 | 0.0 | 0.057984 | 0.342369 |
| GBPJPY\|london\|bullish\|D1 | HIGH+MEDIUM | 1040 | 994 | 360 | 0.220632 | 0.488889 | 39 | 7 | 0.609615 | 0.017857 | 0.088462 | 0.302829 |
| USDJPY\|london\|bearish\|H4+H1_consensus | HIGH+MEDIUM | 551 | 531 | 181 | 0.272345 | 0.524862 | 10 | 10 | 0.635209 | 0.116279 | 0.072595 | 0.252515 |
| XAUUSD\|ny\|bullish\|H4+H1_consensus | HIGH+MEDIUM | 2908 | 2782 | 986 | 0.12468 | 0.464503 | 36 | 90 | 0.617607 | 0.12253 | 0.086657 | 0.249326 |
| US30_cash\|london\|bearish\|D1 | HIGH+MEDIUM | 384 | 355 | 173 | 0.286127 | 0.514451 | 29 | 0 | 0.473958 | 0.035714 | 0.151042 | 0.238945 |

## Cohort Anatomy

### Symbol

| symbol | rows | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | immediate_stop | no_entry_rate_setup | sl_rate_filled | immediate_stop_rate_sl | ambiguity_rate_setup | high_confidence | high_medium_confidence | high_resolved_n | high_mean_r | high_win_rate | high_medium_resolved_n | high_medium_mean_r | high_medium_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | 33471 | 11172 | 4161 | 0.198142 | 0.489065 | 1810 | 2003 | 348 | 6665 | 307 | 39 | 43 | 0.596581 | 0.481375 | 0.021468 | 0.062836 | 9115 | 10816 | 3845 | 0.220371 | 0.496489 | 4161 | 0.198142 | 0.489065 |
| GBPUSD | 31410 | 10670 | 4179 | 0.055283 | 0.433597 | 1601 | 2249 | 329 | 6173 | 227 | 91 | 31 | 0.578538 | 0.538167 | 0.013784 | 0.059981 | 8556 | 10348 | 3885 | 0.030113 | 0.420335 | 4179 | 0.055283 | 0.433597 |
| NAS100 | 24454 | 9821 | 3866 | 0.082611 | 0.440766 | 1547 | 2116 | 203 | 5521 | 286 | 148 | 209 | 0.562163 | 0.547336 | 0.098771 | 0.089502 | 3146 | 9376 | 3146 | 0.075139 | 0.42562 | 3861 | 0.084013 | 0.441336 |
| US30_cash | 16257 | 5406 | 2037 | 0.034706 | 0.405989 | 801 | 1164 | 72 | 3009 | 235 | 125 | 98 | 0.556604 | 0.571429 | 0.084192 | 0.14077 | 1856 | 5005 | 1856 | 0.041477 | 0.411099 | 2031 | 0.035301 | 0.406204 |
| USDJPY | 33481 | 11726 | 4256 | 0.137312 | 0.466165 | 1788 | 2216 | 252 | 6871 | 547 | 52 | 117 | 0.585963 | 0.520677 | 0.052798 | 0.103275 | 9166 | 11114 | 4071 | 0.137982 | 0.460084 | 4256 | 0.137312 | 0.466165 |
| XAGUSD | 33364 | 12350 | 3704 | 0.240003 | 0.49784 | 1770 | 1831 | 103 | 8150 | 119 | 377 | 136 | 0.659919 | 0.49433 | 0.074276 | 0.092227 | 2512 | 11707 | 2512 | 0.215108 | 0.485271 | 3664 | 0.253541 | 0.503275 |
| XAUUSD | 32760 | 12805 | 4607 | 0.087072 | 0.443673 | 1807 | 2445 | 355 | 7709 | 186 | 303 | 186 | 0.60203 | 0.530714 | 0.076074 | 0.082702 | 3362 | 12235 | 3362 | 0.045765 | 0.416419 | 4606 | 0.087199 | 0.443769 |

### Session

| session | rows | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | immediate_stop | no_entry_rate_setup | sl_rate_filled | immediate_stop_rate_sl | ambiguity_rate_setup | high_confidence | high_medium_confidence | high_resolved_n | high_mean_r | high_win_rate | high_medium_resolved_n | high_medium_mean_r | high_medium_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| london | 92373 | 33689 | 12754 | 0.083186 | 0.439 | 5133 | 6923 | 698 | 19771 | 816 | 348 | 347 | 0.586868 | 0.54281 | 0.050123 | 0.073258 | 17713 | 32385 | 11350 | 0.067786 | 0.427401 | 12721 | 0.085799 | 0.44006 |
| ny | 87762 | 31707 | 10737 | 0.135677 | 0.462885 | 4478 | 5529 | 730 | 19439 | 756 | 775 | 414 | 0.613082 | 0.514948 | 0.074878 | 0.101839 | 12996 | 30009 | 8094 | 0.119899 | 0.45194 | 10718 | 0.13741 | 0.463613 |
| tokyo | 25062 | 8554 | 3319 | 0.241748 | 0.506478 | 1513 | 1572 | 234 | 4888 | 335 | 12 | 59 | 0.571429 | 0.473637 | 0.037532 | 0.081132 | 7004 | 8207 | 3233 | 0.245528 | 0.503248 | 3319 | 0.241748 | 0.506478 |

### Year

| year | rows | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | immediate_stop | no_entry_rate_setup | sl_rate_filled | immediate_stop_rate_sl | ambiguity_rate_setup | high_confidence | high_medium_confidence | high_resolved_n | high_mean_r | high_win_rate | high_medium_resolved_n | high_medium_mean_r | high_medium_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 32814 | 11437 | 4224 | 0.129599 | 0.458807 | 1782 | 2201 | 241 | 6788 | 286 | 139 | 74 | 0.593512 | 0.52107 | 0.033621 | 0.101163 | 6041 | 10705 | 3483 | 0.151215 | 0.463681 | 4172 | 0.14236 | 0.464046 |
| 2023 | 49858 | 18854 | 6966 | 0.120701 | 0.457651 | 2858 | 3642 | 466 | 11158 | 536 | 194 | 275 | 0.591811 | 0.522825 | 0.075508 | 0.077437 | 9597 | 18124 | 5856 | 0.095498 | 0.443306 | 6966 | 0.120701 | 0.457651 |
| 2024 | 52578 | 18506 | 6772 | 0.128618 | 0.458358 | 2802 | 3529 | 441 | 10837 | 584 | 313 | 269 | 0.585594 | 0.521116 | 0.076226 | 0.096942 | 10187 | 17609 | 5826 | 0.119404 | 0.449537 | 6772 | 0.128618 | 0.458358 |
| 2025 | 52691 | 18957 | 6518 | 0.097877 | 0.442927 | 2665 | 3507 | 346 | 11726 | 356 | 357 | 109 | 0.618558 | 0.538048 | 0.031081 | 0.075223 | 8873 | 18244 | 5525 | 0.080421 | 0.43095 | 6518 | 0.097877 | 0.442927 |
| 2026 | 17256 | 6196 | 2330 | 0.181495 | 0.486266 | 1017 | 1145 | 168 | 3589 | 145 | 132 | 93 | 0.579245 | 0.491416 | 0.081223 | 0.089413 | 3015 | 5919 | 1987 | 0.154873 | 0.465526 | 2330 | 0.181495 | 0.486266 |

### Regime

| regime | rows | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | immediate_stop | no_entry_rate_setup | sl_rate_filled | immediate_stop_rate_sl | ambiguity_rate_setup | high_confidence | high_medium_confidence | high_resolved_n | high_mean_r | high_win_rate | high_medium_resolved_n | high_medium_mean_r | high_medium_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bearish\|D1 | 21222 | 7981 | 3395 | 0.103695 | 0.448601 | 1397 | 1806 | 192 | 4345 | 180 | 61 | 31 | 0.544418 | 0.531959 | 0.017165 | 0.060393 | 5069 | 7740 | 2979 | 0.150974 | 0.462236 | 3395 | 0.103695 | 0.448601 |
| bearish\|H4+H1_consensus | 15845 | 14068 | 5058 | 0.021235 | 0.417556 | 1866 | 2784 | 408 | 8611 | 211 | 188 | 162 | 0.612098 | 0.550415 | 0.05819 | 0.057791 | 6832 | 13654 | 4087 | 0.03408 | 0.421336 | 5058 | 0.021235 | 0.417556 |
| bearish\|H4_primary | 15063 | 964 | 535 | 0.196448 | 0.471028 | 241 | 262 | 32 | 380 | 30 | 19 | 0 | 0.394191 | 0.48972 | 0.0 | 0.10166 | 618 | 915 | 446 | 0.231407 | 0.479821 | 535 | 0.196448 | 0.471028 |
| bullish\|D1 | 41347 | 18659 | 6941 | 0.168824 | 0.475868 | 2985 | 3508 | 448 | 10843 | 528 | 347 | 294 | 0.581114 | 0.505403 | 0.083808 | 0.097594 | 9237 | 17713 | 5793 | 0.142898 | 0.461937 | 6941 | 0.168824 | 0.475868 |
| bullish\|H4+H1_consensus | 35494 | 30966 | 10071 | 0.142341 | 0.464403 | 4269 | 5248 | 554 | 19472 | 914 | 509 | 330 | 0.628819 | 0.5211 | 0.062881 | 0.098624 | 15055 | 29335 | 8657 | 0.107967 | 0.442763 | 10020 | 0.147656 | 0.466567 |
| bullish\|H4_primary | 18300 | 1312 | 810 | 0.185438 | 0.47284 | 366 | 416 | 28 | 447 | 44 | 11 | 3 | 0.340701 | 0.51358 | 0.007212 | 0.09375 | 902 | 1244 | 715 | 0.110346 | 0.439161 | 809 | 0.186282 | 0.473424 |
| none\|none | 57926 | 0 | 0 |  | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 0 |  | 0.0 | 0 |  | 0.0 |

### Symbol x Session

| symbol_session | rows | setup_rows | resolved_r_n | mean_r | win_rate | tp | sl | timeout | no_entry | same_bar | lower_tf_gappy | immediate_stop | no_entry_rate_setup | sl_rate_filled | immediate_stop_rate_sl | ambiguity_rate_setup | high_confidence | high_medium_confidence | high_resolved_n | high_mean_r | high_win_rate | high_medium_resolved_n | high_medium_mean_r | high_medium_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY\|london | 10470 | 3525 | 1346 | 0.191849 | 0.475483 | 598 | 670 | 78 | 2073 | 91 | 15 | 14 | 0.588085 | 0.497771 | 0.020896 | 0.060142 | 2909 | 3419 | 1249 | 0.218643 | 0.485188 | 1346 | 0.191849 | 0.475483 |
| GBPJPY\|ny | 10480 | 3445 | 1235 | 0.105204 | 0.466397 | 464 | 614 | 157 | 2118 | 68 | 24 | 24 | 0.614804 | 0.497166 | 0.039088 | 0.056313 | 2715 | 3343 | 1058 | 0.124573 | 0.473535 | 1235 | 0.105204 | 0.466397 |
| GBPJPY\|tokyo | 12521 | 4202 | 1580 | 0.276148 | 0.518354 | 748 | 719 | 113 | 2474 | 148 | 0 | 5 | 0.588767 | 0.455063 | 0.006954 | 0.070443 | 3491 | 4054 | 1538 | 0.287676 | 0.521456 | 1580 | 0.276148 | 0.518354 |
| GBPUSD\|london | 20940 | 7254 | 3029 | 0.075216 | 0.44239 | 1195 | 1626 | 208 | 4000 | 165 | 60 | 31 | 0.55142 | 0.536811 | 0.019065 | 0.062035 | 5920 | 7029 | 2865 | 0.046121 | 0.425131 | 3029 | 0.075216 | 0.44239 |
| GBPUSD\|ny | 10470 | 3416 | 1150 | 0.002781 | 0.410435 | 406 | 623 | 121 | 2173 | 62 | 31 | 0 | 0.636124 | 0.541739 | 0.0 | 0.055621 | 2636 | 3319 | 1020 | -0.014851 | 0.406863 | 1150 | 0.002781 | 0.410435 |
| NAS100\|london | 11444 | 4611 | 1841 | 0.044695 | 0.427485 | 719 | 1046 | 76 | 2574 | 148 | 48 | 104 | 0.55823 | 0.568169 | 0.099426 | 0.086966 | 1603 | 4406 | 1603 | 0.062374 | 0.421085 | 1837 | 0.04697 | 0.428416 |
| NAS100\|ny | 13010 | 5210 | 2025 | 0.117083 | 0.45284 | 828 | 1070 | 127 | 2947 | 138 | 100 | 105 | 0.565643 | 0.528395 | 0.098131 | 0.091747 | 1543 | 4970 | 1543 | 0.088399 | 0.430331 | 2024 | 0.117635 | 0.453063 |
| US30_cash\|london | 8189 | 2705 | 1009 | 0.008346 | 0.391477 | 385 | 585 | 39 | 1531 | 128 | 37 | 42 | 0.565989 | 0.579782 | 0.071795 | 0.130869 | 947 | 2516 | 947 | 0.014 | 0.400211 | 1008 | 0.006866 | 0.390873 |
| US30_cash\|ny | 8068 | 2701 | 1028 | 0.06058 | 0.420233 | 416 | 579 | 33 | 1478 | 107 | 88 | 56 | 0.547205 | 0.56323 | 0.096718 | 0.150685 | 909 | 2489 | 909 | 0.070104 | 0.422442 | 1023 | 0.06332 | 0.42131 |
| USDJPY\|london | 10470 | 3720 | 1365 | 0.060874 | 0.430037 | 552 | 766 | 47 | 2180 | 155 | 20 | 30 | 0.586022 | 0.561172 | 0.039164 | 0.094892 | 2967 | 3542 | 1319 | 0.050302 | 0.423806 | 1365 | 0.060874 | 0.430037 |
| USDJPY\|ny | 10470 | 3654 | 1152 | 0.11741 | 0.46441 | 471 | 597 | 84 | 2277 | 205 | 20 | 33 | 0.623153 | 0.518229 | 0.055276 | 0.125889 | 2686 | 3419 | 1057 | 0.136264 | 0.46263 | 1152 | 0.11741 | 0.46441 |
| USDJPY\|tokyo | 12541 | 4352 | 1739 | 0.210493 | 0.495687 | 765 | 853 | 121 | 2414 | 187 | 12 | 54 | 0.554688 | 0.490512 | 0.063306 | 0.091452 | 3513 | 4153 | 1695 | 0.207284 | 0.486726 | 1739 | 0.210493 | 0.495687 |
| XAGUSD\|london | 15572 | 5748 | 1814 | 0.157194 | 0.464168 | 818 | 953 | 43 | 3772 | 49 | 113 | 36 | 0.656228 | 0.525358 | 0.037775 | 0.067154 | 1433 | 5524 | 1433 | 0.15335 | 0.460572 | 1786 | 0.175336 | 0.471445 |
| XAGUSD\|ny | 17792 | 6602 | 1890 | 0.319483 | 0.530159 | 952 | 878 | 60 | 4378 | 70 | 264 | 100 | 0.663132 | 0.46455 | 0.113895 | 0.114056 | 1079 | 6183 | 1079 | 0.297128 | 0.518072 | 1878 | 0.327914 | 0.533546 |
| XAUUSD\|london | 15288 | 6126 | 2350 | 0.049339 | 0.428936 | 866 | 1277 | 207 | 3641 | 80 | 55 | 90 | 0.594352 | 0.543404 | 0.070478 | 0.05093 | 1934 | 5949 | 1934 | -0.018199 | 0.389866 | 2350 | 0.049339 | 0.428936 |
| XAUUSD\|ny | 17472 | 6679 | 2257 | 0.12636 | 0.459016 | 941 | 1168 | 148 | 4068 | 106 | 248 | 96 | 0.609073 | 0.517501 | 0.082192 | 0.111843 | 1428 | 6286 | 1428 | 0.132393 | 0.452381 | 2256 | 0.126636 | 0.45922 |

## Dominant Failure Buckets

### By Symbol

| symbol | truth_failure_bucket | rows | bucket_share_of_cohort | bucket_share_of_setup |
| --- | --- | --- | --- | --- |
| GBPUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 11033 | 0.351258 |  |
| USDJPY | SETUP_MISSING_OR_LOW_QUALITY_POI | 10693 | 0.319375 |  |
| GBPJPY | SETUP_MISSING_OR_LOW_QUALITY_POI | 9717 | 0.290311 |  |
| XAGUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 9321 | 0.279373 |  |
| XAGUSD | SETUP_HTF_NO_DIRECTION | 8819 | 0.264327 |  |
| XAUUSD | SETUP_MISSING_OR_LOW_QUALITY_POI | 8596 | 0.262393 |  |
| XAGUSD | FAIL_NO_FILL | 8150 | 0.244275 | 0.659919 |
| GBPJPY | SETUP_HTF_NO_DIRECTION | 7927 | 0.236832 |  |
| XAUUSD | FAIL_NO_FILL | 7709 | 0.235317 | 0.60203 |
| NAS100 | SETUP_MISSING_OR_LOW_QUALITY_POI | 7427 | 0.303713 |  |
| XAUUSD | SETUP_HTF_NO_DIRECTION | 7404 | 0.226007 |  |
| USDJPY | SETUP_HTF_NO_DIRECTION | 7367 | 0.220035 |  |
| USDJPY | FAIL_NO_FILL | 6871 | 0.205221 | 0.585963 |
| GBPJPY | FAIL_NO_FILL | 6665 | 0.199128 | 0.596581 |
| GBPUSD | SETUP_HTF_NO_DIRECTION | 6510 | 0.207259 |  |
| GBPUSD | FAIL_NO_FILL | 6173 | 0.19653 | 0.578538 |
| NAS100 | FAIL_NO_FILL | 5521 | 0.225771 | 0.562163 |
| US30_cash | SETUP_MISSING_OR_LOW_QUALITY_POI | 5486 | 0.337455 |  |
| NAS100 | SETUP_HTF_NO_DIRECTION | 4119 | 0.168439 |  |
| US30_cash | SETUP_HTF_NO_DIRECTION | 3311 | 0.203666 |  |
| US30_cash | FAIL_NO_FILL | 3009 | 0.185089 | 0.556604 |
| GBPJPY | SETUP_HTF_CONFLICT | 2608 | 0.077918 |  |
| XAUUSD | FAIL_STOP_FIRST | 2259 | 0.068956 | 0.176415 |
| GBPUSD | FAIL_STOP_FIRST | 2218 | 0.070614 | 0.207873 |
| USDJPY | FAIL_STOP_FIRST | 2099 | 0.062692 | 0.179004 |
| USDJPY | SETUP_POI_ALREADY_MITIGATED | 2049 | 0.061199 |  |
| GBPJPY | SETUP_POI_ALREADY_MITIGATED | 2047 | 0.061157 |  |
| NAS100 | FAIL_STOP_FIRST | 1907 | 0.077983 | 0.194176 |
| GBPUSD | SETUP_POI_ALREADY_MITIGATED | 1864 | 0.059344 |  |
| XAUUSD | SUCCESS_TP_FIRST | 1807 | 0.055159 | 0.141117 |
| XAGUSD | SUCCESS_TP_FIRST | 1770 | 0.053051 | 0.14332 |
| XAGUSD | FAIL_STOP_FIRST | 1695 | 0.050803 | 0.137247 |
| NAS100 | SETUP_POI_ALREADY_MITIGATED | 1550 | 0.063384 |  |
| US30_cash | SETUP_HTF_CONFLICT | 1294 | 0.079596 |  |
| US30_cash | FAIL_STOP_FIRST | 1066 | 0.065572 | 0.197188 |

### By Session

| session | truth_failure_bucket | rows | bucket_share_of_cohort | bucket_share_of_setup |
| --- | --- | --- | --- | --- |
| london | SETUP_MISSING_OR_LOW_QUALITY_POI | 28450 | 0.30799 |  |
| ny | SETUP_MISSING_OR_LOW_QUALITY_POI | 26141 | 0.297862 |  |
| london | SETUP_HTF_NO_DIRECTION | 20231 | 0.219014 |  |
| london | FAIL_NO_FILL | 19771 | 0.214034 | 0.586868 |
| ny | SETUP_HTF_NO_DIRECTION | 19497 | 0.222158 |  |
| ny | FAIL_NO_FILL | 19439 | 0.221497 | 0.613082 |
| tokyo | SETUP_MISSING_OR_LOW_QUALITY_POI | 7682 | 0.30652 |  |
| london | FAIL_STOP_FIRST | 6576 | 0.07119 | 0.195197 |
| tokyo | SETUP_HTF_NO_DIRECTION | 5729 | 0.228593 |  |
| london | SUCCESS_TP_FIRST | 5133 | 0.055568 | 0.152364 |
| ny | FAIL_STOP_FIRST | 5115 | 0.058283 | 0.161321 |
| tokyo | FAIL_NO_FILL | 4888 | 0.195036 | 0.571429 |
| ny | SETUP_HTF_CONFLICT | 4818 | 0.054898 |  |
| tokyo | SETUP_HTF_CONFLICT | 1583 | 0.063163 |  |
| tokyo | SETUP_POI_ALREADY_MITIGATED | 1514 | 0.06041 |  |

### By Regime

| regime | truth_failure_bucket | rows | bucket_share_of_cohort | bucket_share_of_setup |
| --- | --- | --- | --- | --- |
| none\|none | SETUP_HTF_NO_DIRECTION | 45457 | 0.784743 |  |
| bullish\|H4+H1_consensus | FAIL_NO_FILL | 19472 | 0.5486 | 0.628819 |
| bullish\|D1 | SETUP_MISSING_OR_LOW_QUALITY_POI | 18618 | 0.450287 |  |
| bullish\|H4_primary | SETUP_MISSING_OR_LOW_QUALITY_POI | 16570 | 0.905464 |  |
| bearish\|H4_primary | SETUP_MISSING_OR_LOW_QUALITY_POI | 13757 | 0.913297 |  |
| bearish\|D1 | SETUP_MISSING_OR_LOW_QUALITY_POI | 11931 | 0.5622 |  |
| none\|none | SETUP_HTF_CONFLICT | 11377 | 0.196406 |  |
| bullish\|D1 | FAIL_NO_FILL | 10843 | 0.262244 | 0.581114 |
| bearish\|H4+H1_consensus | FAIL_NO_FILL | 8611 | 0.543452 | 0.612098 |
| bullish\|H4+H1_consensus | FAIL_STOP_FIRST | 4918 | 0.138559 | 0.158819 |
| bearish\|D1 | FAIL_NO_FILL | 4345 | 0.20474 | 0.544418 |
| bullish\|H4+H1_consensus | SUCCESS_TP_FIRST | 4269 | 0.120274 | 0.137861 |
| bullish\|D1 | SETUP_POI_ALREADY_MITIGATED | 4070 | 0.098435 |  |
| bullish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 3573 | 0.100665 |  |
| bullish\|D1 | FAIL_STOP_FIRST | 3214 | 0.077732 | 0.172249 |
| bullish\|D1 | SUCCESS_TP_FIRST | 2985 | 0.072194 | 0.159976 |
| bearish\|H4+H1_consensus | FAIL_STOP_FIRST | 2622 | 0.165478 | 0.18638 |
| bearish\|H4+H1_consensus | SUCCESS_TP_FIRST | 1866 | 0.117766 | 0.132641 |
| bearish\|D1 | FAIL_STOP_FIRST | 1775 | 0.08364 | 0.222403 |
| bearish\|D1 | SUCCESS_TP_FIRST | 1397 | 0.065828 | 0.175041 |
| bearish\|H4+H1_consensus | SETUP_POI_ALREADY_MITIGATED | 1335 | 0.084254 |  |
| bearish\|D1 | SETUP_POI_ALREADY_MITIGATED | 1310 | 0.061728 |  |
| none\|none | SETUP_SKIP_FIRST_NY_CANDLE | 1092 | 0.018852 |  |
| bullish\|H4+H1_consensus | SETUP_MISSING_OR_LOW_QUALITY_POI | 955 | 0.026906 |  |
| bullish\|H4_primary | FAIL_NO_FILL | 447 | 0.024426 | 0.340701 |
| bearish\|H4+H1_consensus | SETUP_MISSING_OR_LOW_QUALITY_POI | 442 | 0.027895 |  |
| bullish\|H4_primary | SETUP_POI_ALREADY_MITIGATED | 418 | 0.022842 |  |
| bullish\|H4_primary | FAIL_STOP_FIRST | 413 | 0.022568 | 0.314787 |
| bearish\|H4_primary | FAIL_NO_FILL | 380 | 0.025227 | 0.394191 |
| bullish\|H4_primary | SUCCESS_TP_FIRST | 366 | 0.02 | 0.278963 |
| bearish\|H4_primary | SETUP_POI_ALREADY_MITIGATED | 342 | 0.022705 |  |
| bearish\|H4_primary | FAIL_STOP_FIRST | 262 | 0.017394 | 0.271784 |
| bearish\|H4_primary | SUCCESS_TP_FIRST | 241 | 0.015999 | 0.25 |

## NO_ENTRY Anatomy

### Global

| cohort | no_entry_rows | path_n | path_coverage | median_closest_distance_r | p75_closest_distance_r | mean_entry_proximity_pct | near_entry_le_0_25r | near_entry_le_0_25r_rate | near_entry_le_0_50r_rate | near_entry_le_1_00r_rate | fill_touched_in_path | median_bars_until_nearest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_rows | 44098 | 44098 | 1.0 | 2.417945 | 4.820572 | 0.116036 | 2400 | 0.054424 | 0.114495 | 0.232029 | 0 | 32.0 |

### By Symbol x Session

| symbol_session | no_entry_rows | path_n | path_coverage | median_closest_distance_r | p75_closest_distance_r | mean_entry_proximity_pct | near_entry_le_0_25r | near_entry_le_0_25r_rate | near_entry_le_0_50r_rate | near_entry_le_1_00r_rate | fill_touched_in_path | median_bars_until_nearest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAGUSD\|ny | 4378 | 4378 | 1.0 | 2.608077 | 5.000197 | 0.109575 | 201 | 0.045911 | 0.110781 | 0.224075 | 0 | 16.0 |
| XAUUSD\|ny | 4068 | 4068 | 1.0 | 2.341496 | 5.08861 | 0.122196 | 238 | 0.058505 | 0.124877 | 0.24115 | 0 | 10.0 |
| GBPUSD\|london | 4000 | 4000 | 1.0 | 1.88705 | 3.34873 | 0.133825 | 220 | 0.055 | 0.12825 | 0.28475 | 0 | 59.0 |
| XAGUSD\|london | 3772 | 3772 | 1.0 | 2.916025 | 5.533574 | 0.095315 | 170 | 0.045069 | 0.09597 | 0.186108 | 0 | 29.0 |
| XAUUSD\|london | 3641 | 3641 | 1.0 | 2.413788 | 5.195698 | 0.112064 | 256 | 0.07031 | 0.116726 | 0.195825 | 0 | 27.0 |
| NAS100\|ny | 2947 | 2947 | 1.0 | 2.703902 | 5.6808 | 0.122876 | 163 | 0.05531 | 0.126909 | 0.228368 | 0 | 11.0 |
| NAS100\|london | 2574 | 2574 | 1.0 | 2.685556 | 6.388586 | 0.109358 | 109 | 0.042347 | 0.103341 | 0.219891 | 0 | 32.0 |
| GBPJPY\|tokyo | 2474 | 2474 | 1.0 | 2.094282 | 4.028875 | 0.117339 | 114 | 0.046079 | 0.114794 | 0.235247 | 0 | 103.5 |
| USDJPY\|tokyo | 2414 | 2414 | 1.0 | 2.534727 | 4.898624 | 0.1007 | 123 | 0.050953 | 0.089478 | 0.216653 | 0 | 85.0 |
| USDJPY\|ny | 2277 | 2277 | 1.0 | 2.447797 | 5.116397 | 0.108327 | 130 | 0.057093 | 0.108037 | 0.214317 | 0 | 54.0 |
| USDJPY\|london | 2180 | 2180 | 1.0 | 2.477403 | 5.003018 | 0.114015 | 118 | 0.054128 | 0.102752 | 0.244037 | 0 | 79.0 |
| GBPUSD\|ny | 2173 | 2173 | 1.0 | 1.924233 | 3.514523 | 0.143417 | 149 | 0.068569 | 0.132075 | 0.300046 | 0 | 57.0 |
| GBPJPY\|ny | 2118 | 2118 | 1.0 | 2.188266 | 4.05231 | 0.118959 | 95 | 0.044854 | 0.125118 | 0.23796 | 0 | 77.0 |
| GBPJPY\|london | 2073 | 2073 | 1.0 | 1.861456 | 4.387114 | 0.141334 | 147 | 0.070912 | 0.153401 | 0.276893 | 0 | 70.0 |
| US30_cash\|london | 1531 | 1531 | 1.0 | 2.843708 | 6.16705 | 0.099355 | 84 | 0.054866 | 0.089484 | 0.201176 | 0 | 28.0 |
| US30_cash\|ny | 1478 | 1478 | 1.0 | 2.903566 | 5.566819 | 0.105812 | 83 | 0.056157 | 0.094046 | 0.212449 | 0 | 10.0 |

### By Regime

| regime | no_entry_rows | path_n | path_coverage | median_closest_distance_r | p75_closest_distance_r | mean_entry_proximity_pct | near_entry_le_0_25r | near_entry_le_0_25r_rate | near_entry_le_0_50r_rate | near_entry_le_1_00r_rate | fill_touched_in_path | median_bars_until_nearest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bullish\|H4+H1_consensus | 19472 | 19472 | 1.0 | 2.725028 | 5.6808 | 0.106937 | 953 | 0.048942 | 0.103893 | 0.211278 | 0 | 32.0 |
| bullish\|D1 | 10843 | 10843 | 1.0 | 2.312158 | 4.376636 | 0.11154 | 392 | 0.036152 | 0.110486 | 0.238218 | 0 | 30.0 |
| bearish\|H4+H1_consensus | 8611 | 8611 | 1.0 | 2.204569 | 4.200951 | 0.121162 | 590 | 0.068517 | 0.120427 | 0.233887 | 0 | 34.0 |
| bearish\|D1 | 4345 | 4345 | 1.0 | 2.379682 | 4.151881 | 0.12948 | 338 | 0.077791 | 0.129804 | 0.255696 | 0 | 45.0 |
| bullish\|H4_primary | 447 | 447 | 1.0 | 0.930206 | 1.870337 | 0.288149 | 83 | 0.185682 | 0.317673 | 0.53915 | 0 | 22.0 |
| bearish\|H4_primary | 380 | 380 | 1.0 | 1.24157 | 1.996551 | 0.238231 | 44 | 0.115789 | 0.223684 | 0.444737 | 0 | 18.5 |

## SL Anatomy

### Global

| cohort | immediate_stop | path_n | path_coverage | sl_rows | immediate_stop_rate | median_mfe_before_stop_r | p75_mfe_before_stop_r | mfe_ge_0_25r_rate | mfe_ge_0_50r_rate | mfe_ge_1_00r_rate | median_bars_fill_to_stop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_rows | 820 | 14024 | 1.0 | 14024 | 0.058471 | 0.571039 | 0.90107 | 0.811252 | 0.563605 | 0.203223 | 28.0 |

### By Symbol x Session

| symbol_session | immediate_stop | path_n | path_coverage | sl_rows | immediate_stop_rate | median_mfe_before_stop_r | p75_mfe_before_stop_r | mfe_ge_0_25r_rate | mfe_ge_0_50r_rate | mfe_ge_1_00r_rate | median_bars_fill_to_stop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GBPUSD\|london | 31 | 1626 | 1.0 | 1626 | 0.019065 | 0.472477 | 0.727962 | 0.714022 | 0.469865 | 0.141451 | 57.0 |
| XAUUSD\|london | 90 | 1277 | 1.0 | 1277 | 0.070478 | 0.52934 | 0.95213 | 0.793265 | 0.521535 | 0.214565 | 38.0 |
| XAUUSD\|ny | 96 | 1168 | 1.0 | 1168 | 0.082192 | 0.650684 | 0.981856 | 0.917808 | 0.639555 | 0.244007 | 18.0 |
| NAS100\|ny | 105 | 1070 | 1.0 | 1070 | 0.098131 | 0.585537 | 0.937748 | 0.858879 | 0.55514 | 0.234579 | 17.0 |
| NAS100\|london | 104 | 1046 | 1.0 | 1046 | 0.099426 | 0.537112 | 0.888321 | 0.859465 | 0.512428 | 0.162524 | 21.0 |
| XAGUSD\|london | 36 | 953 | 1.0 | 953 | 0.037775 | 0.658097 | 0.924235 | 0.801679 | 0.599161 | 0.206716 | 22.0 |
| XAGUSD\|ny | 100 | 878 | 1.0 | 878 | 0.113895 | 0.695171 | 0.88323 | 0.900911 | 0.656036 | 0.17426 | 13.0 |
| USDJPY\|tokyo | 54 | 853 | 1.0 | 853 | 0.063306 | 0.532508 | 0.829792 | 0.80891 | 0.52286 | 0.173505 | 37.0 |
| USDJPY\|london | 30 | 766 | 1.0 | 766 | 0.039164 | 0.546319 | 0.856432 | 0.872063 | 0.565274 | 0.173629 | 42.0 |
| GBPJPY\|tokyo | 5 | 719 | 1.0 | 719 | 0.006954 | 0.633481 | 1.029467 | 0.815021 | 0.66064 | 0.258693 | 70.0 |
| GBPJPY\|london | 14 | 670 | 1.0 | 670 | 0.020896 | 0.611475 | 1.078733 | 0.786567 | 0.58806 | 0.276119 | 44.0 |
| GBPUSD\|ny | 0 | 623 | 1.0 | 623 | 0.0 | 0.498785 | 0.700081 | 0.659711 | 0.492777 | 0.149278 | 44.0 |
| GBPJPY\|ny | 24 | 614 | 1.0 | 614 | 0.039088 | 0.519581 | 0.93937 | 0.716612 | 0.530945 | 0.226384 | 29.5 |
| USDJPY\|ny | 33 | 597 | 1.0 | 597 | 0.055276 | 0.597215 | 0.975996 | 0.835846 | 0.619765 | 0.244556 | 32.0 |
| US30_cash\|london | 42 | 585 | 1.0 | 585 | 0.071795 | 0.613684 | 0.862869 | 0.801709 | 0.588034 | 0.211966 | 35.0 |
| US30_cash\|ny | 56 | 579 | 1.0 | 579 | 0.096718 | 0.659222 | 0.938154 | 0.80829 | 0.613126 | 0.234888 | 14.0 |

### By Regime

| regime | immediate_stop | path_n | path_coverage | sl_rows | immediate_stop_rate | median_mfe_before_stop_r | p75_mfe_before_stop_r | mfe_ge_0_25r_rate | mfe_ge_0_50r_rate | mfe_ge_1_00r_rate | median_bars_fill_to_stop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bullish\|H4+H1_consensus | 330 | 5248 | 1.0 | 5248 | 0.062881 | 0.587705 | 0.910145 | 0.833841 | 0.594703 | 0.213796 | 25.0 |
| bullish\|D1 | 294 | 3508 | 1.0 | 3508 | 0.083808 | 0.614076 | 0.923501 | 0.840935 | 0.61431 | 0.210376 | 29.0 |
| bearish\|H4+H1_consensus | 162 | 2784 | 1.0 | 2784 | 0.05819 | 0.480843 | 0.814673 | 0.762213 | 0.484914 | 0.176006 | 23.0 |
| bearish\|D1 | 31 | 1806 | 1.0 | 1806 | 0.017165 | 0.546319 | 0.927243 | 0.761351 | 0.51495 | 0.213178 | 42.0 |
| bullish\|H4_primary | 3 | 416 | 1.0 | 416 | 0.007212 | 0.52934 | 0.892716 | 0.889423 | 0.521635 | 0.168269 | 28.0 |
| bearish\|H4_primary | 0 | 262 | 1.0 | 262 | 0.0 | 0.503927 | 0.963371 | 0.70229 | 0.5 | 0.171756 | 52.0 |

## M1/M5 Agreement

| comparable_rows | agreement_rows | disagreement_rows | disagreement_rate |
| --- | --- | --- | --- |
| 73387 | 70737 | 2650 | 0.03611 |

### Top M1 -> M5 Outcome Pairs

| m1_to_m5_outcome | rows |
| --- | --- |
| NO_ENTRY->NO_ENTRY | 43829 |
| SL->SL | 12888 |
| TP->TP | 10574 |
| SL->SAME_BAR | 1761 |
| SAME_BAR->SAME_BAR | 1752 |
| TIMEOUT->TIMEOUT | 1674 |
| TP->SAME_BAR | 814 |
| TIMEOUT->NO_ENTRY | 22 |
| NO_FULL_HORIZON->NO_FULL_HORIZON | 20 |
| TP->TIMEOUT | 15 |
| TIMEOUT->SAME_BAR | 12 |
| SL->TIMEOUT | 11 |
| TP->SL | 5 |
| SAME_BAR->NO_ENTRY | 4 |
| SL->NO_ENTRY | 3 |
| TP->NO_ENTRY | 3 |

### Disagreement Concentration

| truth_outcome | rows |
| --- | --- |
| SL | 1438 |
| TP | 714 |
| LOWER_TF_GAPPY | 383 |
| SAME_BAR | 57 |
| NO_ENTRY | 35 |
| TIMEOUT | 23 |

| gappy_flag | rows |
| --- | --- |
| gappy | 2380 |
| not_gappy | 270 |

| same_bar_flag | rows |
| --- | --- |
| same_bar_involved | 2591 |
| no_same_bar | 59 |

## Synthesis

- Rows are clean for diagnostic use: 205,197 rows, 205,197 unique keys, 0 duplicates, and 0 AI calls.
- Dominant actionable buckets remain NO_ENTRY=44,098, SL=14,024, TP=11,124, SAME_BAR=1,907, LOWER_TF_GAPPY=1,135.
- Best high-confidence diagnostic lead by the transparent priority score is `GBPJPY|tokyo|bullish|D1` with n=430, mean R=+0.4930, WR=60.93%. Treat this as a cohort to study, not a promotion claim.
- NO_ENTRY path anatomy is now measurable without tuning: 44,098/44,098 rows had OHLCV path coverage; 5.44% came within 0.25R of entry.
- SL path anatomy shows whether stops failed immediately or after usable excursion: immediate-stop rate 5.85%, median pre-stop MFE 0.571R.
- M1/M5 disagreement is explicit: 2,650/73,387 comparable rows disagree (3.61%); concentrated same-bar or gappy disagreements should be excluded before parameter work.
- Recommended next research unit: pre-register 2-4 stable candidate cohorts from this report, then run controlled studies with DSR/PBO accounting. Do not sweep entry offsets from the full population.
