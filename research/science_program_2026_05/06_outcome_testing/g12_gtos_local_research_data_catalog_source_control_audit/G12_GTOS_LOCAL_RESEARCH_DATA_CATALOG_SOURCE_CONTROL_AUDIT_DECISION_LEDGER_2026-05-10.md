# Decision Ledger

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "decision_ledger",
  "can_use_tooling_with_conditions": true,
  "changes_live_trading_behavior": false,
  "conditions": [
    "Rerun target builder in the active consuming worktree before citing current_worktree paths or per-file source hashes.",
    "Do not treat bounded negative search rows as global absence proof.",
    "Do not consume large-file deferrals until a dedicated hash manifest exists.",
    "Keep catalog presence SOURCE_CONTROL_ONLY until a separate evidence-class lane authorizes source use."
  ],
  "credentials_touched": false,
  "decision_options": [
    "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
    "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
    "BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS",
    "REJECT_IF_TOOL_OPENS_FORBIDDEN_EVIDENCE_CLASS"
  ],
  "exact_reasons": [
    "Target counts reconcile to 1200 catalog rows, 1076 small-file hash rows, 124 deferrals, 6 search queries, 22 recoverable windows, 20 non-generatable source-state gaps, and 42 manifest-only requests.",
    "Runtime target builder recomputes 1200/1076/124 in this active worktree and independently rehashes 1076 small rows with zero missing or mismatched hashes.",
    "Committed target snapshot has current_worktree paths from a sibling worktree and prior_worktree hash rows whose files are absent now; this is an exact refresh/use-condition follow-up, not a live or validation issue.",
    "All safe flags remain closed: NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
  ],
  "failed_audit_names": [],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false
}
```
