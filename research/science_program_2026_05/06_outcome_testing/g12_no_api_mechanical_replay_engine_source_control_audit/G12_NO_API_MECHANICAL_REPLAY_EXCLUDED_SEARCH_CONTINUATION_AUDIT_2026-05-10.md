# Excluded Search Continuation Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "excluded_searched_continuation_audit",
  "changes_live_trading_behavior": false,
  "continuation_row_count": 5,
  "continuation_terminal_statuses": [
    "CLEARED",
    "BOUNDED_ARTIFACT_WITH_MACHINE_CHECKABLE_COUNTS_AND_DIGESTS",
    "EXACT_PARSER_CONTRACT_BLOCKER",
    "EXACT_EVIDENCE_CLASS_BLOCKER",
    "FORBIDDEN_BOUNDARY_NOT_OPENED"
  ],
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "excluded_by_reason": {
    "EXCLUDED_D1_CONTEXT_ONLY_FOR_INTRADAY_REPLAY": 151,
    "EXCLUDED_DUPLICATE_SOURCE_HASH_ALREADY_SELECTED": 204,
    "EXCLUDED_SOURCE_FAMILY_NOT_OHLCV_REPLAY_INPUT": 2731,
    "EXCLUDED_TIMEFRAME_OR_SCHEMA_NOT_REPLAYABLE": 49
  },
  "excluded_slice_count": 3135,
  "generated_at_utc": "2026-05-10T21:10:22+00:00",
  "issues": [],
  "live_effect": false,
  "native_depth_tick_gtos_blockers_are_exact": true,
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
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "searched_root_count": 12,
  "searched_roots_used": [
    "current_worktree_data",
    "current_research_source_control",
    "absolute_main_tick_root",
    "absolute_main_data_root",
    "absolute_main_shadow_logs",
    "sierra_chart_data_root",
    "prior_worktrees_root"
  ],
  "status": "PASS",
  "validation_safe": false
}
```
