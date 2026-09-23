# Source Status Recomputation Audit

```json
{
  "allowed_statuses": [
    "EXACT_OWNER_ACCESS_REQUIRED",
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "PROXY_VALIDITY_REQUIRES_CONTRACT",
    "RECOVERED_SOURCE_BOUND",
    "SOURCE_EXISTS_NEEDS_PARSER"
  ],
  "artifact_family": "SOURCE_STATUS_RECOMPUTATION_AUDIT",
  "card_count": 17,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T18:00:40Z",
  "live_effect": false,
  "ok": true,
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
  "per_card_rows": [
    {
      "card_id": "ADV-002",
      "failures": [],
      "field_count": 8,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "adversarial_baselines_placebo_explanations",
      "status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "EXE-001",
      "failures": [],
      "field_count": 8,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "execution_science_spread_slippage_fillability",
      "status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "EXE-003",
      "failures": [],
      "field_count": 13,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "execution_science_spread_slippage_fillability",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "EXE-005",
      "failures": [],
      "field_count": 16,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "execution_science_spread_slippage_fillability",
      "status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "GEO-002",
      "failures": [],
      "field_count": 8,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "geometry_topology_path_shape",
      "status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "GEO-003",
      "failures": [],
      "field_count": 15,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "geometry_topology_path_shape",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "GEO-004",
      "failures": [],
      "field_count": 13,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "geometry_topology_path_shape",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "HAZ-003",
      "failures": [],
      "field_count": 23,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "stochastic_tail_hazard_first_passage",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "PROSPECTIVE_CAPTURE_REQUIRED": 10,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "HAZ-004",
      "failures": [],
      "field_count": 16,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "stochastic_tail_hazard_first_passage",
      "status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "MAC-003",
      "failures": [],
      "field_count": 17,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-001",
      "failures": [],
      "field_count": 9,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 1
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-002",
      "failures": [],
      "field_count": 16,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-003",
      "failures": [],
      "field_count": 16,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 1
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "MIC-004",
      "failures": [],
      "field_count": 17,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-005",
      "failures": [],
      "field_count": 16,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "UNC-001",
      "failures": [],
      "field_count": 24,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "UNC-005",
      "failures": [],
      "field_count": 22,
      "fields_match_g0_exact_missing_list": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 6,
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_status_families_present": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": true,
    "PROSPECTIVE_CAPTURE_REQUIRED": true,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": true,
    "RECOVERED_SOURCE_BOUND": true,
    "SOURCE_EXISTS_NEEDS_PARSER": true
  },
  "route_id": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT",
  "schema_version": "g12_scid_ltf_proxy_blocked17_source_status_audit_v1",
  "status_counts": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 35,
    "PROSPECTIVE_CAPTURE_REQUIRED": 25,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": 64,
    "RECOVERED_SOURCE_BOUND": 55,
    "SOURCE_EXISTS_NEEDS_PARSER": 78
  },
  "terminal_source_status_counts": {
    "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY": 6,
    "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED": 4,
    "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED": 7
  },
  "validation_safe": false
}
```
