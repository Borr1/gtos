# NOFILL Close Row Blocker Ledger - 2026-05-08

Rows: `298`
Rows with exact blockers: `204`
Source closed rows: `298`
Exact source-blocked rows: `0`
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Top Blockers
- `80` missing_prereg_opening_drive_field_breakout_close_time
- `80` missing_prereg_opening_drive_field_breakout_side
- `80` missing_prereg_opening_drive_field_range_high
- `80` missing_prereg_opening_drive_field_range_low
- `69` terminal touch replay remains unopened; this lane closes source availability only for prior source-blocked rows
- `54` entry_touched_at_utc is not materialized in pending lifecycle source; future logger must capture it explicitly
- `1` post_entry_terminal_touch_time is not claimable from the M1 path-order row; tick-level terminal sequence should remain a separate audit if needed

## Read-Only Extraction Requests
- None

## Superseded Read-Only Extraction Requests
- `NOFILL-CLOSE-ROW-0127_READONLY_TICK_WINDOW` status `SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE` terminal touch `2026-05-06T07:15:00.634000Z` manifest `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/source_requests/NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json`
