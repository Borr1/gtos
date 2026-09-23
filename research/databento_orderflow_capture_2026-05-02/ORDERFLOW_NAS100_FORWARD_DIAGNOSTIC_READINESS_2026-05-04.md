# Orderflow NAS100 Forward Diagnostic Readiness - 2026-05-04

**Status:** `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Sources

- Databento MBP10
- Databento trades
- Databento MBO for targeted declared windows only
- Sierra .depth where local files are fresh
- MT5 tick features
- MT5/broker actual outcome labels

## Floors And Current Counts

| Metric | Value |
| --- | --- |
| floor_broker_actual_r_rows | 20 |
| floor_mbp10_candidate_rows | 30 |
| current_broker_actual_r_rows | 3 |
| current_declared_databento_requests | 5 |
| current_v2b_forward_pair_rows | 207 |

## Boundary

No live binary orderflow filter is created by this work.
