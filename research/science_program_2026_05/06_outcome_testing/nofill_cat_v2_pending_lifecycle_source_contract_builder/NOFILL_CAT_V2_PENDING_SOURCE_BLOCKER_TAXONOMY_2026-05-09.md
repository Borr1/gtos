# NOFILL CAT V2 Pending Source Blocker Taxonomy

Promotion posture: `NO_PROMOTION_VERDICT`.

Blockers: `8`. Rejects: `65`.

## Blocker Families

### `oti4_may3_source_gaps` (3)

- Rows: `NOFILL-CAT-ROW-0049, NOFILL-CAT-ROW-0050, NOFILL-CAT-ROW-0051`
- Missing source/field: Read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC opening range.
- Contract fields that prevent recurrence: `source_coverage_status, source_path_list, source_hash_manifest, source_coverage_start_utc, source_coverage_end_utc`
- Denominator policy: `outside_accepted_labels_and_denominators_until_exact_source_clearance`
- Result use: `forbidden`

### `oti3_same_tick_order_ambiguities` (4)

- Rows: `NOFILL-CAT-ROW-0130, NOFILL-CAT-ROW-0143, NOFILL-CAT-ROW-0165, NOFILL-CAT-ROW-0178`
- Missing source/field: Higher-resolution or broker-native event-order source proving sequence inside identical timestamp without account/order labels.
- Contract fields that prevent recurrence: `same_tick_same_bar_ambiguity_status, source_granularity, parser_version, quote_side_used`
- Denominator policy: `outside_accepted_labels_and_denominators_until_higher_resolution_event_order_source_exists`
- Result use: `forbidden`

### `original_oti2_source_gap` (1)

- Rows: `NOFILL-CAT-ROW-0241`
- Missing source/field: Side-aware bid/ask tick or approved lower source covering active pending window through cancel.
- Contract fields that prevent recurrence: `quote_side_used, side_aware_entry_touch_status, source_coverage_status, active_pending_window_end_reason`
- Denominator policy: `outside_accepted_labels_and_denominators_until_side_aware_coverage_exists`
- Result use: `forbidden`


## Reject Families

### `oti4_contract_exclusions` (26)

- Reject codes: `BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE, BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION, BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE`
- Policy: `contract_excluded_no_label_no_denominator_no_result_use`

### `oti5_noncanonical_duplicate_projections` (39)

- Reject codes: `REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION`
- Policy: `duplicate_excluded_no_label_no_denominator_no_result_use`
