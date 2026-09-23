# Source Search Saturation Audit

```json
{
  "artifact_family": "source_search_saturation_audit",
  "builder_searched_root_ids": [
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
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "current_root_inventory_aggregate": {
    "files_seen": 18585,
    "forbidden_broker_account_order_history_files_present": 649,
    "raw_market_blob_files_present": 1202,
    "text_files_currently_available_for_safe_scan": 15932
  },
  "current_root_inventory_recomputed": [
    {
      "current_files_seen": 35,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 31,
      "exists_now": true,
      "root_id": "accepted_strategy_field_packet"
    },
    {
      "current_files_seen": 59,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 56,
      "exists_now": true,
      "root_id": "accepted_g12_g0_strategy_field_artifacts"
    },
    {
      "current_files_seen": 128,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 114,
      "exists_now": true,
      "root_id": "accepted_scid_candidate_input_and_neutral_artifacts"
    },
    {
      "current_files_seen": 276,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 260,
      "exists_now": true,
      "root_id": "source_control_sibling_routes"
    },
    {
      "current_files_seen": 177,
      "current_forbidden_broker_files_present": 7,
      "current_raw_market_blob_files_present": 16,
      "current_text_files_safe_scan": 116,
      "exists_now": true,
      "root_id": "shadow_logs_source_safe_nonbroker"
    },
    {
      "current_files_seen": 257,
      "current_forbidden_broker_files_present": 4,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 252,
      "exists_now": true,
      "root_id": "program_control_artifacts"
    },
    {
      "current_files_seen": 1825,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 1825,
      "exists_now": true,
      "root_id": "pipeline_state_artifacts"
    },
    {
      "current_files_seen": 1764,
      "current_forbidden_broker_files_present": 468,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 1249,
      "exists_now": true,
      "root_id": "knowledge_base_nonbroker_records"
    },
    {
      "current_files_seen": 1180,
      "current_forbidden_broker_files_present": 2,
      "current_raw_market_blob_files_present": 544,
      "current_text_files_safe_scan": 509,
      "exists_now": true,
      "root_id": "repo_data_text_manifests_only"
    },
    {
      "current_files_seen": 2,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 2,
      "current_text_files_safe_scan": 0,
      "exists_now": true,
      "root_id": "repo_research_archive"
    },
    {
      "current_files_seen": 12880,
      "current_forbidden_broker_files_present": 168,
      "current_raw_market_blob_files_present": 640,
      "current_text_files_safe_scan": 11518,
      "exists_now": true,
      "root_id": "prior_worktree_gtos_otb"
    },
    {
      "current_files_seen": 0,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 0,
      "exists_now": true,
      "root_id": "prior_worktree_gtos_otl"
    },
    {
      "current_files_seen": 2,
      "current_forbidden_broker_files_present": 0,
      "current_raw_market_blob_files_present": 0,
      "current_text_files_safe_scan": 2,
      "exists_now": true,
      "root_id": "prior_recovery_cache"
    }
  ],
  "evidence_class": "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T02:04:08Z",
  "hard_boundary_skips": {
    "forbidden_broker_account_order_history_fragments": [
      "account_history",
      "account_pnl",
      "account_truth",
      "broker_actual",
      "daily_pnl",
      "mt5_deals",
      "trade_records"
    ],
    "raw_market_blob_suffixes": [
      ".bin",
      ".csv",
      ".depth",
      ".dly",
      ".jsonl.gz",
      ".parquet",
      ".scid"
    ]
  },
  "historical_recovery_explicit_new_strategy_intent_recoveries": 0,
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
  "raw_blob_join_policy": "FORBIDDEN_OR_INSUFFICIENT_FOR_STRATEGY_INTENT; MAY_SUPPORT_FUTURE_MARKET_CONTEXT_CONTRACT_ONLY",
  "required_root_ids_missing_from_builder_ledger": [],
  "route_id": "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT",
  "saturation_audit_note": "Current root inventory is recomputed against a live dirty worktree; exact file counts may drift after the builder. Blocking criteria are missing required root classes, absent safe-scan totals, accepted weak joins, accepted raw/broker joins, or a source-search terminal result other than saturated absence.",
  "schema_version": "g12_scid_combined_source_capture_route_audit_v1",
  "source_search_result": "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS",
  "source_search_saturation_ok": true,
  "validation_safe": false,
  "weak_symbol_time_policy": "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING"
}
```
