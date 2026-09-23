# Sierra Depth Feature Extraction Status - 2026-05-04

**Scope:** research/tooling only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Event:** `XAGUSD_20260501T0815_candidate_443`
**Evidence class:** `FUTURES_PROXY_TRANSFER`

## Source

- Depth file: `C:\SierraChart\Data\MarketDepthData\SIM26-COMEX.2026-05-01.depth`
- Source symbol: `SIM26-COMEX`
- Futures symbol: `SI.v.0`
- Header magic/header/record/version: `0x44444353` / `64` / `24` / `1`
- File records: `1408284`
- Records processed until canonical close: `372298`
- Batches seen until canonical close: `222344`

## Feature Row

| Field | Value |
|---|---:|
| `pre60_median_total_depth10` | 31 |
| `pre60_median_depth10_imbalance` | -0.172414 |
| `pre60_thin_depth10_threshold` | 29 |
| `event15_median_total_depth10` | 31 |
| `event15_median_depth10_imbalance` | -0.172414 |
| `event15_thin_depth10_rate` | 0.226704 |
| `event15_median_max_bid_wall` | 2 |
| `event15_median_max_ask_wall` | 5 |
| `event15_median_near_far_ratio` | 0.409091 |
| `event15_mid_change_ticks` | -5.50003 |
| `event15_sample_count` | 719 |

## Cached Databento Field Comparison

- Status: `matched_cached_databento_feature_row`
- Boundary: `This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.`

| Field | Sierra | Databento | Sierra - Databento |
|---|---:|---:|---:|
| `pre60_median_total_depth10` | 31 | 57 | -26 |
| `event15_median_total_depth10` | 31 | 56 | -25 |
| `pre60_median_depth10_imbalance` | -0.172414 | 0 | -0.172414 |
| `event15_median_depth10_imbalance` | -0.172414 | 0.0188679 | -0.191282 |
| `event15_thin_depth10_rate` | 0.226704 | 0.236167 | -0.00946359 |
| `event15_median_max_bid_wall` | 2 | 5 | -3 |
| `event15_median_max_ask_wall` | 5 | 5 | 0 |
| `event15_median_near_far_ratio` | 0.409091 | 0.283019 | 0.126072 |
| `event15_mid_change_ticks` | -5.50003 | -5.5 | -3.1e-05 |
| `event15_sample_count` | 719 | 741 | -22 |

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
