# SCID Capture Runtime Harness - Context Anchor And G12 Reconciliation

Terminal route: `SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY`.

This route is control-evidence-only and synthetic-only. It does not open
validation, result scoring, strategy edge claims, AI/API calls, broker/account
order/deal/position evidence, raw market blob commits, prompt/config/risk/safety
execution/canary/selector edits, or live behavior.

## Accepted Control Inputs
- Accepted G12 audit route: `research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit`
- Accepted offline schema route: `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package`
- Accepted schema version: `scid_forward_source_capture_v1`
- Accepted candidate-row boundary: `3014`
- Accepted capture groups: `10`
- Accepted capture groups:
- `baseline_control_fields`
- `framework_setup_family`
- `future_orderflow_depth_proxy_requirements`
- `intended_entry_reference`
- `intended_side_direction`
- `intended_stop_reference`
- `intended_target_reference`
- `lifecycle_fill_cancel_expiry_source_status`
- `lower_timeframe_asof_path_availability`
- `poi_type_bounds_source`

## Reconciliation
- The G12 audit accepted the offline schema package as control evidence only.
- The manifest-binding repair is preserved: current G12 prompt hash repair and output-manifest self-hash drift remain nonblocking; all other source/input mismatches remain strict blockers.
- The harness validates runtime-shaped rows against the accepted schema files but generates only synthetic fixture rows locally.
- Runtime producer wiring remains absent.
