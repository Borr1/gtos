# Source Search Saturation Audit

```json
{
  "artifact_family": "source_search_saturation_audit",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T18:13:11Z",
  "hard_boundary_skips": [
    "broker account/order/history/deal/position files were not read or used",
    "raw market blobs were not committed or consumed as result evidence",
    "AI/API, paid vendor, live restart, and trading behavior routes were not opened",
    "price movement was not used to infer historical intent, order observability, lifecycle truth, or ticket state"
  ],
  "historical_non_generatable_boundary": {
    "lifecycle_truth": [
      "lifecycle_fill_cancel_expiry_source_status"
    ],
    "strategy_intent_truth": [
      "intended_side_direction",
      "intended_entry_reference",
      "intended_stop_reference",
      "intended_target_reference",
      "poi_type_bounds_source",
      "framework_setup_family"
    ],
    "why": "These fields require a source packet/log emitted by GTOS at decision or lifecycle time. Market price, ticks, bars, and later path movement cannot recreate them honestly."
  },
  "input_artifact_count": 19,
  "input_artifacts_all_exist_and_hash": true,
  "live_effect": false,
  "ok": true,
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
  "required_search_categories": {
    "absolute_local_roots": true,
    "accepted_artifacts": true,
    "additive_implementation_evidence": true,
    "code_tests_verifiers": true,
    "prior_worktrees": true,
    "shadow_logs": true
  },
  "route_id": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT",
  "same_evidence_class_recovery_routes_pursued": [
    "accepted G0 blocked-32 route ledger and route ranking matrix",
    "accepted SCID forward-capture additive implementation artifacts",
    "accepted combined source-search and forward-capture route artifacts",
    "accepted strategy-field source-expansion packet and G12/G0 ledgers",
    "current worktree source-safe shadow logs",
    "absolute main repo shadow logs and source artifacts",
    "parallel prior worktrees under C:/tmp/gtos_otb",
    "schema/tests/verifiers for SCID forward capture and lifecycle redaction"
  ],
  "same_evidence_class_recovery_routes_pursued_count": 8,
  "searched_root_count": 8,
  "searched_root_ids": [
    "absolute_main_repo_root",
    "current_worktree",
    "prior_parallel_worktree_r1_ready8_materialize",
    "prior_parallel_worktree_r2_ltf_proxy_source",
    "prior_parallel_worktree_r3_future_capture_source",
    "prior_parallel_worktree_r4_expansion_design",
    "prior_parallel_worktree_r5_anti_boxing_intake",
    "prior_parallel_worktree_r6_self_hash_maint"
  ],
  "source_file_summary": {
    "pending_limit_lifecycle": {
      "bytes": 461124,
      "exists": true,
      "line_count": 237,
      "path": "shadow_logs/pending_limit_lifecycle.jsonl",
      "sha256": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49"
    },
    "pending_limit_lifecycle_audit": {
      "bytes": 261922,
      "exists": true,
      "line_count": 89,
      "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
      "sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13"
    },
    "pending_limit_lifecycle_join_backfill": {
      "bytes": 528146,
      "exists": true,
      "line_count": 285,
      "path": "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
      "sha256": "0a146d00f936b85aa730f9e209d1b6ffb1cc387070944420d634c3aff5f504a0"
    },
    "scid_forward_source_capture": {
      "bytes": 0,
      "exists": false,
      "path": "shadow_logs/scid_forward_source_capture.jsonl",
      "sha256": null
    },
    "strategy_follow_candidates": {
      "bytes": 2461794,
      "exists": true,
      "line_count": 190,
      "path": "shadow_logs/strategy_follow_candidates.jsonl",
      "sha256": "79a78b9c8bc4f521de6a774d1519a90446fe6e731ef6626c6d9a1e126ee27e57"
    }
  },
  "target_evidence_class": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY",
  "target_route_id": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
  "validation_safe": false
}
```
