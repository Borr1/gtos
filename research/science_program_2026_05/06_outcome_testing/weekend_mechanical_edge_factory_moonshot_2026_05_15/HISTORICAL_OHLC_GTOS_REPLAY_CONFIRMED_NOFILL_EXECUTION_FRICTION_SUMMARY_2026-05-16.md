# Historical OHLC GTOS Replay Confirmed No-Fill Execution-Friction Control

Generated UTC: `2026-05-16T04:09:51Z`

This packet converts tick/M1-confirmed no-fill signatures into execution-friction and fillability branch-control descriptors while preserving the full unfilled signature denominator.

## Counts

- `bucket_rows`: `80`
- `confirmed_branch_rows`: `7008`
- `cost_status_input_rows`: `15328`
- `cross_family_input_rows`: `266`
- `cross_signature_input_rows`: `816`
- `entry_friction_rows`: `489`
- `family_rows`: `192`
- `full_signature_rows`: `7824`
- `nofill_context_input_rows`: `400`
- `path_ambiguity_input_rows`: `9185`
- `question_rows`: `6`
- `source_manifest_rows`: `9`
- `split_unfilled_input_rows`: `7824`
- `unfilled_entry_probe_input_rows`: `489`
- `unique_unfilled_entry_input_rows`: `489`
- `unfilled_signature_probe_input_rows`: `7824`

## Confirmed Distance Buckets

- `CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE`: `1984`
- `CONFIRMED_NOFILL_MISS_WITHIN_ROLLING_MEDIAN_RANGE`: `4128`
- `CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD`: `112`
- `CONFIRMED_NOFILL_STATUS_CONFLICTS_WITH_EXISTING_COST_THRESHOLD`: `784`

## Immediate Work

- Materialize near-miss entry-offset and market-entry branch controls from the full near-miss ledger.
- Convert far-miss retest-limit rows into avoid/retest-redesign controls and compare against market-proxy descriptors.
- Split confirmed no-fill branches by same-M15 ambiguity and exact-spread family context.
- Join execution-friction family rows into the cost/fill/path synthesis packet preserving all families.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
