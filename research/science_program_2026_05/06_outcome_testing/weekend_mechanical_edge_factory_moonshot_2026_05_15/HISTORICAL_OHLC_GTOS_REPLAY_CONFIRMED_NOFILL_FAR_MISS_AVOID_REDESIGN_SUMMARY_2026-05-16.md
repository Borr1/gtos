# Historical OHLC GTOS Replay Confirmed No-Fill Far-Miss Avoid/Retest Redesign

Generated UTC: `2026-05-16T04:49:20Z`

This branch-local packet preserves the full confirmed no-fill friction denominator and routes far-miss and within-range miss rows into separate avoid/retest redesign and source-confidence ledgers.

## Counts

- `source_manifest_rows`: `16`
- `friction_branch_input_rows`: `7008`
- `friction_entry_input_rows`: `489`
- `friction_family_input_rows`: `192`
- `source_alignment_signature_input_rows`: `784`
- `source_alignment_cost_model_input_rows`: `196`
- `source_alignment_family_input_rows`: `160`
- `m1_spread_signature_input_rows`: `2256`
- `m1_spread_family_input_rows`: `480`
- `cost_sensitivity_family_input_rows`: `384`
- `cost_fill_status_input_rows`: `15328`
- `recovered_cross_family_input_rows`: `266`
- `path_ambiguity_input_rows`: `9185`
- `cost_split_ambiguity_input_rows`: `2847`
- `denominator_rows`: `7008`
- `in_scope_far_and_within_rows`: `6112`
- `avoid_filter_branch_rows`: `1984`
- `retest_redesign_branch_rows`: `6112`
- `source_confidence_branch_rows`: `6112`
- `family_synthesis_rows`: `192`
- `bucket_rows`: `60`
- `question_rows`: `6`

## In-Scope Miss Classes

- `FAR_MISS_BEYOND_ROLLING_MEDIAN_RANGE`: `1984`
- `WITHIN_RANGE_MISS_AT_OR_BELOW_ROLLING_MEDIAN_RANGE`: `4128`

## Claim Boundary

Historical OHLC GTOS replay confirmed no-fill far/within-range avoid and retest-redesign packet only. Rows preserve the confirmed no-fill denominator, split beyond-rolling-median-range misses and within-rolling-median-range misses as separate branch-control classes, and attach source-confidence, cost/fill/path family, source-alignment, M1 spread replay, and ambiguity context. No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, scoring, ranking, or live behavior change is claimed.

## Not Completion

This far/within-range confirmed no-fill avoid/retest-redesign packet does not complete the 60-hour moonshot objective.

No scoring, ranking, validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
