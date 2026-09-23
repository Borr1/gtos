# As-Of Hash Redaction Policy

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "artifact_family": "ASOF_HASH_REDACTION_POLICY",
  "asof_policy": [
    "Source event time used for context must be <= decision_asof_utc.",
    "Publication_or_capture_asof_utc must be recorded separately from source event time.",
    "Delayed-feed, Sunday/holiday, clear-book-only, sparse-symbol, and stale-window states must be explicit flags.",
    "No target, result, cancel, post-fill, account, order, deal, position, or PnL field can select source windows."
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
  "generated_at_utc": "2026-05-13T02:48:20Z",
  "hash_policy": [
    "Small committed artifacts must carry sha256.",
    "Large external raw files must carry path, size, mtime, and sha256 or a G12-accepted hash-deferral reason before future use.",
    "Any no-commit hash job must write only metadata and hashes, not raw market bytes.",
    "Text artifacts should use byte hash plus any accepted LF-normalized hash policy only when prior G12 accepts equivalence."
  ],
  "hash_status_counts_from_g12_audit": {
    "HASHED_NOW": 11932,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 180,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 491,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 421
  },
  "hash_status_counts_from_source_inventory": {
    "HASHED_NOW": 11932,
    "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 180,
    "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 491,
    "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 421
  },
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
  "raw_market_blob_commit_policy": "No raw .depth, .scid, parquet, vendor, broker, or market blob is committed by this route.",
  "redaction_policy": [
    "Do not consume or emit broker account/order/history/deal/position identifiers.",
    "Do not emit credentials, account numbers, API keys, or vendor auth material.",
    "Use source family, symbol, contract, window, path, size, mtime, and hash/deferral ids only."
  ],
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "staleness_policy": [
    "Fail closed if source-status row is action-required or stale.",
    "Fail closed if proxy mapping predates a contract roll without refreshed roll metadata.",
    "Fail closed if raw source file was still being written and no no-change completion check exists."
  ],
  "validation_safe": false
}
```
