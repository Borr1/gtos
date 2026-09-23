# G0 NOFILL CAT V2 Pending Lifecycle Hygiene Synthesis

Promotion posture: `NO_PROMOTION_VERDICT`.

Headline: No-fill V2 is most useful as pending lifecycle observability control evidence.

Accepted denominator: `225` input-only source/control rows.

## Pending Hygiene Findings

### PEND-HYG-001

- Claim: Terminal-before-entry states are large enough to demand explicit pending lifecycle telemetry.
- Evidence: 110 accepted input-only rows carry nofill_terminal_before_entry.
- Uncertainty: The artifact cannot say whether current cancellation behavior is good or bad.
- Next action: Capture terminal touch, entry touch, pending cancel/expiry, cancel reason, and source coverage prospectively.

### PEND-HYG-002

- Claim: No-entry-through-horizon is a distinct source state from missing label.
- Evidence: 32 source-corrected accepted rows carry source_corrected_no_entry_through_pending_horizon.
- Uncertainty: The stale horizon and active pending-state context are incomplete.
- Next action: Separate untouched entry, late cancellation, stale POI, and source coverage states.

### PEND-HYG-003

- Claim: Fill/path categories should become event-order primitives, not current results.
- Evidence: OTI2 contributes 29 accepted rows across three event-order labels.
- Uncertainty: Small subsets and same-tick blockers prevent result interpretation.
- Next action: Freeze event-order categorical contract before any future result lane.


## Label Families

### `nofill_terminal_before_entry` (110)

- Source/control learning: Pending ideas can become lifecycle-invalid before side-aware entry touch; cancellation and expiry state need first-class event capture.
- Proves: The approved source path reached the terminal area before an entry event under the source contract.
- Does not prove: It does not prove a trading outcome, cancellation quality, or live rule fitness.
- Likely issue type: `real_pending_order_lifecycle_hygiene_signal`
- Uncertainty: The current label lacks full cancel reason, broker-side pending state, and prospective as-of capture.
- Future route: Preregister a pending lifecycle hygiene capture lane that records terminal-before-entry, pending cancel/expiry, and source coverage prospectively.
- Capture fields: `pending_create_utc, pending_cancel_or_expiry_utc, terminal_touch_utc, side_aware_entry_touch_utc_or_no_touch, cancel_reason, source_coverage_status`

### `source_corrected_no_entry_through_pending_horizon` (32)

- Source/control learning: Some no-fill rows are true no-entry-through-horizon states rather than missing labels.
- Proves: Corrected source fields show no side-aware entry touch through the frozen pending horizon.
- Does not prove: It does not decide whether the pending order should have expired earlier or whether a live cancellation rule should change.
- Likely issue type: `pending_window_and_staleness_contract_gap`
- Uncertainty: Cancel reason, pending horizon rule, and source coverage must be captured together before any rule design.
- Future route: Create a no-entry horizon source contract that separates untouched entry, stale POI, late cancel, and source coverage states.
- Capture fields: `pending_horizon_start_utc, pending_horizon_end_utc, entry_touch_absent_proof, coverage_start_utc, coverage_end_utc, horizon_end_reason`

### `opening_drive_source_projection_ready_no_result_label` (51)

- Source/control learning: Opening-drive source projections are reconstructable, but they are projection inventory, not result evidence.
- Proves: A range/breakout/as-of projection can be built for future source-contract work.
- Does not prove: It does not assign lifecycle outcome or performance meaning; duplicate-key clustering makes premature denominator use dangerous.
- Likely issue type: `source_projection_and_duplicate_inflation_risk`
- Uncertainty: The family is concentrated in a small duplicate-key set and needs a frozen projection denominator before labels.
- Future route: Run a separate opening-drive categorical source-contract route with frozen range fields, side-match rules, and duplicate policy before outcome opening.
- Capture fields: `opening_range_start_utc, opening_range_end_utc, range_high, range_low, range_complete_asof, breakout_side, candidate_side_match_status, duplicate_projection_key`

### `fill_path_entry_before_protective_level_no_terminal_observed` (22)

- Source/control learning: Fill/path rows can enter a post-entry transition state without terminal observation in the approved path window.
- Proves: Entry can be ordered before protective level while terminal area is unobserved inside the source window.
- Does not prove: It does not score the leg or infer whether the absence of terminal observation is favorable or unfavorable.
- Likely issue type: `event_order_contract_and_window_end_gap`
- Uncertainty: The terminal absence could be real, a window limit, or source-end artifact; future rows need source window end reason.
- Future route: Freeze an event-order categorical contract with same-tick and no-terminal states as categories, not results.
- Capture fields: `entry_event_utc, protective_event_utc, terminal_event_utc_or_null, source_window_end_reason, same_tick_or_same_bar_flag`

### `fill_path_entry_before_protective_level_before_terminal_area` (4)

- Source/control learning: The source can order a complete three-event fill path in a small subset.
- Proves: Entry, protective, and terminal predicates can be sequenced from approved source rows.
- Does not prove: It does not validate a strategy, because event order is not a promoted result metric.
- Likely issue type: `event_order_contract_ready_but_underpowered`
- Uncertainty: The subset is small and must remain a category until a separate preregistration exists.
- Future route: Use this event category as one frozen state in a future result contract after owner and G12 gates.
- Capture fields: `entry_event_utc, protective_event_utc, terminal_event_utc, quote_side_used`

### `fill_path_entry_before_terminal_area_before_protective_level` (3)

- Source/control learning: The strongest semantic event order exists but remains descriptive only.
- Proves: Entry, terminal, and protective predicates can be sequenced in terminal-before-protective order for a small subset.
- Does not prove: It does not authorize any result claim or live path-management rule.
- Likely issue type: `promising_event_order_category_not_validation`
- Uncertainty: Small subset and no frozen result contract make all outcome interpretation forbidden here.
- Future route: Preserve this as an input-only categorical state in any future preregistered fill/path result lane.
- Capture fields: `entry_event_utc, terminal_event_utc, protective_event_utc, same_tick_flag`

### `canonical_duplicate_geometry_source_ready_no_label_assigned` (3)

- Source/control learning: Duplicate-conflict families need canonical source-identity rows before any packet can be trusted.
- Proves: The canonical geometry rule can select a countable source-identity row.
- Does not prove: It does not assign a lifecycle label or any result meaning.
- Likely issue type: `denominator_control_requirement`
- Uncertainty: Canonical identity is necessary but not sufficient for future outcome denominators.
- Future route: Make canonical duplicate controls mandatory in every no-fill and pending lifecycle packet builder.
- Capture fields: `nofill_duplicate_key, duplicate_group_id, canonical_counting_row_id, noncanonical_projection_count, canonical_selection_reason`


## Boundary

The synthesis does not score outcomes, validate a rule, change cancellation logic, or touch live behavior.
