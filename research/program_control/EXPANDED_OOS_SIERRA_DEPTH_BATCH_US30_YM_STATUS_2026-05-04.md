# Sierra Depth Feature Extraction Status - 2026-05-04

**Scope:** research/tooling only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Event:** `US30_cash_20260417T1545_candidate_110`
**Evidence class:** `FUTURES_PROXY_TRANSFER`

## Source

- Depth file: `C:\SierraChart\Data\MarketDepthData\YMM26-CBOT.2026-04-17.depth`
- Source symbol: `YMM26-CBOT`
- Futures symbol: `YM.v.0`
- Header magic/header/record/version: `0x44444353` / `64` / `24` / `1`
- File records: `3784052`
- Records processed until canonical close: `2385547`
- Batches seen until canonical close: `2171164`

## Feature Row

| Field | Value |
|---|---:|
| `pre60_median_total_depth10` | 107 |
| `pre60_median_depth10_imbalance` | -0.0769231 |
| `pre60_thin_depth10_threshold` | 100 |
| `event15_median_total_depth10` | 105.5 |
| `event15_median_depth10_imbalance` | -0.0654206 |
| `event15_thin_depth10_rate` | 0.217778 |
| `event15_median_max_bid_wall` | 8 |
| `event15_median_max_ask_wall` | 8 |
| `event15_median_near_far_ratio` | 0.337349 |
| `event15_mid_change_ticks` | 13 |
| `event15_sample_count` | 900 |

## Cached Databento Field Comparison

- Status: `matched_cached_databento_feature_row`
- Boundary: `This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.`

| Field | Sierra | Databento | Sierra - Databento |
|---|---:|---:|---:|
| `pre60_median_total_depth10` | 107 | 107 | 0 |
| `event15_median_total_depth10` | 105.5 | 105.5 | 0 |
| `pre60_median_depth10_imbalance` | -0.0769231 | -0.0769231 | 0 |
| `event15_median_depth10_imbalance` | -0.0654206 | -0.0654206 | 0 |
| `event15_thin_depth10_rate` | 0.217778 | 0.217778 | 0 |
| `event15_median_max_bid_wall` | 8 | 8 | 0 |
| `event15_median_max_ask_wall` | 8 | 8 | 0 |
| `event15_median_near_far_ratio` | 0.337349 | 0.337349 | 0 |
| `event15_mid_change_ticks` | 13 | 13 | 0 |
| `event15_sample_count` | 900 | 900 | 0 |

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
