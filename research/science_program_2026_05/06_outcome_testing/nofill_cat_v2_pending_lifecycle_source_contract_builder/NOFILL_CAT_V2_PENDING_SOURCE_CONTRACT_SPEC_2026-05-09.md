# NOFILL CAT V2 Pending Source Contract Spec

Promotion posture: `NO_PROMOTION_VERDICT`.

Schema version: `nofill_cat_v2_pending_lifecycle_source_contract_v1`.

## Objective

Machine-checkable source-only pending lifecycle capture contract with duplicate denominator controls folded into the same lane.

## Frozen Facts

- `298 = 225 accepted + 8 blocked + 65 rejected`
- `225 = 52 prior accepted + 173 source-corrected accepted`
- Accepted labels are input-only: `true`
- Blockers/rejects excluded from labels, denominators, results, validation, and promotion: `true`
- Duplicate posture: `{'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}`

## Contract Controls

- No accepted input-only label may be treated as performance or validation evidence.
- No blocked or rejected row may enter accepted-label, row-level result, unique-key result, validation, or promotion denominators.
- Every future packet must publish row-level and unique-key denominators before outcome opening.
- Every touch/no-touch field must carry source coverage status, quote side, parser version, source path, and hash manifest.
- Same-tick or same-bar event ordering must be an ambiguity state unless higher-resolution source proves order.

## Deep Questions

### DQ-001: What exact fields would have prevented the 110 terminal-before-entry rows from requiring forensic reconstruction?

- Claim: They needed explicit pending lifecycle event capture plus side-aware touch ordering.
- Evidence: 110 accepted input-only rows carry nofill_terminal_before_entry in the frozen row ledger.
- Uncertainty: The current packet cannot judge cancellation quality or live rule fitness.
- Exact field/control: `pending_create_utc, pending_cancel_or_expiry_utc, cancel_or_expiry_reason_code, side_aware_entry_touch_utc, terminal_area_touch_utc, active_pending_window_end_reason, source_coverage_status`
- Owner: `SOURCE_BUILDER`
- Falsification condition: A future source-hashed packet with these fields still cannot order terminal touch versus entry touch for otherwise complete rows.

### DQ-002: What exact fields would have prevented the 32 no-entry-through-horizon rows from staying source-control only?

- Claim: They need active pending window proof, no-touch proof through the window, and horizon-end reason before any future result design.
- Evidence: 32 accepted source-corrected rows carry source_corrected_no_entry_through_pending_horizon.
- Uncertainty: They still do not become results without a separate preregistered result lane.
- Exact field/control: `active_pending_window_start_utc, active_pending_window_end_utc, active_pending_window_end_reason, no_touch_proof_through_utc, source_coverage_start_utc, source_coverage_end_utc, source_coverage_status`
- Owner: `SOURCE_BUILDER`
- Falsification condition: A future no-touch row has full coverage and horizon fields but still cannot distinguish untouched entry from missing source.

### DQ-003: What fields separate pending lifecycle hygiene from fill/path event-order research?

- Claim: Pending hygiene is create/cancel/expiry plus active-window and touch/no-touch proof; fill/path research is entry/protective/terminal sequence after entry touch.
- Evidence: G0 separates 142 pending hygiene labels from 29 OTI2 event-order labels.
- Uncertainty: A row can require both contracts, but the field families must stay separate.
- Exact field/control: `pending_create_utc, pending_cancel_or_expiry_utc, cancel_or_expiry_reason_code, entry_touch_proof fields, protective_level_touch_utc, terminal_area_touch_utc, same_tick_same_bar_ambiguity_status`
- Owner: `SOURCE_BUILDER`
- Falsification condition: A verifier allows event-order labels without pending-window coverage or allows pending lifecycle labels to imply post-entry result order.

### DQ-004: Which fields are required before a future no-fill result lane can exist without leakage?

- Claim: The source contract must freeze source coverage, duplicate denominator, label boundary, and forbidden-field scans before outcomes open.
- Evidence: Current route preserves NO_PROMOTION_VERDICT and keeps blockers/rejects outside denominators.
- Uncertainty: Sample floor and owner approval are outside this lane and remain closed.
- Exact field/control: `source_hash_manifest, source_path_list, row_level_denominator_scope, unique_key_denominator_scope, canonical_counting_row_id, label_assignment_boundary, forbidden_substitute_field_scan_status`
- Owner: `FUTURE_PREREGISTRATION_DESIGN_LANE`
- Falsification condition: A future result lane can alter denominator, source coverage, or accepted labels after seeing outcomes.

### DQ-005: What duplicate controls must be machine-enforced rather than human-read from markdown?

- Claim: Every packet must reject missing row-level denominator, unique-key denominator, duplicate group, canonical row, exclusion policy, and generated fallback duplicate keys.
- Evidence: 225 accepted row-level inputs reduce to 182 unique accepted duplicate keys, with 39 noncanonical OTI5 projections rejected.
- Uncertainty: Canonical selection can still be wrong if future source identity fields are incomplete.
- Exact field/control: `row_level_denominator_scope, unique_key_denominator_scope, nofill_duplicate_key, duplicate_group_id, canonical_counting_row_id, is_canonical_counting_row, noncanonical_projection_exclusion_policy`
- Owner: `DUPLICATE_DENOMINATOR_VERIFIER_CONTROL`
- Falsification condition: The duplicate verifier accepts a record missing one required control or containing a generated fallback key.

### DQ-006: Which residual blockers become easier to solve after this contract exists?

- Claim: The 3 OTI4 May 3 gaps and 1 original OTI2 active-window gap become easier; the 4 OTI3 same-tick rows remain blocked without higher-resolution event order.
- Evidence: G0 blocker ledger classifies 3 OTI4 rows as recoverable with read-only tick/M1/lower OHLC, 1 OTI2 row as recoverable with side-aware coverage, and 4 OTI3 rows as same-tick order ambiguity.
- Uncertainty: Local source existence is not the same as coverage inside the exact frozen window.
- Exact field/control: `source_coverage_start_utc, source_coverage_end_utc, source_coverage_status, quote_side_used, source_granularity, same_tick_same_bar_ambiguity_status`
- Owner: `RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`
- Falsification condition: A blocker-clear lane finds complete side-aware source coverage and still cannot apply this taxonomy to clear or keep the row blocked.

### DQ-007: Which source contract fields should be captured prospectively in shadow logs, and which must remain research-only proposals until separately approved?

- Claim: Source/provenance and pending lifecycle event fields are prospectively useful; live wiring, cancellation action, and result use need separate approval.
- Evidence: The prompt allows prospective capture backlog but forbids live behavior changes.
- Uncertainty: Actual logger wiring can touch live paths later and therefore needs a separate scoped approval/test lane.
- Exact field/control: `prospective_capture_mode, pending_create_utc, pending_cancel_or_expiry_utc, cancel_or_expiry_reason_code, source_coverage_status, source_hash_manifest, live_wiring_requires_separate_approval`
- Owner: `FUTURE_SHADOW_TELEMETRY_LANE`
- Falsification condition: A future capture patch changes order behavior, selector logic, risk, execution, or cancellation decisions while claiming this source contract as authorization.

### DQ-008: What is the most likely way a future agent could accidentally contaminate this lane, and how does this contract prevent it?

- Claim: The highest-risk contamination is using account/order/broker result labels or noncanonical duplicate rows to rescue ambiguous source rows.
- Evidence: The prompt forbids broker/account/order labels and G0 shows 39 noncanonical duplicate projections rejected.
- Uncertainty: A verifier can catch schema contamination, but reviewer discipline is still needed for narrative claims.
- Exact field/control: `forbidden_substitute_field_scan_status, noncanonical_projection_exclusion_policy, label_assignment_boundary, validation_safe=false, outcome_review_opened=false`
- Owner: `NOLEAK_AUDITOR`
- Falsification condition: Generated schema field_names include forbidden result/account/order/hidden fields, or blocked/rejected rows enter accepted denominators.

### DQ-009: What is the highest-learning next route after this contract?

- Claim: Run a G12 audit of this pending source contract first, then use the audited contract to clear exact residual blockers.
- Evidence: This route creates machine-checkable controls; a G12 audit is the safest next gate before source-access or preregistration lanes reuse them.
- Uncertainty: If the owner prioritizes direct source access, residual blocker clear can run next but must keep the G12 audit before any result lane.
- Exact field/control: `G12_PENDING_SOURCE_CONTRACT_AUDIT, RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE, FILL_PATH_EVENT_ORDER_CONTRACT`
- Owner: `NEXT_PROMPT_PACK`
- Falsification condition: The G12 audit finds the contract is incomplete or the residual blocker lane needs fields not represented here.


## Source Authority

- `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`
- `research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json`
