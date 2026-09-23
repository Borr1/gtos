# Read-Only Monitoring Alignment Synthesis

- **route_id:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "alignment_target_count": 12,
  "artifact_family": "read_only_monitoring_alignment_synthesis",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY",
  "field_groups_with_alignment": [
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
  "generated_at_utc": "2026-05-12T04:18:03Z",
  "live_effect": false,
  "live_wiring_added": false,
  "missing_alignment_groups": [],
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
  "producer_files_modified": [],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "read_only_alignment_only": true,
  "route_id": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
  "target_summary": [
    {
      "aligned_field_groups": [
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "framework_setup_family"
      ],
      "observed_key_count": 39,
      "path": "shadow_logs/candidate_features_log.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "framework_setup_family",
        "poi_type_bounds_source",
        "baseline_control_fields"
      ],
      "observed_key_count": 36,
      "path": "shadow_logs/strategy_follow_candidates.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "framework_setup_family",
        "intended_side_direction"
      ],
      "observed_key_count": 29,
      "path": "shadow_logs/strategy_follow_evaluations.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "poi_type_bounds_source",
        "framework_setup_family"
      ],
      "observed_key_count": 31,
      "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "observed_key_count": 58,
      "path": "shadow_logs/pending_limit_lifecycle.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "observed_key_count": 46,
      "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "observed_key_count": 37,
      "path": "shadow_logs/candidate_ltf_path_order.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "observed_key_count": 32,
      "path": "shadow_logs/prefill_delivery_path.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "observed_key_count": 36,
      "path": "shadow_logs/sierra_proxy_registry_status.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "observed_key_count": 36,
      "path": "shadow_logs/sierra_depth_feature_snapshots.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "observed_key_count": 31,
      "path": "shadow_logs/databento_live_trigger_decisions.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    },
    {
      "aligned_field_groups": [
        "baseline_control_fields"
      ],
      "observed_key_count": 28,
      "path": "shadow_logs/context_control_ledger.jsonl",
      "producer_modified": false,
      "raw_values_copied": false,
      "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING",
      "running_process_altered": false
    }
  ],
  "validation_safe": false
}
```
