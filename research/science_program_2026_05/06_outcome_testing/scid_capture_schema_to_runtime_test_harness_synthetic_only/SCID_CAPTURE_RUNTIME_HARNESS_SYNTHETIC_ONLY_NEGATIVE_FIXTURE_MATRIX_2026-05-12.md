# Negative Fixture Matrix

## bad_enum
- Cases: `7`
- Field groups: `baseline_control_fields, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `7`

## duplicate_key_drift
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## forbidden_identifier
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## manifest_repair_invalid
- Cases: `1`
- Field groups: `route-level`
- Expected valid: `0`
- Expected invalid: `1`

## manifest_repair_valid
- Cases: `1`
- Field groups: `route-level`
- Expected valid: `1`
- Expected invalid: `0`

## missing_required
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## positive_base
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `10`
- Expected invalid: `0`

## positive_variant
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `10`
- Expected invalid: `0`

## schema_version_mismatch
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## stale_asof
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## unavailable_source
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `2`
- Expected invalid: `8`
- Inapplicable proofs:
  - `baseline_control_fields`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `framework_setup_family`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `intended_entry_reference`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `intended_side_direction`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `intended_stop_reference`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `intended_target_reference`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `lifecycle_fill_cancel_expiry_source_status`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.
  - `poi_type_bounds_source`: SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.

## unexpected_field
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

## unsafe_flag
- Cases: `10`
- Field groups: `baseline_control_fields, framework_setup_family, future_orderflow_depth_proxy_requirements, intended_entry_reference, intended_side_direction, intended_stop_reference, intended_target_reference, lifecycle_fill_cancel_expiry_source_status, lower_timeframe_asof_path_availability, poi_type_bounds_source`
- Expected valid: `0`
- Expected invalid: `10`

