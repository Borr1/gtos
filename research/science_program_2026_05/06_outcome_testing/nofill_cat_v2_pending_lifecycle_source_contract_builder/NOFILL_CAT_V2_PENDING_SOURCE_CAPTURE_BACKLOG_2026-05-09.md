# NOFILL CAT V2 Pending Source Capture Backlog

Promotion posture: `NO_PROMOTION_VERDICT`.

Boundary: All backlog items are source/control or prospective shadow proposals. This lane does not wire live loggers or change live trading behavior.

### `PEND-CAP-001`: Machine-enforce duplicate denominator manifest in every future no-fill packet builder.

- Priority: `P0`
- Source fields: `row_level_denominator_scope, unique_key_denominator_scope, nofill_duplicate_key, duplicate_group_id, canonical_counting_row_id, is_canonical_counting_row, noncanonical_projection_exclusion_policy`
- Prospective shadow only: `true`
- May modify live code in this lane: `false`
- Separate owner approval for live wiring: `true`
- Forbidden: `result_scoring, registry_edit, live_order_behavior_change`
- Success check: Verifier rejects missing denominators, missing canonical row ID, missing group ID, non-exclusion policy, and generated fallback keys.

### `PEND-CAP-002`: Pending lifecycle source shadow capture schema.

- Priority: `P1`
- Source fields: `pending_create_utc, pending_cancel_or_expiry_utc, cancel_or_expiry_reason_code, active_pending_window_start_utc, active_pending_window_end_utc, active_pending_window_end_reason`
- Prospective shadow only: `true`
- May modify live code in this lane: `false`
- Separate owner approval for live wiring: `true`
- Forbidden: `cancel_rule_change, execution_change, selector_change`
- Success check: Rows can distinguish pending create, cancel, expiry, horizon end, stale POI, and source truncation without account/order labels.

### `PEND-CAP-003`: Side-aware touch/no-touch and coverage manifest.

- Priority: `P1`
- Source fields: `side_aware_entry_touch_status, side_aware_entry_touch_utc, terminal_area_touch_status, protective_level_touch_status, no_touch_proof_through_utc, quote_side_used, source_coverage_status`
- Prospective shadow only: `true`
- May modify live code in this lane: `false`
- Separate owner approval for live wiring: `true`
- Forbidden: `broker_fill_substitution, account_history_substitution, post_outcome_score`
- Success check: No-touch and touch labels cannot exist without quote side and source coverage status.

### `PEND-CAP-004`: Residual blocker clear source-access lane for exactly 8 blockers.

- Priority: `P2`
- Source fields: `source_path_list, source_hash_manifest, source_coverage_status, same_tick_same_bar_ambiguity_status`
- Prospective shadow only: `false`
- May modify live code in this lane: `false`
- Separate owner approval for live wiring: `false`
- Forbidden: `accepted_row_scoring, rejected_row_scoring, broker_actual_r, account_history`
- Success check: Each blocker is cleared or remains blocked from exact source coverage/event-order proof only.

### `PEND-CAP-005`: Fill/path event-order contract derived from pending source fields.

- Priority: `P2`
- Source fields: `entry_touch_proof, terminal_area_touch_proof, protective_level_touch_proof, same_tick_same_bar_ambiguity_status`
- Prospective shadow only: `true`
- May modify live code in this lane: `false`
- Separate owner approval for live wiring: `true`
- Forbidden: `performance_comparison, result_lane_opening, guessed_sequence`
- Success check: Event-order categories can be emitted as categories while same-tick/same-bar ambiguity remains explicit.
