# Cost, Slippage, And Exit Accounting Coverage - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Coverage

| Metric | Count |
|---|---:|
| `slippage_rows` | 3 |
| `entry_spread_rows` | 3 |
| `entry_slippage_rows` | 3 |
| `time_in_trade_rows` | 0 |
| `pending_lifecycle_rows` | 0 |
| `close_side_cost_rows` | 0 |

## Join Plan

1. Use slippage.ticket and pending lifecycle trade_state_ticket for entry fill quality.
2. Use time-in-trade rows only after a closed broker trade exists; they are exit diagnostics, not live exit changes.
3. Do not evaluate partial close, trailing, BE, or exit variants as promotion candidates until close-side spread/cost and actual broker-R are present.

## Blocker

Close-side spread/cost is not yet a complete live shadow log; add execution telemetry before exit-policy promotion work.
