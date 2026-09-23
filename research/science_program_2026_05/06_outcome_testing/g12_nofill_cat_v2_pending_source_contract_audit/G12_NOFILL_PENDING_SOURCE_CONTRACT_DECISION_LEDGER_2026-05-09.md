# G12 NOFILL Pending Source Contract Decision Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.
Decision: `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_FOR_FUTURE_AUDITED_SOURCE_LANES`.
Decision scope: `future_source_control_routing_only`.

## Frozen Counts

- Universe partition: `{'universe': 298, 'accepted': 225, 'blocked': 8, 'rejected': 65}`
- Accepted split: `{'accepted_prior': 52, 'accepted_source_corrected': 173}`
- Duplicate posture: `{'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}`

## Audit Question Answers

### AQ-001: Does the 46-field schema include every required field family?

- Answer: YES
- Status: `PASS`
- Evidence: Schema field review shows field_count=46 and no missing required families or required field names.

### AQ-002: Are schema fields decision-time/source-safe?

- Answer: YES
- Status: `PASS`
- Evidence: No forbidden broker/account/result/hidden-label field names or allowed source types were found.

### AQ-003: Does duplicate verifier reject missing denominator/canonical/generated identity cases?

- Answer: YES
- Status: `PASS`
- Evidence: Duplicate review executes the valid example and all invalid examples from the control JSON.

### AQ-004: Are the 8 blockers and 65 rejects outside labels, denominators, and result/validation/promotion use?

- Answer: YES
- Status: `PASS`
- Evidence: Row-ledger boundary scan found no blocked/rejected label, denominator, safety-flag, or live-effect violations.

### AQ-005: Does capture backlog contain enough prospective/source-safe fields?

- Answer: YES
- Status: `PASS`
- Evidence: Capture backlog review covers duplicate, pending lifecycle, side-aware touch, coverage/hash, and ambiguity topics.

### AQ-006: Can residual blocker source-access lane run from this contract as written?

- Answer: YES_FOR_SOURCE_CONTROL_ROUTING_ONLY
- Status: `PASS`
- Evidence: CAN_RUN_FROM_CONTRACT_AS_WRITTEN_FOR_SOURCE_CONTROL_ROUTING_ONLY

### AQ-007: What is the strongest counterargument against accepting this contract?

- Answer: The contract is necessary but not sufficient: it cannot prove source availability, clear the 8 blockers, or prevent misuse if future agents skip the verifier and treat input labels as results.
- Status: `ANSWERED`
- Evidence: Recorded in the decision ledger and no-leak/blocker review.

### AQ-008: What amendments would make the contract harder to misuse?

- Answer: Add future packet-level source_coverage_gap_code, event_order_resolution_method, and parser-code hash requirements. These are nonblocking implementation hardening items; the current contract is acceptable as a source/control contract.
- Status: `ANSWERED`
- Evidence: Schema review nonblocking_hardening_amendments.

### AQ-009: What future route is highest expected value and what remains closed?

- Answer: Highest expected value is NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE using this contract. Quantitative result, validation, promotion, registry, broker/account/order, and live behavior routes remain closed.
- Status: `ANSWERED`
- Evidence: Next prompt pack and route decisions.


## Route Decisions

### `NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

- Decision: `ACCEPT_AS_HIGHEST_EXPECTED_VALUE_NEXT_SOURCE_CONTROL_ROUTE`
- Allowed use: Clear or preserve exactly the 8 blockers using source proof only.
- Forbidden use: No result scoring, validation, promotion, broker/account/order labels, or live behavior.

### `NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT`

- Decision: `ACCEPT_AS_FUTURE_SOURCE_CONTROL_CONTRACT_ROUTE`
- Allowed use: Categorical event-order source contract only.
- Forbidden use: No path-R, actual-R, result scoring, or selector use.

### `NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE`

- Decision: `REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED`
- Allowed use: None in this audit.
- Forbidden use: Closed until separate frozen preregistration, sample floor, no-leak proof, G12 gate, and owner approval.

### `LIVE_TRADING_BEHAVIOR_OR_PROMPT_SRC_CONFIG_CHANGE`

- Decision: `REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED`
- Allowed use: None.
- Forbidden use: Live prompts, src trading logic, risk, execution, permissions, safety, selectors, MT5, canaries, credentials, and order behavior.


## Strongest Counterargument

The source contract can still be misused if a future lane treats accepted categorical labels as results or skips duplicate/source-coverage verification. It also cannot clear the 8 blockers by itself.

## Why This Is Not A Blocker

Those weaknesses are lane-boundary and future-execution risks, not defects in the source/control contract. The schema, duplicate verifier, no-leak audit, blocker taxonomy, capture backlog, and completion audit are machine-checkable and sufficient for future audited source/control routing.

## Nonblocking Hardening Amendments

- Future packet builders should emit a per-row source_coverage_gap_code whenever source_coverage_status is not COMPLETE.
- Future packet builders should freeze event_order_resolution_method as source_tick, lower_tf_bound, same_tick_ambiguous, or unavailable_source.
- Future source_hash_manifest entries should include parser code hash plus data file hashes, not only data file paths.
