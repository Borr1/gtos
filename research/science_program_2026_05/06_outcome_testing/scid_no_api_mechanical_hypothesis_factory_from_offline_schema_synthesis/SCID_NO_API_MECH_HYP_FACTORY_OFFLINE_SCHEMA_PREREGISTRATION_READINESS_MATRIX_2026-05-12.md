# Preregistration Readiness Matrix

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "preregistration_readiness_matrix",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:31:11Z",
  "live_effect": false,
  "matrix_row_count": 40,
  "no_rows_are_validation_or_result_rows": true,
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
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "rows": [
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "GEO-001",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ],
      "card_id": "GEO-002",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "GEO-003",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "GEO-004",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ],
      "card_id": "GEO-005",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "framework_setup_family"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "HAZ-001",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "HAZ-002",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "HAZ-003",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "HAZ-004",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "HAZ-005",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ],
      "card_id": "MIC-001",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "MIC-002",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "MIC-003",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "MIC-004",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "MIC-005",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "BEH-001",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "BEH-002",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "BEH-003",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ],
      "card_id": "BEH-004",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "BEH-005",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "MAC-001",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ],
      "card_id": "MAC-002",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "MAC-003",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "MAC-004",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ],
      "card_id": "MAC-005",
      "exact_next_source_control_route": "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ],
      "card_id": "EXE-001",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "EXE-002",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "EXE-003",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "EXE-004",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "EXE-005",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "UNC-001",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ],
      "card_id": "UNC-002",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "framework_setup_family"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "UNC-003",
      "exact_next_source_control_route": "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "UNC-004",
      "exact_next_source_control_route": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "UNC-005",
      "exact_next_source_control_route": "SCID_NO_API_FEATURE_REPRESENTATION_SOURCE_CONTROL_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "ADV-001",
      "exact_next_source_control_route": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ],
      "card_id": "ADV-002",
      "exact_next_source_control_route": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "requires_future_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "requires_ltf_orderflow_proxy_expansion": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "blocked_unavailable_fields": [],
      "card_id": "ADV-003",
      "exact_next_source_control_route": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": true,
      "readiness": "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
      "requires_future_capture_groups": [],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "blocked_unavailable_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "decision_asof_utc",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "side_emission_reason_code"
      ],
      "card_id": "ADV-004",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "intended_side_direction"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "blocked_unavailable_fields": [
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
      ],
      "card_id": "ADV-005",
      "exact_next_source_control_route": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "preregisterable_now_source_control_only": false,
      "readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "requires_future_capture_groups": [
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "requires_ltf_orderflow_proxy_expansion": false,
      "science_domain": "adversarial_baselines_placebo_explanations"
    }
  ],
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "status_counts": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8
  },
  "validation_safe": false
}
```
