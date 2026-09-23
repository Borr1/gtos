# Sierra Depth Feature Extraction Status - 2026-05-04

**Scope:** research/tooling only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Event:** `NAS100_20260428T0730_candidate_141`
**Evidence class:** `FUTURES_PROXY_TRANSFER`

## Source

- Depth file: `C:\SierraChart\Data\MarketDepthData\NQM26-CME.2026-04-28.depth`
- Source symbol: `NQM26-CME`
- Futures symbol: `NQ.v.0`
- Header magic/header/record/version: `0x44444353` / `64` / `24` / `1`
- File records: `29763005`
- Records processed until canonical close: `2738849`
- Batches seen until canonical close: `2493477`

## Feature Row

| Field | Value |
|---|---:|
| `pre60_median_total_depth10` | 54 |
| `pre60_median_depth10_imbalance` | -0.0384615 |
| `pre60_thin_depth10_threshold` | 49 |
| `event15_median_total_depth10` | 54 |
| `event15_median_depth10_imbalance` | -0.0188679 |
| `event15_thin_depth10_rate` | 0.193548 |
| `event15_median_max_bid_wall` | 5 |
| `event15_median_max_ask_wall` | 5 |
| `event15_median_near_far_ratio` | 0.315789 |
| `event15_mid_change_ticks` | -41.5 |
| `event15_sample_count` | 899 |

## Cached Databento Field Comparison

- Status: `matched_cached_databento_feature_row`
- Boundary: `This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.`

| Field | Sierra | Databento | Sierra - Databento |
|---|---:|---:|---:|
| `pre60_median_total_depth10` | 54 | 54 | 0 |
| `event15_median_total_depth10` | 54 | 54 | 0 |
| `pre60_median_depth10_imbalance` | -0.0384615 | -0.0384615 | 0 |
| `event15_median_depth10_imbalance` | -0.0188679 | -0.0188679 | 0 |
| `event15_thin_depth10_rate` | 0.193548 | 0.193548 | 0 |
| `event15_median_max_bid_wall` | 5 | 5 | 0 |
| `event15_median_max_ask_wall` | 5 | 5 | 0 |
| `event15_median_near_far_ratio` | 0.315789 | 0.315789 | 0 |
| `event15_mid_change_ticks` | -41.5 | -41.5 | 0 |
| `event15_sample_count` | 899 | 899 | 0 |

## Synthesis

- Status: `DEPTH_FEATURE_EXTRACTION_COMPLETE`
- No-leak status: `PASS_PRE_DECISION_WINDOWS_ONLY`
- Sierra .depth is parsed into the registered ladder-depth feature family.
- Feature windows are pre-decision only: pre60 and event15 ending at the canonical M15 close.
- The comparison to cached Databento, when present, is source/field parity only and not a promotion or validation claim.

## Remaining Blockers

- One event window does not establish source equivalence.
- Sierra depth records are source/proxy transfer and not MT5 broker execution truth.
- Actual broker-R label coverage remains sparse for orderflow promotion.
