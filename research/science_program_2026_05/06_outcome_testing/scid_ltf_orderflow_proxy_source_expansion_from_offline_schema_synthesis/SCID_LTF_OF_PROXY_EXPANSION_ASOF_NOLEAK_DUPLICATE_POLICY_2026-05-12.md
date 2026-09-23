# As Of No Leak Publication Duplicate Policy Ledger

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "ASOF_NOLEAK_PUBLICATION_DUPLICATE_POLICY_LEDGER",
  "asof_policies": [
    {
      "rule": "Only events with source timestamp <= decision_asof_utc may populate decision-time fields.",
      "source_family": "LTF bars/ticks"
    },
    {
      "rule": "Pre-decision windows only; post-decision depth/trades may be forensic context only and cannot enter source/control input packet.",
      "source_family": "orderflow/depth"
    },
    {
      "rule": "Publication/session bucket must be known as of candidate time or marked unavailable.",
      "source_family": "session volatility"
    },
    {
      "rule": "Proxy contract, roll, inverse mapping, point value, and timezone policy must be frozen before row admission.",
      "source_family": "proxy mapping"
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_policy": {
    "candidate_input_row_id_expected_unique": 3014,
    "duplicate_proxy_denominator_key_expected_unique": 3014,
    "duplicate_rule": "Carry accepted duplicate_proxy_denominator_key exactly; never convert source groups into result denominators."
  },
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "forbidden_fields_fail_closed": [
    "broker account/order/history/deal/position identifiers",
    "terminal target status",
    "R/PnL/win-rate/expectancy/performance/result labels",
    "post-cancel or post-fill source-state unless lane explicitly owns lifecycle capture"
  ],
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
  "validation_safe": false
}
```
