# Sierra Depth Feature Extraction Status - 2026-05-04

**Scope:** research/tooling only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Event:** `XAUUSD_20260417T1315_candidate_76`
**Evidence class:** `FUTURES_PROXY_TRANSFER`

## Source

- Depth file: `C:\SierraChart\Data\MarketDepthData\GCM26-COMEX.2026-04-17.depth`
- Source symbol: `GCM26-COMEX`
- Futures symbol: `GC.v.0`
- Header magic/header/record/version: `0x44444353` / `64` / `24` / `1`
- File records: `4663601`
- Records processed until canonical close: `2065716`
- Batches seen until canonical close: `1747916`

## Feature Row

| Field | Value |
|---|---:|
| `pre60_median_total_depth10` | 54 |
| `pre60_median_depth10_imbalance` | -0.0588235 |
| `pre60_thin_depth10_threshold` | 45 |
| `event15_median_total_depth10` | 48 |
| `event15_median_depth10_imbalance` | -0.0805405 |
| `event15_thin_depth10_rate` | 0.36 |
| `event15_median_max_bid_wall` | 4 |
| `event15_median_max_ask_wall` | 5 |
| `event15_median_near_far_ratio` | 0.294118 |
| `event15_mid_change_ticks` | 364.5 |
| `event15_sample_count` | 900 |

## Cached Databento Field Comparison

- Status: `matched_cached_databento_feature_row`
- Boundary: `This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.`

| Field | Sierra | Databento | Sierra - Databento |
|---|---:|---:|---:|
| `pre60_median_total_depth10` | 54 | 52 | 2 |
| `event15_median_total_depth10` | 48 | 47 | 1 |
| `pre60_median_depth10_imbalance` | -0.0588235 | -0.0612245 | 0.00240096 |
| `event15_median_depth10_imbalance` | -0.0805405 | -0.0805405 | 0 |
| `event15_thin_depth10_rate` | 0.36 | 0.334444 | 0.0255556 |
| `event15_median_max_bid_wall` | 4 | 4 | 0 |
| `event15_median_max_ask_wall` | 5 | 5 | 0 |
| `event15_median_near_far_ratio` | 0.294118 | 0.3 | -0.00588235 |
| `event15_mid_change_ticks` | 364.5 | 364.5 | -0.0004883 |
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
