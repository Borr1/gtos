# NOFILL CAT V2 Duplicate Denominator Verifier Control

Promotion posture: `NO_PROMOTION_VERDICT`.

## Duplicate Posture

- Accepted row-level source inputs: `225`
- Accepted unique no-fill duplicate keys: `182`
- Accepted duplicate-key collision groups: `5`
- Accepted duplicate-key collision rows: `48`
- OTI5 canonical duplicate rows accepted: `3`
- OTI5 noncanonical duplicate projections rejected: `39`

## Required Fields

- `row_level_denominator_scope`
- `unique_key_denominator_scope`
- `nofill_duplicate_key`
- `duplicate_group_id`
- `canonical_counting_row_id`
- `is_canonical_counting_row`
- `noncanonical_projection_exclusion_policy`

## Machine-Enforced Rejections

- `missing_row_level_denominator_scope`
- `missing_unique_key_denominator_scope`
- `missing_duplicate_group_id`
- `missing_canonical_counting_row_id`
- `missing_noncanonical_projection_exclusion_policy`
- `generated_or_fallback_nofill_duplicate_key`
- `generated_or_fallback_duplicate_group_id`

## Invalid Example Coverage

| case_id | expected_errors |
| --- | --- |
| missing_row_level_denominator | missing_row_level_denominator_scope |
| missing_unique_key_denominator | missing_unique_key_denominator_scope |
| missing_duplicate_group_id | missing_duplicate_group_id |
| missing_canonical_row_id | missing_canonical_counting_row_id |
| missing_noncanonical_exclusion_policy | missing_noncanonical_projection_exclusion_policy, noncanonical_projection_exclusion_policy_not_enforcing_exclusion |
| generated_fallback_duplicate_key | generated_or_fallback_nofill_duplicate_key |
