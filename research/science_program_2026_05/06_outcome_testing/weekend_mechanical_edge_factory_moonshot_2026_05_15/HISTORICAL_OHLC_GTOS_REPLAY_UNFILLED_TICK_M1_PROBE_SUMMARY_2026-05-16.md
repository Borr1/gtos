# Historical OHLC GTOS Replay Unfilled Tick/M1 Probe

Generated UTC: `2026-05-16T03:37:11Z`

This packet probes every unique cost-invariant unfilled retest-limit entry window with read-only MT5 ticks and M1 bars, then joins probe labels to all unfilled signatures.

## Counts

- `bucket_rows`: `45`
- `entry_window_probe_rows`: `489`
- `question_rows`: `3`
- `recon_route_input_rows`: `192`
- `route_family_probe_rows`: `12`
- `signature_probe_rows`: `7824`
- `source_manifest_rows`: `4`
- `unfilled_signature_input_rows`: `7824`
- `unique_entry_variant_input_rows`: `489`

## Entry Probe Status

- `M1_BID_BAR_TOUCH_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED`: `49`
- `M1_CONFIRMS_NO_BID_BAR_TOUCH`: `367`
- `TICK_CONFIRMS_NO_FILL_SIDE_TOUCH`: `71`
- `TICK_FILL_SIDE_TOUCH_RECOVERED`: `2`

## Immediate Work

- Recompute target/stop paths for any recovered fill rows with source-safe ordering.
- Join tick-confirmed no-fill rows to no-fill geometry and exact-spread controls.
- Split unavailable windows by date/symbol and run broader MT5/local-source acquisition or stress proxy.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
