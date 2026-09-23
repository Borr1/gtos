# Searched Root Acquisition Ladder Ledger

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "SEARCHED_ROOT_ACQUISITION_LADDER_LEDGER",
  "blocker_acceptance_policy": "A missing-data blocker is accepted only after current worktree, source-control artifacts, absolute production roots, Sierra roots, and prior C:/tmp worktrees are searched or recorded missing.",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
  "ladder_rows": [
    {
      "exists": true,
      "files_seen": 145,
      "ladder_step": 1,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION\\data",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_data_ltf_and_sierra_roots",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 144,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 1,
      "ladder_step": 1,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION\\data\\ticks",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_tick_root",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 0,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 20,
      "ladder_step": 2,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION\\shadow_logs",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_shadow_context_logs",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 20,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 56,
      "ladder_step": 3,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION\\research\\sierrachart_data_source_research_2026-05-02",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_sierra_source_research",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 56,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 133,
      "ladder_step": 3,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION\\research\\databento_orderflow_capture_2026-05-02",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_databento_orderflow_research",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 133,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 92,
      "ladder_step": 4,
      "path": "C:\\tmp\\gtos_otb\\SCID_LTF_OF_EXPANSION",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "current_worktree_orderflow_scripts_tests",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 92,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 35,
      "ladder_step": 5,
      "path": "C:\\SierraChart\\Data",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "external_sierra_scid_data_root",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 35,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 150,
      "ladder_step": 5,
      "path": "C:\\SierraChart\\Data\\MarketDepthData",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "external_sierra_depth_data_root",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 150,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 101,
      "ladder_step": 6,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "absolute_production_tick_root",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 101,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 82,
      "ladder_step": 6,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "absolute_production_sierra_ohlcv_roots",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 82,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 31,
      "ladder_step": 6,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "absolute_production_shadow_context_logs",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 31,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 0,
      "ladder_step": 7,
      "path": "C:\\tmp\\gtos_otl",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "prior_tmp_gtos_otl_worktree",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 0,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 1,
      "ladder_step": 7,
      "path": "C:\\tmp\\gtos_recovery",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "prior_tmp_gtos_recovery_worktree",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 0,
      "status": "SEARCHED"
    },
    {
      "exists": true,
      "files_seen": 0,
      "ladder_step": 7,
      "path": "C:\\tmp\\gtos_large_file_backup_20260509",
      "proof_or_impossibility": "Metadata/source-control search completed without raw blob commit.",
      "root_id": "prior_tmp_large_file_backup",
      "skipped_forbidden_broker_account_order_history_deal_position_sources": 0,
      "sources_selected": 0,
      "status": "SEARCHED"
    }
  ],
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
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "searched_beyond_current_worktree": true,
  "searched_root_count": 14,
  "selected_source_count": 844,
  "validation_safe": false
}
```
