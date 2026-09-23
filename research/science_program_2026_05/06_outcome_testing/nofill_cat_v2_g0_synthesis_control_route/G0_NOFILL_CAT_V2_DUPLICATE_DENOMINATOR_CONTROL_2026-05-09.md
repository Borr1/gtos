# G0 NOFILL CAT V2 Duplicate Denominator Control

Promotion posture: `NO_PROMOTION_VERDICT`.

## Duplicate Posture

- Accepted row-level source inputs: `225`
- Accepted unique no-fill duplicate keys: `182`
- Accepted duplicate-key collision groups: `5`
- Accepted duplicate-key collision rows: `48`
- OTI5 canonical duplicate rows accepted: `3`
- OTI5 noncanonical duplicate projections rejected: `39`

## Mandatory Controls

### `DUP-001`

- Control: Freeze denominator scope before outcome opening.
- Evidence: Current source-control denominator is 225 row-level accepted inputs, but unique accepted duplicate keys are 182.
- Required check: Every future packet must state row-level versus unique-key denominator before labels/results.
- Failure mode prevented: Inflating sample size by mixing projections and unique opportunities.

### `DUP-002`

- Control: Keep noncanonical duplicate projections outside labels and denominators.
- Evidence: 39 OTI5 noncanonical duplicate projections are rejected and carry no label.
- Required check: Rows with REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION must not appear in accepted labels or future result route denominators.
- Failure mode prevented: Counting repeated projections as independent evidence.

### `DUP-003`

- Control: Separate source projection readiness from lifecycle result labels.
- Evidence: 51 opening-drive projection rows collapse into 8 unique no-fill duplicate keys and are no-result labels.
- Required check: Projection-ready labels may populate source inventory only until a separate categorical contract freezes denominator and labels.
- Failure mode prevented: Turning source inventory into hidden result evidence.

### `DUP-004`

- Control: Require stable nofill_duplicate_key and duplicate_group_id provenance.
- Evidence: The G12 audit found no forbidden generated-key leakage and accepted OTI5 canonical source identity only.
- Required check: Future builders must reject missing or generated fallback duplicate keys unless they are explicitly quarantined and audited.
- Failure mode prevented: Silent duplicate drift across rebuilt packets.

### `DUP-005`

- Control: Publish both row-level and unique-key counts in every synthesis.
- Evidence: Current duplicate posture is {'accepted_row_level_source_inputs': 225, 'accepted_unique_nofill_duplicate_keys': 182, 'accepted_duplicate_collision_groups': 5, 'accepted_duplicate_collision_rows': 48, 'opening_drive_collision_rows': 48, 'oti5_canonical_duplicate_rows_accepted': 3, 'oti5_noncanonical_duplicate_projections_rejected': 39}.
- Required check: Completion audit must reconcile both counts and collision groups.
- Failure mode prevented: False confidence from a single denominator.


## Future Builder Requirements

- Publish accepted row-level count and unique duplicate-key count.
- Publish duplicate collision groups and rows.
- Reject noncanonical projection rows before label assignment.
- Freeze denominator scope before any outcome opening.
- Scan for generated fallback duplicate keys.
