# Capture-Only Implementation Route Specification

- **route_id:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS`
- **evidence_class:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "capture_only_implementation_route_specification",
  "as_of_rules": [
    "Strategy source fields must be emitted at or before candidate decision_asof_utc.",
    "Explanatory market context must carry capture/publication/as-of timestamp and must be marked as candidate input or explanatory-only.",
    "Fields discovered after neutral target computation require separate G12 acceptance before any result design uses them."
  ],
  "capture_route_is_ranked_first": true,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY",
  "g12_acceptance_criteria": [
    "3014-row coverage or exact fail-closed exclusions.",
    "Field enum validity and no inferred historical intent.",
    "Source hashes and parser versions present.",
    "Duplicate/proxy denominator preservation.",
    "No target/result/performance or broker evidence fields.",
    "No live behavior or trading-surface diff unless owner-approved in a separate route."
  ],
  "generated_at_utc": "2026-05-12T00:19:24Z",
  "implementation_boundary": "This G0 emits a contract/prompt only. Future implementation must remain additive, fail-open, source/control-only, and no-live-effect unless separately owner-approved.",
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
  "rank_1_route": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
  "redaction_rules": [
    "No broker account/order/history/deal/position identifiers.",
    "No credentials, tickets, terminal account fields, or realized broker result fields.",
    "No target/result/performance labels.",
    "No raw market-data blob commits."
  ],
  "required_capture_field_groups": [
    {
      "field_group": "intended_side_direction",
      "schema_fields": [
        "intended_side",
        "direction_source",
        "direction_asof_utc",
        "source_artifact_hash"
      ],
      "truth_class": "explicit strategy source-state only; never infer from price movement"
    },
    {
      "field_group": "intended_entry_reference",
      "schema_fields": [
        "entry_reference_type",
        "entry_reference_price",
        "entry_source",
        "entry_asof_utc",
        "source_artifact_hash"
      ],
      "truth_class": "explicit candidate source-state only"
    },
    {
      "field_group": "intended_stop_reference",
      "schema_fields": [
        "stop_reference_type",
        "stop_reference_price",
        "stop_source",
        "stop_asof_utc",
        "source_artifact_hash"
      ],
      "truth_class": "explicit stop source-state only"
    },
    {
      "field_group": "intended_target_reference",
      "schema_fields": [
        "target_reference_type",
        "target_reference_price",
        "target_source",
        "target_asof_utc",
        "source_artifact_hash"
      ],
      "truth_class": "explicit target source-state only; neutral horizons are not targets"
    },
    {
      "field_group": "poi_type_bounds_source",
      "schema_fields": [
        "poi_type",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_timeframe",
        "poi_source_hash",
        "poi_asof_utc"
      ],
      "truth_class": "as-of structure/source-state only"
    },
    {
      "field_group": "framework_setup_family",
      "schema_fields": [
        "setup_family",
        "framework_source",
        "framework_asof_utc",
        "framework_source_hash"
      ],
      "truth_class": "explicit source family, not target behavior"
    },
    {
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "schema_fields": [
        "candidate_source_state_id",
        "pending_intent_created_utc",
        "nonbroker_fill_state",
        "cancel_state",
        "expiry_state",
        "source_state_hash"
      ],
      "truth_class": "non-broker GTOS lifecycle source-state only"
    },
    {
      "field_group": "lower_timeframe_asof_path_availability",
      "schema_fields": [
        "ltf_timeframe",
        "ltf_source_file",
        "ltf_source_hash",
        "ltf_window_start_utc",
        "ltf_window_end_utc",
        "ltf_record_count",
        "ltf_parser_version"
      ],
      "truth_class": "recoverable market/source availability, not result scoring"
    },
    {
      "field_group": "future_orderflow_depth_proxy_requirements",
      "schema_fields": [
        "proxy_instrument",
        "source_vendor_or_local_file",
        "source_hash",
        "book_or_trade_schema",
        "asof_publication_or_capture_utc",
        "proxy_mapping_version"
      ],
      "truth_class": "explanatory market context with proxy caveats, not strategy intent"
    },
    {
      "field_group": "adversarial_baseline_assignment",
      "schema_fields": [
        "baseline_family",
        "control_assignment_asof_utc",
        "duplicate_policy",
        "source_artifact_hash"
      ],
      "truth_class": "control design metadata only"
    }
  ],
  "route_id": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS",
  "schema_version": "g0_scid_strategy_field_packet_synthesis_v1",
  "validation_safe": false
}
```
