# Phase 3 Raw-OHLC Prequential Replay Report

**Created UTC:** 2026-05-03T20:52:52.216551+00:00
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
| ac19f0e227eafa5cba7b7328c835faa67ff7110d23191ee3330244caf133ee1e | 22856aa+dirty | LOCKED_HISTORICAL_RAW_OHLC_REPLAY | same_dataset_historical_raw_ohlc_diagnostic | 4d65dd89311e04ca6259729034225fee40784519cb0dae11d5c469547709b099 |

## Run Scope

| source_scope | start | end | max_candles_per_symbol | max_events | include_blocked_controls | symbols | rows_replayed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BOUNDED_DIAGNOSTIC | 2026-04-15T00:00:00Z | 2026-04-17T17:00:00Z |  | 500 | True | GBPJPY,GBPUSD,NAS100,US30_cash,USDJPY,XAGUSD,XAUUSD | 72 |

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
| XAGUSD | M15 | AVAILABLE | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_M15.csv | 3357 | 2025-11-03 15:15:00 | 2026-05-01 20:45:00 | 1380 |
| XAGUSD | M5 | AVAILABLE | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_M5.csv | 5093 | 2025-11-03 15:20:00 | 2026-05-01 20:45:00 | 2931 |
| XAGUSD | M1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_M1.csv | 7214 | 2025-11-03 15:24:00 | 2026-05-01 20:49:00 | 5642 |
| XAGUSD | H1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_H1.csv | 1509 | 2025-11-03 15:00:00 | 2026-05-01 20:00:00 | 384 |
| XAGUSD | H4 | DERIVED_FROM_H1 | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_H1.csv |  | 2025-11-03 15:00:00 | 2026-05-01 20:00:00 | 384 |
| XAGUSD | D1 | AVAILABLE | data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504\XAGUSD_D1.csv | 136 | 2025-11-03 00:00:00 | 2026-05-01 00:00:00 | 28 |
| XAUUSD | M15 | MISSING |  | 0 |  |  |  |
| XAUUSD | M5 | MISSING |  | 0 |  |  |  |
| XAUUSD | M1 | MISSING |  | 0 |  |  |  |
| XAUUSD | H1 | MISSING |  | 0 |  |  |  |
| XAUUSD | H4 | MISSING |  | 0 |  |  |  |
| XAUUSD | D1 | MISSING |  | 0 |  |  |  |

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
| 72 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |

## Decision Counts

| SKIP | TAKE |
| --- | --- |
| 66 | 6 |

## Pre-AI Gate Counts

| WOULD_SEND_AI |
| --- |
| 72 |

## Score

| actions_taken | scoring_population_actions | resolved_r_n | sum_r | mean_r | win_rate |
| --- | --- | --- | --- | --- | --- |
| 6 | 6 | 4 | 6.0 | 1.5 | 1.0 |

## Action Outcomes

| NO_ENTRY | TP |
| --- | --- |
| 2 | 4 |

## Scoring Exclusions

|  |
|  |
|  |

## Cohort Scores

| cohort_key | actions_taken | population_actions | resolved_r_n | sum_r | mean_r | win_rate | outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| XAGUSD\|london\|bullish\|D1 | 6 | 6 | 4 | 6.0 | 1.5 | 1.0 | {'NO_ENTRY': 2, 'TP': 4} |

## Period Scores

| period | actions_taken | resolved_r_n | sum_r | mean_r |
| --- | --- | --- | --- | --- |
| 2026-04 | 6 | 4 | 6.0 | 1.5 |

## Interpretation

- This is a raw-candle replay adapter validation, not a promotion dossier.
- The result can prioritize future research and catch leakage or data-coverage issues.
- Same-dataset historical positives or negatives cannot be called live alpha proof.
