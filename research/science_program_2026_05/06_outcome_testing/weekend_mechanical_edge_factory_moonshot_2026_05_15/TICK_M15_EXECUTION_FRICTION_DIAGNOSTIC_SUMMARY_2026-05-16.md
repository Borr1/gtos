# Tick M15 Execution/Friction Diagnostics

Generated UTC: `2026-05-15T16:32:40Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: spread/tick-velocity diagnostics only. No fill simulation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `residual_rows`: `18`
- `flagged_friction_row_rows`: `785`
- `bucket_rows`: `3`
- `question_rows`: `18`

## Buckets

- `FRICTION_MOVEMENT_DOMINATES_SPREAD_DIAGNOSTIC`: `10`
- `FRICTION_SPREAD_COMPETES_WITH_MOVEMENT`: `1`
- `FRICTION_WEAKER_THAN_DENOMINATOR`: `7`

## Boundary

- Movement-to-spread ratios are raw diagnostics, not trade returns.
- Entry geometry and path/fill ordering remain required before any strategy claim.
