# G0 NOFILL CAT V2 Residual Blocker Route Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

Blocked rows: `8`. Rejected rows: `65`.

Boundary: The 8 blockers and 65 rejects remain outside accepted labels, denominators, result use, validation use, and promotion use.

## Blocker Routes

### `oti4_may3_source_gaps` (3)

- Rows: `NOFILL-CAT-ROW-0049, NOFILL-CAT-ROW-0050, NOFILL-CAT-ROW-0051`
- Current status: `recoverable_only_if_an_approved_read_only_source_covers_the_frozen_opening_range`
- Feasibility class: `LIKELY_RECOVERABLE_WITH_SOURCE_ACCESS_OR_ALTERNATE_M1_LOWER_OHLC`
- Evidence: Prior OTI4 source search found local tick files but zero ticks in the 2026-05-03 13:00-13:30 UTC frozen range. This G0 route found local NAS100 and XAUUSD May 3 tick parquet files for feasibility search, but did not consume them for labels.
- Exact unblocker: Read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC with source hash and as-of provenance.
- Forbidden unblockers: `MT5 order/account/history calls, broker result fields, post-outcome inference`
- Recommended route: `NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`
- Priority: `P2_AFTER_G0_SOURCE_CONTRACT_BACKLOG`

### `oti3_same_tick_order_ambiguities` (4)

- Rows: `NOFILL-CAT-ROW-0130, NOFILL-CAT-ROW-0143, NOFILL-CAT-ROW-0165, NOFILL-CAT-ROW-0178`
- Current status: `not_orderable_from_current_tick_granularity`
- Feasibility class: `TRUE_IMPOSSIBILITY_FROM_CURRENT_APPROVED_TICK_ROWS_RECOVERABLE_ONLY_WITH_HIGHER_RES_EVENT_ORDER`
- Evidence: Each row has entry and protective predicates on the same first source timestamp under the frozen contract. This G0 route found USDJPY tick/source artifacts, including the May 1 parquet and prior OTI3 April 20 read-only tick artifact, but those artifacts preserve the same timestamp ambiguity.
- Exact unblocker: Higher-resolution or broker-native event-order source that proves sequence inside the identical timestamp without account/order labels.
- Forbidden unblockers: `guessing sequence, using broker realized results, using account/order history labels`
- Recommended route: `PARK_UNTIL_HIGHER_RES_EVENT_ORDER_SOURCE_EXISTS`
- Priority: `P5_LOW_FEASIBILITY`

### `original_oti2_source_gap` (1)

- Rows: `NOFILL-CAT-ROW-0241`
- Current status: `recoverable_if_side_aware_active_window_source_exists`
- Feasibility class: `POTENTIALLY_RECOVERABLE_WITH_TARGETED_XAUUSD_SIDE_AWARE_TICK_COVERAGE`
- Evidence: Prior G12 and forensics artifacts say M1 context is not side-aware proof and XAUUSD tick coverage misses the active pending window through cancel. This G0 route found XAUUSD 2026-05-05 tick parquet in the absolute local tick root, but did not open a blocker-clearing extraction.
- Exact unblocker: Side-aware bid/ask tick or approved lower source covering the active pending window through cancel.
- Forbidden unblockers: `M1-only inference as side-aware proof, live order labels, account history`
- Recommended route: `NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`
- Priority: `P3_AFTER_OTI4_SOURCE_GAPS`


## Reject Families

### `oti4_contract_exclusions` (26)

- Status: `CONTRACT_EXCLUDED_NO_LABEL_NO_DENOMINATOR`
- Next action: Do not route unless a separate contract revision is approved before label assignment.

### `oti5_noncanonical_duplicate_projections` (39)

- Status: `DUPLICATE_EXCLUDED_NO_LABEL_NO_DENOMINATOR`
- Next action: Keep excluded; use only as duplicate-control evidence.
