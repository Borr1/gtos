# NOFILL CAT V2 Label-Family Analysis

Promotion posture: `NO_PROMOTION_VERDICT`.

All counts are descriptive source-control summaries over accepted input-only rows.

## canonical_duplicate_geometry_source_ready_no_label_assigned

- Count: `3` rows; `3` unique no-fill duplicate keys.
- Mechanism: The duplicate-geometry rule selected a canonical countable source-identity row but did not assign a result label.
- Proves: Duplicate-control can collapse a repeated projection family into source-identity evidence.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence, not a lifecycle result label.
- Failure anatomy: The prior duplicate conflict was a denominator-control issue; canonical source identity fixes countability but cannot infer lifecycle outcome.
- Future hypothesis: Keep canonical duplicate controls as a precondition for future packet builders, and never let noncanonical projections enter result denominators.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT': 3}` |
| Symbol | `{'NAS100': 1, 'XAGUSD': 2}` |
| Session | `{'london': 1, 'ny': 2}` |
| Side | `{'LONG': 1, 'SHORT': 2}` |

## fill_path_entry_before_protective_level_before_terminal_area

- Count: `4` rows; `4` unique no-fill duplicate keys.
- Mechanism: Source-ordered events show entry, then protective level, then terminal area.
- Proves: The source can order three lifecycle predicates for a small subset of fill/path rows.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence.
- Failure anatomy: The row family can express a complete lifecycle ordering, but the label does not say whether the order was good, bad, or tradable.
- Future hypothesis: Use this ordering as a future categorical state in a frozen result contract, not as current performance evidence.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2': 4}` |
| Symbol | `{'USDJPY': 4}` |
| Session | `{'tokyo': 4}` |
| Side | `{'SHORT': 4}` |

## fill_path_entry_before_protective_level_no_terminal_observed

- Count: `22` rows; `22` unique no-fill duplicate keys.
- Mechanism: Source-ordered events show entry before the protective level, with no terminal-area event observed inside the approved path window.
- Proves: A fill/path transition can be categorized as entry then protective without observed terminal completion in the source window.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence.
- Failure anatomy: Lifecycle evidence can enter a post-entry transition state that lacks terminal observation; that is an ordering fact, not a result.
- Future hypothesis: Collect fill/path transition labels prospectively with same-tick blockers separated before any post-entry result lane opens.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2': 22}` |
| Symbol | `{'GBPJPY': 14, 'NAS100': 8}` |
| Session | `{'london': 8, 'tokyo': 14}` |
| Side | `{'LONG': 22}` |

## fill_path_entry_before_terminal_area_before_protective_level

- Count: `3` rows; `3` unique no-fill duplicate keys.
- Mechanism: Source-ordered events show entry, then terminal area, then protective level.
- Proves: The source can identify a terminal-area-before-protective lifecycle ordering in a small subset.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence.
- Failure anatomy: This is the strongest-looking lifecycle ordering semantically, but it remains descriptive because no result values or broker facts are opened.
- Future hypothesis: If a later result lane is approved, freeze this label as one event-order category before opening any quantitative scoring.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2': 3}` |
| Symbol | `{'USDJPY': 3}` |
| Session | `{'tokyo': 3}` |
| Side | `{'LONG': 3}` |

## nofill_terminal_before_entry

- Count: `110` rows; `110` unique no-fill duplicate keys.
- Mechanism: The approved source path reaches the terminal area before a side-aware entry touch.
- Proves: A pending idea can become lifecycle-invalid before it ever becomes an entry event under the source contract.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence.
- Failure anatomy: The setup lifecycle can end upstream of fill; pending-intent hygiene needs explicit terminal-before-entry observation and cancellation context.
- Future hypothesis: Preregister a pending-hygiene capture lane that measures how often terminal-before-entry states arrive before current cancellation logic can respond.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT': 58, 'prior_g12_categorical_packet_audit': 52}` |
| Symbol | `{'NAS100': 17, 'US30_cash': 2, 'USDJPY': 60, 'XAGUSD': 25, 'XAUUSD': 6}` |
| Session | `{'london': 25, 'ny': 61, 'tokyo': 24}` |
| Side | `{'LONG': 22, 'SHORT': 88}` |

## opening_drive_source_projection_ready_no_result_label

- Count: `51` rows; `8` unique no-fill duplicate keys.
- Mechanism: Opening-drive range/breakout/as-of source projection is ready, but no result label is assigned.
- Proves: The source projection can be reconstructed for future contract work.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence, not a no-fill result label.
- Failure anatomy: Projection readiness is useful inventory, but duplicate-key clustering shows it can inflate row counts if converted into denominator evidence too early.
- Future hypothesis: Build a separate opening-drive categorical contract audit that freezes denominator and label assignment before any outcomes are opened.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION': 51}` |
| Symbol | `{'GBPJPY': 4, 'NAS100': 11, 'US30_cash': 1, 'XAGUSD': 35}` |
| Session | `{'london': 14, 'ny': 33, 'tokyo': 4}` |
| Side | `{'LONG': 15, 'SHORT': 36}` |

## source_corrected_no_entry_through_pending_horizon

- Count: `32` rows; `32` unique no-fill duplicate keys.
- Mechanism: Corrected source fields show no side-aware entry touch through the frozen pending horizon.
- Proves: Some no-fill rows are true no-entry-through-horizon source states, not missing labels.
- Does not prove: not R/performance, not win rate, not expectancy, not broker actual-R, not account history, not validation, not promotion, not live-gate or live-order evidence.
- Failure anatomy: The pending window can expire without a side-aware entry event; without richer cancellation telemetry, this cannot decide whether the setup should have expired earlier.
- Future hypothesis: Preregister a no-entry horizon lane that separates late cancellation, stale POI, and genuinely untouched entry states before any rule change is considered.

| Slice | Counts |
|---|---|
| Source lane | `{'OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET': 32}` |
| Symbol | `{'NAS100': 24, 'XAUUSD': 8}` |
| Session | `{'london': 8, 'ny': 24}` |
| Side | `{'LONG': 24, 'SHORT': 8}` |

## OTI2 Fill/Path Rollup

The OTI2 rows are source-ordered event-order categories around entry, protective level, and terminal area.

Non-claim: They are not PnL, not broker realized outcomes, and not validation evidence.
