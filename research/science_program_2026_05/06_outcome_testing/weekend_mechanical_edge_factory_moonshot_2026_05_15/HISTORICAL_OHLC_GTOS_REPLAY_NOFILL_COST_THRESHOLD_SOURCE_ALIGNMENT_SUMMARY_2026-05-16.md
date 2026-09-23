# Historical OHLC GTOS Replay No-Fill Cost-Threshold Source Alignment

Generated UTC: `2026-05-16T04:19:35Z`

This packet splits confirmed no-fill rows where M1 path reaches spread-adjusted effective thresholds while the original retest entry remains untouched.

## Counts

- `bucket_rows`: `40`
- `conflict_branch_input_rows`: `784`
- `conflict_entry_input_rows`: `49`
- `cost_model_alignment_rows`: `196`
- `cost_status_input_rows`: `15328`
- `entry_alignment_rows`: `49`
- `family_alignment_rows`: `160`
- `friction_branch_input_rows`: `7008`
- `friction_entry_input_rows`: `489`
- `friction_family_input_rows`: `192`
- `path_ambiguity_input_rows`: `9185`
- `question_rows`: `6`
- `signature_alignment_rows`: `784`
- `source_manifest_rows`: `6`

## Entry Alignment

- `CONFLICT_NOT_M1_PROXY_SOURCE_RECHECK`: `1`
- `M1_TOUCHES_ALL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED`: `47`
- `M1_TOUCHES_PARTIAL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED`: `1`

## Immediate Work

- Recompute M1 spread-adjusted fill path descriptors for all-spread-threshold-touch entries.
- Split partial threshold touches by cost model and threshold shift.
- Join source-alignment signatures to same-M15 ambiguity controls before target/stop descriptor claims.
- Feed source-alignment families into the cost/fill/path synthesis packet preserving all families.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
