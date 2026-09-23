# Same Evidence Blocker Pursuit Ledger

```json
{
  "artifact_family": "same_evidence_class_blocker_pursuit_ledger",
  "blocked15_card_count": 15,
  "blocked17_field_status_counts": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 35,
    "PROSPECTIVE_CAPTURE_REQUIRED": 25,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": 64,
    "RECOVERED_SOURCE_BOUND": 55,
    "SOURCE_EXISTS_NEEDS_PARSER": 78
  },
  "blocked17_terminal_source_status_counts": {
    "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY": 6,
    "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED": 4,
    "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED": 7
  },
  "capture_group_rows": [
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
      "capture_group": "framework_setup_family",
      "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
      "recovered_source_state_rows": 190
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "capture_group": "future_orderflow_depth_proxy_requirements",
      "current_materialization_status": "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION",
      "exact_next_action": "Use the accepted LTF/orderflow/proxy source-status lane: attach parser/source-hash/as-of/proxy-validity requirements to each card, then G12 audit the candidate-attached packet before scoring.",
      "historical_status_after_search": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
      "next_action_type": "ROUTED_TO_ACCEPTED_LTF_PROXY_SOURCE_STATUS_CONTROL",
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
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "capture_group": "intended_side_direction",
      "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
      "recovered_source_state_rows": 190
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "capture_group": "intended_stop_reference",
      "current_materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "exact_next_action": "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator remains blocked until candidate-attached source rows are frozen and audited.",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "next_action_type": "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT",
      "recovered_source_state_rows": 190
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "capture_group": "intended_target_reference",
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
    },
    {
      "accepted_40_denominator_unblocked_now": false,
      "capture_group": "lower_timeframe_asof_path_availability",
      "current_materialization_status": "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION",
      "exact_next_action": "Use the accepted LTF/orderflow/proxy source-status lane: attach parser/source-hash/as-of/proxy-validity requirements to each card, then G12 audit the candidate-attached packet before scoring.",
      "historical_status_after_search": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
      "next_action_type": "ROUTED_TO_ACCEPTED_LTF_PROXY_SOURCE_STATUS_CONTROL",
      "recovered_source_state_rows": 0
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
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "every_item_has_exact_next_requirement": true,
  "evidence_class": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T01:18:09Z",
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
  "principle": "No blocker family is terminal if same-evidence-class source/control pursuit remains. Every blocker below is cleared, routed to accepted evidence, or reduced to an exact source/capture/parser/access/G12 requirement.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT",
  "same_class_open_items": [
    {
      "exact_requirement": "source_safe_mso_snapshot_and_poi_logger with POI type/bounds/source bars/snapshot hash/rule version",
      "item": "POI/bounds historical source-state rows",
      "status": "TRUE_HISTORICAL_SOURCE_GAP_REDUCED_TO_FORWARD_CAPTURE_REQUIREMENT"
    },
    {
      "exact_requirement": "decision-window LTF source pointer/cache id, file hash, parser version, bars-present-by-timeframe, as-of descriptor",
      "item": "LTF parser attachment",
      "status": "SOURCE_EXISTS_NEEDS_PARSER_REDUCED_TO_PARSER_HASH_ASOF_REQUIREMENT"
    },
    {
      "exact_requirement": "proxy instrument/contract/source family/capture as-of/feature schema/proxy-transfer limits; broker-native truth claims remain zero",
      "item": "Orderflow/depth proxy validity",
      "status": "PROXY_CONTEXT_REDUCED_TO_PROXY_CONTRACT_REQUIREMENT"
    },
    {
      "exact_requirement": "forward nonbroker source-state logger with redacted bridge hashes only; no broker account/order/history/deal/position evidence",
      "item": "Non-generatable historical lifecycle/source-state truth",
      "status": "PROSPECTIVE_CAPTURE_REQUIRED"
    }
  ],
  "schema_version": "g0_scid_blocked_unblocking_synthesis_v1",
  "unresolved_vague_blockers": [],
  "validation_safe": false
}
```
