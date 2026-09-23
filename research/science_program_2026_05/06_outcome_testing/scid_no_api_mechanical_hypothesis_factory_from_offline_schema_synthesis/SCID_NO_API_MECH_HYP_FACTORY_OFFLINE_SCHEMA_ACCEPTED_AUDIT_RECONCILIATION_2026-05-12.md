# Accepted Audit Reconciliation

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g0_offline_schema_synthesis_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "accepted_g12_offline_schema_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "accepted_source_capture_g12_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "artifact_family": "accepted_audit_reconciliation",
  "candidate_rows_coverage_expectation": 3014,
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
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_proxy_denominator_key_coverage_expectation": 3014,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "exact_reconciliation_checks": [
    {
      "check_id": "candidate_rows_3014",
      "status": "PASS"
    },
    {
      "check_id": "duplicate_proxy_denominator_keys_3014",
      "status": "PASS"
    },
    {
      "check_id": "ten_capture_groups_preserved",
      "status": "PASS"
    },
    {
      "check_id": "manifest_binding_repair_preserved",
      "status": "PASS"
    },
    {
      "check_id": "safe_flags_preserved",
      "status": "PASS"
    },
    {
      "check_id": "no_result_or_validation_opened",
      "status": "PASS"
    }
  ],
  "generated_at_utc": "2026-05-12T05:31:11Z",
  "live_effect": false,
  "manifest_binding_repair": [
    "The current G12 prompt hash supersedes the stale pre-hardening prompt hash.",
    "The builder output manifest self-hash remains non-blocking because it is self-referential: SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING.",
    "All other source/input/artifact hash mismatches are strict blockers.",
    "Future prompt packs must cite this repair note before comparing G12/builder manifest hashes."
  ],
  "non_generatable_historical_strategy_intent_source_state_families": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
  ],
  "offline_schema_boundary": "offline schema/parser/fixture/validator/read-only alignment evidence only; live wiring absent",
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
  "recoverable_market_context_families": [
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "source_search_saturation": {
    "builder_totals": {
      "explicit_candidate_id_hits": 36168,
      "explicit_duplicate_key_hits": 39182,
      "explicit_key_rg_file_hits": 358,
      "files_seen": 13143,
      "files_selected_for_parse": 987,
      "json_records_scanned": 856006,
      "parse_errors": 8,
      "skipped_forbidden_broker_account_order_history_files": 9,
      "skipped_raw_market_blob_files": 0,
      "strategy_like_files_selected_for_parse": 663,
      "strategy_like_records_without_explicit_scid_key": 580730,
      "strategy_like_rg_file_hits": 10063,
      "text_files_scanned": 978,
      "weak_symbol_time_hits": 13412
    },
    "searched_root_ids": [
      "accepted_g12_g0_strategy_field_artifacts",
      "accepted_scid_candidate_input_and_neutral_artifacts",
      "accepted_strategy_field_packet",
      "knowledge_base_nonbroker_records",
      "pipeline_state_artifacts",
      "prior_recovery_cache",
      "prior_worktree_gtos_otb",
      "prior_worktree_gtos_otl",
      "program_control_artifacts",
      "repo_data_text_manifests_only",
      "repo_research_archive",
      "shadow_logs_source_safe_nonbroker",
      "source_control_sibling_routes"
    ],
    "source_search_result": "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS",
    "weak_symbol_time_policy": "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING"
  },
  "validation_safe": false
}
```
