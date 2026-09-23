# Implementation Readiness Matrix

- **route_id:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "all_ten_capture_groups_covered": true,
  "artifact_family": "implementation_readiness_matrix",
  "candidate_rows_coverage_expectation": 3014,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_proxy_denominator_key_coverage_expectation": 3014,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY",
  "generated_at_utc": "2026-05-12T04:18:03Z",
  "implementation_boundary": "OFFLINE_SCHEMA_READY_DESIGN_AND_TEST_HARNESS_NEXT_LIVE_WIRING_ABSENT",
  "live_effect": false,
  "matrix_row_count": 10,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL",
  "rows": [
    {
      "capture_group": "side",
      "field_group": "intended_side_direction",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 4,
        "required_field_count": 34,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_side_direction.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_strategy_decision_packet_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 39,
          "path": "shadow_logs/candidate_features_log.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e66badc28cc8e2232f144bce80001d094cbcfbb9cc17259108583879aad64742"
        },
        {
          "observed_key_count": 29,
          "path": "shadow_logs/strategy_follow_evaluations.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "abb631d1e8dd2c947f64730724fb19cd3675156de7fc098c3f71ea4d41ccce34"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
        "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
        "missing_field_fixture": "missing_required_intended_side_direction"
      }
    },
    {
      "capture_group": "entry",
      "field_group": "intended_entry_reference",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 5,
        "required_field_count": 35,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_entry_reference.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_strategy_decision_packet_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 39,
          "path": "shadow_logs/candidate_features_log.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e66badc28cc8e2232f144bce80001d094cbcfbb9cc17259108583879aad64742"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "entry reference must be present before fill, cancel, expiry, or target horizon is known",
        "no_leak_rule": "no fill-derived or hindsight-optimized entry references",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "entry_reference_type_market_limit_zone_midpoint_other",
        "missing_field_fixture": "missing_required_intended_entry_reference"
      }
    },
    {
      "capture_group": "stop",
      "field_group": "intended_stop_reference",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 5,
        "required_field_count": 35,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_stop_reference.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_strategy_decision_packet_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 39,
          "path": "shadow_logs/candidate_features_log.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e66badc28cc8e2232f144bce80001d094cbcfbb9cc17259108583879aad64742"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
        "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "stop_reference_price",
        "missing_field_fixture": "missing_required_intended_stop_reference"
      }
    },
    {
      "capture_group": "target",
      "field_group": "intended_target_reference",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 5,
        "required_field_count": 35,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_target_reference.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_strategy_decision_packet_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 39,
          "path": "shadow_logs/candidate_features_log.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e66badc28cc8e2232f144bce80001d094cbcfbb9cc17259108583879aad64742"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
        "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "target_reference_price",
        "missing_field_fixture": "missing_required_intended_target_reference"
      }
    },
    {
      "capture_group": "POI",
      "field_group": "poi_type_bounds_source",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 7,
        "required_field_count": 37,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_poi_type_bounds_source.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_mso_snapshot_and_poi_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 36,
          "path": "shadow_logs/strategy_follow_candidates.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "889cd5012d71bd1d373e9714a96e7c5fdc2630e474660c52df185c4fe45c4aab"
        },
        {
          "observed_key_count": 31,
          "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "31ff1c7d0e817c3d13abadf70b13ce644b52b71eabba5aaf187bfa3f0e3efdd2"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
        "no_leak_rule": "do not reconstruct POI from later price movement or result-selection logic",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "missing_field_fixture": "missing_required_poi_type_bounds_source"
      }
    },
    {
      "capture_group": "framework",
      "field_group": "framework_setup_family",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 6,
        "required_field_count": 36,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "source_safe_strategy_decision_packet_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 39,
          "path": "shadow_logs/candidate_features_log.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e66badc28cc8e2232f144bce80001d094cbcfbb9cc17259108583879aad64742"
        },
        {
          "observed_key_count": 36,
          "path": "shadow_logs/strategy_follow_candidates.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "889cd5012d71bd1d373e9714a96e7c5fdc2630e474660c52df185c4fe45c4aab"
        },
        {
          "observed_key_count": 29,
          "path": "shadow_logs/strategy_follow_evaluations.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "abb631d1e8dd2c947f64730724fb19cd3675156de7fc098c3f71ea4d41ccce34"
        },
        {
          "observed_key_count": 31,
          "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "31ff1c7d0e817c3d13abadf70b13ce644b52b71eabba5aaf187bfa3f0e3efdd2"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
        "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "frameworks_evaluated",
        "missing_field_fixture": "missing_required_framework_setup_family"
      }
    },
    {
      "capture_group": "lifecycle",
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 7,
        "required_field_count": 37,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_lifecycle_fill_cancel_expiry_source_status.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "nonbroker_pending_intent_lifecycle_event_logger",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 58,
          "path": "shadow_logs/pending_limit_lifecycle.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "1ba92c58f50ed4926de3213489da9a3e1e4c9b9cae2cede01a596cb912739c15"
        },
        {
          "observed_key_count": 46,
          "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "5f8bfc093066244a8db5e4d13d94ced393098b122622a477a0131173f1d96495"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
        "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "pending_intent_id",
        "missing_field_fixture": "missing_required_lifecycle_fill_cancel_expiry_source_status"
      }
    },
    {
      "capture_group": "LTF",
      "field_group": "lower_timeframe_asof_path_availability",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 7,
        "required_field_count": 37,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_lower_timeframe_asof_path_availability.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "ltf_source_availability_and_path_descriptor_capture",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 37,
          "path": "shadow_logs/candidate_ltf_path_order.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "f22b52a4f561414b1ca48b05747f1191e5df9c7c46d1f6849dbfa0e03480a0f3"
        },
        {
          "observed_key_count": 32,
          "path": "shadow_logs/prefill_delivery_path.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "e01e8fb90545a1f7657b1738ce9e68b441e2fa30250e9212ce402355b88c358c"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
        "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "ltf_timeframes_available",
        "missing_field_fixture": "missing_required_lower_timeframe_asof_path_availability"
      }
    },
    {
      "capture_group": "orderflow/proxy",
      "field_group": "future_orderflow_depth_proxy_requirements",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 8,
        "required_field_count": 38,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_future_orderflow_depth_proxy_requirements.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "orderflow_depth_proxy_context_capture",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 36,
          "path": "shadow_logs/sierra_proxy_registry_status.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "c5cfb22a4090a94818a1e1e4ed8c631e4b70a84f0af38edf0a20864539574c97"
        },
        {
          "observed_key_count": 36,
          "path": "shadow_logs/sierra_depth_feature_snapshots.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "bdfbe77a9c12bf735d1e50b8dd8740064ac6710099ed8a95a42f1670008f6056"
        },
        {
          "observed_key_count": 31,
          "path": "shadow_logs/databento_live_trigger_decisions.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "3194f4a626fe2582412a6432a1b9829e0e3ffbf96336086f80ba8b3d275c8fe0"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless marked forensic-only",
        "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "proxy_instrument",
        "missing_field_fixture": "missing_required_future_orderflow_depth_proxy_requirements"
      }
    },
    {
      "capture_group": "baseline-control",
      "field_group": "baseline_control_fields",
      "fixture_category": "missing_field_fail_closed",
      "g12_acceptance_condition": "Recompute schema closure, required fields, parser policy, source hash, row coverage, duplicate key, as-of, no-leak, redaction, forbidden-surface, read-only alignment, fixture behavior, and manifest-repair policy.",
      "offline_schema": {
        "closed_additional_properties": true,
        "group_field_count": 7,
        "required_field_count": 37,
        "schema_path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_baseline_control_fields.schema.json"
      },
      "parser": {
        "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
        "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
        "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        "schema_version_check": "required exact match to scid_forward_source_capture_v1",
        "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
      },
      "prospective_source_or_logger_field": "offline_baseline_control_assignment_manifest",
      "read_only_artifact_alignment": [
        {
          "observed_key_count": 36,
          "path": "shadow_logs/strategy_follow_candidates.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "889cd5012d71bd1d373e9714a96e7c5fdc2630e474660c52df185c4fe45c4aab"
        },
        {
          "observed_key_count": 28,
          "path": "shadow_logs/context_control_ledger.jsonl",
          "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
          "shape_hash": "2d23066a9602ba29ffe3d9fefcf915adab09e459c3ce37ce4c046a4a9f4a6346"
        }
      ],
      "redaction_no_leak_rule": {
        "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
        "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
      },
      "validator": {
        "accepted_g12_fixture_recompute": true,
        "common_fail_closed_categories": [
          "missing_field_fail_closed",
          "forbidden_broker_identifier",
          "stale_asof_violation",
          "duplicate_denominator_consistency"
        ],
        "missing_field": "partition_assignment",
        "missing_field_fixture": "missing_required_baseline_control_fields"
      }
    }
  ],
  "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
  "validation_safe": false
}
```
