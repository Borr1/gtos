# NOFILL Close Forensics And Learning - 2026-05-08

Rows: `298`
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Learning
- `entry_not_touched_through_tick_horizon_source_confirmed`: OTI5 tick paths prove no entry touch through the cited tick horizon; terminal scoring remains blocked.
- `terminal_sequence_tick_source_projected_no_score`: OTI4 terminal touch times can be projected from tick sources under the frozen parser, but opening-drive prereg field gaps remain non-result blockers.
- `price_compatible_m1_source_recovered`: OTI3's earlier Sierra scale blocker is resolved by a price-compatible MT5 USDJPY M1 CSV for source availability only.
- `entry_not_touched_before_terminal_area_source_confirmed`: OTI2 M1 path-order rows prove terminal-area touch before entry touch without carrying R.
- `entry_touched_terminal_sequence_unclaimed_source_confirmed`: The lone OTI2 unresolved row remains terminal-sequence unclaimed from M1 path order despite entry touch evidence.
- `pending_cancelled_wrong_side_before_fill_source_confirmed`: Wrong-side cancellations are internally source-confirmed as no-fill lifecycle closures; they are not performance outcomes.
- `pending_still_open_at_frozen_horizon_source_confirmed`: OTI1 still-pending rows can be source-closed to a frozen lifecycle horizon, but entry-touch timestamps remain a required future logger field.
- `pending_cancelled_system_or_new_day_before_fill_source_confirmed`: Some earlier still-pending rows closed later by system/new-day cancellation in sanitized lifecycle audit source.

## Read-Only Extraction Requests
- None

## Superseded Extraction Requests
- `NOFILL-CLOSE-ROW-0127_READONLY_TICK_WINDOW` superseded by OTR061 local source evidence.
