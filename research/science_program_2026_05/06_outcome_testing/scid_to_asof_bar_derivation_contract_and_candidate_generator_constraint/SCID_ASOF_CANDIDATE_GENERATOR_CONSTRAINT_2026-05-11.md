# SCID As-Of Candidate Generator Constraint

- Route: `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`
- Evidence class: `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "candidate_packet_schema_frozen": true,
  "candidate_rows_allowed_now": false,
  "validation_execution_allowed": false
}
```

## Payload

```json
{
  "allowed_candidate_feature_families": [
    "as_of_ohlcv_bars",
    "as_of_bid_ask_volume_from_scid_record",
    "as_of_trade_count",
    "source_gap_flags",
    "source_session_flags_from_frozen_calendar",
    "duplicate_proxy_metadata",
    "source_provenance_hashes",
    "predecision_market_structure_features_if_computed_only_from_included_bars"
  ],
  "artifact_family": "candidate_generator_constraint",
  "changes_live_trading_behavior": false,
  "constraint_decision": "FUTURE_CANDIDATE_GENERATOR_INPUTS_ONLY_NO_VALIDATION_ROWS",
  "credentials_touched": false,
  "evidence_class": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY",
  "forbidden_candidate_feature_families": [
    "r_multiple",
    "realized_r",
    "actual_r",
    "broker_actual_r",
    "pnl",
    "profit",
    "loss",
    "win",
    "win_rate",
    "expectancy",
    "performance",
    "cost",
    "slippage",
    "spread_paid",
    "commission",
    "outcome",
    "result",
    "label",
    "path_label",
    "target_hit",
    "stop_hit",
    "future_",
    "next_bar",
    "post_decision",
    "account",
    "balance",
    "equity",
    "order",
    "ticket",
    "deal",
    "position",
    "fill_price",
    "close_price",
    "ai_response",
    "claude",
    "prompt_output",
    "live_trade"
  ],
  "future_packet_preconditions": [
    "this contract accepted by independent G12 contract audit",
    "source segment references rehashed against accepted manifest",
    "bar builder lane emits only as-of bars and provenance hashes",
    "duplicate/proxy policy copied by value into packet",
    "365 discovery exclusions copied by reference and enforced",
    "four adversarial baselines copied exactly by id",
    "no sealed validation/result prompt opened in the same lane"
  ],
  "generated_at_utc": "2026-05-11T11:51:25Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_candidate_input_row_fields": [
    "candidate_input_row_id",
    "row_hash",
    "candidate_family_id",
    "symbol",
    "canonical_economic_group",
    "source_file_name",
    "segment_records_sha256",
    "interval",
    "decision_asof_utc",
    "bar_window_start_utc",
    "bar_window_end_utc",
    "included_bar_hashes",
    "last_included_bar_end_exclusive_utc",
    "asof_feature_schema_version",
    "duplicate_key",
    "partition_assignment",
    "forbidden_field_scan_passed",
    "candidate_input_only_status"
  ],
  "required_packet_fields": [
    "packet_id",
    "packet_schema_version",
    "contract_ref",
    "contract_sha256",
    "builder_script_ref",
    "builder_script_sha256",
    "source_segment_manifest_ref",
    "source_segment_manifest_sha256",
    "g12_repair_reaudit_ref",
    "discovery_exclusion_ledger_ref",
    "adversarial_baseline_ids",
    "duplicate_proxy_policy_ref",
    "partition_assignment",
    "validation_safe",
    "outcome_review_opened",
    "live_effect"
  ],
  "route_id": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
  "schema_version": "scid_to_asof_bar_contract_v1",
  "silent_validation_guard": {
    "candidate_acceptance_claim_allowed": false,
    "candidate_packet_status_value": "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
    "future_lane_required_for_scoring": "SEPARATE_G0_OR_OWNER_APPROVED_SEALED_VALIDATION_EXECUTION_PROMPT",
    "path_label_columns_allowed": false,
    "performance_or_cost_columns_allowed": false,
    "result_columns_allowed": false
  },
  "summary": {
    "candidate_packet_schema_frozen": true,
    "candidate_rows_allowed_now": false,
    "validation_execution_allowed": false
  },
  "validation_safe": false
}
```
