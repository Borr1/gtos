# Duplicate

- **route_id:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET`
- **evidence_class:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "duplicate_proxy_denominator_preservation_ledger",
  "candidate_rows": 3014,
  "changes_live_trading_behavior": false,
  "counts_by_canonical_economic_group": {
    "EURUSD_FUTURES_6E_PROXY": 48,
    "GBPUSD_FUTURES_6B_PROXY": 509,
    "NAS100_NQ_FUTURES_PROXY": 509,
    "US30_DOW_FUTURES_PROXY": 509,
    "USDJPY_FUTURES_6J_PROXY": 509,
    "XAGUSD_SILVER_FUTURES_PROXY": 421,
    "XAUUSD_GOLD_FUTURES_PROXY": 509
  },
  "credentials_touched": false,
  "duplicate_key_collisions": {},
  "evidence_class": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY",
  "generated_at_utc": "2026-05-11T23:23:39Z",
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
  "preservation_rule": "Do not replace canonical candidate_input_row_id or duplicate_proxy_denominator_key. Later result-design lanes must preserve these keys exactly and keep proxy/duplicate denominator policy separate from row-count policy.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
  "schema_version": "scid_strategy_field_source_expansion_packet_v1",
  "unique_candidate_ids": 3014,
  "unique_duplicate_proxy_denominator_keys": 3014,
  "validation_safe": false
}
```
