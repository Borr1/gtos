# Candidate Window Source Group Coverage Matrix

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "all_candidate_groups_covered": true,
  "artifact_family": "CANDIDATE_WINDOW_SOURCE_GROUP_COVERAGE_MATRIX",
  "candidate_summary": {
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
  "coverage_row_count": 7,
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
  "result_denominator_opened": false,
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "rows": [
    {
      "broker_native_market_tick_context_present_external_prior_root": false,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 48,
      "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
      "cfd_symbol": "EURUSD",
      "contracts_or_roots": [
        "6EM26-CME",
        "EURUSD"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "6EM26-CME.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 509,
      "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY",
      "cfd_symbol": "GBPUSD",
      "contracts_or_roots": [
        "6BM26-CME"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "6BM26-CME.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 509,
      "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY",
      "cfd_symbol": "NAS100",
      "contracts_or_roots": [
        "NQM26-CME",
        "MNQM26-CME"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "NQM26-CME.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 509,
      "canonical_economic_group": "US30_DOW_FUTURES_PROXY",
      "cfd_symbol": "US30_cash",
      "contracts_or_roots": [
        "YMM26-CBOT",
        "MYMM26-CBOT"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "YMM26-CBOT.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 509,
      "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY",
      "cfd_symbol": "USDJPY",
      "contracts_or_roots": [
        "6JM26-CME"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY_INVERSE_FX_CONTRACT",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "6JM26-CME.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 421,
      "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY",
      "cfd_symbol": "XAGUSD",
      "contracts_or_roots": [
        "SIM26-COMEX",
        "SILM26-COMEX"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "SIM26-COMEX.scid"
    },
    {
      "broker_native_market_tick_context_present_external_prior_root": true,
      "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
      "candidate_rows": 509,
      "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
      "cfd_symbol": "XAUUSD",
      "contracts_or_roots": [
        "GCM26-COMEX",
        "MGCM26-COMEX",
        "XAUUSD"
      ],
      "converted_m1_present": true,
      "converted_m5_present": true,
      "fail_closed_if_missing": [],
      "immediate_source_control_expandability": "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE",
      "path_context_shadow_sources_present": true,
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "session_volatility_context_present": true,
      "sierra_depth_present": true,
      "sierra_scid_present": true,
      "source_file_name": "GCM26-COMEX.scid"
    }
  ],
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "validation_safe": false
}
```
