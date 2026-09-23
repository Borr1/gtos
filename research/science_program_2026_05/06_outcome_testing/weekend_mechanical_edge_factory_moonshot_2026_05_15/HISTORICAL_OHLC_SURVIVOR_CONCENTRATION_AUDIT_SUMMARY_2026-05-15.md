# Historical OHLC Survivor Concentration Audit

Generated UTC: `2026-05-15T15:31:54Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT`

Survivor concentration and event-clustering audit only. This is not sealed validation, R/PnL, expectancy, fillability, live-readiness, or a promotion verdict.

## Counts

- `input_survivor_rows`: `44`
- `audit_rows`: `44`
- `event_cluster_rows`: `5492`
- `cluster_resilient_route_rows`: `20`

## Audit Buckets

- `CLUSTER_DUPLICATE_HEAVY`: `6`
- `CLUSTER_WEIGHTED_SIGN_FRAGILE`: `6`
- `DESCRIPTIVE_CLUSTER_AND_CONCENTRATION_RESILIENT`: `20`
- `TIME_SPLIT_SIGN_FRAGILE`: `12`

## Boundary

- Cluster-resilient rows remain research candidates, not trade rules.
- Cluster weighting removes adjacent-event inflation but does not provide sealed validation.
- No row includes spread, fillability, slippage, commission, or lifecycle truth.
