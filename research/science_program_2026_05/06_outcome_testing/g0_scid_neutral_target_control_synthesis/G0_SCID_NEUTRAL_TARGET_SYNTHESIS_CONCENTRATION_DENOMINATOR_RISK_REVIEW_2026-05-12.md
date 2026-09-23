# Concentration And Denominator Risk Review

- **route_id:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS`
- **evidence_class:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "concentration_denominator_risk_review",
  "candidate_rows": 3014,
  "canonical_economic_group_counts": {
    "EURUSD_FUTURES_6E_PROXY": 48,
    "GBPUSD_FUTURES_6B_PROXY": 509,
    "NAS100_NQ_FUTURES_PROXY": 509,
    "US30_DOW_FUTURES_PROXY": 509,
    "USDJPY_FUTURES_6J_PROXY": 509,
    "XAGUSD_SILVER_FUTURES_PROXY": 421,
    "XAUUSD_GOLD_FUTURES_PROXY": 509
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "denominator_group_count": 7,
  "denominator_policy_for_next_route": [
    "Preserve candidate row id and duplicate_proxy_denominator_key exactly.",
    "Preserve canonical_economic_group and source_file_name in every closure row.",
    "Fail closed when a strategy-field source maps multiple records to one candidate without a deterministic as-of tie-breaker."
  ],
  "duplicate_key_collision_count": 0,
  "duplicate_key_count": 3014,
  "evidence_class": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-11T22:53:11Z",
  "live_effect": false,
  "max_group_share": 0.16887856668878568,
  "max_symbol_share": 0.16887856668878568,
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
  "partition_counts": {
    "SEALED_VALIDATION_CANDIDATE_DESIGN": 2432,
    "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": 582
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS",
  "schema_version": "g0_scid_neutral_target_control_synthesis_v1",
  "small_denominator_risks": [
    "EURUSD has 48 candidate rows and must not drive future route selection by itself.",
    "XAGUSD_SI has 421 candidate rows while most other primary groups have 509; future pooled claims need group-aware concentration caps.",
    "The packet has zero duplicate-key collisions, but future strategy-field joins can reintroduce denominator ambiguity if source fields are many-to-one."
  ],
  "symbol_counts": {
    "EURUSD": 48,
    "GBPUSD_6B": 509,
    "NAS100_NQ": 509,
    "US30_YM": 509,
    "USDJPY_6J": 509,
    "XAGUSD_SI": 421,
    "XAUUSD_GC": 509
  },
  "validation_safe": false
}
```
