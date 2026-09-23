# G12 No-Fill Source-Correction Learning Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

- The original 52 categorical lifecycle-only labels remain accepted and have zero overlap with corrected or still-blocked rows.
- OTI2 V2 is the correct consolidation point for OTI1 entry-touch rows and OTI3 entry-before-terminal rows; its labels remain categorical event-order evidence only.
- OTI5 duplicate conflicts are denominator problems, not performance evidence: 3 canonical rows survive and 39 repeated projections are excluded.
- OTI4 source correction proves 51 opening-drive projections ready, 26 contract exclusions, and 3 true May 3 source gaps.
- The four OTI3 same-timestamp rows stay blocked because the source tick itself crosses multiple event thresholds at one timestamp.

## Remaining Exact Blockers

- `NOFILL-CLOSE-ROW-0049`: `BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP` - Preserve exact source gap and request read-only tick or M1/lower OHLC source for the frozen opening range.
- `NOFILL-CLOSE-ROW-0050`: `BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP` - Preserve exact source gap and request read-only tick or M1/lower OHLC source for the frozen opening range.
- `NOFILL-CLOSE-ROW-0051`: `BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP` - Preserve exact source gap and request read-only tick or M1/lower OHLC source for the frozen opening range.
- `NOFILL-CLOSE-ROW-0130`: `BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE` - Preserve exact blocker until the named source/order evidence is supplied.
- `NOFILL-CLOSE-ROW-0143`: `BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE` - Preserve exact blocker until the named source/order evidence is supplied.
- `NOFILL-CLOSE-ROW-0165`: `BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE` - Preserve exact blocker until the named source/order evidence is supplied.
- `NOFILL-CLOSE-ROW-0178`: `BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE` - Preserve exact blocker until the named source/order evidence is supplied.
- `NOFILL-CLOSE-ROW-0241`: `BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED+BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP` - Preserve exact blocker until the named source/order evidence is supplied.
