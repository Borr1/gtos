# Accepted G12 Audit Reconciliation

- **route_id:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS`
- **evidence_class:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_control_evidence_only": true,
  "accepted_promotion": false,
  "accepted_strategy_performance": false,
  "accepted_validation_execution": false,
  "artifact_family": "accepted_g12_audit_reconciliation",
  "candidate_rows": 3014,
  "changes_live_trading_behavior": false,
  "closure_rows": 3014,
  "counts_by_canonical_economic_group": {
    "EURUSD_FUTURES_6E_PROXY": 48,
    "GBPUSD_FUTURES_6B_PROXY": 509,
    "NAS100_NQ_FUTURES_PROXY": 509,
    "US30_DOW_FUTURES_PROXY": 509,
    "USDJPY_FUTURES_6J_PROXY": 509,
    "XAGUSD_SILVER_FUTURES_PROXY": 421,
    "XAUUSD_GOLD_FUTURES_PROXY": 509
  },
  "counts_by_symbol": {
    "EURUSD": 48,
    "GBPUSD_6B": 509,
    "NAS100_NQ": 509,
    "US30_YM": 509,
    "USDJPY_6J": 509,
    "XAGUSD_SI": 421,
    "XAUUSD_GC": 509
  },
  "credentials_touched": false,
  "evidence_class": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY",
  "exact_reconciliation_checks": [
    {
      "actual": "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY",
      "check_id": "g12_terminal_decision",
      "expected": "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY",
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "candidate_rows",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "closure_rows",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3,
      "check_id": "closed_field_families",
      "expected": 3,
      "status": "PASS"
    },
    {
      "actual": 7,
      "check_id": "fail_closed_field_families",
      "expected": 7,
      "status": "PASS"
    },
    {
      "actual": 2,
      "check_id": "prospective_capture_field_families",
      "expected": 2,
      "status": "PASS"
    },
    {
      "actual": 1,
      "check_id": "forbidden_field_families",
      "expected": 1,
      "status": "PASS"
    },
    {
      "actual": 0,
      "check_id": "forbidden_result_key_hits",
      "expected": 0,
      "status": "PASS"
    },
    {
      "actual": 0,
      "check_id": "forbidden_broker_key_hits",
      "expected": 0,
      "status": "PASS"
    }
  ],
  "fail_prospective_forbidden_audit_ok": true,
  "field_status_audit_ok": true,
  "generated_at_utc": "2026-05-12T00:19:24Z",
  "live_effect": false,
  "noleak_forbidden_surface_audit_ok": true,
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
  "route_id": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS",
  "row_coverage_ok": true,
  "safe_flags_closed": {
    "NO_PROMOTION_VERDICT": true,
    "live_effect": false,
    "outcome_review_opened": false,
    "validation_safe": false
  },
  "schema_version": "g0_scid_strategy_field_packet_synthesis_v1",
  "source_hash_input_binding_verified": true,
  "terminal_decision_from_g12": "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY",
  "unique_candidate_ids": 3014,
  "unique_duplicate_proxy_denominator_keys": 3014,
  "validation_safe": false
}
```
