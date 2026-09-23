# Source Field Mapping Matrix

- **route_id:** `SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN`
- **evidence_class:** `SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_card_count": 40,
  "accepted_domain_count": 8,
  "accepted_readiness_split": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8
  },
  "artifact_family": "source_field_mapping_matrix",
  "capture_group_statuses": [
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_baseline_control_fields",
      "candidate_time": true,
      "field_group": "baseline_control_fields",
      "group_specific_fields": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_framework_setup_family",
      "candidate_time": true,
      "field_group": "framework_setup_family",
      "group_specific_fields": [
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "selected_framework_or_none",
        "setup_family"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "builder": "build_scid_future_orderflow_depth_proxy_requirements",
      "candidate_time": true,
      "field_group": "future_orderflow_depth_proxy_requirements",
      "group_specific_fields": [
        "derived_feature_schema_version",
        "orderflow_proxy_availability_status",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "source_hash_present": false,
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_intended_entry_reference",
      "candidate_time": true,
      "field_group": "intended_entry_reference",
      "group_specific_fields": [
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_intended_side_direction",
      "candidate_time": true,
      "field_group": "intended_side_direction",
      "group_specific_fields": [
        "side_emission_reason_code",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_intended_stop_reference",
      "candidate_time": true,
      "field_group": "intended_stop_reference",
      "group_specific_fields": [
        "stop_buffer_rule_id",
        "stop_reference_price",
        "stop_reference_type",
        "stop_source_snapshot_hash",
        "stop_source_structure_id"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_intended_target_reference",
      "candidate_time": true,
      "field_group": "intended_target_reference",
      "group_specific_fields": [
        "risk_reward_reference",
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "target_source_snapshot_hash"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_lifecycle_fill_cancel_expiry_source_status",
      "candidate_time": false,
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "group_specific_fields": [
        "intent_state_after",
        "intent_state_before",
        "pending_intent_id",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "implemented": true,
      "lifecycle_time": true,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "builder": "build_scid_lower_timeframe_asof_path_availability",
      "candidate_time": true,
      "field_group": "lower_timeframe_asof_path_availability",
      "group_specific_fields": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "decision_minus_window_start_utc",
        "ltf_availability_status",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "source_hash_present": false,
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_row_present": true,
      "validator_required": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "builder": "build_scid_poi_type_bounds_source",
      "candidate_time": true,
      "field_group": "poi_type_bounds_source",
      "group_specific_fields": [
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound"
      ],
      "implemented": true,
      "lifecycle_time": false,
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "source_hash_present": true,
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_row_present": true,
      "validator_required": true
    }
  ],
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "domain_totals": [
    {
      "card_count": 5,
      "card_ids": [
        "GEO-001",
        "GEO-002",
        "GEO-003",
        "GEO-004",
        "GEO-005"
      ],
      "outside_current_gtos_ob_framing_count": 3,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 2,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 3
      },
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "card_count": 5,
      "card_ids": [
        "HAZ-001",
        "HAZ-002",
        "HAZ-003",
        "HAZ-004",
        "HAZ-005"
      ],
      "outside_current_gtos_ob_framing_count": 5,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 1,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 2,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 2
      },
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "card_count": 5,
      "card_ids": [
        "MIC-001",
        "MIC-002",
        "MIC-003",
        "MIC-004",
        "MIC-005"
      ],
      "outside_current_gtos_ob_framing_count": 4,
      "readiness_counts": {
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 5
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "card_count": 5,
      "card_ids": [
        "BEH-001",
        "BEH-002",
        "BEH-003",
        "BEH-004",
        "BEH-005"
      ],
      "outside_current_gtos_ob_framing_count": 4,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 4,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 1
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "card_count": 5,
      "card_ids": [
        "MAC-001",
        "MAC-002",
        "MAC-003",
        "MAC-004",
        "MAC-005"
      ],
      "outside_current_gtos_ob_framing_count": 4,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 2,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 1,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 2
      },
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "card_count": 5,
      "card_ids": [
        "EXE-001",
        "EXE-002",
        "EXE-003",
        "EXE-004",
        "EXE-005"
      ],
      "outside_current_gtos_ob_framing_count": 5,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 2,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 3
      },
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "card_count": 5,
      "card_ids": [
        "UNC-001",
        "UNC-002",
        "UNC-003",
        "UNC-004",
        "UNC-005"
      ],
      "outside_current_gtos_ob_framing_count": 4,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 2,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 2,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 1
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "card_count": 5,
      "card_ids": [
        "ADV-001",
        "ADV-002",
        "ADV-003",
        "ADV-004",
        "ADV-005"
      ],
      "outside_current_gtos_ob_framing_count": 4,
      "readiness_counts": {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 2,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 1,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 2
      },
      "science_domain": "adversarial_baselines_placebo_explanations"
    }
  ],
  "evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "generated_at_utc": "2026-05-12T12:45:17Z",
  "live_effect": false,
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
  "route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "rows": [
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "session-only is the placebo itself",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "ADV-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can a session-only matched placebo be preregistered now for every future card family?",
      "mechanism_family": "session_only_matched_placebo",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "adversarial_baselines_placebo_explanations",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "volatility-only null",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "ADV-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can volatility-only matched controls be specified before any target or result opening?",
      "mechanism_family": "volatility_only_placebo",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "adversarial_baselines_placebo_explanations",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "duplicate-key random proxy assignment",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "ADV-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can duplicate-key-preserving random proxy assignment be frozen as a future replay adversarial baseline?",
      "mechanism_family": "duplicate_key_random_proxy_placebo",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "adversarial_baselines_placebo_explanations",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "side-flip placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "ADV-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "intended_side_direction"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_side_direction",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "After side capture is G12-accepted, can a side-flip placebo detect hidden beta or one-sided artifacts?",
      "mechanism_family": "side_flip_placebo_after_capture",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "adversarial_baselines_placebo_explanations",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "intended_side_direction"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "decision_asof_utc",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "side_emission_reason_code"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "translated-POI placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "ADV-005",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "After POI capture is G12-accepted, can a source-safe translated-POI placebo detect path-shape artifacts?",
      "mechanism_family": "fake_poi_translation_placebo",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "adversarial_baselines_placebo_explanations",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "session-only null is the primary hypothesis competitor",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "BEH-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can accepted symbol/session/time buckets preregister opening-participant constraint families independent of setup outcome?",
      "mechanism_family": "session_open_constraint_family",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "same symbol with random session handoff flag",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "BEH-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can cross-session handoff candidates be defined from source time buckets and future lifecycle/POI fields?",
      "mechanism_family": "london_to_ny_inventory_transfer",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "random offset placebo around same price scale",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "BEH-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can entry/POI references later define round-number crowding as a control-only family before result design?",
      "mechanism_family": "round_number_crowding_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "calendar-window placebo shifted by one non-event day",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "BEH-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_capture_groups_required": [
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can predecision calendar windows be registered as participant-constraint context without using outcomes?",
      "mechanism_family": "news_cooling_participant_constraint",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "duplicate-key shuffle preserving symbol/session",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "BEH-005",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can repeated attention to the same source-frozen level be counted from POI/lifecycle source truth before result opening?",
      "mechanism_family": "repeat_attention_decay_without_outcomes",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "session-liquidity placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "EXE-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can spread/quote state be captured as a predecision fillability context without broker account/order evidence?",
      "mechanism_family": "spread_state_fillability_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "candidate timestamp shuffled within same session",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "EXE-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can source lifecycle rows define fill-delay source states without account history or deal IDs?",
      "mechanism_family": "fill_delay_lifecycle_surface",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional",
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "range-only placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "EXE-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can LTF quote-gap descriptors around intended entry be preregistered for no-API replay?",
      "mechanism_family": "quote_gap_around_entry_reference",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "session-only orderability placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "EXE-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can an orderability context be expressed through source/control fields without changing execution behavior?",
      "mechanism_family": "source_only_orderability_window",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "random eligible-candidate placebo with same source coverage",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "EXE-005",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can market-context fillability proxies be defined for future replay without account/order/deal/position evidence?",
      "mechanism_family": "fillability_proxy_without_broker_truth",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version",
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "same symbol/session/time bucket with shuffled POI-width bins",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "GEO-001",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "framework_setup_family",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Does source-frozen POI width relative to the prior swing ladder define distinct predecision path-shape families?",
      "mechanism_family": "poi_width_vs_prior_swing_ladder",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "geometry_topology_path_shape",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "volatility-only matched compression placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "GEO-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Do M1/M5/M15 compression descriptors before decision separate compact-coil candidates from dispersed path candidates?",
      "mechanism_family": "multi_scale_compression_before_decision",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "geometry_topology_path_shape",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "random route-window permutation within same session",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "GEO-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can the no-API replay later distinguish clean void traversal into a source-frozen POI from chopped traversal?",
      "mechanism_family": "structural_void_route_to_poi",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "geometry_topology_path_shape",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "entry-time matched straight-line placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "GEO-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Does the predecision path angle into the candidate level form a mechanical curvature family independent of current framework labels?",
      "mechanism_family": "retest_angle_curvature_descriptor",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "geometry_topology_path_shape",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "framework-label shuffle within source_symbol_session_partition",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "GEO-005",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "framework_setup_family"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "framework_setup_family",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can framework-qualified flags define a source-only topology of agreement, partial overlap, and contradiction?",
      "mechanism_family": "framework_agreement_topology",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "geometry_topology_path_shape",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "framework_setup_family"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "Poisson-like random spacing matched by symbol/session",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "HAZ-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Are accepted candidates clustered in waiting-time bursts by symbol/session before any result horizon opens?",
      "mechanism_family": "candidate_density_waiting_time",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "stochastic_tail_hazard_first_passage",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "lifecycle time randomized within same candidate day",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "HAZ-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "After lifecycle capture exists, can source-only time-to-fill/cancel/expiry states define hazard families without broker history?",
      "mechanism_family": "decision_to_intent_lifecycle_hazard",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "stochastic_tail_hazard_first_passage",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional",
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "same timeframe availability placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "HAZ-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_entry_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_stop_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "intended_target_reference",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Does LTF same-bar ambiguity risk have a source-only predecision descriptor that must gate future replay interpretation?",
      "mechanism_family": "same_bar_ambiguity_hazard",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "stochastic_tail_hazard_first_passage",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version",
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "candidate_input_row_id",
        "stop_reference_price",
        "stop_reference_type",
        "stop_buffer_rule_id",
        "stop_source_structure_id",
        "stop_source_snapshot_hash",
        "candidate_input_row_id",
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "risk_reward_reference",
        "target_source_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "volatility-only placebo with identical range bucket",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "HAZ-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Do predecision tail-expansion descriptors mark candidates that occur after abnormal range expansion, before any path outcome?",
      "mechanism_family": "tail_expansion_predecision_state",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "stochastic_tail_hazard_first_passage",
      "source_groups_required_for_packet_design": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "day-of-week and hour-only placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "HAZ-005",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can session/time/source partition fields preregister a transition-clock question without side or result labels?",
      "mechanism_family": "regime_transition_hazard_clock",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "stochastic_tail_hazard_first_passage",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "same symbol/session random calendar reassignment",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MAC-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can accepted candidate partitions preregister calendar context families without touching outcome fields?",
      "mechanism_family": "day_of_week_month_turn_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "macro timestamp placebo shifted outside publication as-of",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MAC-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_capture_groups_required": [
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can a no-API macro source-control route attach as-of dollar/rates context before future replay?",
      "mechanism_family": "dollar_rates_context_state",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "single-asset trend placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MAC-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can index/rates/dollar cross-asset state be attached as source-control context for metals, JPY, and indices?",
      "mechanism_family": "risk_on_cross_asset_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "time-of-day-only placebo excluding fix labels",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MAC-004",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can LBMA/fix-window proximity be preregistered as context for candidate timing without opening results?",
      "mechanism_family": "fixing_window_context",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "volatility-only placebo without event label",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MAC-005",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_capture_groups_required": [
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can as-of event-volatility source fields be specified for future no-API replay partitioning?",
      "mechanism_family": "event_volatility_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "proxy-instrument random date alignment placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MIC-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Does an as-of depth/proxy imbalance context exist at decision time for later no-API replay grouping?",
      "mechanism_family": "depth_imbalance_at_decision_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "volume-only placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MIC-002",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can orderflow/depth source capture express replenishment after a sweep before decision without future-depth leakage?",
      "mechanism_family": "absorption_replenishment_proxy",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "same POI with shuffled proxy timestamp",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MIC-003",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "poi_type_bounds_source",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can trapped-flow proxies be attached to source-frozen POI bounds for later family testing?",
      "mechanism_family": "trapped_flow_near_poi",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "symbol-only proxy placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MIC-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can futures/CFD proxy stability be preregistered as a context eligibility family before any result lane?",
      "mechanism_family": "proxy_basis_stability_gate",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_groups_required_for_packet_design": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "session liquidity placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "MIC-005",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can SCID/depth source families mark low-liquidity path segments leading into a candidate without broker evidence?",
      "mechanism_family": "liquidity_vacuum_path_context",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "missingness-only placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "UNC-001",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_capture_groups_required": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "future_orderflow_depth_proxy_requirements",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can missingness and source availability become a preregistered uncertainty-control family without training a model?",
      "mechanism_family": "feature_availability_uncertainty_control",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_groups_required_for_packet_design": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version",
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "framework flag permutation placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "UNC-002",
      "current_gtos_ob_framing_relation": "ADJACENT_TO_GTOS_OB_STARTING_POINT",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_capture_groups_required": [
        "framework_setup_family"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "framework_setup_family",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can framework_qualified_flags express model-disagreement-like uncertainty without AI/API calls or ML execution?",
      "mechanism_family": "framework_disagreement_source_control",
      "outside_current_gtos_ob_framing": false,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "framework_setup_family"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "label-family swap placebo in audit only",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "UNC-003",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE",
      "future_capture_groups_required": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lifecycle_fill_cancel_expiry_source_status",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can future no-API replay maintain strict separation between source fields, synthetic path context, lifecycle state, and any later result family?",
      "mechanism_family": "label_family_separation_guard",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional"
      ]
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "accepted_readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "random source-completeness placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "UNC-004",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_capture_groups_required": [],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        }
      ],
      "mechanical_question": "Can source-hash completeness, as-of status, and duplicate integrity provide confidence-control strata without predictive scores?",
      "mechanism_family": "source_contract_confidence_without_scores",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields"
      ],
      "terminal_status": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
      "unavailable_fields_blocking_result_design": []
    },
    {
      "accepted_descriptor_fields_required_now": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons"
      ],
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "admissible_partition": "Current route may preregister source/control questions over the accepted 3,014-row inventory only. Future partitions must be frozen through baseline_control_fields.partition_assignment before any direction-aware result design opens.",
      "adversarial_baseline_or_placebo": "representation-name shuffle placebo",
      "as_of_no_leak_rule": "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, and fail closed on any post-decision path, target/status, result, broker, account, order, deal, position, validation, or selected-performance field.",
      "card_id": "UNC-005",
      "current_gtos_ob_framing_relation": "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
      "duplicate_denominator_policy": "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator.",
      "exact_next_source_control_route": "SCID_NO_API_FEATURE_REPRESENTATION_SOURCE_CONTROL_ROUTE",
      "future_capture_groups_required": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "group_resolutions": [
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "baseline_control_fields",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "framework_setup_family",
          "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
          "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        },
        {
          "can_run_in_parallel_with_activation_monitoring": true,
          "field_group": "lower_timeframe_asof_path_availability",
          "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
          "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF"
        }
      ],
      "mechanical_question": "Can representation families be frozen for future no-API feature extraction without fitting or selecting a model?",
      "mechanism_family": "representation_family_preregistration",
      "outside_current_gtos_ob_framing": true,
      "safe_flags": {
        "NO_PROMOTION_VERDICT": true,
        "live_effect": false,
        "outcome_review_opened": false,
        "validation_safe": false
      },
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_groups_required_for_packet_design": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
      "unavailable_fields_blocking_result_design": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash",
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ]
    }
  ],
  "schema_version": "scid_no_api_40_card_prereg_replay_input_design_v1",
  "validation_safe": false
}
```
