# Repair Followup Source Request Ledger

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "repair_followup_source_request_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_owner_source_access_requirements": [],
  "followup_count": 3,
  "followups": [
    {
      "blocking_for_tooling_acceptance": false,
      "class": "source_control_catalog_snapshot_refresh",
      "exact_action": "Rerun the target builder in the active consuming worktree before citing current_worktree absolute paths; the committed target snapshot was generated from a sibling worktree but runtime recompute is correct.",
      "followup_id": "G12-CAT-FOLLOWUP-001",
      "owner_access_required": false,
      "severity": "implementation_followup"
    },
    {
      "blocking_for_tooling_acceptance": false,
      "class": "prior_worktree_snapshot_hash_reproducibility",
      "exact_action": "Do not cite the 46 persisted prior_worktree_root hash rows as current files; rerun the target builder in the consuming worktree to refresh the bounded catalog before source use.",
      "followup_id": "G12-CAT-FOLLOWUP-002",
      "owner_access_required": false,
      "severity": "implementation_followup"
    },
    {
      "blocking_for_tooling_acceptance": false,
      "class": "future_prompt_use_condition",
      "exact_action": "Future data-heavy prompts must run the target builder in the active worktree and treat catalog rows as SOURCE_CONTROL_ONLY until a lane-specific source contract, as-of rule, duplicate policy, and no-leak gate exist.",
      "followup_id": "G12-CAT-USE-CONDITION-001",
      "owner_access_required": false,
      "severity": "use_condition"
    }
  ],
  "generated_at_utc": "2026-05-10T07:24:26Z",
  "lazy_blockers_remaining": [],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false
}
```
