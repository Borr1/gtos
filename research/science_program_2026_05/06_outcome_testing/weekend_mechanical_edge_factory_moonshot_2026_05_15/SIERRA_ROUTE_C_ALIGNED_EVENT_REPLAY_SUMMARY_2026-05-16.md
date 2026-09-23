# Sierra to Route C Aligned Event Replay

Generated UTC: `2026-05-15T17:46:44Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: event-level cooccurrence diagnostics only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `aligned_join_rows`: `60`
- `route_event_rows`: `2143`
- `sierra_event_rows`: `8239`
- `bucket_rows`: `2`
- `question_rows`: `2`

## Buckets

- `DATE_LEVEL_ONLY_NO_INTRADAY_COOCCURRENCE`: `11`
- `INTRADAY_COOCCURRENCE_PRESENT_DESCRIPTIVE`: `49`

## Next Same-Resource Work

- For intraday cooccurrence rows, build same-timestamp source-confirmation controls.
- For date-only rows, run date-shuffled controls before treating them as regime context.
- For no-overlap rows, emit capture/acquisition requirements instead of dropping the source family.
