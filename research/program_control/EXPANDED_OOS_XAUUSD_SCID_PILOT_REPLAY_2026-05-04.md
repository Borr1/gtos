# Phase 3 Raw-OHLC Prequential Replay Report

**Created UTC:** 2026-05-03T20:45:12.850628+00:00
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
| ac19f0e227eafa5cba7b7328c835faa67ff7110d23191ee3330244caf133ee1e | 22856aa+dirty | LOCKED_HISTORICAL_RAW_OHLC_REPLAY | same_dataset_historical_raw_ohlc_diagnostic | 468202d16f337c5143be99c32bb6efc6948c5bfad012fb3e2a074b31e66578e5 |

## Run Scope

| source_scope | start | end | max_candles_per_symbol | max_events | include_blocked_controls | symbols | rows_replayed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDED_DIAGNOSTIC | 2026-04-15T13:00:00Z | 2026-04-17T17:00:00Z |  | 500 | True | GBPJPY,GBPUSD,NAS100,US30_cash,USDJPY,XAGUSD,XAUUSD | 76 |

## Data Inventory

| symbol | timeframe | status | path | rows | first | last | gap_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GBPJPY | M15 | MISSING |  | 0 |  |  |  |
| GBPJPY | M5 | MISSING |  | 0 |  |  |  |
| GBPJPY | M1 | MISSING |  | 0 |  |  |  |
| GBPJPY | H1 | MISSING |  | 0 |  |  |  |
| GBPJPY | H4 | MISSING |  | 0 |  |  |  |
| GBPJPY | D1 | MISSING |  | 0 |  |  |  |
| GBPUSD | M15 | MISSING |  | 0 |  |  |  |
| GBPUSD | M5 | MISSING |  | 0 |  |  |  |
| GBPUSD | M1 | MISSING |  | 0 |  |  |  |
| GBPUSD | H1 | MISSING |  | 0 |  |  |  |
| GBPUSD | H4 | MISSING |  | 0 |  |  |  |
| GBPUSD | D1 | MISSING |  | 0 |  |  |  |
| NAS100 | M15 | MISSING |  | 0 |  |  |  |
| NAS100 | M5 | MISSING |  | 0 |  |  |  |
| NAS100 | M1 | MISSING |  | 0 |  |  |  |
| NAS100 | H1 | MISSING |  | 0 |  |  |  |
| NAS100 | H4 | MISSING |  | 0 |  |  |  |
| NAS100 | D1 | MISSING |  | 0 |  |  |  |
| US30_cash | M15 | MISSING |  | 0 |  |  |  |
| US30_cash | M5 | MISSING |  | 0 |  |  |  |
| US30_cash | M1 | MISSING |  | 0 |  |  |  |
| US30_cash | H1 | MISSING |  | 0 |  |  |  |
| US30_cash | H4 | MISSING |  | 0 |  |  |  |
| US30_cash | D1 | MISSING |  | 0 |  |  |  |
| USDJPY | M15 | MISSING |  | 0 |  |  |  |
| USDJPY | M5 | MISSING |  | 0 |  |  |  |
| USDJPY | M1 | MISSING |  | 0 |  |  |  |
| USDJPY | H1 | MISSING |  | 0 |  |  |  |
| USDJPY | H4 | MISSING |  | 0 |  |  |  |
| USDJPY | D1 | MISSING |  | 0 |  |  |  |
| XAGUSD | M15 | MISSING |  | 0 |  |  |  |
| XAGUSD | M5 | MISSING |  | 0 |  |  |  |
| XAGUSD | M1 | MISSING |  | 0 |  |  |  |
| XAGUSD | H1 | MISSING |  | 0 |  |  |  |
| XAGUSD | H4 | MISSING |  | 0 |  |  |  |
| XAGUSD | D1 | MISSING |  | 0 |  |  |  |
| XAUUSD | M15 | AVAILABLE | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M15.csv | 11885 | 2025-10-28 14:15:00 | 2026-05-01 20:30:00 | 133 |
| XAUUSD | M5 | AVAILABLE | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M5.csv | 35618 | 2025-10-28 14:15:00 | 2026-05-01 20:40:00 | 145 |
| XAUUSD | M1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M1.csv | 177692 | 2025-10-28 14:19:00 | 2026-05-01 20:44:00 | 241 |
| XAUUSD | H1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_H1.csv | 2981 | 2025-10-28 14:00:00 | 2026-05-01 20:00:00 | 130 |
| XAUUSD | H4 | DERIVED_FROM_H1 | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_H1.csv |  | 2025-10-28 14:00:00 | 2026-05-01 20:00:00 | 130 |
| XAUUSD | D1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_D1.csv | 158 | 2025-10-28 00:00:00 | 2026-05-01 00:00:00 | 28 |

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
| 76 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 46 | 30 |

## Pre-AI Gate Counts

| SKIP_FIRST_NY_CANDLE | WOULD_SEND_AI |
| --- | --- |
| 3 | 73 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 30 | 10 | 0 | 0.0 |  |  |

## Action Outcomes

| NO_ENTRY | SAME_BAR |
| --- | --- |
| 10 | 20 |

## Scoring Exclusions

| mechanical_outcome_excluded |
| --- |
| 20 |

## Cohort Scores

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|ny\|bullish\|D1 | 30 | 10 | 0 | 0.0 |  |  | {'NO_ENTRY': 10, 'SAME_BAR': 20} |

## Period Scores

| period | actions_taken | resolved_r_n | sum_r | mean_r |
| --- | --- | --- | --- | --- |
| 2026-04 | 30 | 0 | 0.0 |  |

## Interpretation

- This is a raw-candle replay adapter validation, not a promotion dossier.
- The result can prioritize future research and catch leakage or data-coverage issues.
- Same-dataset historical positives or negatives cannot be called live alpha proof.
