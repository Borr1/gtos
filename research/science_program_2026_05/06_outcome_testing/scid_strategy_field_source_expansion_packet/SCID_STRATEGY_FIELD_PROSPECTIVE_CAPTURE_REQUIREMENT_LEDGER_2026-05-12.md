# Prospective

- **route_id:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET`
- **evidence_class:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "prospective_capture_source_requirement_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY",
  "exact_owner_access_source_capture_approval_requirements": [
    {
      "owner_action_needed_now": false,
      "reason": "This packet can complete with prospective requirements; no approved source-safe extraction is needed to classify current field status.",
      "requirement": "If a future route wants LTF/path/orderflow/depth fields for historical SCID rows, it must register exact symbols, files/windows, parser, hashes, as-of convention, and no-leak policy before extraction."
    },
    {
      "owner_action_needed_now": false,
      "reason": "The controlling prompt explicitly forbids broker evidence.",
      "requirement": "If a future route wants broker account/order/history/deal/position truth, it requires a separate owner-approved evidence class and is forbidden here."
    }
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
  "requirements": [
    {
      "as_of_rule": "Capture only fields timestamped at or before decision_asof_utc for candidate inputs, or explicitly mark future explanatory source fields as not candidate-decision inputs.",
      "current_status": "PROSPECTIVE_CAPTURE_REQUIRED",
      "field_family": "lower_timeframe_asof_path_availability",
      "future_source_or_logger": "scid_ltf_path_availability_v1",
      "g12_acceptance_requirement": "Independent G12 audit must verify source hash, timestamp/as-of policy, row joins, and no-leak allowlist before use.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must record availability and source hashes only; no future path/result scoring may enter this packet.",
      "redaction_rule": "No broker account/order/history/deal/position evidence; no credentials; no target/result labels.",
      "required_fields": [
        "ltf_timeframe",
        "ltf_source_file",
        "ltf_source_hash",
        "ltf_window_start_utc",
        "ltf_window_end_utc",
        "ltf_record_count",
        "ltf_parser_version"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "recoverable/requestable market/source data when local Sierra/tick/LTF files exist; otherwise prospective capture"
    },
    {
      "as_of_rule": "Capture only fields timestamped at or before decision_asof_utc for candidate inputs, or explicitly mark future explanatory source fields as not candidate-decision inputs.",
      "current_status": "PROSPECTIVE_CAPTURE_REQUIRED",
      "field_family": "future_orderflow_depth_proxy_requirements",
      "future_source_or_logger": "scid_orderflow_depth_proxy_context_v1",
      "g12_acceptance_requirement": "Independent G12 audit must verify source hash, timestamp/as-of policy, row joins, and no-leak allowlist before use.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must separate source-control explanatory context from candidate-decision fields and preserve futures-to-CFD proxy caveats.",
      "redaction_rule": "No broker account/order/history/deal/position evidence; no credentials; no target/result labels.",
      "required_fields": [
        "proxy_instrument",
        "source_vendor_or_local_file",
        "source_hash",
        "book_or_trade_schema",
        "asof_publication_or_capture_utc",
        "proxy_mapping_version"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "recoverable/requestable market/source data, not strategy intent"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "intended_side_direction",
      "future_source_or_logger": "strategy_source_field_capture_v1.side_direction",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must read explicit strategy/candidate source-state, never infer side from later price path.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "intended_side",
        "direction_source",
        "direction_asof_utc",
        "source_artifact_hash"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical GTOS intent/source-state unless an explicit source-state artifact is found"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "intended_entry_reference",
      "future_source_or_logger": "strategy_source_field_capture_v1.entry_reference",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must distinguish neutral bar close reference from intended strategy entry.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "intended_entry_reference_type",
        "intended_entry_reference_price",
        "entry_reference_source",
        "entry_reference_asof_utc"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical GTOS intent/source-state"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "intended_stop_reference",
      "future_source_or_logger": "strategy_source_field_capture_v1.stop_reference",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must consume explicit stop source-state, not derive stop from excursion or target path.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "intended_stop_reference_type",
        "intended_stop_reference_price",
        "stop_source",
        "stop_asof_utc"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical GTOS intent/source-state"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "intended_target_reference",
      "future_source_or_logger": "strategy_source_field_capture_v1.target_reference",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must consume explicit target source-state; neutral horizon rows are not target references.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "intended_target_reference_type",
        "intended_target_reference_price",
        "target_source",
        "target_asof_utc"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical GTOS intent/source-state"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "poi_type_bounds_source",
      "future_source_or_logger": "strategy_source_field_capture_v1.poi",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must read explicit POI/structure artifacts generated as-of the candidate.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "poi_type",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_timeframe",
        "poi_source_hash",
        "poi_asof_utc"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical structure/source-state unless source-safe as-of MSO snapshots exist"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "framework_setup_family",
      "future_source_or_logger": "strategy_source_field_capture_v1.framework",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser must preserve OB/FVG/breaker/structural/source-only unknown without using target behavior.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "setup_family",
        "framework_source",
        "framework_asof_utc",
        "framework_source_hash"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical GTOS intent/source-state"
    },
    {
      "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
      "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
      "field_family": "lifecycle_fill_cancel_expiry_source_status",
      "future_source_or_logger": "candidate_lifecycle_source_state_v1",
      "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
      "owner_or_future_lane_action_required": true,
      "parser_requirement": "Parser may consume source-safe GTOS pending-intent/lifecycle logs only; broker account/order/deal/position history remains forbidden in this lane.",
      "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
      "required_fields": [
        "candidate_source_state_id",
        "pending_intent_created_utc",
        "nonbroker_fill_state",
        "cancel_state",
        "expiry_state",
        "source_state_hash"
      ],
      "schema_version_required": "scid_strategy_source_fields_v1",
      "truth_class": "non-generatable historical lifecycle source-state if not already logged"
    }
  ],
  "route_id": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
  "schema_version": "scid_strategy_field_source_expansion_packet_v1",
  "validation_safe": false
}
```
