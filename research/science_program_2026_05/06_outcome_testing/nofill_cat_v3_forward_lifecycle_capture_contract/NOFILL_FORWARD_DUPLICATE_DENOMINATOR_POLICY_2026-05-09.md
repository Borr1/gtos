# NOFILL Forward Duplicate Denominator Policy 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Denominators

- row-level accepted input denominator: `225`
- primary unique denominator: `182` `nofill_duplicate_key` values
- secondary denominator: `139` `duplicate_group_id` values

## Rules

- apply accepted-first filtering to accepted_input_only rows before any duplicate count
- exclude reject-overlap rows before label or denominator assignment
- exclude source-control and source-impossible rows from result labels and performance denominators
- require canonical_row_id and is_canonical_row before counting duplicate groups
- fail rows with generated, fallback, missing, or non-stable duplicate keys

## Blocking Examples

Rows with generated/fallback duplicate keys, noncanonical projections, source-control state, source-impossible state, or reject-overlap state cannot enter any performance denominator. That is true even if the row has useful market-structure evidence.
