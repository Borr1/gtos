# Accepted Audit Reconciliation

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g0_offline_schema_decision": "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE",
  "accepted_g12_combined_source_capture_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "accepted_g12_offline_schema_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "artifact_family": "ACCEPTED_AUDIT_RECONCILIATION",
  "candidate_boundary": {
    "candidate_boundary_status": "PRESERVED_3014_SOURCE_CONTROL_COVERAGE_NOT_RESULT_DENOMINATOR",
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
    "source_file_counts": {
      "6BM26-CME.scid": 509,
      "6EM26-CME.scid": 48,
      "6JM26-CME.scid": 509,
      "GCM26-COMEX.scid": 509,
      "NQM26-CME.scid": 509,
      "SIM26-COMEX.scid": 421,
      "YMM26-CBOT.scid": 509
    },
    "symbol_counts": {
      "EURUSD": 48,
      "GBPUSD_6B": 509,
      "NAS100_NQ": 509,
      "US30_YM": 509,
      "USDJPY_6J": 509,
      "XAGUSD_SI": 421,
      "XAUUSD_GC": 509
    },
    "unique_candidate_input_row_ids": 3014,
    "unique_duplicate_proxy_denominator_keys": 3014
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
  "live_effect": false,
  "live_wiring_absent": true,
  "manifest_binding_repair_preserved": {
    "all_other_hash_mismatches_strict": true,
    "blocking_unrepaired_hash_mismatches": [],
    "current_g12_prompt_hash_rebound": [
      {
        "current_sha256": "c01d6ddbfe917972ef0995fc3c5f54f13c9ee706ff4acc4a002def552469dfe7",
        "manifest_sha256": "d6eca5dcfe78f6bd6a1f0301ab7d43a59ec81d24fef10ccb48f7438d6fea7d25",
        "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md"
      }
    ],
    "self_referential_manifest_hash_drift_nonblocking": true
  },
  "offline_only_boundary": "offline schema/parser/fixture/validator/read-only alignment evidence only",
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
  "reconciliation_checks": [
    {
      "actual": 3014,
      "check_id": "candidate_rows_3014",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "unique_candidate_ids_3014",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "unique_duplicate_keys_3014",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 10,
      "check_id": "ten_capture_groups",
      "expected": 10,
      "status": "PASS"
    }
  ],
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "ten_capture_groups": [
    "side",
    "entry",
    "stop",
    "target",
    "POI",
    "framework",
    "lifecycle",
    "LTF",
    "orderflow/proxy",
    "baseline-control"
  ],
  "validation_safe": false
}
```
