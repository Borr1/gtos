# External Approval Source Gate Ledger

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "approval_gates": [
    {
      "current_status": "METADATA_MANIFESTED_HASH_DEFERRED",
      "exact_approval_required": "Owner approval for no-commit raw parse/hash/export job naming contracts, dates, fields, parser, output path, and raw-blob non-commit policy.",
      "gate_id": "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT",
      "needed_for": "Hash-bound SCID/depth row materialization or selected candidate-window extraction.",
      "source": "C:/SierraChart/Data and MarketDepthData"
    },
    {
      "current_status": "ABSOLUTE_ROOT_FOUND_CURRENT_WORKTREE_EMPTY",
      "exact_approval_required": "Owner approval to consume/copy/hash selected symbol/date parquet files without raw blob commit.",
      "gate_id": "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
      "needed_for": "Broker-native market tick/spread LTF context, not account/order evidence.",
      "source": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks"
    },
    {
      "current_status": "BLOCKED_NO_API_PAID_VENDOR_CALLS_ALLOWED_IN_THIS_ROUTE",
      "exact_approval_required": "Separate pre-call manifest with dataset, symbols, windows, estimated cost/free-credit proof, cap, and owner approval.",
      "gate_id": "GATE_DATABENTO_NEW_PULL",
      "needed_for": "Any uncached historical orderflow/depth window.",
      "source": "Databento futures MBO/MBP/trades"
    },
    {
      "current_status": "LIVE_WIRING_ABSENT_REQUIRED_BY_ACCEPTED_PACKAGE",
      "exact_approval_required": "Future implementation route plus owner approval; must be additive, fail-open, no-decision-impact, and G12/G0 accepted.",
      "gate_id": "GATE_LIVE_WIRING",
      "needed_for": "Actual runtime population of accepted offline schema groups.",
      "source": "forward capture logger/runtime integration"
    },
    {
      "current_status": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
      "exact_approval_required": "Separate owner-approved broker-truth evidence lane only; this route must not open it.",
      "gate_id": "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
      "needed_for": "Not needed in this route; explicitly forbidden.",
      "source": "account/order/history/deal/position evidence"
    }
  ],
  "artifact_family": "EXTERNAL_APPROVAL_SOURCE_GATE_LEDGER",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
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
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "unresolved_vague_blockers": [],
  "validation_safe": false
}
```
