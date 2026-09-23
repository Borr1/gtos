# Tick M15 Target Control Triage

Generated UTC: `2026-05-15T16:01:51Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: development triage only. No validation, R/PnL, live-readiness, or promotion verdict.

## Counts

- Input control rows: `420`
- Triage rows: `420`
- Bucket rows: `4`
- Placebo-ready rows (all flagged_n >= 20): `92`

## Buckets

- `PLACEBO_READY_N_GE20_FLAT_OR_NEGATIVE_ABS_DELTA`: `24`
- `PLACEBO_READY_N_GE20_POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA`: `42`
- `PLACEBO_READY_N_GE20_POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA`: `26`
- `SMALL_N_LT20_NO_SIGNIFICANCE_CLAIM`: `328`

## Boundary

- `flagged_n >= 20` is only the minimum descriptive threshold for follow-up.
- Every input control row is preserved in the triage ledger.
- No row is promoted or ranked.
