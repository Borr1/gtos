# Proxy Validity Approval As-Of Audit

```json
{
  "all_proxy_rows_context_only": true,
  "approval_gate_ids": [
    "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
    "GATE_DATABENTO_NEW_PULL",
    "GATE_LIVE_WIRING",
    "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
    "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT"
  ],
  "artifact_family": "proxy_validity_approval_asof_audit",
  "asof_policy_count": 4,
  "asof_policy_gaps": [],
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_policy": {
    "candidate_input_row_id_expected_unique": 3014,
    "duplicate_proxy_denominator_key_expected_unique": 3014,
    "duplicate_rule": "Carry accepted duplicate_proxy_denominator_key exactly; never convert source groups into result denominators."
  },
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "expected_approval_gate_ids": [
    "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
    "GATE_DATABENTO_NEW_PULL",
    "GATE_LIVE_WIRING",
    "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
    "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT"
  ],
  "forbidden_fields_fail_closed": [
    "broker account/order/history/deal/position identifiers",
    "terminal target status",
    "R/PnL/win-rate/expectancy/performance/result labels",
    "post-cancel or post-fill source-state unless lane explicitly owns lifecycle capture"
  ],
  "generated_at_utc": "2026-05-12T07:45:56Z",
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
  "proxy_label_failures": [],
  "proxy_rows": 7,
  "proxy_validity_approval_asof_ok": true,
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "unresolved_vague_blockers": [],
  "vague_gate_failures": [],
  "validation_safe": false
}
```
