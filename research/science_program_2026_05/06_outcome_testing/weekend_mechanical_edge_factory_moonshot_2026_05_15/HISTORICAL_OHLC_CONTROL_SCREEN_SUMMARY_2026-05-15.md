# Historical OHLC Same-Context Control Screen

Generated UTC: `2026-05-15T15:25:28Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_SAME_CONTEXT_CONTROL_SCREEN`

Same-symbol/session/horizon control screen only. This is not sealed validation, strategy performance, expectancy, live-readiness, or a promotion verdict.

## Counts

- `baseline_rows`: `285`
- `event_groups`: `2565`
- `control_screen_rows`: `2565`
- `bucket_summary_rows`: `202`
- `route_queue_rows`: `477`

## Screen Buckets

- `MATERIAL_CONTRACTION_AFTER_NEUTRAL_PRIMITIVE`: `166`
- `MATERIAL_EXPANSION_AFTER_NEUTRAL_PRIMITIVE`: `8`
- `MATERIAL_MIXED_DIRECTIONAL_CONTROL_DELTA`: `367`
- `MATERIAL_NEGATIVE_DIRECTIONAL_CONTROL_DELTA`: `712`
- `MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA`: `469`
- `SMALL_OR_CONCENTRATED_SAMPLE`: `843`

## Next Controls

- route-queue rows require neighbor-window placebo and time-block shuffled-label controls
- directional movement deltas are not R, PnL, expectancy, fillability, or live validation
- neutral compression rows are movement-volatility descriptors only
- no row may be promoted without duplicate/concentration, split, and cost/fill controls
