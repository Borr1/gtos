# SCID Combined Schema Redaction As-Of No-Leak Specification

- **route_id:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE`
- **evidence_class:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "schema_redaction_asof_noleak_specification",
  "as_of_policy": [
    "source decision fields must be timestamped at or before decision_asof_utc",
    "LTF/orderflow context must use only pre-decision source windows unless forensic-only",
    "baseline-control assignment must be frozen before result opening"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_policy": "candidate_input_row_id and duplicate_proxy_denominator_key must remain one-to-one for all 3,014 rows; future cohorts require a new immutable denominator ledger",
  "evidence_class": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY",
  "generated_at_utc": "2026-05-12T01:06:39Z",
  "live_effect": false,
  "no_leak_policy": [
    "no target/result/performance fields in source/capture artifacts",
    "no price-derived historical intent",
    "no weak symbol-time join accepted as source truth",
    "no broker/account evidence in this evidence class"
  ],
  "offline_schema_versions": {
    "baseline_control": "scid_baseline_control_assignment_v1",
    "candidate_status": "scid_combined_candidate_source_capture_status_v1",
    "future_capture": "scid_forward_source_capture_v1"
  },
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
  "redaction_policy": [
    "no credentials",
    "no account balances",
    "no broker account/order/history/deal/position payloads",
    "no raw market blob commit",
    "redacted bridge hashes only where a future evidence class permits order observability"
  ],
  "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
  "schema_version": "scid_combined_source_capture_route_v1",
  "validation_safe": false
}
```
