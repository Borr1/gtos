# Candidate Boundary And Capture Group Recomputation Audit

```json
{
  "artifact_family": "candidate_boundary_capture_group_recomputation_audit",
  "builder_reconciliation_mismatches": [],
  "candidate_boundary_capture_groups_ok": true,
  "candidate_summary_recomputed": {
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
  "duplicate_samples": {
    "candidate_input_row_id_duplicates": [],
    "duplicate_key_duplicates": []
  },
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "expected_canonical_economic_groups": [
    "EURUSD_FUTURES_6E_PROXY",
    "GBPUSD_FUTURES_6B_PROXY",
    "NAS100_NQ_FUTURES_PROXY",
    "US30_DOW_FUTURES_PROXY",
    "USDJPY_FUTURES_6J_PROXY",
    "XAGUSD_SILVER_FUTURES_PROXY",
    "XAUUSD_GOLD_FUTURES_PROXY"
  ],
  "generated_at_utc": "2026-05-12T07:45:55Z",
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
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "ten_capture_groups_expected": [
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
  "ten_capture_groups_recomputed_from_reconciliation": [
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
