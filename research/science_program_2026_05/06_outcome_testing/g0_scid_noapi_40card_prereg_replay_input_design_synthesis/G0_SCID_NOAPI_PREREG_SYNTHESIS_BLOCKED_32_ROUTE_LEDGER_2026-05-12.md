# Blocked 32 Route Ledger

- **route_id:** `G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS`
- **evidence_class:** `G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "blocked_32_route_ledger",
  "assigned_route_counts": {
    "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15": 15,
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17": 17
  },
  "blocked_card_count": 32,
  "blocked_cards": [
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "ADV-002",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "ADV-004",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "decision_asof_utc",
        "duplicate_proxy_denominator_key",
        "side_emission_reason_code",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_side_direction"
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "ADV-005",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "BEH-002",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "intent_state_after",
        "intent_state_before",
        "mso_snapshot_hash",
        "pending_intent_id",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "BEH-003",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "BEH-004",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "BEH-005",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "intent_state_after",
        "intent_state_before",
        "mso_snapshot_hash",
        "pending_intent_id",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "EXE-001",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "EXE-002",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "intent_state_after",
        "intent_state_before",
        "pending_intent_id",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "EXE-003",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "EXE-004",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "intent_state_after",
        "intent_state_before",
        "pending_intent_id",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "EXE-005",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "derived_feature_schema_version",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "GEO-001",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound",
        "selected_framework_or_none",
        "setup_family"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "science_domain": "geometry_topology_path_shape",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "GEO-002",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "GEO-003",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "GEO-004",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "GEO-005",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "selected_framework_or_none",
        "setup_family"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "science_domain": "geometry_topology_path_shape",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "HAZ-002",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "intent_state_after",
        "intent_state_before",
        "pending_intent_id",
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "HAZ-003",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "risk_reward_reference",
        "stop_buffer_rule_id",
        "stop_reference_price",
        "stop_reference_type",
        "stop_source_snapshot_hash",
        "stop_source_structure_id",
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "target_source_snapshot_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "HAZ-004",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "duplicate_proxy_denominator_key",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "MAC-002",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MAC-003",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "derived_feature_schema_version",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "session_bucket",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "MAC-005",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MIC-001",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "derived_feature_schema_version",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MIC-002",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "derived_feature_schema_version",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MIC-003",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "derived_feature_schema_version",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MIC-004",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "derived_feature_schema_version",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "session_bucket",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "MIC-005",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "derived_feature_schema_version",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "UNC-001",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "derived_feature_schema_version",
        "duplicate_proxy_denominator_key",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "partition_assignment",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "session_bucket",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "UNC-002",
      "exact_missing_fields_or_source_status": [
        "candidate_input_row_id",
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "selected_framework_or_none",
        "setup_family"
      ],
      "exact_next_source_control_route_from_target": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "assigned_next_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "card_id": "UNC-003",
      "exact_missing_fields_or_source_status": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "intent_state_after",
        "intent_state_before",
        "partition_assignment",
        "pending_intent_id",
        "redacted_order_bridge_hash_optional",
        "session_bucket",
        "source_event_clock_basis",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "shortest_valid_unblocking_route": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
      "terminal_status": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "assigned_next_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "card_id": "UNC-005",
      "exact_missing_fields_or_source_status": [
        "asof_path_descriptor_version",
        "bars_present_by_timeframe",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "candidate_input_row_id",
        "decision_asof_utc",
        "decision_minus_window_start_utc",
        "duplicate_proxy_denominator_key",
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available",
        "partition_assignment",
        "selected_framework_or_none",
        "session_bucket",
        "setup_family",
        "symbol",
        "time_of_day_bucket"
      ],
      "exact_next_source_control_route_from_target": "SCID_NO_API_FEATURE_REPRESENTATION_SOURCE_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "shortest_valid_unblocking_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
      "terminal_status": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED"
    }
  ],
  "blocked_is_exact_dependency_not_passive_waiting": true,
  "blocked_readiness_split": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17
  },
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "dependency_group_counts": {
    "baseline_control_fields": 9,
    "framework_setup_family": 4,
    "future_orderflow_depth_proxy_requirements": 8,
    "intended_entry_reference": 8,
    "intended_side_direction": 1,
    "intended_stop_reference": 1,
    "intended_target_reference": 1,
    "lifecycle_fill_cancel_expiry_source_status": 6,
    "lower_timeframe_asof_path_availability": 13,
    "poi_type_bounds_source": 7
  },
  "evidence_class": "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T14:25:41Z",
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
  "remaining_dependency_blockers_from_g12": 2,
  "route_id": "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS",
  "schema_version": "g0_scid_noapi_prereg_synthesis_v1",
  "target_next_source_control_route_counts": {
    "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION": 3,
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE": 11,
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 16,
    "SCID_NO_API_FEATURE_REPRESENTATION_SOURCE_CONTROL_ROUTE": 1,
    "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE": 1
  },
  "validation_safe": false
}
```
