# Expanded OOS Sierra Depth Parity Checkpoint - 2026-05-04

**Status:** `SIERRA_DEPTH_PARITY_PILOT_COMPLETE`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; no live trading logic, prompts, risk, execution, safety, AI/API calls, or new Databento pulls.

## Registered Pilot

| Field | Value |
|---|---|
| Batch | `sierra_depth_nq_nas100_parity_pilot_20260504` |
| Event | `NAS100_20260428T0730_candidate_141` |
| GTOS symbol | `NAS100` |
| Sierra source | `NQM26-CME` |
| Futures symbol | `NQ.v.0` |
| Canonical close | `2026-04-28T07:30:00+00:00` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Allowed windows | `pre60`, `event15` |
| Forbidden windows | `post15`, `post60` |

## Result

The Sierra `.depth` parser/extractor is now implemented and tested in `scripts/extract_sierra_depth_features.py`.

The registered NQ/NAS100 pilot extracted `899` event15 samples from `C:/SierraChart/Data/MarketDepthData/NQM26-CME.2026-04-28.depth`, processing `2,738,849` records and `2,493,477` batches up to the canonical close.

The cached Databento MBP10 comparison row matched exactly on every registered comparison field:

| Field | Sierra - cached Databento |
|---|---:|
| `pre60_median_total_depth10` | 0 |
| `pre60_median_depth10_imbalance` | 0 |
| `event15_median_total_depth10` | 0 |
| `event15_median_depth10_imbalance` | 0 |
| `event15_thin_depth10_rate` | 0 |
| `event15_median_max_bid_wall` | 0 |
| `event15_median_max_ask_wall` | 0 |
| `event15_median_near_far_ratio` | 0 |
| `event15_mid_change_ticks` | 0 |
| `event15_sample_count` | 0 |

## Boundary

This closes the `.depth` extractor/parity blocker for one registered NQ window only. It does not authorize broad Sierra depth equivalence claims or any promotion claim.

Next work should batch this extractor across registered first-wave depth families, emit family-level status tables, and keep every downstream synthesis at `NO_PROMOTION_VERDICT` until replay and label coverage are complete.
