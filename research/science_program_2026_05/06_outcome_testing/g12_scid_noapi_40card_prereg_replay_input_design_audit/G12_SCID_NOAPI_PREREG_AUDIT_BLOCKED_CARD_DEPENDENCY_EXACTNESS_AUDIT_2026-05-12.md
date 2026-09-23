# Blocked Card Dependency Exactness Audit

```json
{
  "artifact_family": "blocked_card_dependency_exactness_audit",
  "blocked_card_count": 32,
  "blocked_readiness_split": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17
  },
  "blocked_rows": [
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "ADV-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 8,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "ADV-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 7,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "intended_side_direction"
      ],
      "row_failures": [],
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "ADV-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "row_failures": [],
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "BEH-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 15,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "row_failures": [],
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "BEH-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "row_failures": [],
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "BEH-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 1,
      "missing_field_or_status_count": 9,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "BEH-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 15,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "row_failures": [],
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-001",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 8,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "EXE-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "row_failures": [],
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "EXE-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "row_failures": [],
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "row_failures": [],
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "GEO-001",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 14,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "row_failures": [],
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 8,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 15,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "GEO-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 7,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "row_failures": [],
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "HAZ-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 13,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "row_failures": [],
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "HAZ-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 5,
      "missing_field_or_status_count": 23,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "row_failures": [],
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "HAZ-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "MAC-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 1,
      "missing_field_or_status_count": 9,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MAC-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 17,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "row_failures": [],
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "MAC-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 1,
      "missing_field_or_status_count": 9,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-001",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 9,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "row_failures": [],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "row_failures": [],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-004",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 17,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "UNC-001",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 24,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "row_failures": [],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "UNC-002",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 7,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "row_failures": [],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "card_id": "UNC-003",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 2,
      "missing_field_or_status_count": 16,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "row_failures": [],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "UNC-005",
      "exact_dependency_row_ok": true,
      "group_resolution_summary_count": 3,
      "missing_field_or_status_count": 22,
      "parallelizable_with_activation_or_monitoring_routes": true,
      "required_capture_groups": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "row_failures": [],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    }
  ],
  "blocked_rows_only_for_blocked_cards": true,
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY",
  "expected_blocked_card_count": 32,
  "failures": [],
  "generated_at_utc": "2026-05-12T13:39:28Z",
  "live_effect": false,
  "ok": true,
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
  "route_id": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT",
  "schema_version": "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1",
  "target_evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "target_route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "validation_safe": false
}
```
