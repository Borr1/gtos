# Historical OHLC GTOS Replay Path-Control Packet

Generated UTC: `2026-05-16T02:51:40Z`

This packet joins the 15,328 replay cost/fill rows to post-signal M15 target/stop path controls.

## Counts

- `ambiguity_rows`: `9185`
- `bucket_rows`: `223`
- `cost_fill_input_rows`: `15328`
- `cost_fill_status_rows`: `15328`
- `event_descriptor_rows`: `15328`
- `path_control_grid_rows`: `245248`
- `question_rows`: `4`
- `source_manifest_rows`: `8`
- `target_stop_contract_rows`: `16`

## First-Touch Status Counts

- `NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON`: `37521`
- `POST_SIGNAL_ENTRY_NOT_FILLED_WITHIN_HORIZON`: `31296`
- `STOP_TOUCH_BEFORE_TARGET_M15_PROXY`: `20975`
- `STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `57651`
- `TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS`: `9185`
- `TARGET_TOUCH_BEFORE_STOP_M15_PROXY`: `14129`
- `TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `74491`

## Immediate Work

- Build cost-sensitivity deltas by zero-cost versus observed/fallback spread proxies.
- Route same-M15 target/stop ambiguity into M1/tick reconstruction or conservative stress bounds.
- Split post-signal unfilled limit entries from market-entry variants.
- Compare path-control descriptors against no-fill and Route C source-control families.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
