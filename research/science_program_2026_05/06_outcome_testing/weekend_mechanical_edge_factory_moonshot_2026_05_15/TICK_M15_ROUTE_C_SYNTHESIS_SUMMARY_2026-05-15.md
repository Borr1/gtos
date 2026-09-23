# Tick M15 Route C Synthesis

Generated UTC: `2026-05-15T16:07:07Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: Route C development synthesis only. No validation, R/PnL, live-readiness, or promotion verdict.

## Counts

- Tick parquet files: `114`
- Tick rows from parquet metadata: `39003954`
- M15 primitive event rows: `8977`
- Target event-horizon rows: `22229`
- Placebo control rows: `92`
- Residual descriptor rows: `18`
- Residual blocker rows: `108`

## Placebo Buckets

- `DESCRIPTIVE_RESIDUAL_AFTER_NEIGHBOR_AND_ROTATED_PLACEBO`: `18`
- `EXPLAINED_OR_WEAKENED_BY_PLACEBO`: `12`
- `MIXED_AFTER_PLACEBO`: `62`

## Boundary

- Residual rows are follow-up descriptors, not ranked candidates.
- Every residual row has open blockers for permutation, concentration, sealed/future, entry geometry, cost, and broker-proxy limitations.
