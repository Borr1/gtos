# Source Status Recomputation Audit

```json
{
  "artifact_family": "SOURCE_STATUS_RECOMPUTATION_AUDIT",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY",
  "failures": [],
  "field_status_counts": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 35,
    "PROSPECTIVE_CAPTURE_REQUIRED": 25,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": 64,
    "RECOVERED_SOURCE_BOUND": 55,
    "SOURCE_EXISTS_NEEDS_PARSER": 78
  },
  "generated_at_utc": "2026-05-13T04:46:17Z",
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
  "per_card_source_exists_field_counts": {
    "ADV-002": 6,
    "EXE-001": 6,
    "EXE-003": 6,
    "EXE-005": 6,
    "GEO-002": 6,
    "GEO-003": 6,
    "GEO-004": 6,
    "HAZ-003": 6,
    "HAZ-004": 6,
    "MIC-002": 6,
    "MIC-005": 6,
    "UNC-001": 6,
    "UNC-005": 6
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT",
  "sample_source_exists_rows": [
    {
      "card_id": "ADV-002",
      "field": "asof_path_descriptor_version",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "ADV-002",
      "field": "bars_present_by_timeframe",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "ADV-002",
      "field": "decision_minus_window_start_utc",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "ADV-002",
      "field": "ltf_source_file_pointer_or_cache_id",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "ADV-002",
      "field": "ltf_source_hash",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "ADV-002",
      "field": "ltf_timeframes_available",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "EXE-001",
      "field": "asof_path_descriptor_version",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "card_id": "EXE-001",
      "field": "bars_present_by_timeframe",
      "next_requirement": "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    }
  ],
  "schema_version": "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_v1",
  "source_exists_card_count": 13,
  "source_exists_card_ids": [
    "ADV-002",
    "EXE-001",
    "EXE-003",
    "EXE-005",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "HAZ-003",
    "HAZ-004",
    "MIC-002",
    "MIC-005",
    "UNC-001",
    "UNC-005"
  ],
  "source_exists_field_row_count": 78,
  "source_exists_fields": [
    "asof_path_descriptor_version",
    "bars_present_by_timeframe",
    "decision_minus_window_start_utc",
    "ltf_source_file_pointer_or_cache_id",
    "ltf_source_hash",
    "ltf_timeframes_available"
  ],
  "upstream_card_count": 17,
  "validation_safe": false
}
```
