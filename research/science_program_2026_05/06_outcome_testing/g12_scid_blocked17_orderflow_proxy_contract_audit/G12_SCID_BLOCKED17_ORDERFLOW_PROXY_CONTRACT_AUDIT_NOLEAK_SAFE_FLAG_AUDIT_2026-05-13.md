# No-Leak Safe-Flag Audit

```json
{
  "artifact_family": "NOLEAK_SAFE_FLAG_AUDIT",
  "asof_policy": [
    "Source event time used for context must be <= decision_asof_utc.",
    "Publication_or_capture_asof_utc must be recorded separately from source event time.",
    "Delayed-feed, Sunday/holiday, clear-book-only, sparse-symbol, and stale-window states must be explicit flags.",
    "No target, result, cancel, post-fill, account, order, deal, position, or PnL field can select source windows."
  ],
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "checks": {
    "asof_policy_present": true,
    "broker_account_order_history_deal_position_sources_consumed_zero": true,
    "broker_native_cfd_truth_claims_zero": true,
    "hash_policy_present": true,
    "paid_vendor_access_opened_false": true,
    "raw_market_blob_commit_policy_blocks_raw_commit": true,
    "raw_market_blob_commits_added_zero": true,
    "redaction_policy_present": true,
    "target_artifact_safe_flags_ok": true,
    "target_no_leak_ok": true,
    "target_text_forbidden_true_flag_hits_zero": true
  },
  "credentials_touched": false,
  "evidence_class": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T04:50:06Z",
  "hash_policy": [
    "Small committed artifacts must carry sha256.",
    "Large external raw files must carry path, size, mtime, and sha256 or a G12-accepted hash-deferral reason before future use.",
    "Any no-commit hash job must write only metadata and hashes, not raw market bytes.",
    "Text artifacts should use byte hash plus any accepted LF-normalized hash policy only when prior G12 accepts equivalence."
  ],
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
  "raw_market_blob_commits_added": 0,
  "redaction_policy": [
    "Do not consume or emit broker account/order/history/deal/position identifiers.",
    "Do not emit credentials, account numbers, API keys, or vendor auth material.",
    "Use source family, symbol, contract, window, path, size, mtime, and hash/deferral ids only."
  ],
  "route_id": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT",
  "safe_flag_failure_count": 0,
  "safe_flag_failures": [],
  "safe_flag_rows": [
    {
      "artifact_key": "completion",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "manifest",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "source_contract",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "equivalence",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "blocker",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "source_dependency",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "asof_hash",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "noleak",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "route_decision",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "context_schema",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "target_verification",
      "errors": [],
      "ok": true
    },
    {
      "artifact_key": "target_focused_test",
      "errors": [],
      "ok": true
    }
  ],
  "schema_version": "g12_scid_blocked17_orderflow_proxy_contract_audit_v1",
  "target_text_forbidden_true_flag_hits": [],
  "validation_safe": false
}
```
