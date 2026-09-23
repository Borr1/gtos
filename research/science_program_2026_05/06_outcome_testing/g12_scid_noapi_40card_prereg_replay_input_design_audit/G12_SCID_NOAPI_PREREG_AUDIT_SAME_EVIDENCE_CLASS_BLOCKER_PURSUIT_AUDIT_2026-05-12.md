# Same Evidence Class Blocker Pursuit Audit

```json
{
  "artifact_family": "same_evidence_class_blocker_pursuit_audit",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T13:39:28Z",
  "live_effect": false,
  "no_vague_blockers_left": true,
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
  "proof_or_impossibility_standard": "A blocker remains only when accepted artifacts show fail-closed source unavailable status, no live row landing, or a later source-status/proxy/parser/G12 gate is required. No price, broker, outcome, or performance inference is used.",
  "pursued_group_count": 10,
  "pursued_group_rows": [
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 40,
      "field_group": "baseline_control_fields",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 4,
      "field_group": "framework_setup_family",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "cards_requiring_group": 8,
      "field_group": "future_orderflow_depth_proxy_requirements",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
      "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF",
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 8,
      "field_group": "intended_entry_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_side_direction",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_stop_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_target_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 6,
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "cards_requiring_group": 13,
      "field_group": "lower_timeframe_asof_path_availability",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
      "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF",
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 7,
      "field_group": "poi_type_bounds_source",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    }
  ],
  "remaining_exact_dependency_blocker_count": 2,
  "remaining_exact_dependency_blockers": [
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "cards_requiring_group": 8,
      "field_group": "future_orderflow_depth_proxy_requirements",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
      "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF",
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "UNAVAILABLE_FAIL_CLOSED",
      "cards_requiring_group": 13,
      "field_group": "lower_timeframe_asof_path_availability",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof must be provided by source-status expansion or prospective capture before later packet use.",
      "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF",
      "source_hash_policy": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_field_status": "SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "synthetic_verifier_row_present": true
    }
  ],
  "resolved_inside_this_prompt": [
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 40,
      "field_group": "baseline_control_fields",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 4,
      "field_group": "framework_setup_family",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 8,
      "field_group": "intended_entry_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_side_direction",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_stop_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 1,
      "field_group": "intended_target_reference",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 6,
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    },
    {
      "availability_status": "CAPTURED_SOURCE_SAFE",
      "cards_requiring_group": 7,
      "field_group": "poi_type_bounds_source",
      "implemented_in_additive_capture_matrix": true,
      "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
      "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
      "source_hash_policy": "STRICT_SHA256_REQUIRED",
      "synthetic_field_status": "CAPTURED_SOURCE_SAFE",
      "synthetic_verifier_row_present": true
    }
  ],
  "resolved_inside_this_prompt_count": 8,
  "route_id": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT",
  "schema_version": "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1",
  "target_evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "target_route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "validation_safe": false
}
```
