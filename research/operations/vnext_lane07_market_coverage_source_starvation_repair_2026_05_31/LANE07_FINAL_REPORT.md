# Lane 07 Market Coverage Source Starvation Repair

Generated: `2026-05-31T14:13:40.514361+00:00`

## Result

- 24-symbol source integrity rows: `24`
- 24-symbol opportunity funnel rows: `24`
- 24-symbol starvation decision rows: `24`
- Material rows classified: `331`
- Repair rows: `5`

## Starvation Classes

- `genuinely_quiet_no_candidate`: `3`
- `not_starved_order_placement_reached`: `2`
- `risk_missing_or_selected_cell_bridge_blocked`: `18`
- `schedule_blocked_or_genuinely_quiet_current_window`: `1`

## Boundary

This route performed local source/logging/test/verifier work only. It did not place, modify, or cancel broker orders; did not call paid APIs; did not change credentials; did not push remotely; and did not alter live trading selection/risk/safety behavior.
