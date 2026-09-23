# G12 NOFILL CAT V2 Decision Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

Decision: `ACCEPT_AS_INPUT_ONLY_CATEGORICAL_LIFECYCLE_EVIDENCE_WITH_BLOCKED_AND_REJECTED_FAMILIES_PRESERVED`.
Status: `PASS`.

## Exact Partition

- `298 = 225 accepted + 8 blocked + 65 rejected`.
- `225 = 52 prior accepted + 173 source-corrected accepted`.
- Accepted, blocked, and rejected row id sets have zero overlap.

## Accepted Label Counts

| Label | Count |
|---|---:|
| `canonical_duplicate_geometry_source_ready_no_label_assigned` | 3 |
| `fill_path_entry_before_protective_level_before_terminal_area` | 4 |
| `fill_path_entry_before_protective_level_no_terminal_observed` | 22 |
| `fill_path_entry_before_terminal_area_before_protective_level` | 3 |
| `nofill_terminal_before_entry` | 110 |
| `opening_drive_source_projection_ready_no_result_label` | 51 |
| `source_corrected_no_entry_through_pending_horizon` | 32 |

## Source Lane Counts

| Source lane | Accepted rows |
|---|---:|
| `OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET` | 32 |
| `OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2` | 29 |
| `OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT` | 58 |
| `OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION` | 51 |
| `OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT` | 3 |
| `prior_g12_categorical_packet_audit` | 52 |

## Interpretation

Accepted means narrow input-only categorical evidence. It does not mean R, win rate, expectancy, broker actual-R, validation, promotion, or a live gate.
