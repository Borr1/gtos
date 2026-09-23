# Historical OHLC GTOS Replay Cost/Fill Packet

Generated UTC: `2026-05-16T02:37:23Z`

This packet preserves the full OHLC frontier denominator and materializes source-safe replay/cost/fill input grids for the 6 GTOS replay contracts.

## Counts

- `blocker_resolution_rows`: `30`
- `bucket_rows`: `29`
- `cluster_binding_rows_consumed`: `588`
- `cost_fill_grid_rows`: `15328`
- `cost_proxy_rows`: `8`
- `entry_variant_rows`: `3832`
- `question_rows`: `3`
- `route_status_rows`: `477`
- `source_manifest_rows`: `9`
- `target_action_rows`: `24`
- `target_contract_rows`: `6`
- `target_event_rows`: `958`

## Target Route Event Counts

- `GBPJPY|ny_core|SWEEP_LOW_CLOSE_BACK_INSIDE_16|h16`: `146`
- `GBPJPY|ny_core|SWEEP_LOW_CLOSE_BACK_INSIDE_16|h4`: `146`
- `GBPJPY|tokyo_kz|LOWER_WICK_EXHAUSTION|h4`: `243`
- `GBPJPY|tokyo_kz|SWEEP_HIGH_CLOSE_BACK_INSIDE_16|h4`: `104`
- `GBPJPY|tokyo_kz|SWEEP_LOW_CLOSE_BACK_INSIDE_16|h4`: `156`
- `XAUUSD|ny_core|SWEEP_LOW_CLOSE_BACK_INSIDE_16|h4`: `163`

## Immediate Work

- Join cost/fill grid to source-safe target/stop path controls.
- Split replay contracts by cluster binding and date concentration.
- Route exact spread/slippage/fill gaps into owned/current/free source acquisition or proxy stress.
- Compare OHLC replay controls against no-fill and Route C challenger families.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
