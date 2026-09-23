# Historical OHLC GTOS Replay Cost-Sensitivity Packet

Generated UTC: `2026-05-16T03:02:13Z`

This packet compares zero-cost path descriptors against median/max/static spread proxy descriptors for every entry variant and target/stop contract.

## Counts

- `bucket_rows`: `119`
- `cost_fill_status_input_rows`: `15328`
- `model_delta_rows`: `183936`
- `path_grid_input_rows`: `245248`
- `question_rows`: `3`
- `signature_rows`: `61312`
- `source_manifest_rows`: `4`
- `target_stop_contract_input_rows`: `16`

## Cost Sensitivity Status Counts

- `COST_INVARIANT_DESCRIPTOR`: `48230`
- `COST_INVARIANT_POST_SIGNAL_UNFILLED`: `7824`
- `SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE`: `320`
- `ZERO_TO_SPREAD_PROXY_DESCRIPTOR_SHIFT`: `4938`

## Immediate Work

- Split changed cost-sensitive signatures by route and entry variant.
- Route gradient-sensitive rows into exact spread/slippage source search or conservative stress bounds.
- Split cost-invariant post-signal unfilled rows from market-entry path controls.
- Join cost sensitivity to same-M15 ambiguity and no-fill geometry controls.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
