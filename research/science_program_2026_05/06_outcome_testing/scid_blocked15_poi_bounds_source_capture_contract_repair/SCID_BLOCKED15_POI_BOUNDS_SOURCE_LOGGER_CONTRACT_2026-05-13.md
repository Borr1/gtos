# Source Logger Contract

```json
{
  "accepted_40_denominator_unblocked_now": false,
  "artifact_family": "source_logger_contract",
  "as_of_rule": {
    "forbidden": "post-decision path, target status, fill/cancel/result labels, broker/account/order/history/deal/position evidence",
    "mso_snapshot_asof_utc": "must be <= decision_asof_utc",
    "poi_detection_asof_utc": "must be <= decision_asof_utc",
    "source_bar_refs.bar_end_exclusive_utc": "must be <= decision_asof_utc",
    "source_observed_asof_utc": "must be <= decision_asof_utc"
  },
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
  "field_contracts": [
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "schema_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "route_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "evidence_class",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "candidate_input_row_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "duplicate_proxy_denominator_key",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "target_card_ids",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "field_group",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "decision_asof_utc",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_observed_asof_utc",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_event_clock_basis",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_logger_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_logger_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "parser_contract_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_identifier",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_hash_policy",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_hash",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "redaction_policy_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "forbidden_value_policy_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "missing_status_policy",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "field_status",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "fail_closed_reason_code",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "downstream_g12_acceptance_rule",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_type_enum_ob_fvg_breaker_swing_other_none",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_mechanism_family",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_subtype",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_lower_bound",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_upper_bound",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_bound_currency_or_points",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "tick_size",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "price_precision",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "bounds_normalization_rule_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_source_timeframe",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_source_bar_ids",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_bar_refs",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_bar_set_hash",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "mso_snapshot_schema_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "mso_snapshot_asof_utc",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "mso_snapshot_hash",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "market_state_builder_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "market_state_input_hash",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_detection_rule_version",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "poi_detection_code_hash",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "selected_poi_id",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "mso_snapshot_commitment",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "card_dependency_statuses",
      "required": true
    },
    {
      "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "name": "source_truth_class",
      "required": true
    }
  ],
  "field_group": "poi_type_bounds_source",
  "g12_acceptance_criteria": [
    "Verify all five target cards have exact fail-closed requirements.",
    "Verify all source hashes and MSO/source-bar hashes recompute.",
    "Verify no as-of timestamp is after decision_asof_utc.",
    "Verify no forbidden broker/account/order/history/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, promotion, AI/API, paid-vendor, raw-blob, or live-behavior field is present.",
    "Verify no accepted 40-card denominator row moves to result eligibility from this contract alone."
  ],
  "generated_at_utc": "2026-05-13T03:45:00Z",
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
  "parser_requirement": {
    "canonical_hash": "sha256(canonical JSON with sorted keys, compact separators, ASCII escaping)",
    "duplicate_policy": "candidate_input_row_id maps to one duplicate_proxy_denominator_key across the packet",
    "fail_closed_policy": [
      "POI_BOUNDS_CAPTURED_SOURCE_SAFE",
      "POI_BOUNDS_NO_POI_SOURCE_SAFE",
      "POI_BOUNDS_SOURCE_UNAVAILABLE_FAIL_CLOSED",
      "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
      "POI_BOUNDS_ASOF_VIOLATION_FAIL_CLOSED",
      "POI_BOUNDS_HASH_MISMATCH_FAIL_CLOSED",
      "POI_BOUNDS_FORBIDDEN_FIELD_FAIL_CLOSED",
      "POI_BOUNDS_DEPENDENCY_MISSING_FAIL_CLOSED"
    ],
    "input_format": "append-only JSONL or synthetic fixture JSON/JSONL",
    "mso_snapshot_hash": "sha256(mso_snapshot_commitment)",
    "source_bar_set_hash": "sha256(source_bar_refs)",
    "source_hash": "sha256(row without source_hash)"
  },
  "poi_mechanism_families_v2": [
    "ob_zone",
    "fvg_gap",
    "breaker_zone",
    "swing_boundary",
    "liquidity_sweep_zone",
    "round_number_band",
    "volume_profile_zone",
    "geometry_envelope",
    "macro_calendar_context_zone",
    "other_source_bound_poi",
    "none"
  ],
  "poi_type_enum_v1_compatibility": [
    "ob",
    "fvg",
    "breaker",
    "swing",
    "other",
    "none"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proposed_append_only_path": "shadow_logs/scid_poi_bounds_source_capture.jsonl",
  "redaction_rule": {
    "allowed_identifiers": "candidate ids, source-local synthetic or hashed ids, source-bar hashes, redacted bridge hashes only",
    "forbidden_key_fragments": [
      "account",
      "broker_order",
      "broker_actual",
      "deal",
      "expectancy",
      "mt5_order",
      "mt5_position",
      "order_history",
      "pnl",
      "position",
      "profit",
      "raw_ohlc",
      "raw_market",
      "realized",
      "result",
      "r_multiple",
      "ticket",
      "win_rate"
    ],
    "policy_id": "SCID_POI_BOUNDS_NO_BROKER_ORDER_ACCOUNT_DEAL_POSITION_IDS_V1"
  },
  "route_id": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
  "schema_version": "scid_blocked15_poi_bounds_capture_contract_v1",
  "schema_version_required": "scid_blocked15_poi_bounds_capture_contract_v1",
  "source_logger_id": "source_safe_mso_snapshot_and_poi_logger",
  "target_cards": [
    "ADV-005",
    "BEH-002",
    "BEH-003",
    "BEH-005",
    "GEO-001"
  ],
  "validation_safe": false
}
```
