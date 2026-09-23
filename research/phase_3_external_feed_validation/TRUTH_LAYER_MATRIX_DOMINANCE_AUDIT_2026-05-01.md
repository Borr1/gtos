# Phase 3 Truth-Layer Matrix Dominance Audit

**Created UTC:** 2026-05-01T10:06:00.857219+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Spec:** `research\phase_3_external_feed_validation\TRUTH_LAYER_MATRIX_FOLLOWUP_HYPOTHESES_V1.json`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- This audit exists to decide what should be prioritized for the next raw-OHLC replay session.
- DSR, PBO, effective_N, and prospective confirmation are not computed here.

## Data Integrity

| rows_scanned | unique_keys | duplicate_keys | ai_attempted_rows | ai_call_count_sum |
| --- | --- | --- | --- | --- |
| 205197 | 205197 | 0 | 0 | 0 |

## Families

| family_id | cohort_count | resolved_r_n | sum_r | mean_r | cohorts_clear | cohorts_blocked | family_status | blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| truth_layer_dominance_watchlist_v1 | 3 | 1262 | 575.9903 | 0.456411 | 0 | 3 | BLOCKED_DIAGNOSTIC_ONLY | single_year_dominance |
| truth_layer_non_primary_strong_leads_v1 | 3 | 655 | 264.146 | 0.403276 | 3 | 0 | CLEAR_DIAGNOSTIC_ONLY |  |

## Cohort Audit

| cohort_key | family_id | resolved_r_n | mean_r | win_rate | valid_year_folds | positive_valid_year_folds | top_year | top_year_resolved_share | top_year_excluded_mean_r | top_month | top_month_resolved_share | audit_status | audit_blockers | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|london\|bearish\|D1 | truth_layer_non_primary_strong_leads_v1 | 154 | 0.428571 | 0.571429 | 3 | 3 | 2022 | 0.337662 | 0.642157 | 2022-11 | 0.220779 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY | [] | eligible raw-OHLC adapter target; still not promotion proof |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | truth_layer_non_primary_strong_leads_v1 | 252 | 0.387224 | 0.563492 | 4 | 4 | 2023 | 0.34127 | 0.32478 | 2022-11 | 0.15873 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY | [] | eligible raw-OHLC adapter target; still not promotion proof |
| XAGUSD\|london\|bullish\|D1 | truth_layer_non_primary_strong_leads_v1 | 249 | 0.403878 | 0.558233 | 3 | 3 | 2025 | 0.35743 | 0.354791 | 2023-04 | 0.228916 | CLEARED_FOR_RAW_REPLAY_PRIORITY_DIAGNOSTIC_ONLY | [] | eligible raw-OHLC adapter target; still not promotion proof |
| NAS100\|ny\|bullish\|D1 | truth_layer_dominance_watchlist_v1 | 631 | 0.373786 | 0.545166 | 3 | 3 | 2025 | 0.581616 | 0.228632 | 2023-06 | 0.123613 | BLOCKED_single_year_dominance | ['single_year_dominance'] | do not deepen until blockers are explained or separate protocol is registered |
| US30_cash\|ny\|bullish\|H4+H1_consensus | truth_layer_dominance_watchlist_v1 | 320 | 0.508648 | 0.590625 | 3 | 3 | 2024 | 0.45625 | 0.513014 | 2024-08 | 0.128125 | BLOCKED_single_year_dominance | ['single_year_dominance'] | do not deepen until blockers are explained or separate protocol is registered |
| XAUUSD\|ny\|bullish\|D1 | truth_layer_dominance_watchlist_v1 | 311 | 0.570303 | 0.62701 | 3 | 3 | 2025 | 0.453376 | 0.622731 | 2025-10 | 0.157556 | BLOCKED_single_year_dominance | ['single_year_dominance'] | do not deepen until blockers are explained or separate protocol is registered |

## Year Folds

| cohort_key | year | population_rows | resolved_r_n | resolved_share | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|london\|bearish\|D1 | 2022 | 105 | 52 | 0.337662 | 0.5 | 0.009615 | 0.403846 | 21 | 31 | 0 | 53 |
| USDJPY\|london\|bearish\|D1 | 2023 | 39 | 36 | 0.233766 | 4.0 | 0.111111 | 0.444444 | 16 | 20 | 0 | 3 |
| USDJPY\|london\|bearish\|D1 | 2024 | 94 | 17 | 0.11039 | 8.0 | 0.470588 | 0.588235 | 10 | 7 | 0 | 77 |
| USDJPY\|london\|bearish\|D1 | 2025 | 166 | 49 | 0.318182 | 53.5 | 1.091837 | 0.836735 | 41 | 8 | 0 | 117 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2022 | 94 | 59 | 0.234127 | 13.8444 | 0.234651 | 0.542373 | 22 | 25 | 12 | 35 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2023 | 188 | 86 | 0.34127 | 43.6671 | 0.507757 | 0.593023 | 51 | 35 | 0 | 102 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2024 | 95 | 55 | 0.218254 | 27.069 | 0.492164 | 0.6 | 30 | 18 | 7 | 40 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2025 | 81 | 52 | 0.206349 | 13.0 | 0.25 | 0.5 | 26 | 26 | 0 | 29 |
| XAGUSD\|london\|bullish\|D1 | 2022 | 73 | 73 | 0.293173 | 32.0 | 0.438356 | 0.575342 | 42 | 31 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2023 | 75 | 75 | 0.301205 | 29.2665 | 0.39022 | 0.546667 | 41 | 34 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2024 | 12 | 12 | 0.048193 | -4.5 | -0.375 | 0.25 | 3 | 9 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2025 | 89 | 89 | 0.35743 | 43.799 | 0.492124 | 0.595506 | 53 | 36 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2023 | 144 | 144 | 0.228209 | 72.6872 | 0.504772 | 0.583333 | 84 | 60 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2024 | 99 | 99 | 0.156894 | 6.1716 | 0.062339 | 0.424242 | 42 | 57 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2025 | 367 | 367 | 0.581616 | 175.5 | 0.478202 | 0.591281 | 217 | 150 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2026 | 21 | 21 | 0.033281 | -18.5 | -0.880952 | 0.047619 | 1 | 20 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2023 | 91 | 91 | 0.284375 | 56.5 | 0.620879 | 0.648352 | 59 | 32 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2024 | 146 | 146 | 0.45625 | 73.5029 | 0.503445 | 0.575342 | 84 | 62 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2025 | 58 | 58 | 0.18125 | 55.2644 | 0.952834 | 0.775862 | 45 | 13 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2026 | 25 | 25 | 0.078125 | -22.5 | -0.9 | 0.04 | 1 | 24 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2022 | 27 | 27 | 0.086817 | 13.8642 | 0.513489 | 0.592593 | 16 | 11 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2023 | 37 | 37 | 0.118971 | 3.0 | 0.081081 | 0.432432 | 16 | 21 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2024 | 26 | 26 | 0.083601 | 9.0 | 0.346154 | 0.538462 | 14 | 12 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2025 | 141 | 141 | 0.453376 | 71.5 | 0.507092 | 0.602837 | 85 | 56 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2026 | 80 | 80 | 0.257235 | 80.0 | 1.0 | 0.8 | 64 | 16 | 0 | 0 |

## Top Month Concentration

| cohort_key | month | population_rows | resolved_r_n | resolved_share | sum_r | mean_r | win_rate | tp | sl | timeout | no_entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY\|london\|bearish\|D1 | 2022-11 | 60 | 34 | 0.220779 | 16.0 | 0.470588 | 0.588235 | 20 | 14 | 0 | 26 |
| USDJPY\|london\|bearish\|D1 | 2025-02 | 117 | 31 | 0.201299 | 41.5 | 1.33871 | 0.935484 | 29 | 2 | 0 | 86 |
| USDJPY\|london\|bearish\|D1 | 2023-12 | 20 | 20 | 0.12987 | -2.5 | -0.125 | 0.35 | 7 | 13 | 0 | 0 |
| USDJPY\|london\|bearish\|D1 | 2023-02 | 19 | 16 | 0.103896 | 6.5 | 0.40625 | 0.5625 | 9 | 7 | 0 | 3 |
| USDJPY\|london\|bearish\|D1 | 2022-12 | 39 | 15 | 0.097403 | -12.5 | -0.833333 | 0.066667 | 1 | 14 | 0 | 24 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2022-11 | 70 | 40 | 0.15873 | 15.0 | 0.375 | 0.55 | 22 | 18 | 0 | 30 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2023-11 | 48 | 37 | 0.146825 | 25.5 | 0.689189 | 0.675676 | 25 | 12 | 0 | 11 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2024-12 | 36 | 26 | 0.103175 | 4.0 | 0.153846 | 0.461538 | 12 | 14 | 0 | 10 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2023-07 | 68 | 25 | 0.099206 | 29.1562 | 1.166248 | 0.84 | 21 | 4 | 0 | 43 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 2022-05 | 24 | 19 | 0.075397 | -1.1556 | -0.060821 | 0.526316 | 0 | 7 | 12 | 5 |
| XAGUSD\|london\|bullish\|D1 | 2023-04 | 57 | 57 | 0.228916 | 7.2665 | 0.127482 | 0.438596 | 25 | 32 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2022-12 | 38 | 38 | 0.15261 | -3.0 | -0.078947 | 0.368421 | 14 | 24 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2025-09 | 34 | 34 | 0.136546 | 18.799 | 0.552912 | 0.617647 | 21 | 13 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2025-06 | 17 | 17 | 0.068273 | 18.0 | 1.058824 | 0.823529 | 14 | 3 | 0 | 0 |
| XAGUSD\|london\|bullish\|D1 | 2022-03 | 14 | 14 | 0.056225 | 21.0 | 1.5 | 1.0 | 14 | 0 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2023-06 | 78 | 78 | 0.123613 | 54.3972 | 0.6974 | 0.653846 | 51 | 27 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2025-07 | 78 | 78 | 0.123613 | 57.0 | 0.730769 | 0.692308 | 54 | 24 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2025-06 | 66 | 66 | 0.104596 | 61.5 | 0.931818 | 0.772727 | 51 | 15 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2025-05 | 52 | 52 | 0.082409 | -19.5 | -0.375 | 0.25 | 13 | 39 | 0 | 0 |
| NAS100\|ny\|bullish\|D1 | 2025-10 | 44 | 44 | 0.069731 | 33.5 | 0.761364 | 0.704545 | 31 | 13 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2024-08 | 41 | 41 | 0.128125 | 46.0029 | 1.122022 | 0.756098 | 31 | 10 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2023-12 | 27 | 27 | 0.084375 | 13.0 | 0.481481 | 0.592593 | 16 | 11 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2024-05 | 27 | 27 | 0.084375 | 10.5 | 0.388889 | 0.555556 | 15 | 12 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2024-09 | 27 | 27 | 0.084375 | 18.0 | 0.666667 | 0.666667 | 18 | 9 | 0 | 0 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 2026-04 | 25 | 25 | 0.078125 | -22.5 | -0.9 | 0.04 | 1 | 24 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2025-10 | 49 | 49 | 0.157556 | 6.0 | 0.122449 | 0.44898 | 22 | 27 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2026-01 | 48 | 48 | 0.154341 | 62.0 | 1.291667 | 0.916667 | 44 | 4 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2025-12 | 29 | 29 | 0.093248 | 21.0 | 0.724138 | 0.689655 | 20 | 9 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2023-04 | 22 | 22 | 0.07074 | 18.0 | 0.818182 | 0.727273 | 16 | 6 | 0 | 0 |
| XAUUSD\|ny\|bullish\|D1 | 2025-04 | 20 | 20 | 0.064309 | 5.0 | 0.25 | 0.5 | 10 | 10 | 0 | 0 |

## Next Session Recommendation

- Start raw-OHLC replay adapter with cleared diagnostic targets: USDJPY|london|bearish|D1, USDJPY|tokyo|bearish|H4+H1_consensus, XAGUSD|london|bullish|D1
- Keep dominance-watchlist names blocked until a specific dominance/fold-rescue protocol is registered: NAS100|ny|bullish|D1, US30_cash|ny|bullish|H4+H1_consensus, XAUUSD|ny|bullish|D1
- Carry NO_PROMOTION_VERDICT language into the fresh session.
