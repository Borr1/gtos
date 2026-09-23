# SCID Combined Forward Capture Contract

- **route_id:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE`
- **evidence_class:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "forward_capture_contract",
  "candidate_rows_covered": 3014,
  "changes_live_trading_behavior": false,
  "contract_boundary": "proposed offline/source logger schema only; no live wiring or behavior change is implemented by this route",
  "credentials_touched": false,
  "evidence_class": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY",
  "field_groups": [
    {
      "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
      "field_group": "intended_side_direction",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "decision_asof_utc",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "side_emission_reason_code"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "entry reference must be present in the source decision packet before any fill, cancel, expiry, or target horizon is known",
      "field_group": "intended_entry_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "no fill-derived or hindsight-optimized entry references",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
      "field_group": "intended_stop_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "stop_reference_price",
        "stop_reference_type",
        "stop_buffer_rule_id",
        "stop_source_structure_id",
        "stop_source_snapshot_hash"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
      "field_group": "intended_target_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "risk_reward_reference",
        "target_source_snapshot_hash"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
      "field_group": "poi_type_bounds_source",
      "future_source_or_logger": "source_safe_mso_snapshot_and_poi_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
      "no_leak_rule": "do not reconstruct POI from later price movement or from result-selection logic",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
      "field_group": "framework_setup_family",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "future_source_or_logger": "nonbroker_pending_intent_lifecycle_event_logger",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels in this evidence class",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
      "field_group": "lower_timeframe_asof_path_availability",
      "future_source_or_logger": "ltf_source_availability_and_path_descriptor_capture",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
      "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "decision_asof_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless explicitly marked forensic-only",
      "field_group": "future_orderflow_depth_proxy_requirements",
      "future_source_or_logger": "orderflow_depth_proxy_context_capture",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
      "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "source_hash",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    },
    {
      "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
      "field_group": "baseline_control_fields",
      "future_source_or_logger": "offline_baseline_control_assignment_manifest",
      "g12_acceptance_requirement": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status for every candidate before any result-design lane can consume it",
      "historical_status_after_search": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
      "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds",
      "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
      "redaction_rule": "no credential, account balance, broker ticket, deal id, order id, position id, or account-history payload; use source-local event ids or salted hashes only where an identifier is needed",
      "required_fields": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id"
      ],
      "schema_version_required": "scid_forward_source_capture_v1"
    }
  ],
  "field_groups_required_by_prompt": [
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
  "generated_at_utc": "2026-05-12T01:06:39Z",
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
  "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
  "schema_version": "scid_combined_source_capture_route_v1",
  "validation_safe": false
}
```
