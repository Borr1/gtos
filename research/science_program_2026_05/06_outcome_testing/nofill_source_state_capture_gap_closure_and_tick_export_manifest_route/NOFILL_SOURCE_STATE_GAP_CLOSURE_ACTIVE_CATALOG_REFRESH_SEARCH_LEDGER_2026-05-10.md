# Nofill Source State Gap Closure Active Catalog Refresh Search Ledger 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "active_catalog_counts": {
    "catalog_row_count": 1200,
    "hash_manifest_hashed_file_count": 1076,
    "hash_manifest_large_file_deferral_count": 124,
    "missing_window_row_count": 42,
    "readable_root_count": 16,
    "search_query_count": 6
  },
  "artifact_family": "active_catalog_refresh_and_search_ledger",
  "catalog_builder_rerun": {
    "command": "python research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py",
    "rerun_ok": true,
    "returncode": 0,
    "stderr_text": "",
    "stdout_json": {
      "artifact_count": 35,
      "can_mark_goal_complete": true,
      "catalog_row_count": 1200,
      "changes_live_trading_behavior": false,
      "credentials_touched": false,
      "hash_manifest_hashed_file_count": 1076,
      "hash_manifest_large_file_deferral_count": 124,
      "live_effect": false,
      "missing_window_row_count": 42,
      "noleak_audit_passed": true,
      "opens_live_restart": false,
      "opens_live_trading_behavior": false,
      "opens_mt5_order_account_history_behavior": false,
      "opens_paid_api_or_databento_route": false,
      "opens_promotion": false,
      "opens_registry_edit": false,
      "opens_remote_push": false,
      "opens_result_scoring": false,
      "opens_validation": false,
      "outcome_review_opened": false,
      "promotion_verdict": "NO_PROMOTION_VERDICT",
      "readable_root_count": 16,
      "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
      "search_query_count": 6,
      "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
      "validation_safe": false
    },
    "stdout_text": null
  },
  "catalog_negative_query_count": 4,
  "catalog_positive_query_count": 2,
  "catalog_presence_policy": [
    "SOURCE_CONTROL_ONLY",
    "not_validation_safe",
    "not_global_absence_proof",
    "not_permission_to_use_forbidden_broker_or_result_surfaces"
  ],
  "catalog_search_query_count": 6,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T08:33:44Z",
  "live_effect": false,
  "missing_window_counts": {
    "non_generatable_source_state_count": 20,
    "recoverable_market_data_count": 22,
    "recovered_local_market_data_count": 0
  },
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "row_level_search_evidence_count": 37,
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "searched_roots_union": [
    "absolute_main_data_root",
    "absolute_main_exports",
    "absolute_main_external_data",
    "absolute_main_shadow_logs",
    "absolute_main_tick_root",
    "current_worktree_data_root",
    "current_worktree_exports",
    "current_worktree_external_data",
    "current_worktree_science_routes",
    "current_worktree_shadow_logs",
    "current_worktree_tick_root",
    "owner_documents_candidate_root",
    "prior_worktree_root",
    "sierra_chart_data_root",
    "sierra_chart_depth_root",
    "sierra_chart_root"
  ],
  "validation_safe": false
}
```
