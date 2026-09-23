# NOFILL CAT Failure Learning Ledger - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Failure Anatomy
- `pending_lifecycle_rows`: Blocked because entry_touched_at_utc is not materialized; fill/cancel/expiry/still-pending labels require that field or source-hashed quote touch proof before labels.
- `opening_drive_terminal_projection_rows`: Tick terminal-first evidence exists, including row 0127, but missing prereg opening-drive range/breakout source fields remain exact result blockers under the G12 contract.
- `price_compatible_m1_rows`: Recovered M1 source proves price compatibility only; no side-aware quote/tick terminal replay is opened, so categorical result labels are blocked.
- `entry_touched_unclaimed_row`: The row has an entry touch and unclaimed post-entry terminal order; it belongs in a separate fill/path contract, not this no-fill closure packet.
- `duplicate_conflict_rows`: Three nofill_duplicate_key groups have same source family but differing geometry/order across repeated rows; the contract blocks those groups rather than selecting a convenient row.

## Exact Unblockers
- `pending_lifecycle_unblocker`: Future logger or source packet must materialize entry_touched_at_utc/fill/cancel/expiry/horizon fields without broker/account/live labels.
- `opening_drive_unblocker`: Source-correction or contract-revision lane must source-hash breakout_close_time, breakout_side, range_high, and range_low before categorical result labels for those rows.
- `m1_price_only_unblocker`: Separate accepted conservative quote contract or tick/quote path replay is required; M1 OHLC price compatibility alone is not enough.
- `duplicate_conflict_unblocker`: Source audit must resolve whether repeated rows share one geometry/order or represent separate opportunities before any conflicted key can count.
