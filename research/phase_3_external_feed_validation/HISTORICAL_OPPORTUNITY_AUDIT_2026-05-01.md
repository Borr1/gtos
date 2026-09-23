# Phase 3 Historical Pre-AI Opportunity Audit

**Created UTC:** 2026-05-01T02:36:03.837942+00:00
**Dataset:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z.jsonl`
**Bundle:** `calendar_macro_bundle_v1`
**Rows:** 205197
**Would send AI:** 135062 (65.82%)

## Scope

- Research-only artifact; no live trading logic, prompt, or config file was changed.
- No paid AI/API replay was run; this script does not call the primary analyzer.
- `WOULD_SEND_AI` means the deterministic offline pre-AI gates pass; it is not an AI `CANDIDATE`, an L2-verified setup, or an executable trade.
- KZ enumeration uses local MT5 CSV exports and canonical M15 candle closes.
- External features are selected by publication/as-of timestamps no later than the evaluated candle close.
- LBMA calendar schedule features are marked missing unless the cached previous/current/next fix is within 7 days of the candle.
- Higher-timeframe replay policy: `partial_htf`. This approximates live MT5 partial HTF context when set to `partial_htf`; historical final OHLCV cannot perfectly reconstruct live in-progress HTF bars.

## Input Data

- Symbols: `XAUUSD, XAGUSD, NAS100, US30_cash, GBPUSD, USDJPY, GBPJPY`
- Data dirs: `data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1, data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1`
- Timeframe: `M15`
- Start: `None`
- End: `None`

## Gate Counts

| pre_ai_gate_status | rows |
| --- | --- |
| PRE_AI_POI_REJECT | 12209 |
| PRE_SCREEN_REJECT | 56834 |
| SKIP_FIRST_NY_CANDLE | 1092 |
| WOULD_SEND_AI | 135062 |

## Counts By Symbol

| symbol | rows |
| --- | --- |
| GBPJPY | 33471 |
| GBPUSD | 31410 |
| NAS100 | 24454 |
| US30_cash | 16257 |
| USDJPY | 33481 |
| XAGUSD | 33364 |
| XAUUSD | 32760 |

## Counts By Year

| year | rows |
| --- | --- |
| 2022 | 32814 |
| 2023 | 49858 |
| 2024 | 52578 |
| 2025 | 52691 |
| 2026 | 17256 |

## Counts By Kill Zone

| kill_zone | rows |
| --- | --- |
| london | 92373 |
| ny | 87762 |
| tokyo | 25062 |

## Top Gate Reasons

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

## Symbol x Gate Status

| symbol | pre_ai_gate_status | rows |
| --- | --- | --- |
| GBPJPY | PRE_AI_POI_REJECT | 1931 |
| GBPJPY | PRE_SCREEN_REJECT | 10535 |
| GBPJPY | WOULD_SEND_AI | 21005 |
| GBPUSD | PRE_AI_POI_REJECT | 2027 |
| GBPUSD | PRE_SCREEN_REJECT | 7843 |
| GBPUSD | WOULD_SEND_AI | 21540 |
| NAS100 | PRE_AI_POI_REJECT | 1055 |
| NAS100 | PRE_SCREEN_REJECT | 5656 |
| NAS100 | WOULD_SEND_AI | 17743 |
| US30_cash | PRE_AI_POI_REJECT | 813 |
| US30_cash | PRE_SCREEN_REJECT | 4605 |
| US30_cash | WOULD_SEND_AI | 10839 |
| USDJPY | PRE_AI_POI_REJECT | 1591 |
| USDJPY | PRE_SCREEN_REJECT | 9013 |
| USDJPY | WOULD_SEND_AI | 22877 |
| XAGUSD | PRE_AI_POI_REJECT | 2531 |
| XAGUSD | PRE_SCREEN_REJECT | 10511 |
| XAGUSD | WOULD_SEND_AI | 20322 |
| XAUUSD | PRE_AI_POI_REJECT | 2261 |
| XAUUSD | PRE_SCREEN_REJECT | 8671 |
| XAUUSD | SKIP_FIRST_NY_CANDLE | 1092 |
| XAUUSD | WOULD_SEND_AI | 20736 |

## Year x Gate Status

| year | pre_ai_gate_status | rows |
| --- | --- | --- |
| 2022 | PRE_AI_POI_REJECT | 1957 |
| 2022 | PRE_SCREEN_REJECT | 10204 |
| 2022 | SKIP_FIRST_NY_CANDLE | 234 |
| 2022 | WOULD_SEND_AI | 20419 |
| 2023 | PRE_AI_POI_REJECT | 3278 |
| 2023 | PRE_SCREEN_REJECT | 12043 |
| 2023 | SKIP_FIRST_NY_CANDLE | 257 |
| 2023 | WOULD_SEND_AI | 34280 |
| 2024 | PRE_AI_POI_REJECT | 3287 |
| 2024 | PRE_SCREEN_REJECT | 14339 |
| 2024 | SKIP_FIRST_NY_CANDLE | 259 |
| 2024 | WOULD_SEND_AI | 34693 |
| 2025 | PRE_AI_POI_REJECT | 2867 |
| 2025 | PRE_SCREEN_REJECT | 15673 |
| 2025 | SKIP_FIRST_NY_CANDLE | 258 |
| 2025 | WOULD_SEND_AI | 33893 |
| 2026 | PRE_AI_POI_REJECT | 820 |
| 2026 | PRE_SCREEN_REJECT | 4575 |
| 2026 | SKIP_FIRST_NY_CANDLE | 84 |
| 2026 | WOULD_SEND_AI | 11777 |

## Kill Zone x Gate Status

| kill_zone | pre_ai_gate_status | rows |
| --- | --- | --- |
| london | PRE_AI_POI_REJECT | 5484 |
| london | PRE_SCREEN_REJECT | 25207 |
| london | WOULD_SEND_AI | 61682 |
| ny | PRE_AI_POI_REJECT | 5516 |
| ny | PRE_SCREEN_REJECT | 24315 |
| ny | SKIP_FIRST_NY_CANDLE | 1092 |
| ny | WOULD_SEND_AI | 56839 |
| tokyo | PRE_AI_POI_REJECT | 1209 |
| tokyo | PRE_SCREEN_REJECT | 7312 |
| tokyo | WOULD_SEND_AI | 16541 |

## External Snapshot Coverage

| match_status | rows |
| --- | --- |
| MISSING_ALL_SOURCES | 30 |
| PARTIAL_SOURCES | 205167 |

### Feature Availability

| source | available_rows | missing_rows |
| --- | --- | --- |
| cftc_cot | 28800 | 176397 |
| flashalpha_gex | 0 | 205197 |
| fred | 205167 | 30 |
| lbma_calendar | 9217 | 195980 |
| wgc | 0 | 205197 |

## Mechanical Outcome Coverage

| mechanical_outcome | rows |
| --- | --- |
| NOT_EVALUATED | 131247 |
| NO_ENTRY | 44098 |
| SAME_BAR | 8686 |
| SL | 10504 |
| TIMEOUT | 1641 |
| TP | 9021 |

## Data Integrity

- No AI calls made: 0
- Unique keys: 205197
- Duplicate keys: 0
- First candle close: `2022-02-02T07:15:00+00:00`
- Last candle close: `2026-04-30T15:30:00+00:00`

## Known Limitations

- This is a deterministic pre-AI opportunity population, not a paid historical AI candidate replay.
- News/calendar blocking is not replayed here; external calendar/macro rows are attached as research features.
- FRED rows use current-vintage cached values with a conservative publication-time model; vintage-perfect ALFRED reconstruction is outside this offline artifact.
- If native H4 CSVs are absent, H4 is derived from local H1 bars and marked through `ohlcv_source__H4`.
- Mechanical outcomes are diagnostic OB-retest outcomes inferred from deterministic bias and local OHLCV; they are not AI trade outcomes.
