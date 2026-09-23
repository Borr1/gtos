# GTOS Worktree Bootstrap Data-Root Resolver

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "absolute_data_root_resolver_schema": {
    "exists": "boolean",
    "forbidden_file_tokens": [
      "account",
      "broker_actual_r",
      "deal",
      "history",
      "order",
      "position",
      "pnl",
      "slippage",
      "trade_record"
    ],
    "hash_policy": "sha256 small files; dedicated route for large files",
    "permission_status": "readable | access_denied | absent",
    "root_id": "stable identifier",
    "root_path": "absolute or repo-relative path",
    "root_role": "ticks | bars | shadow_logs | source_artifacts | sierra_cache | vendor_cache | prior_worktree",
    "scan_patterns": "extensions or exact file names"
  },
  "artifact_family": "worktree_bootstrap_data_root_resolver_design",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T06:33:15Z",
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
  "prior_worktree_cache_search_policy": [
    "Treat prior worktree data as discovery leads until source hashes and commit context are bound.",
    "Search exact route names and manifests before broad recursive scans.",
    "Never admit a row solely because it exists in a stale worktree."
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "safe_reference_guidance": [
    "Prefer source-reference manifests over copying heavy files into a route.",
    "Use symlink or copy only after owner approval if the target sits outside writable roots or if files are large.",
    "Record original path, copied path, raw SHA, file size, and as-of rule whenever a source file is moved into a packet."
  ],
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false,
  "worktree_local_absence_rule": "Worktree-local absence is an intermediate state; the final artifact must record recovery, exact owner/export action, or non-generatable source truth.",
  "worktree_preflight_checklist": [
    "Regenerate LIVE_STATE and record HEAD.",
    "Record cwd and writable roots.",
    "Run git status and cached diff path list.",
    "Resolve current worktree data roots.",
    "Resolve absolute main repo data roots.",
    "Resolve prior worktree roots under C:\\tmp\\gtos_otb.",
    "Resolve Sierra/vendor cache roots if present.",
    "Record positive and negative root evidence before final blocker classification."
  ]
}
```
