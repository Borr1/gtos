# Fixture Generator And Mutation Ledger

Generator module: `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/runtime_harness_synthetic_only_2026_05_12.py`.

## Generators
- `positive_row(field_group, variant)` emits accepted-schema rows for every capture group.
- `unavailable_row(field_group)` emits source-unavailable fail-closed rows; only LTF/orderflow are accepted as valid fail-closed market-context rows.
- `build_manifest_repair_payload(valid)` emits manifest-binding repair continuity payloads.

## Mutators
- Missing required group field.
- Stale as-of timestamp.
- Recursive forbidden broker/order/deal/position identifier.
- Unsafe flag flip.
- Schema-version mismatch.
- Closed-schema unexpected field.
- Duplicate denominator-key drift for identical candidate id.
- Unavailable-source routing.
- Group-specific enum violation where the accepted schema exposes a group enum.

All values are synthetic and do not encode live market, result, broker, account,
order, deal, position, validation, strategy edge, or performance evidence.
