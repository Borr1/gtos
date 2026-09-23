# Historical OHLC GTOS Replay Confirmed No-Fill Near-Miss Entry Controls

Generated UTC: `2026-05-16T04:50:51Z`

This packet materializes branch-local near-miss entry-offset and market-entry controls. It preserves every confirmed near-miss branch row and records direct source-join absences as source requirements, not completion blockers.

## Counts

- `bucket_rows`: `61`
- `friction_branch_input_rows`: `7008`
- `friction_entry_input_rows`: `489`
- `friction_signature_input_rows`: `7824`
- `market_entry_branch_rows`: `896`
- `m1_spread_entry_input_rows`: `49`
- `m1_spread_signature_input_rows`: `2256`
- `near_miss_branch_rows`: `112`
- `near_miss_entry_rows`: `7`
- `offset_branch_rows`: `224`
- `question_rows`: `5`
- `source_manifest_rows`: `24`
- `source_requirement_rows`: `560`
- `unique_near_miss_events`: `7`
- `unique_near_miss_entry_ids`: `7`

## Offset First-Touch Status

- `NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON`: `118`
- `STOP_TOUCH_BEFORE_TARGET_M15_PROXY`: `4`
- `STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `22`
- `TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS`: `10`
- `TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `70`

## Market First-Touch Status

- `NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON`: `338`
- `STOP_TOUCH_BEFORE_TARGET_M15_PROXY`: `12`
- `STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `166`
- `TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS`: `6`
- `TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY`: `374`

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
