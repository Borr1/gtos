# Sierra to Route C Date-Regime Split

Generated UTC: `2026-05-15T17:54:50Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: date-regime split only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `focus_replay_rows`: `1`
- `date_rows`: `75`
- `event_pair_rows`: `36`
- `date_shift_control_rows`: `14250`
- `bucket_rows`: `4`
- `question_rows`: `4`
- `intraday_offset_count_per_date`: `190`

## Buckets

- `DATE_HAS_ROUTE_ONLY`: `2`
- `DATE_HAS_SIERRA_ONLY`: `63`
- `DATE_INTRADAY_PLACEBO_COMPETES`: `5`
- `DATE_SHARED_NO_INTRADAY_COOCCURRENCE`: `5`

## Next Same-Resource Work

- Inspect every event pair on dates above intraday offsets.
- Convert date-local placebo-competing rows into generic timing/context rather than confirmation.
- Emit capture requirements for route-only dates.
