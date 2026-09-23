# Decision Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
  "artifact_family": "DECISION_LEDGER",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_checks": [
    {
      "check": "mandatory_context_read_from_disk",
      "passed": true
    },
    {
      "check": "accepted_g12_artifacts_read",
      "passed": true
    },
    {
      "check": "blocked17_denominator_preserved",
      "passed": true
    },
    {
      "check": "other_blocked15_excluded",
      "passed": true
    },
    {
      "check": "ready8_and_expansion_untouched",
      "passed": true
    },
    {
      "check": "all_17_cards_reconciled",
      "passed": true
    },
    {
      "check": "source_inventory_13024_rows_accounted",
      "passed": true
    },
    {
      "check": "broad_non_ob_proxy_ltf_routes_ranked",
      "passed": true
    },
    {
      "check": "safe_flags_preserved",
      "passed": true
    }
  ],
  "denominator_counts": {
    "blocked17_included": 17,
    "expansion_candidates_outside_denominator": 8,
    "other_blocked15_excluded": 15,
    "ready8_excluded": 8
  },
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-13T01:20:09Z",
  "live_effect": false,
  "objective_restatement": "Synthesize the accepted G12 blocked-17 LTF/orderflow/proxy source-status audit into a ranked, runnable source-control unblocking route bundle while preserving all denominators and safe flags.",
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
  "ranked_route_ids": [
    "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
    "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
    "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
    "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
    "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE"
  ],
  "result_gate_status": "CLOSED_UNTIL_SOURCE_INPUT_PREREQUISITES_PASS_AND_SEPARATE_RESULT_GATE_AUTHORIZES_OUTCOME_OPENING",
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "source_category_counts": {
    "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT": 60,
    "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 186,
    "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 593,
    "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 6142,
    "OTHER_RELEVANT_SOURCE_METADATA": 931,
    "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE": 30,
    "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 4545,
    "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 504,
    "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE": 33
  },
  "source_inventory_count": 13024,
  "source_status_counts": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 35,
    "PROSPECTIVE_CAPTURE_REQUIRED": 25,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": 64,
    "RECOVERED_SOURCE_BOUND": 55,
    "SOURCE_EXISTS_NEEDS_PARSER": 78
  },
  "terminal_decision": "ACCEPT_AS_G0_SOURCE_CONTROL_UNBLOCKING_ROUTE_BUNDLE_FOR_BLOCKED17",
  "validation_safe": false
}
```
