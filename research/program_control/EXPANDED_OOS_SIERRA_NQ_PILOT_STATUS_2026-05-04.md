# Expanded OOS Sierra NQ Pilot Status - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch registry:** `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_BATCH_REGISTRY_2026-05-04.json`  

## Direct Result

The first converted-source deterministic replay path is working.

Sierra `NQM26-CME.scid` was converted into a GTOS-compatible OHLCV root for `NAS100`, then consumed by `scripts/run_raw_ohlc_prequential_replay.py` through `--data-dir` without modifying production replay, live trading logic, prompts, risk settings, execution behavior, or safety gates.

## Conversion Evidence

| Field | Value |
| --- | --- |
| Converter | `scripts/convert_sierra_scid_to_ohlcv.py` |
| Manifest | `data/sierra_ohlcv_roots/sierra_nq_to_nas100_pilot_20260504/manifest.json` |
| Source | `C:\SierraChart\Data\NQM26-CME.scid` |
| Output file symbol | `NAS100` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Raw records read | `16,876,939` |
| Invalid records skipped | `0` |
| Timeframes written | `M1`, `M5`, `M15`, `H1`, `D1` |

| Timeframe | Rows | First | Last |
| --- | ---: | --- | --- |
| M1 | 70,210 | 2025-10-29 22:43:00 | 2026-05-01 20:59:00 |
| M5 | 18,877 | 2025-10-29 22:40:00 | 2026-05-01 20:55:00 |
| M15 | 7,683 | 2025-10-29 22:30:00 | 2026-05-01 20:45:00 |
| H1 | 2,340 | 2025-10-29 22:00:00 | 2026-05-01 20:00:00 |
| D1 | 153 | 2025-10-29 00:00:00 | 2026-05-01 00:00:00 |

## Replay Evidence

| Field | Value |
| --- | --- |
| Replay tool | `scripts/run_raw_ohlc_prequential_replay.py` |
| Summary | `data/external/validation/expanded_oos_full_unblocking/sierra_nq_to_nas100_pilot_20260504/raw_ohlc_prequential_replay_20260503T202915Z.json` |
| Event log | `data/external/validation/expanded_oos_full_unblocking/sierra_nq_to_nas100_pilot_20260504/raw_ohlc_prequential_events_20260503T202913Z.jsonl` |
| Report | `research/program_control/EXPANDED_OOS_SIERRA_NQ_PILOT_REPLAY_2026-05-04.md` |
| Opened replay slice | `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` |
| Rows replayed | `76` |
| Actions taken | `0` |
| Resolved R rows | `0` |
| Integrity status | `PASS` |
| AI/API calls | `0` |

Guardrails:

| Check | Count |
| --- | ---: |
| Future candle exposure violations | 0 |
| HTF as-of violations | 0 |
| Forbidden observation violations | 0 |
| AI attempted rows | 0 |
| AI call count sum | 0 |

## Label Status

Status: `REPLAY_PATH_WORKS_NO_FROZEN_CANDIDATE_MATCHES`.

The converted NQ pilot rows produced NAS100 NY `WOULD_SEND_AI` events, but the raw cohort was `NAS100|ny|bullish|H4+H1_consensus`. The current frozen blocked-control cohort in `RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json` is `NAS100|ny|bullish|D1`, so all `76` events were correctly skipped as `raw_cohort_non_match`.

This means:

- `actual_broker_r`: not applicable; this is futures-proxy transfer evidence.
- `path_synthetic_r`: not computable in this slice because zero actions were taken.
- `fill_no_fill`: not computable in this slice because zero actions were taken.
- Candidate survival: no survival claim. This is adapter/replay-path evidence only.

## Slice Ledger

| Slice | Status | Holdout impact |
| --- | --- | --- |
| Full converted NQ source file | `CONVERTED_FOR_LOOKBACK` | not outcome-opened by conversion alone |
| `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` | `BURNED_FOR_NQ_PILOT` | cannot be reused as pure OOS for NQ pilot claims |
| `2026-04-20T00:00:00Z` to `2026-05-01T21:00:00Z` | `RESERVED_NOT_OPENED_BY_PILOT` | still reserved |

## Costs

| Source | Incremental cost |
| --- | ---: |
| MT5 | $0 |
| Sierra local parsing | $0 |
| Databento | $0 |
| AI/API | $0 |

## Interpretation

- The first missing-adapter blocker is unblocked for Sierra `.scid` to OHLCV replay roots.
- The bounded replay path is verified, but the opened slice produced no frozen candidate matches.
- No validation, promotion, or live-trading change is implied.
- Next work should broaden conversion/status coverage across the first-wave families and add replay or label-status evidence for each feasible family.
