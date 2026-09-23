# Cost, Slippage, And Exit Accounting Coverage

**Promotion verdict:** `NO_PRODUCTION_PROMOTION_DECISION`

## Coverage

| Metric | Count |
|---|---:|
| `slippage_rows` | 13 |
| `entry_slippage_log_rows` | 13 |
| `close_slippage_log_rows` | 0 |
| `entry_spread_rows` | 13 |
| `entry_slippage_rows` | 13 |
| `close_slippage_rows` | 0 |
| `close_commission_rows` | 0 |
| `close_swap_rows` | 0 |
| `close_deal_id_rows` | 0 |
| `time_in_trade_rows` | 51 |
| `pending_lifecycle_rows` | 877 |
| `close_side_cost_rows` | 0 |

## Join Plan

1. Use slippage.ticket and pending lifecycle trade_state_ticket for entry fill quality.
2. Use slippage_event_type=close rows for close-side slippage, BE, partial-close, commission/swap, and MT5 deal-id coverage.
3. Use time-in-trade rows only after a closed broker trade exists; they are exit diagnostics, not live exit changes.
4. Do not evaluate partial close, trailing, BE, or exit variants as promotion candidates until close-side spread/cost and actual broker-R are present.

## Blocker

Close-side spread/cost is not yet a complete live shadow log; add execution telemetry before exit-policy promotion work.
