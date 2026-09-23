# CNR T3 Frozen Lifecycle Contract - 2026-05-08

Contract id: `CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1`
Contract sha256: `7b0d6ad66733f58fff534c4e945631318b253f6973aa38e4a865e4f5d6a8890f`
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Freeze Order
Written before any beyond-original-horizon tick extension scan.

## Allowed Labels
- `target_after_original_horizon`
- `stop_after_original_horizon`
- `ambiguous_target_stop_after_original_horizon`
- `still_no_terminal_after_extended_horizon`
- `source_horizon_insufficient`
- `not_packet_eligible`

## Eligibility
- Row must be an accepted/quarantined CNR/OTI row with original terminal_status exactly NO_TERMINAL_WITHIN_ORDERED_HORIZON.
- Row must have source-hashed quote/path/geometry sufficient to bind symbol, side, path_start_utc, original_horizon_end_utc, original entry, original stop, original TP1, source row hash, and tick source hashes.
- Rows whose only lifecycle state is no-fill, no-entry, still-pending, target-already-passed, source-blocked, or terminal-order-unclaimed are inventoried but labelled not_packet_eligible.
- The 94 G12-blocked CNR061 rows remain excluded from scoring/packet labels; only accepted OTI8 sidecar hashes may be packetized.

## Terminal Rule
- `LONG`: bid >= original_take_profit_1 is target; bid <= original_stop_loss is stop
- `SHORT`: ask <= original_take_profit_1 is target; ask >= original_stop_loss is stop

## No-Leak Boundary
- row identity and upstream hashes
- symbol, side, session, timing family, target family
- original path start/end, extended horizon cap
- original entry, stop, TP1 geometry
- tick source file paths and sha256 hashes
- categorical lifecycle label
- terminal event timestamp and quote side only
- duplicate denominator fields
- NO_PROMOTION_VERDICT and false validation/live flags

Forbidden fields: `account_history`, `broker_actual_r`, `dsr`, `expectancy`, `hidden_path_label`, `live_order_state`, `live_trade_result`, `live_trade_results`, `pbo`, `performance`, `promotion_statistic`, `synthetic_r`, `win_rate`

## Blocked Rows
The 94 G12-blocked CNR061 rows are verified only as excluded and are not opened, scored, or lifecycle-labelled.
