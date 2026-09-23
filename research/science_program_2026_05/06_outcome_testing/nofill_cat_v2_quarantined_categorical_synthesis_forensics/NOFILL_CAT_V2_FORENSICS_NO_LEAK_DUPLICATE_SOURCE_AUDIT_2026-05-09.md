# NOFILL CAT V2 No-Leak / Duplicate / Source Audit

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.

| Check | Status | Evidence |
|---|---|---|
| `exact_partition_298_225_8_65` | `PASS` | `{"accepted": 225, "blocked": 8, "rejected": 65}` |
| `accepted_required_source_fields_non_null` | `PASS` | `{}` |
| `accepted_label_counts_expected` | `PASS` | `{"canonical_duplicate_geometry_source_ready_no_label_assigned": 3, "fill_path_entry_before_protective_level_before_terminal_area": 4, "fill_path_entry_before_protective_level_no_terminal_observed": 22, "fill_path_entr...` |
| `accepted_source_lane_counts_expected` | `PASS` | `{"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32, "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29, "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58, "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION"...` |
| `blocker_codes_expected` | `PASS` | `{"BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4, "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1, "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1, "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3}` |
| `reject_decisions_expected` | `PASS` | `{"REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26, "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39}` |
| `blockers_have_no_labels` | `PASS` | `[]` |
| `rejects_have_no_labels` | `PASS` | `[]` |
| `blocked_or_rejected_not_in_denominator` | `PASS` | `[]` |
| `source_hash_reference_status` | `PASS` | `{"g12_source_status": "PASS", "source_hash_drift_classification": "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION"}` |
| `label_duplicate_no_leak_status` | `PASS` | `{"countable_scope": {"performance_outcome_rows": 0, "row_level_input_only_categorical_evidence": 225, "unique_duplicate_key_input_only_categorical_evidence": 182, "validation_or_promotion_rows": 0}, "g12_noleak_status...` |
| `generated_forbidden_output_keys` | `PASS` | `[]` |

## Source Hash References

- G12 source status: `PASS`.
- V2 source status: `PASS`.
- Source drift classification: `NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION`.

## Duplicate Policy

Accepted duplicate-key collisions are confined to opening-drive source projections that are not result labels; the OTI5 duplicate-conflict family is canonicalized to 3 accepted source-identity rows and 39 noncountable rejects.
