# Expanded OOS Sierra Depth Parity NQ Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch:** `sierra_depth_nq_nas100_parity_pilot_20260504`  

## Registered Question

Can local Sierra `.depth` files be decoded into the same pre-decision ladder-depth feature family used by cached Databento MBP-10 diagnostics for a registered NAS100/NQ event window?

## Registered Window

| Field | Value |
|---|---|
| Event ID | `NAS100_20260428T0730_candidate_141` |
| GTOS symbol | `NAS100` |
| Sierra source | `NQM26-CME` |
| Futures proxy | `NQ.v.0` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Canonical close | `2026-04-28T07:30:00+00:00` |
| Feature windows | `pre60`, `event15` |
| Forbidden windows | `post15`, `post60` |
| Sierra depth file | `C:/SierraChart/Data/MarketDepthData/NQM26-CME.2026-04-28.depth` |
| Cached Databento comparison | `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FEATURES_2026-05-02.json` |

## Boundary

This run is a parser/field-parity and source-transfer availability test. It cannot validate broker execution truth, tune a live filter, or promote orderflow/depth behavior.
