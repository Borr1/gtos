# Historical OHLC GTOS Replay Recovered-Unfilled Path Controls

Generated UTC: `2026-05-16T03:46:49Z`

This packet recomputes M15 target/stop paths for recovered unfilled entry probes while separating exact tick fills from M1 bid-bar proxy recoveries.

## Counts

- `bucket_rows`: `32`
- `entry_path_rows`: `51`
- `question_rows`: `3`
- `recovered_entry_input_rows`: `51`
- `recovered_signature_input_rows`: `816`
- `signature_path_rows`: `816`
- `source_manifest_rows`: `6`
- `unfilled_entry_probe_input_rows`: `489`
- `unfilled_signature_probe_input_rows`: `7824`

## Recovered Path Status

- `EXACT_TICK_RECOVERED_FILL_PATH_AFTER_FILL_BAR_ORDERED_M15`: `20`
- `EXACT_TICK_RECOVERED_FILL_PATH_WITH_FILL_BAR_ORDER_AMBIGUITY`: `12`
- `M1_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED_PATH_STRESS`: `196`
- `M1_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED_WITH_FILL_BAR_ORDER_AMBIGUITY`: `588`

## Immediate Work

- Join recovered exact/proxy rows to no-fill geometry and exact-spread controls.
- Route fill-bar order-ambiguous recovered rows to M1/tick ordering stress.
- Split tick-confirmed no-fill families into execution-friction avoid/fillability branches.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
