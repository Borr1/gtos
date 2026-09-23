# Historical OHLC GTOS Replay Cost/Fill/Path Family Synthesis

Generated UTC: `2026-05-16T04:48:43Z`

This packet joins all currently available family-level replay evidence into one branch queue.

## Counts

- `cost_family_input_rows`: `384`
- `recovered_family_input_rows`: `266`
- `confirmed_nofill_family_input_rows`: `192`
- `source_alignment_family_input_rows`: `160`
- `m1_spread_family_input_rows`: `480`
- `m1_spread_signature_input_rows`: `2256`
- `m1_fill_bar_family_input_rows`: `480`
- `m1_fill_bar_signature_input_rows`: `2256`
- `partial_repair_entry_input_rows`: `2`
- `partial_repair_signature_input_rows`: `128`
- `target_stop_contract_input_rows`: `16`
- `family_synthesis_rows`: `386`
- `branch_queue_rows`: `386`
- `bucket_rows`: `30`
- `question_rows`: `6`
- `source_manifest_rows`: `11`

## Branch Queue Status

- `ACTIVE_EXACT_SPREAD_STRESS_REQUIRED`: `115`
- `ACTIVE_FAR_MISS_AVOID_REDESIGN_REQUIRED`: `92`
- `ACTIVE_M1_FILL_BAR_SOURCE_REPAIR_REQUIRED`: `4`
- `ACTIVE_M1_SPREAD_REPLAY_SYNTHESIS_REQUIRED`: `32`
- `ACTIVE_NEAR_MISS_ENTRY_CONTROL_REQUIRED`: `16`
- `ACTIVE_PARTIAL_SOURCE_RECHECK_REPAIR_SYNTHESIS_REQUIRED`: `32`
- `ACTIVE_RECOVERED_FILL_SPLIT_REQUIRED`: `16`
- `PRESERVE_BASELINE_FAMILY_DESCRIPTOR`: `79`

## Immediate Work

- run M1 fill-bar ordering stress for unresolved fill-bar target/stop rows
- run partial/source-recheck repair for source-alignment leftovers
- run near-miss entry-offset and market-entry controls
- run far-miss avoid/retest-redesign controls
- materialize src/execution/orchestrator proposal patches from fillability evidence

No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.
