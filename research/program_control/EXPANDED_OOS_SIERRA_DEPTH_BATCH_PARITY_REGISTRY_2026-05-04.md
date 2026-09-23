# Expanded OOS Sierra Depth Batch Parity Registry - 2026-05-04

**Status:** `REGISTERED_PRE_RUN`  
**Batch:** `sierra_depth_first_wave_candidate_parity_batch_20260504`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; no live trading logic, prompts, risk, execution, safety, AI/API calls, or new Databento pulls.

## Selection Rule

First manifest `CANDIDATE` event per currently supported GTOS symbol/futures family with an existing local Sierra `.depth` file and cached MBP10 feature row.

## Registered Events

| GTOS | Event | Sierra source | Cached futures row | Tick size | Canonical close |
|---|---|---|---|---:|---|
| GBPUSD | `GBPUSD_20260417T0800_candidate_34` | `6BM26-CME` | `6B.v.0` | 0.0001 | `2026-04-17T08:00:00+00:00` |
| XAUUSD | `XAUUSD_20260417T1315_candidate_76` | `GCM26-COMEX` | `GC.v.0` | 0.1 | `2026-04-17T13:15:00+00:00` |
| US30_cash | `US30_cash_20260417T1545_candidate_110` | `YMM26-CBOT` | `YM.v.0` | 1.0 | `2026-04-17T15:45:00+00:00` |
| NAS100 | `NAS100_20260428T0730_candidate_141` | `NQM26-CME` | `NQ.v.0` | 0.25 | `2026-04-28T07:30:00+00:00` |
| XAGUSD | `XAGUSD_20260501T0815_candidate_443` | `SIM26-COMEX` | `SI.v.0` | 0.005 | `2026-05-01T08:15:00+00:00` |

Allowed feature windows are `pre60` and `event15`; `post15` and `post60` are forbidden for this batch.

Boundary: source/field parity and data availability only. This registry does not authorize OOS validation, replay claims, or promotion.
