# G0 NOFILL CAT V2 Synthesis Control Decision Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS_G0_SOURCE_CONTROL_SYNTHESIS`.
Decision: `ACCEPT_G12_FORENSICS_AS_SOURCE_CONTROL_LEARNING_AND_ROUTE_NEXT_CONTROL_WORK`.

## Reconciled Counts

- Universe: `298`
- Accepted input-only rows: `225`
- Blocked rows: `8`
- Rejected rows: `65`
- Accepted split: `{'accepted_prior': 52, 'accepted_source_corrected': 173}`
- Duplicate posture: `{'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'opening_drive_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}`

## Accepted Labels

| label | count |
| --- | --- |
| canonical_duplicate_geometry_source_ready_no_label_assigned | 3 |
| fill_path_entry_before_protective_level_before_terminal_area | 4 |
| fill_path_entry_before_protective_level_no_terminal_observed | 22 |
| fill_path_entry_before_terminal_area_before_protective_level | 3 |
| nofill_terminal_before_entry | 110 |
| opening_drive_source_projection_ready_no_result_label | 51 |
| source_corrected_no_entry_through_pending_horizon | 32 |

## Accepted Source Lanes

| source_lane | count |
| --- | --- |
| OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET | 32 |
| OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2 | 29 |
| OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT | 58 |
| OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION | 51 |
| OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT | 3 |
| prior_g12_categorical_packet_audit | 52 |

## Decisions And Adversarial Answers

### G0-D001: What has V2 evidence established about pending lifecycle hygiene?

- Claim: It established that pending ideas need explicit lifecycle state capture before result interpretation: terminal-before-entry and no-entry-through-horizon are common source-control states.
- Evidence: Accepted label counts include nofill_terminal_before_entry=110 and source_corrected_no_entry_through_pending_horizon=32 inside the 225 input-only rows.
- Uncertainty: The rows do not contain complete prospective cancel reason or live pending-state telemetry.
- Falsification condition: A future source-hashed capture lane shows terminal-before-entry/no-entry-through-horizon states are artifacts of the rebuilt source contract rather than prospective pending lifecycle states.
- Exact next action: Build pending lifecycle hygiene capture/spec lane with source coverage and cancel/expiry fields.
- Owner: `G0_SOURCE_BUILDER`

### G0-D002: Which accepted label families are source-control learning only?

- Claim: All seven accepted label families are input-only categorical source/control learning and none is a result label.
- Evidence: Accepted labels reconcile exactly to {'canonical_duplicate_geometry_source_ready_no_label_assigned': 3, 'fill_path_entry_before_protective_level_before_terminal_area': 4, 'fill_path_entry_before_protective_level_no_terminal_observed': 22, 'fill_path_entry_before_terminal_area_before_protective_level': 3, 'nofill_terminal_before_entry': 110, 'opening_drive_source_projection_ready_no_result_label': 51, 'source_corrected_no_entry_through_pending_horizon': 32} and every row keeps validation_safe=false, outcome_review_opened=false, live_effect=false.
- Uncertainty: Future lanes may reuse these categories only after a separate frozen contract and G12/owner gate.
- Falsification condition: Any generated result lane consumes these labels as performance evidence without a separate preregistered denominator and G12 acceptance.
- Exact next action: Carry label-family proofs/non-claims into future prompt packs and verifiers.
- Owner: `G0_CONTROL`

### G0-D003: What source contract changes are implied?

- Claim: Future source contracts must capture pending create/cancel/expiry, side-aware entry touch or no-touch proof, terminal/protective event order, source coverage, duplicate key policy, and opening-drive range/breakout fields.
- Evidence: Accepted rows split across OTI1/OTI2/OTI3/OTI4/OTI5 and blockers identify missing range, side-aware active-window, and same-tick order fields.
- Uncertainty: Some fields may require a new source-access route or prospective shadow capture rather than reconstruction.
- Falsification condition: A source audit proves existing committed artifacts already contain all fields with as-of hashes.
- Exact next action: Use the source contract backlog in this route as the next builder prompt input.
- Owner: `SOURCE_BUILDER`

### G0-D004: What duplicate denominator controls are mandatory?

- Claim: Future no-fill work must distinguish 225 row-level source inputs from 182 unique duplicate keys and must exclude noncanonical projections from denominators.
- Evidence: Duplicate posture reconciles to {'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'opening_drive_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}; OTI5 accepts 3 canonical rows and rejects 39 noncanonical projections.
- Uncertainty: A future result lane must freeze whether denominator is row-level source input or unique opportunity key before opening outcomes.
- Falsification condition: A builder demonstrates no duplicate-key collision under a stricter future denominator while preserving source identity.
- Exact next action: Make duplicate denominator verification a required preflight for no-fill packet builders.
- Owner: `G0_CONTROL`

### G0-D005: Which residual blocker route is worth running?

- Claim: Run a narrow source-access blocker route only for the 3 OTI4 May 3 source gaps and 1 OTI2 active-window gap first; park the 4 OTI3 same-tick ambiguities until higher-resolution event order exists.
- Evidence: OTI4/OTI2 blockers name recoverable source coverage requirements; OTI3 blockers are identical-timestamp ordering impossibilities from current tick rows.
- Uncertainty: If a broker-native event-order source exists without account/order labels, OTI3 can be revisited.
- Falsification condition: A source search finds approved higher-resolution sequence evidence for OTI3, or finds approved OTI4/OTI2 windows are unavailable.
- Exact next action: Write a source-access lane prompt that targets exactly the 8 blockers without scoring any row.
- Owner: `SOURCE_ACCESS_LANE`

### G0-D006: What future preregistration design is allowed?

- Claim: A future design lane may freeze denominator, source fields, sample floor, no-leak proof, duplicate policy, and G12/owner gates; it must not open outcomes.
- Evidence: G12 next prompt pack explicitly separates optional preregistration design from any quantitative result lane.
- Uncertainty: Owner approval and sample floor remain undefined for any future result lane.
- Falsification condition: Owner explicitly approves a result lane with frozen contract and G12 acceptance.
- Exact next action: Rank the preregistration design behind source contract and duplicate control work.
- Owner: `PREREG_DESIGN_LANE`

### G0-D007: How does this connect to primitive science without overclaiming?

- Claim: The no-fill evidence improves the science program by turning failed/blocked lifecycle rows into source primitives: pending hygiene, event order, source coverage, duplicate identity, and projection readiness.
- Evidence: The accepted categories are source-control states, not outcomes; they can feed future capture and hypothesis design without touching live behavior.
- Uncertainty: Whether any primitive later improves trading must be tested only under a separate preregistered lane.
- Falsification condition: Prospective capture shows the categories are not stable or are redundant with existing logs.
- Exact next action: Treat these categories as feature/capture candidates, not selectors.
- Owner: `G0_RESEARCH_PROGRAM_CONTROL`

### G0-D008: What is the strongest useful signal hidden in non-result evidence?

- Claim: The strongest useful signal is not performance; it is that many pending opportunities fail or remain untouched before entry, so the operating system needs cleaner pending lifecycle observability.
- Evidence: 142 accepted rows combine terminal-before-entry and no-entry-through-horizon categories.
- Uncertainty: The operational cause may be source-contract boundaries, stale horizons, or actual pending lifecycle design.
- Falsification condition: Prospective logging shows terminal/no-entry states vanish once capture is cleaner.
- Exact next action: Prioritize pending lifecycle hygiene capture before result scoring.
- Owner: `SOURCE_BUILDER`

### G0-D009: What would a lazy synthesis miss?

- Claim: A lazy synthesis would collapse all 225 accepted rows into one denominator and miss that opening-drive projection rows are duplicate-clustered source inventory while OTI2 rows are event-order categories.
- Evidence: Opening-drive has 51 row-level inputs but only 8 unique duplicate keys; OTI2 labels are 22/4/3 event-order states.
- Uncertainty: Future denominator choices can still be mishandled if not machine-checked.
- Falsification condition: A future verifier proves denominator and label-family isolation for every packet.
- Exact next action: Use the duplicate denominator control artifact as mandatory future verifier input.
- Owner: `G0_CONTROL`

### G0-D010: Which accepted families are likely design issues versus source artifacts?

- Claim: Terminal-before-entry and no-entry-through-horizon are most likely pending-hygiene design signals; opening-drive projection and canonical duplicate labels are more likely source/denominator control artifacts; OTI2 is event-order contract learning.
- Evidence: Label mechanisms and blocker/reject ledgers separate lifecycle terminal/no-touch states from projection readiness and duplicate identity.
- Uncertainty: Only prospective capture can separate true design issue from source reconstruction artifact.
- Falsification condition: Prospective capture attributes terminal/no-entry states to source gaps rather than pending lifecycle behavior.
- Exact next action: Classify future capture fields by design-signal versus source-control role.
- Owner: `G0_SOURCE_BUILDER`

### G0-D011: What hypotheses become possible?

- Claim: Hypotheses can now target stale pending cancellation, no-touch horizon expiry, fill/path event-order taxonomy, opening-drive projection contracts, and duplicate-safe source identity.
- Evidence: The seven label families provide separated categories that avoid mixing terminal, untouched, filled path, projection, and duplicate states.
- Uncertainty: Hypotheses remain unvalidated and cannot use outcomes until a future frozen result contract exists.
- Falsification condition: A future source contract cannot reproduce these categories prospectively.
- Exact next action: Move hypotheses into source-safe prompt packs with explicit non-result gates.
- Owner: `PREREG_DESIGN_LANE`

### G0-D012: What is the clean path to a future frozen result contract?

- Claim: First harden source contracts and duplicate controls, then collect prospective source-hashed categories, then freeze denominator/sample floor/no-leak policy, then open a separate G12/owner-approved result lane.
- Evidence: Current G12 acceptance is explicitly source/control only; 8 blockers and 65 rejects remain outside labels and denominators.
- Uncertainty: Sample floor and owner approval are not in this lane.
- Falsification condition: Owner closes the route or source contracts prove infeasible.
- Exact next action: Rank source-control lanes ahead of result design.
- Owner: `G0_GOVERNOR`

### G0-D013: What is the strongest counterargument against the next route?

- Claim: The strongest counterargument is that better pending lifecycle capture may only produce cleaner non-trades, not a new edge.
- Evidence: Current evidence is categorical and non-result by design.
- Uncertainty: Learning value may be operational rather than performance-linked.
- Falsification condition: Prospective capture shows no stable category, no preventable lifecycle ambiguity, and no useful source coverage improvement.
- Exact next action: Design the next route to measure source coverage and lifecycle ambiguity reduction, not performance.
- Owner: `SOURCE_BUILDER`

### G0-D014: Where could false confidence enter?

- Claim: False confidence can enter through duplicate denominators, label-family mixing, same-tick order ambiguity, treating rejected rows as hidden outcomes, and overreading accepted source-lane imbalance.
- Evidence: The row ledger has 5 duplicate collision groups, 4 same-tick blockers, 65 rejects, and source-lane counts that are not balanced by design.
- Uncertainty: A future lane can still create new leakage if it adds generated fallback keys or post-event fields.
- Falsification condition: Verifier scans and source-hash controls prove no such leakage in a frozen future packet.
- Exact next action: Keep forbidden-key scans, duplicate checks, and blocker/reject exclusion tests in every route.
- Owner: `G0_CONTROL`

### G0-D015: What is the highest-learning next move beyond the OB-retest backbone?

- Claim: Build pending lifecycle and event-order source primitives first; they can improve market-state awareness and operational hygiene without relying on OB-retest performance claims.
- Evidence: No-fill categories describe opportunity lifecycle states independent of the current edge's outcome math.
- Uncertainty: Any live-system improvement remains hypothetical until prospective source capture and separate validation exist.
- Falsification condition: The primitives fail to reproduce prospectively or add no interpretable ambiguity reduction.
- Exact next action: Prioritize source-control builders over outcome replay.
- Owner: `G0_RESEARCH_PROGRAM_CONTROL`


## Non-Claims

- No result scoring was opened.
- No validation-safe posture was opened.
- No selector, registry, prompt, risk, execution, permission, safety, canary, MT5, credential, remote, paid/API, Databento, or live-order behavior changed.
