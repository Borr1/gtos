# NOFILL CAT V2 Future Hypothesis And Capture Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

## Route Decision

- Primary: `G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT`
- Secondary: `NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`
- Quantitative result lane: `FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR`

## Future Control Lanes

### G12 synthesis-control audit

- Purpose: Independently verify this forensics packet's counts, non-claims, label-family analysis, blocker/reject learning, and no-leak posture.
- Opens results: `False`

### Residual 8 blocker-clear access lane

- Purpose: Target only exact source/order blockers without touching accepted/rejected rows.
- Opens results: `False`

### Pending-intent hygiene capture

- Purpose: Capture terminal-before-entry and no-entry-through-horizon facts prospectively with source hashes and cancel/expiry context.
- Opens results: `False`

Capture fields:
- `pending_create_utc`
- `pending_cancel_or_expiry_utc`
- `terminal_touch_utc`
- `side_aware_entry_touch_utc_or_no_touch`
- `source_coverage_status`
- `cancel_reason`

### Fill/path event-order categorical contract

- Purpose: Freeze event-order categories and same-tick blocker handling before any future result packet.
- Opens results: `False`

Capture fields:
- `entry_event_utc`
- `protective_event_utc`
- `terminal_event_utc`
- `same_tick_or_same_bar_flag`
- `quote_side_used`
- `source_window_end_reason`

### Opening-drive source projection contract

- Purpose: Turn source projection readiness into a frozen categorical contract with denominator and duplicate policy before labels are assigned.
- Opens results: `False`

Capture fields:
- `opening_range_start_end`
- `breakout_side`
- `range_complete_asof`
- `candidate_side_match_status`
- `duplicate_projection_key`

### Future quantitative result dossier gate

- Purpose: Only if the owner wants scoring later, freeze preregistration, denominator, source fields, sample floor, no-leak proof, duplicate policy, and G12 acceptance before any result values are opened.
- Opens results: `not_in_this_lane`

Minimum requirements:
- frozen prereg before outcome opening
- sample floor and denominator policy
- source-hashed side-aware event fields
- blocked/rejected row exclusion proof
- separate G12 gate
- explicit owner approval

## Hard Non-Claims

- This synthesis does not choose a trading rule.
- This synthesis does not validate cancellation timing.
- This synthesis does not promote any selector or live gate.
- This synthesis does not use broker actual-R or account history.
