# NOFILL Forward Lifecycle Capture Contract 2026-05-09

- route_id: `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT`
- schema_version: `nofill_cat_v3_forward_lifecycle_capture_contract_v1`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Contract Boundary

This is a forward source-capture contract. It defines what must be captured before later no-fill review can be considered. It does not score outcomes, does not promote a signal, does not validate an edge, does not change live trading behavior, and does not open account/order-history routes.

## Frozen Counts

- `universe_rows`: `298`
- `accepted_row_level_inputs`: `225`
- `source_control_rows`: `4`
- `source_impossible_rows`: `4`
- `rejected_rows`: `65`
- `accepted_unique_nofill_duplicate_keys`: `182`
- `accepted_secondary_duplicate_group_ids`: `139`

Primary label counts carried as input/control vocabulary only:

- `nofill_terminal_before_entry`: `110`
- `source_corrected_no_entry_through_pending_horizon`: `32`
- `fill_path_entry_before_protective_level_no_terminal_observed`: `22`
- `fill_path_entry_before_protective_level_before_terminal_area`: `4`
- `fill_path_entry_before_terminal_area_before_protective_level`: `3`
- `opening_drive_source_projection_ready_no_result_label`: `8`
- `canonical_duplicate_geometry_source_ready_no_label_assigned`: `3`

Opening-drive source projection remains `51` row-level inputs, of which `8` are primary accepted labels under the frozen G0 presentation. The `47` reject-overlap rows are neutralized by accepted-first filtering.

## Required Field Families

- `capture_backlog_control`: capture_backlog_item_id, capture_backlog_status, exact_next_source_if_unresolved, impossible_from_source_code, source_control_state
- `decision_asof`: decision_asof_utc
- `duplicate_denominator`: nofill_duplicate_key, duplicate_group_id, canonical_row_id, is_canonical_row, noncanonical_projection_rule, accepted_first_filtering_status, reject_overlap_exclusion_status, source_control_source_impossible_exclusion_status, concentration_bucket
- `event_order_resolution`: event_order_resolution_method, event_sequence, same_tick_same_bar_ambiguity_status, tie_policy, impossible_from_source_code, exact_next_source_if_unresolved
- `label_family_separation`: source_control_state, input_only_categorical_label, future_result_label_status, broker_actual_r_status, hidden_path_label_status, live_account_order_label_status
- `no_leak_audit`: validation_safe, outcome_review_opened, live_effect, promotion_verdict, forbidden_field_scan_status
- `pending_horizon_cancel_expiry`: pending_horizon_start_utc, pending_horizon_end_utc, cancel_expiry_utc, cancel_expiry_reason_code
- `pending_intent_creation`: pending_intent_created_utc, intended_entry_price, side_aware_quote_reference, intended_stop_or_protective_area, intended_terminal_or_target_area
- `row_identity_provenance`: forward_capture_row_id, source_route, source_row_id, symbol, broker_symbol, source_symbol, session, side, decision_timeframe, candidate_id, trade_id_source_safe, source_packet_id, source_inventory_id, source_artifact_hash, parser_version, parser_code_hash, builder_version, controlling_head
- `source_coverage_quote`: tick_coverage_window_start_utc, tick_coverage_window_end_utc, lower_tf_coverage_window_start_utc, lower_tf_coverage_window_end_utc, missing_coverage_intervals, quote_side, spread_state, timezone_normalization, broker_server_timestamp_policy, source_granularity, first_quote_utc, last_quote_utc, source_file_hashes
- `tick_or_ltf_source_manifest`: source_manifest_id, source_manifest_created_utc
- `touch_no_touch_proof`: side_aware_entry_touch_status, entry_touch_first_utc, terminal_area_touch_status, terminal_area_first_touch_utc, protective_area_touch_status, protective_area_first_touch_utc, no_entry_through_source_window_proof, no_entry_through_pending_horizon_proof, terminal_before_entry_categorical_proof

## Row Completion Rule

A row is contract-complete only when identity, pending intent, source coverage, touch/no-touch proof, event-order resolution, duplicate denominator controls, and no-leak guards are present. Missing source is not a failure to classify; it is a first-class blocker with `exact_next_source_if_unresolved`.
