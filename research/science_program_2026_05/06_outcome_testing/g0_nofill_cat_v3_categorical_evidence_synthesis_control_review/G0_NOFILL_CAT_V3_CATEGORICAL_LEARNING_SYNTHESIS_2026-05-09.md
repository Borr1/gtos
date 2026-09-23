# G0 NOFILL CAT V3 Categorical Learning Synthesis

Promotion posture: `NO_PROMOTION_VERDICT`.

Primary denominator: `nofill_duplicate_key`. Row-level counts remain descriptive source inventory.

## Primary Count-Control View

| Label | Primary Duplicate-Key Count | Scope Risk |
|---|---:|---|
| `canonical_duplicate_geometry_source_ready_no_label_assigned` | 3 | single source lane OTI5_G6_CUSUM |
| `fill_path_entry_before_protective_level_before_terminal_area` | 4 | single source lane OTI3_G3_GEOMETRY; single symbol USDJPY; single session tokyo; single side SHORT |
| `fill_path_entry_before_protective_level_no_terminal_observed` | 22 | single source lane OTI1_LIFECYCLE; single side LONG |
| `fill_path_entry_before_terminal_area_before_protective_level` | 3 | single source lane OTI3_G3_GEOMETRY; single symbol USDJPY; single session tokyo; single side LONG |
| `nofill_terminal_before_entry` | 110 | dominant label family, broadest but still source-lane and side skewed |
| `opening_drive_source_projection_ready_no_result_label` | 8 | single source lane OTI4_G6_OPENING_DRIVE |
| `source_corrected_no_entry_through_pending_horizon` | 32 | single source lane OTI1_LIFECYCLE |

## Label-Family Learning

### nofill_terminal_before_entry

- Mechanism clue: Terminal-area state can appear before a side-aware entry touch; pending-entry geometry and stale intent handling are the main control questions.
- Source/control meaning: The approved source can distinguish terminal-before-entry lifecycle order for many accepted duplicate keys.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Forward capture should log pending creation, terminal-area touch, entry-touch absence, cancel/expiry reason, spread/source coverage, and POI age.

### source_corrected_no_entry_through_pending_horizon

- Mechanism clue: Some accepted rows are true no-entry-through-horizon states after source correction, suggesting pending horizon and cancellation windows matter.
- Source/control meaning: No side-aware entry event was found through the frozen pending horizon under the source contract.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Capture as-of horizon start/end, last eligible quote, cancel reason, and whether the untouched state is stale-POI, late-cancel, or normal expiry.

### fill_path_entry_before_protective_level_no_terminal_observed

- Mechanism clue: Source can identify entry before protective-level touch while terminal observation remains absent in the approved window.
- Source/control meaning: This is a fill/path event-order category with an unresolved terminal observation, not a trade result.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: A future event-order contract needs event timestamps, source window end reason, terminal search coverage, and same-tick ambiguity flags.

### fill_path_entry_before_protective_level_before_terminal_area

- Mechanism clue: A small USDJPY Tokyo family has source-ordering through entry, protective level, then terminal area.
- Source/control meaning: The source can order a full three-event path for the row family, but only as a categorical state.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Needs broker-native quote-event sequencing for the unresolved USDJPY rows before any broader interpretation.

### fill_path_entry_before_terminal_area_before_protective_level

- Mechanism clue: A small USDJPY Tokyo family has source-ordering through entry, terminal area, then protective level.
- Source/control meaning: The source can distinguish the opposite terminal/protective order for a small categorical family.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Keep as event-order vocabulary for a future frozen result contract; do not infer usefulness from the ordering alone.

### opening_drive_source_projection_ready_no_result_label

- Mechanism clue: Opening-drive projections can be source-ready but remain label-incomplete; row-level projections collapse sharply under duplicate keys.
- Source/control meaning: The source-projection family is ready for a future contract-design lane, not a result lane.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Needs a separate frozen opening-drive result contract with as-of breakout/range definitions, event-order labels, duplicate policy, and post-count G12 audit before any result opening.

### canonical_duplicate_geometry_source_ready_no_label_assigned

- Mechanism clue: A small canonical duplicate-geometry residue exists after source-identity cleanup.
- Source/control meaning: Duplicate identity and geometry controls can preserve source-ready rows without assigning an outcome label.
- Does not mean: not a result score, not validation evidence, not a promotion basis, not broker/account/live-order evidence, not a hidden-label substitute.
- Next capture or blocker: Needs clearer label assignment rules or a source-control return lane if future cohorts produce more rows of this type.

## Hostile Review Answer

- A hostile review should treat every category as possibly duplicated, source-leaked, session-specific, broker-impossible, or over-interpreted until controls show otherwise.
- The duplicate controls handle row-repeat risk for opening-drive projections, but they also show that row-level counts can exaggerate projection-heavy categories.
- Source-impossible USDJPY rows are not inferred away; they remain exact blockers needing broker-native quote-event sequencing.
- The dominant terminal-before-entry family is useful mechanism vocabulary, not proof that any future action is beneficial.

## What Could Destroy The Interpretation

- A future source-hash mismatch or stale source artifact.
- A future accepted duplicate-key label/geometry conflict.
- Evidence that label definitions used post-event or hidden fields.
- A broader cohort showing the same labels are only an artifact of one source lane, symbol, or session.
- Broker-native quote-event data changing the four USDJPY source-impossible row classifications.
