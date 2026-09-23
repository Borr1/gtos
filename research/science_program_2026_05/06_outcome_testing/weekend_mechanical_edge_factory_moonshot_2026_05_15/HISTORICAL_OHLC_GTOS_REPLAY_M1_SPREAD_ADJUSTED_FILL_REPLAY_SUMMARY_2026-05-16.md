# Historical OHLC GTOS Replay M1 Spread-Adjusted Fill Replay

Generated UTC: `2026-05-16T04:27:13Z`

This packet replays all source-alignment entries where M1 touches every nonzero spread-adjusted threshold while zero entry remains untouched.

## Counts

- `bucket_rows`: `53`
- `cost_model_replay_rows`: `141`
- `entry_replay_rows`: `49`
- `family_replay_rows`: `480`
- `question_rows`: `4`
- `signature_replay_rows`: `2256`
- `source_alignment_cost_model_input_rows`: `196`
- `source_alignment_entry_input_rows`: `49`
- `source_alignment_signature_input_rows`: `784`
- `source_manifest_rows`: `5`
- `target_stop_contract_input_rows`: `16`

## M1 First-Touch Status

- `FILL_BAR_TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY_ORDER_UNRESOLVED`: `176`
- `NO_TARGET_OR_STOP_TOUCH_WITHIN_M1_REPLAY_HORIZON`: `536`
- `TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY`: `1544`

## Immediate Work

- Split fill-bar order-unresolved M1 replay rows with conservative target/stop interval bounds.
- Join M1 spread-adjusted replay families into cost/fill/path synthesis.
- Compare spread-adjusted replay descriptors against near-miss market-entry branches.
- Route partial/source-recheck source-alignment rows into separate repair packets.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
