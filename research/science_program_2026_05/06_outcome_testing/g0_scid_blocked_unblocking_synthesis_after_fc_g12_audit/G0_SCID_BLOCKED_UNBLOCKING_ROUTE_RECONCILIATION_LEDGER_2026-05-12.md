# Route Reconciliation Ledger

```json
{
  "accepted40_blocked_ids_match_blocked32": true,
  "accepted_40_card_denominator_count": 40,
  "accepted_g12_decisions_preserved": {
    "anti_boxing": "ACCEPT_AS_G12_SCID_ANTI_BOXING_ROUTE_INTAKE_CONTROL_EVIDENCE_ONLY",
    "blocked15_future_capture": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
    "blocked17_ltf_proxy": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
    "expansion": "ACCEPT_AS_G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_CONTROL_EVIDENCE_ONLY",
    "ready8": "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
  },
  "artifact_family": "blocked_card_route_reconciliation_ledger",
  "assigned_route_counts": {
    "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15": 15,
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17": 17
  },
  "blocked15_card_count": 15,
  "blocked15_card_ids": [
    "ADV-004",
    "ADV-005",
    "BEH-002",
    "BEH-003",
    "BEH-004",
    "BEH-005",
    "EXE-002",
    "EXE-004",
    "GEO-001",
    "GEO-005",
    "HAZ-002",
    "MAC-002",
    "MAC-005",
    "UNC-002",
    "UNC-003"
  ],
  "blocked17_card_count": 17,
  "blocked17_card_ids": [
    "ADV-002",
    "EXE-001",
    "EXE-003",
    "EXE-005",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "HAZ-003",
    "HAZ-004",
    "MAC-003",
    "MIC-001",
    "MIC-002",
    "MIC-003",
    "MIC-004",
    "MIC-005",
    "UNC-001",
    "UNC-005"
  ],
  "blocked32_card_count": 32,
  "blocked32_card_ids": [
    "ADV-002",
    "ADV-004",
    "ADV-005",
    "BEH-002",
    "BEH-003",
    "BEH-004",
    "BEH-005",
    "EXE-001",
    "EXE-002",
    "EXE-003",
    "EXE-004",
    "EXE-005",
    "GEO-001",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "GEO-005",
    "HAZ-002",
    "HAZ-003",
    "HAZ-004",
    "MAC-002",
    "MAC-003",
    "MAC-005",
    "MIC-001",
    "MIC-002",
    "MIC-003",
    "MIC-004",
    "MIC-005",
    "UNC-001",
    "UNC-002",
    "UNC-003",
    "UNC-005"
  ],
  "capture_group_count": 10,
  "capture_groups": [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source"
  ],
  "card_route_rows": [
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use.",
          "next_action_type": "LTF_PARSER_AND_ASOF_ATTACHMENT_REQUIRED",
          "status_counts": {
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
        }
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_side_direction"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_side_direction",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "intended_entry_reference"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "poi_type_bounds_source",
          "current_materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
          "exact_next_action": "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger `source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; then run G12 audit before any denominator movement.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
          "next_action_type": "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT",
          "recovered_source_state_rows": 0
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_entry_reference",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "poi_type_bounds_source",
          "current_materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
          "exact_next_action": "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger `source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; then run G12 audit before any denominator movement.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
          "next_action_type": "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT",
          "recovered_source_state_rows": 0
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        }
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "poi_type_bounds_source"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_entry_reference",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "poi_type_bounds_source",
          "current_materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
          "exact_next_action": "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger `source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; then run G12 audit before any denominator movement.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
          "next_action_type": "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT",
          "recovered_source_state_rows": 0
        }
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "baseline_control_fields",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Immediate source-control materialization is available: freeze baseline/partition/control assignment manifests for blocked cards, then require G12 packet audit before any future scoring gate.",
          "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "poi_type_bounds_source",
          "current_materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
          "exact_next_action": "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger `source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; then run G12 audit before any denominator movement.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
          "next_action_type": "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT",
          "recovered_source_state_rows": 0
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        }
      ],
      "science_domain": "behavioral_game_theory_session_participant_constraints",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use.",
          "next_action_type": "LTF_PARSER_AND_ASOF_ATTACHMENT_REQUIRED",
          "status_counts": {
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
        }
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_entry_reference",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_entry_reference",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        }
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "poi_type_bounds_source",
          "current_materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
          "exact_next_action": "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger `source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; then run G12 audit before any denominator movement.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
          "next_action_type": "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT",
          "recovered_source_state_rows": 0
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "framework_setup_family",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use.",
          "next_action_type": "LTF_PARSER_AND_ASOF_ATTACHMENT_REQUIRED",
          "status_counts": {
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
        }
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "framework_setup_family",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lifecycle_fill_cancel_expiry_source_status",
        "intended_entry_reference"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "intended_entry_reference",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
            "PROSPECTIVE_CAPTURE_REQUIRED": 10,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use.",
          "next_action_type": "LTF_PARSER_AND_ASOF_ATTACHMENT_REQUIRED",
          "status_counts": {
            "PROSPECTIVE_CAPTURE_REQUIRED": 3,
            "RECOVERED_SOURCE_BOUND": 7,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
        }
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "terminal_next_action": "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's decision window; G12 audit parser coverage before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "baseline_control_fields",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Immediate source-control materialization is available: freeze baseline/partition/control assignment manifests for blocked cards, then require G12 packet audit before any future scoring gate.",
          "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROSPECTIVE_CAPTURE_REQUIRED": 3,
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "baseline_control_fields",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Immediate source-control materialization is available: freeze baseline/partition/control assignment manifests for blocked cards, then require G12 packet audit before any future scoring gate.",
          "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 1
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 1
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROSPECTIVE_CAPTURE_REQUIRED": 3,
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 2,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use.",
          "next_action_type": "ORDERFLOW_PROXY_CONTRACT_REQUIRED",
          "status_counts": {
            "PROSPECTIVE_CAPTURE_REQUIRED": 3,
            "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
            "RECOVERED_SOURCE_BOUND": 7,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        }
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_next_action": "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and no-broker-truth language; require G12 source-contract audit before result packet use."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "framework_setup_family"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "framework_setup_family",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        }
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
      "blocked_lane": "blocked15_future_capture_source_state",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "baseline_control_fields",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Immediate source-control materialization is available: freeze baseline/partition/control assignment manifests for blocked cards, then require G12 packet audit before any future scoring gate.",
          "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 190
        },
        {
          "accepted_40_denominator_unblocked_now": false,
          "capture_group": "lifecycle_fill_cancel_expiry_source_status",
          "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
          "exact_next_action": "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the broker-account/order/history/deal/position evidence ban and require G12 source-control audit.",
          "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
          "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
          "recovered_source_state_rows": 73
        }
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_next_action": "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, then require G12 audit before any packet/result gate."
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "blocked_lane": "blocked17_ltf_orderflow_proxy_source_status",
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
      "may_score_results_now": false,
      "required_capture_groups": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "same_evidence_class_actions": [
        {
          "accepted_40_denominator_unblocked_now": false,
          "exact_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately.",
          "next_action_type": "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED",
          "status_counts": {
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 6,
            "PROSPECTIVE_CAPTURE_REQUIRED": 3,
            "RECOVERED_SOURCE_BOUND": 7,
            "SOURCE_EXISTS_NEEDS_PARSER": 6
          },
          "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        }
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_next_action": "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; materialize recoverable parser contracts and prospective capture requirements separately."
    }
  ],
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T01:18:09Z",
  "lane_counts": {
    "blocked15_future_capture_source_state": 15,
    "blocked17_ltf_orderflow_proxy_source_status": 17
  },
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
  "readiness_split": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17
  },
  "ready8_card_count": 8,
  "ready8_card_ids": [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004"
  ],
  "recovered_source_state_rows": 1213,
  "required_capture_group_counts_across_blocked32": {
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
  "route_id": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT",
  "schema_version": "g0_scid_blocked_unblocking_synthesis_v1",
  "science_domain_counts": {
    "adversarial_baselines_placebo_explanations": 3,
    "behavioral_game_theory_session_participant_constraints": 4,
    "execution_science_spread_slippage_fillability": 5,
    "geometry_topology_path_shape": 5,
    "macro_session_calendar_cross_asset_context": 3,
    "microstructure_orderflow_liquidity_trapped_flow": 5,
    "ml_meta_labeling_model_disagreement_uncertainty_controls": 4,
    "stochastic_tail_hazard_first_passage": 3
  },
  "validation_safe": false
}
```
