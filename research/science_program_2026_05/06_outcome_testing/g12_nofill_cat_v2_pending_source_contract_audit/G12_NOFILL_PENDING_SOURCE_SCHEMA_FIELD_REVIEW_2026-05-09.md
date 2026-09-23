# G12 NOFILL Pending Source Schema Field Review

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.
Field count: `46`.

## Family Counts

| family | count |
| --- | --- |
| active_pending_window | 3 |
| cancel_expiry_reason | 1 |
| decision_asof | 1 |
| duplicate_denominator | 6 |
| entry_touch_proof | 3 |
| forbidden_field_guard | 1 |
| identity_provenance | 6 |
| label_family_separation | 2 |
| missing_source_blocker_taxonomy | 1 |
| no_touch_proof | 1 |
| noncanonical_projection_exclusion | 1 |
| pending_cancel_expiry | 2 |
| pending_create | 2 |
| prospective_capture | 1 |
| protective_level_touch_proof | 3 |
| quote_side | 1 |
| same_tick_same_bar_ambiguity | 1 |
| source_coverage | 3 |
| source_granularity_parser | 2 |
| source_hash_path | 2 |
| terminal_area_touch_proof | 3 |

## Missing Or Unsafe Findings

- Missing required families: `[]`
- Missing required field names: `[]`
- Forbidden schema field names: `[]`

## Nonblocking Hardening Amendments

- Future packet builders should emit a per-row source_coverage_gap_code whenever source_coverage_status is not COMPLETE.
- Future packet builders should freeze event_order_resolution_method as source_tick, lower_tf_bound, same_tick_ambiguous, or unavailable_source.
- Future source_hash_manifest entries should include parser code hash plus data file hashes, not only data file paths.
