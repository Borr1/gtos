# Sierra Depth Feature Extraction Status - 2026-05-04

**Scope:** research/tooling only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Event:** `GBPUSD_20260417T0800_candidate_34`
**Evidence class:** `FUTURES_PROXY_TRANSFER`

## Source

- Depth file: `C:\SierraChart\Data\MarketDepthData\6BM26-CME.2026-04-17.depth`
- Source symbol: `6BM26-CME`
- Futures symbol: `6B.v.0`
- Header magic/header/record/version: `0x44444353` / `64` / `24` / `1`
- File records: `1683222`
- Records processed until canonical close: `259797`
- Batches seen until canonical close: `235368`

## Feature Row

| Field | Value |
|---|---:|
| `pre60_median_total_depth10` | 1932 |
| `pre60_median_depth10_imbalance` | 0.0021254 |
| `pre60_thin_depth10_threshold` | 1878 |
| `event15_median_total_depth10` | 1883 |
| `event15_median_depth10_imbalance` | 0.0106114 |
| `event15_thin_depth10_rate` | 0.42899 |
| `event15_median_max_bid_wall` | 115 |
| `event15_median_max_ask_wall` | 110 |
| `event15_median_near_far_ratio` | 0.340126 |
| `event15_mid_change_ticks` | 4.49955 |
| `event15_sample_count` | 683 |

## Cached Databento Field Comparison

- Status: `matched_cached_databento_feature_row`
- Boundary: `This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.`

| Field | Sierra | Databento | Sierra - Databento |
|---|---:|---:|---:|
| `pre60_median_total_depth10` | 1932 | 1926 | 6 |
| `event15_median_total_depth10` | 1883 | 1877 | 6 |
| `pre60_median_depth10_imbalance` | 0.0021254 | 0.00238892 | -0.000263526 |
| `event15_median_depth10_imbalance` | 0.0106114 | 0.0103965 | 0.000214895 |
| `event15_thin_depth10_rate` | 0.42899 | 0.457278 | -0.0282887 |
| `event15_median_max_bid_wall` | 115 | 115 | 0 |
| `event15_median_max_ask_wall` | 110 | 109 | 1 |
| `event15_median_near_far_ratio` | 0.340126 | 0.332154 | 0.00797227 |
| `event15_mid_change_ticks` | 4.49955 | 4.5 | -0.00045 |
| `event15_sample_count` | 683 | 632 | 51 |

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
