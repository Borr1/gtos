# Historical OHLC GTOS Replay M1 Spread Partial/Source-Recheck Repair

Generated UTC: `2026-05-16T04:46:16Z`

This packet repairs the two M1 replay route-split rows from the spread-adjusted fill replay packet using the source-alignment cost-model/signature ledgers plus read-only MT5 M1 bars.

## Counts

- `bucket_rows`: `46`
- `cost_model_repair_rows`: `8`
- `entry_repair_rows`: `2`
- `m1_replay_cost_model_rows_for_repair_entries`: `0`
- `m1_replay_entry_input_rows`: `49`
- `m1_replay_signature_rows_for_repair_entries`: `0`
- `question_rows`: `5`
- `replayed_signature_scope_rows`: `64`
- `signature_scope_rows`: `128`
- `source_alignment_cost_model_input_rows`: `196`
- `source_alignment_entry_input_rows`: `49`
- `source_alignment_signature_input_rows`: `784`
- `source_manifest_rows`: `8`
- `target_stop_contract_input_rows`: `16`

## Entry Repair Status

- `PARTIAL_REPAIR_REPLAY_TOUCHED_COST_MODELS_KEEP_UNTOUCHED_NOFILL`: `1`
- `SOURCE_RECHECK_REPAIR_M1_CONFIRMS_ALL_NONZERO_THRESHOLDS_ZERO_UNTOUCHED`: `1`

## Cost-Model Repair Status

- `PARTIAL_THRESHOLD_TOUCHED_COST_MODEL_REPLAYABLE`: `1`
- `PARTIAL_THRESHOLD_UNTOUCHED_COST_MODEL_REMAINS_NOFILL`: `2`
- `SOURCE_RECHECK_M1_CONFIRMS_THRESHOLD_TOUCH_REPLAYABLE`: `3`
- `ZERO_COST_CONTROL_UNTOUCHED_REMAINS_NOFILL`: `2`

## Immediate Work

- Feed repaired partial/static and source-recheck/M1-confirmed branches into cost/fill/path family synthesis.
- Preserve untouched partial median/max/zero scopes as no-fill controls.
- Route fill-bar ambiguous repaired scopes into interval-bound or tick-order stress before descriptor claims.
- Compare repaired branches against near-miss market-entry and far-miss redesign packets on the shared family denominator.

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
