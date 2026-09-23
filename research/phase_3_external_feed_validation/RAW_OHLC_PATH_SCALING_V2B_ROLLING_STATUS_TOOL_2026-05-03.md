# V2b OB-Boundary Rolling Status Tool

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation status: `BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS`

## Synthesis

V2b remains unvalidated because post-cutoff OB-boundary/J46 rows exist, but no resolved STRUCT_OB_BOUNDARY_V2/J46 pairs exist after the registered cutoff.

## Scope Counters

| Metric | Value |
| --- | --- |
| total_rows_seen | 264 |
| wanted_variant_rows_seen | 110 |
| rows_after_cutoff | 264 |
| wanted_rows_after_cutoff | 110 |
| wanted_resolved_rows_after_cutoff | 0 |
| rows_rejected_at_or_before_cutoff | 0 |
| rows_missing_candle_close | 0 |
| rows_missing_net_r | 110 |
| first_candle_close_utc | 2026-05-01T00:15:00+00:00 |
| last_candle_close_utc | 2026-05-01T09:30:00+00:00 |
| first_prospective_candle_close_utc | 2026-05-01T00:15:00+00:00 |
| last_prospective_candle_close_utc | 2026-05-01T09:30:00+00:00 |

## Rolling Status Ladder

| Step | Status | Passed | Count | Metrics |
| --- | --- | --- | --- | --- |
| post_cutoff_rows | PASS | True | 264 | n/a |
| wanted_post_cutoff_rows | PASS | True | 110 | n/a |
| resolved_pairs | BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS | False | 0 | n/a |
| sample_floor | NOT_EVALUABLE_NO_RESOLVED_PAIRS | n/a | n/a | {} |

## Missing Net-R Diagnostics

| Metric | Value |
| --- | --- |
| rows_missing_net_r | 110 |
| by_variant | {"J46_J49_ONLY": 22, "PATH_LOCK_HALF_GAIN_V0": 22, "STRUCT_FVG_MID_EDGE_V2": 22, "STRUCT_OB_BOUNDARY_V2": 22, "STRUCT_SWING_PROTECTED_V2": 22} |
| by_outcome | {"SETUP_NOT_REFINABLE": 110} |
| by_skip_reason | {"NO_BEARISH_OB": 110} |
| by_fallback_reason | {"none": 110} |
| by_selected_timeframe | {"M15": 110} |
| by_reason | {"outcome=SETUP_NOT_REFINABLE\|skip=NO_BEARISH_OB\|fallback=none": 110} |

## Lower-Timeframe Availability

| Metric | Value |
| --- | --- |
| selected_timeframe_counts_after_cutoff | {"M15": 264} |
| wanted_selected_timeframe_counts_after_cutoff | {"M15": 110} |
| wanted_resolved_selected_timeframe_counts_after_cutoff | {} |
| wanted_lower_tf_rows_after_cutoff | 0 |
| wanted_lower_tf_rate_after_cutoff | 0.000000 |
| wanted_resolved_lower_tf_rows_after_cutoff | 0 |
| wanted_resolved_lower_tf_rate_after_cutoff | n/a |

## Pairwise Candidate Versus Comparators

| Comparator | paired n | mean delta | sum delta | candidate better | comparator better |
| --- | --- | --- | --- | --- | --- |
| J46_J49_ONLY | 0 | n/a | 0.000000 | 0 | 0 |
| STRUCT_SWING_PROTECTED_V2 | 0 | n/a | 0.000000 | 0 | 0 |
| STRUCT_FVG_MID_EDGE_V2 | 0 | n/a | 0.000000 | 0 | 0 |
| PATH_LOCK_HALF_GAIN_V0 | 0 | n/a | 0.000000 | 0 | 0 |

## Acceptance Gates

| Gate | Status | Passed | Detail |
| --- | --- | --- | --- |
| global_pairwise_positive | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| all_major_groups_nonnegative | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| target_not_weaker_than_negative_controls | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| blocked_controls_not_driver | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| cohort_breadth | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| single_cohort_cap | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| sample_floor | NOT_EVALUABLE_NO_PROSPECTIVE_PAIRS | n/a | No resolved prospective OB-boundary/J46 pairs exist after the registered cutoff. |
| no_leak | PASS | True | Runner summary lower-TF no-leak diagnostic checked. |

## OB Boundary Group Deltas

| Group | paired n | mean delta | sum delta |
| --- | --- | --- | --- |
| all_enabled | 0 | n/a | 0.000000 |
| all_excluding_gbpusd_control | 0 | n/a | 0.000000 |
| target_cohorts | 0 | n/a | 0.000000 |
| primary_controlled_family | 0 | n/a | 0.000000 |
| cleared_non_primary_targets | 0 | n/a | 0.000000 |
| negative_controls | 0 | n/a | 0.000000 |
| blocked_dominance_controls | 0 | n/a | 0.000000 |

## Top Raw Cohorts

| Cohort | paired n | mean delta | sum delta | groups |
| --- | --- | --- | --- | --- |

## Answered Questions

- Does the current available V2 event log contain any prospective event rows after the registered cutoff? Yes.
- Does it contain registered V2b OB-boundary/J46 rows after the cutoff? Yes.
- Does it contain resolved STRUCT_OB_BOUNDARY_V2/J46 pairs after the cutoff? No.
- Can same-event V2 rows validate V2b? No; rows at or before the cutoff are explicitly excluded.
- Does the evaluator log missing net-R reasons and lower-TF availability? Yes; see row_diagnostics.
- Can V2b promote live logic from this evaluator? No; every output keeps NO_PROMOTION_VERDICT.

## Ambiguity Ledger

- Prospective V2b validation depends on future event rows after the cutoff; discovery-set lift remains non-promotional.
- Cost remains an R-sensitivity model, not true broker spread/slippage reconstruction.
- No-leak discipline can be checked only when the runner summary exposes lower-TF start diagnostics.
- Sample floors are intentionally conservative; small positive forward samples must remain interim only.

## Opened Questions

1. Will OB-boundary remain positive once enough post-cutoff rows accumulate?
2. Will target cohorts still beat negative controls outside the discovery event log?
3. Will raw-cohort breadth survive, or collapse into one symbol/session pocket?
4. Does OB-boundary keep lower right-tail truncation than swing/FVG on future rows?

## Next Steps

1. Keep collecting/replaying prospective rows after 2026-04-30T17:00:00+00:00 until sample floors are met or the hypothesis fails early.
2. Do not treat V3 reentry discovery results as validation until this V2b level-quality question is answered on unseen rows.
3. If broad V2b fails but one cohort persists, register a fresh cohort-specific hypothesis before testing it.
4. Preserve NO_PROMOTION_VERDICT until a separate promotion dossier exists.
