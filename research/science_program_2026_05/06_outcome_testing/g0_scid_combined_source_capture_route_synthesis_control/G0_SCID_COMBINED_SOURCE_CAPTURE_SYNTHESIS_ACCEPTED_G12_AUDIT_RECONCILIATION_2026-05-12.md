# Accepted G12 Audit Reconciliation

- **route_id:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g12_control_evidence_only": true,
  "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "artifact_family": "ACCEPTED_G12_AUDIT_RECONCILIATION",
  "blocking_unrepaired_hash_mismatches": [],
  "candidate_rows": 3014,
  "capture_contract_exactness_ok": true,
  "changes_live_trading_behavior": false,
  "control_evidence_boundary": "Accepted as source/control evidence only; not validation, not strategy performance, not live behavior.",
  "credentials_touched": false,
  "evidence_class": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY",
  "exact_reconciliation_checks": [
    {
      "actual": 3014,
      "check_id": "candidate_rows",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "unique_candidate_ids",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "unique_duplicate_keys",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "field_status_recomputation",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "source_search_saturation",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "capture_contract_exactness",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "noleak_forbidden_surface",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "hash_binding_after_repair",
      "expected": true,
      "status": "PASS"
    }
  ],
  "field_status_recomputation_ok": true,
  "generated_at_utc": "2026-05-12T02:35:23Z",
  "live_effect": false,
  "noleak_forbidden_surface_ok": true,
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
  "route_id": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_combined_source_capture_synthesis_v1",
  "source_hash_manifest_binding_ok_after_repair": true,
  "source_search_result": "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS",
  "source_search_saturation_ok": true,
  "unique_candidate_input_row_ids": 3014,
  "unique_duplicate_proxy_denominator_keys": 3014,
  "validation_safe": false
}
```
