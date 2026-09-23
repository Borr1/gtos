# Field Status Summary

- **route_id:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET`
- **evidence_class:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "field_status_summary",
  "candidate_counts_by_symbol": {
    "EURUSD": 48,
    "GBPUSD_6B": 509,
    "NAS100_NQ": 509,
    "US30_YM": 509,
    "USDJPY_6J": 509,
    "XAGUSD_SI": 421,
    "XAUUSD_GC": 509
  },
  "changes_live_trading_behavior": false,
  "closed_field_families": [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons"
  ],
  "credentials_touched": false,
  "evidence_class": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY",
  "fail_closed_field_families": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
  ],
  "field_status_counts_by_field": {
    "broker_account_order_history_deal_position_evidence": {
      "FORBIDDEN_IN_THIS_EVIDENCE_CLASS": 3014
    },
    "canonical_candidate_and_denominator": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "framework_setup_family": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "future_orderflow_depth_proxy_requirements": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "intended_entry_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_side_direction": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_stop_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_target_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lifecycle_fill_cancel_expiry_source_status": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lower_timeframe_asof_path_availability": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "poi_type_bounds_source": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "source_control_coverage_not_computable_reasons": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "source_symbol_session_partition": {
      "CLOSED_FROM_SOURCE": 3014
    }
  },
  "field_status_enum": [
    "CLOSED_FROM_SOURCE",
    "FAIL_CLOSED_MISSING_SOURCE_FIELD",
    "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
    "PROSPECTIVE_CAPTURE_REQUIRED"
  ],
  "forbidden_field_families": [
    "broker_account_order_history_deal_position_evidence"
  ],
  "generated_at_utc": "2026-05-11T23:23:39Z",
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
  "prospective_capture_field_families": [
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "route_id": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
  "row_count": 3014,
  "schema_version": "scid_strategy_field_source_expansion_packet_v1",
  "unique_candidate_ids": 3014,
  "validation_safe": false,
  "weakest_source_field_closure_group": {
    "group": "NAS100_NQ_FUTURES_PROXY::SEALED_VALIDATION_CANDIDATE_DESIGN",
    "non_closed_status_count": 4180,
    "why": "All strategy-intent fields fail closed uniformly; source coverage is weakest for neutral-only candidates because no explicit strategy/source-state join exists."
  }
}
```
