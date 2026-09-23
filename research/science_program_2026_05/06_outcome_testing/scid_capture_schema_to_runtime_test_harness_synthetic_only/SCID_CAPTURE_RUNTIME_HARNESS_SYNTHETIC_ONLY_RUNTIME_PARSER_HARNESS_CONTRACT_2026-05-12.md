# Runtime Parser Harness Contract

## Boundary
The harness is a parser/validator contract only. It does not implement or wire a
producer. Future runtime producers must emit rows conforming to the accepted
offline schema package and must preserve the `candidate_input_row_id` and
`duplicate_proxy_denominator_key` exactly.

## Parser Contract
1. Load the accepted schema bundle from `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas`.
2. Reject unknown `field_group` and unknown `schema_version`.
3. Enforce closed `additionalProperties: false` group schemas.
4. Enforce all required common and group-specific fields.
5. Enforce `source_observed_asof_utc <= decision_asof_utc`.
6. Enforce strict source hash for captured rows.
7. Allow `SOURCE_UNAVAILABLE_FAIL_CLOSED` only for LTF/orderflow market-context groups.
8. Reject duplicate candidate ids with denominator-key drift.
9. Recursively reject broker/account/order/deal/position/result/performance keys or values.
10. Return structured fail-closed errors; never infer missing fields from price path, result labels, broker records, AI output, or future market movement.
