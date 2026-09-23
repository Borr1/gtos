# Expanded OOS Sierra Depth Batch Parity Status - 2026-05-04

**Status:** `BATCH_PARITY_STATUS_COMPLETE_MIXED`  
**Batch:** `sierra_depth_first_wave_candidate_parity_batch_20260504`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; no live trading logic, prompts, risk, execution, safety, AI/API calls, or new Databento pulls.

## Summary

The Sierra `.depth` extractor ran across five registered first-wave candidate windows with local Sierra depth and cached Databento MBP10 comparison rows.

| Result class | Count |
|---|---:|
| Registered events | 5 |
| Extracted events | 5 |
| `data_status=ok` | 5 |
| Exact cached MBP10 matches | 2 |
| Near matches with small field deltas | 1 |
| Mismatches requiring source/sampling audit | 2 |

## Rows

| GTOS | Futures | Event | Status | Sierra samples | Cached samples | Nonzero deltas | Max abs delta |
|---|---|---|---|---:|---:|---:|---:|
| GBPUSD | `6B.v.0` | `GBPUSD_20260417T0800_candidate_34` | `MISMATCH_SAMPLE_CLOCK_OR_SOURCE_DIFF` | 683 | 632 | 9 | 51 |
| XAUUSD | `GC.v.0` | `XAUUSD_20260417T1315_candidate_76` | `NEAR_MATCH_SMALL_FIELD_DELTAS` | 900 | 900 | 6 | 2 |
| US30_cash | `YM.v.0` | `US30_cash_20260417T1545_candidate_110` | `EXACT_CACHED_MBP10_MATCH` | 900 | 900 | 0 | 0 |
| NAS100 | `NQ.v.0` | `NAS100_20260428T0730_candidate_141` | `EXACT_CACHED_MBP10_MATCH` | 899 | 899 | 0 | 0 |
| XAGUSD | `SI.v.0` | `XAGUSD_20260501T0815_candidate_443` | `MISMATCH_SOURCE_OR_DEPTH_DEFINITION_AUDIT_REQUIRED` | 719 | 741 | 9 | 26 |

## Interpretation

The broad path works: local Sierra `.depth` can be parsed and converted into the registered MBP10-compatible depth fields across five families.

Parity is not universal. `YM` and `NQ` matched the cached MBP10 rows exactly. `GC` is close enough to flag as a small field-definition/sampling-difference audit, not a blocker for tooling. `6B` and `SI` need source/sampling definition audits before their depth fields are treated as Databento-equivalent.

This is a source/field parity and data-availability batch only. It is not OOS validation, replay performance, or a live-filter claim.
