# G12 NOFILL Pending Source Duplicate Denominator Review

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.

## Duplicate Posture

`{'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}`

## Invalid Case Coverage

| case_id | expected_errors | actual_errors | status |
| --- | --- | --- | --- |
| missing_row_level_denominator | missing_row_level_denominator_scope | missing_row_level_denominator_scope | PASS |
| missing_unique_key_denominator | missing_unique_key_denominator_scope | missing_unique_key_denominator_scope | PASS |
| missing_duplicate_group_id | missing_duplicate_group_id | missing_duplicate_group_id | PASS |
| missing_canonical_row_id | missing_canonical_counting_row_id | missing_canonical_counting_row_id | PASS |
| missing_noncanonical_exclusion_policy | missing_noncanonical_projection_exclusion_policy, noncanonical_projection_exclusion_policy_not_enforcing_exclusion | missing_noncanonical_projection_exclusion_policy, noncanonical_projection_exclusion_policy_not_enforcing_exclusion | PASS |
| generated_fallback_duplicate_key | generated_or_fallback_nofill_duplicate_key | generated_or_fallback_nofill_duplicate_key | PASS |

## Machine Rejection Coverage

- missing row-level denominator
- missing unique-key denominator
- missing duplicate group
- missing canonical counting row
- missing or non-enforcing noncanonical projection exclusion policy
- generated/fallback no-fill duplicate key

## Strongest Counterargument

Duplicate policy is only protective when every future packet builder runs a machine verifier before outcome opening; markdown-only review would not be enough.
