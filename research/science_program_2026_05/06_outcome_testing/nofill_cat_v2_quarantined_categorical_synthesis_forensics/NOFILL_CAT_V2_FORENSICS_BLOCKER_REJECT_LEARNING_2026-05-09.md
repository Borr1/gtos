# NOFILL CAT V2 Blocker/Reject Learning

Promotion posture: `NO_PROMOTION_VERDICT`.

Blocked rows: `8`. Rejected rows: `65`.

## Blocker Codes

| Value | Count |
|---|---:|
| `BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE` | 4 |
| `BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP` | 1 |
| `BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED` | 1 |
| `BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP` | 3 |

## Reject Codes

| Value | Count |
|---|---:|
| `BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE` | 12 |
| `BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE` | 6 |
| `BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION` | 8 |
| `REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION` | 39 |

## Reject Decisions

| Value | Count |
|---|---:|
| `REJECT_FROM_REBUILD_CONTRACT_EXCLUDED` | 26 |
| `REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE` | 39 |

## Blocker Families

### oti4_may3_source_gaps

- Rows: `3` - `['NOFILL-CAT-ROW-0049', 'NOFILL-CAT-ROW-0050', 'NOFILL-CAT-ROW-0051']`
- Status: `EXACT_SOURCE_GAP`
- Learning: Local NAS100/XAUUSD tick files exist but have zero rows in the frozen 2026-05-03 13:00-13:30 UTC opening range; the OTI4 source-search ledger found no approved CSV/OHLC substitute.
- Exact unblocker: Read-only tick parquet or M1/lower OHLC covering the frozen opening range, source-hashed with as-of provenance.

### oti3_same_tick_order_ambiguities

- Rows: `4` - `['NOFILL-CAT-ROW-0130', 'NOFILL-CAT-ROW-0143', 'NOFILL-CAT-ROW-0165', 'NOFILL-CAT-ROW-0178']`
- Status: `SOURCE_SAFE_ORDERING_IMPOSSIBLE_FROM_CURRENT_TICK_ROWS`
- Learning: The first source timestamp has a single tick row satisfying entry and protective predicates simultaneously; current approved data has no intra-tick order.
- Exact unblocker: Higher-resolution or broker-native event-order source that proves intra-tick sequence without account/order labels.

### original_oti2_source_gap

- Rows: `1` - `['NOFILL-CAT-ROW-0241']`
- Status: `EXACT_ACTIVE_WINDOW_SOURCE_GAP`
- Learning: M1 context is not side-aware tick proof and XAUUSD tick coverage misses the active pending window through cancel.
- Exact unblocker: Side-aware bid/ask tick or approved lower source covering the active pending window through cancel.

## Reject Families

### oti4_contract_excluded

- Rows: `26`
- Status: `CONTRACT_EXCLUDED_NO_LABEL`
- Learning: These rows fail the frozen OTI4 source contract and therefore cannot be label or denominator evidence.

### oti5_noncanonical_duplicate_projections

- Rows: `39`
- Status: `DUPLICATE_EXCLUDED_NO_LABEL`
- Learning: These are repeated noncanonical projections. Counting them would inflate the denominator.

## Saturation

All 8 blockers are exact from approved inputs; each has a precise source/access unblocker or source-safe impossibility proof.
