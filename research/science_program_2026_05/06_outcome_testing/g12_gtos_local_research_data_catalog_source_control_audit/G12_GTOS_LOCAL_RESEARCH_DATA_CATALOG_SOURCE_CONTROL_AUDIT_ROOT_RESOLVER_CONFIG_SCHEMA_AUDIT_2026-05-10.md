# Root Resolver Config Schema Audit

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "absolute_heavy_data_awareness_present": true,
  "accepted_followup_required": true,
  "artifact_family": "root_resolver_config_schema_audit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_followup": "Rerun the target builder in the active consuming worktree before citing current_worktree absolute paths; the committed target snapshot was generated from a sibling worktree but runtime recompute is correct.",
  "generated_at_utc": "2026-05-10T07:24:26Z",
  "live_effect": false,
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
  "persisted_current_worktree_path_mismatch_count": 6,
  "persisted_current_worktree_path_mismatches": [
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data\\ticks",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\shadow_logs",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\exports",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data\\external",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\research\\science_program_2026_05\\06_outcome_testing"
  ],
  "persisted_current_worktree_paths": [
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data\\ticks",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\shadow_logs",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\exports",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\data\\external",
    "C:\\tmp\\gtos_otb\\GTOSDATACAT\\research\\science_program_2026_05\\06_outcome_testing"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "read_policies": [
    "stat_and_hash_small_safe_files_only"
  ],
  "required_roots_missing": [],
  "required_roots_present": [
    "absolute_main_data_root",
    "absolute_main_shadow_logs",
    "absolute_main_tick_root",
    "current_worktree_data_root",
    "current_worktree_tick_root",
    "owner_documents_candidate_root",
    "prior_worktree_root",
    "sierra_chart_data_root",
    "sierra_chart_depth_root",
    "sierra_chart_root"
  ],
  "root_count": 16,
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "runtime_current_worktree_paths_match_active_repo": true,
  "runtime_target_builder_current_worktree_paths": [
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\data",
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\data\\ticks",
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\shadow_logs",
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\exports",
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\data\\external",
    "C:\\tmp\\gtos_otb\\G12GTOSDATACAT\\research\\science_program_2026_05\\06_outcome_testing"
  ],
  "schema_required_fields": [
    "root_id",
    "root_path",
    "root_role",
    "source_family_hint",
    "max_depth",
    "max_files",
    "include_extensions",
    "read_policy",
    "scan_enabled"
  ],
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false
}
```
