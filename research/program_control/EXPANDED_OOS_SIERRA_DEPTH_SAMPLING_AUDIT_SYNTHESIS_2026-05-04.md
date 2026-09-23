# Expanded OOS Sierra Depth Sampling Audit Synthesis - 2026-05-04

**Status:** `SAMPLING_PARITY_AUDIT_COMPLETE`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; no live trading logic, prompts, risk, execution, safety, AI/API calls, or new Databento pulls.

## Purpose

The five-family Sierra depth batch found exact cached MBP10 parity for `YM` and `NQ`, near parity for `GC`, and mismatches for `6B` and `SI`. This audit checks whether the `6B` and `SI` mismatches are mainly sample-second coverage problems or deeper source/depth-definition problems.

## Result

| Family | Event | Source | Classification | Event15 Sierra | Event15 cached | Common | Common max delta | Status |
|---|---|---|---|---:|---:|---:|---:|---|
| GBPUSD/6B | `GBPUSD_20260417T0800_candidate_34` | `6BM26-CME` | `SAMPLING_CLOCK_MAJOR_CONTRIBUTOR` | 683 | 632 | 632 | 5 | sampling-policy alignment can unblock |
| XAGUSD/SI | `XAGUSD_20260501T0815_candidate_443` | `SIM26-COMEX` | `SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS` | 719 | 741 | 718 | 25 | source/depth-definition blocked |
| XAGUSD/SI alt | `XAGUSD_20260501T0815_candidate_443` | `SILM26-COMEX` | `SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS` | 722 | 741 | 679 | 25 | alternate local source not better |

## Interpretation

`6B` is not a hard source rejection. Cached Databento sample seconds are a subset of Sierra sample seconds for the registered event15 window. Masking Sierra to the cached Databento seconds reduces the max registered-field delta from `51` to `5` contracts. The practical next step is a sampling-policy alignment mode, not a new paid data pull.

`SI` remains blocked for depth equivalence. Common-second masking does not reduce the event15 max delta: Sierra `SIM26-COMEX` still has `-25` contracts of median total-depth10 versus cached `SI.v.0`, and median depth10 imbalance remains materially shifted. The alternate local `SILM26-COMEX` source is not better.

## Updated Batch Read

| Family | Status |
|---|---|
| `YM` | exact cached MBP10 parity |
| `NQ` | exact cached MBP10 parity |
| `GC` | near parity; small field deltas |
| `6B` | sampling policy alignment required |
| `SI` | source/depth-definition blocked |

Boundary: this is sampling/source parity only. It is not replay validation, OOS evidence, or a live-filter claim.
