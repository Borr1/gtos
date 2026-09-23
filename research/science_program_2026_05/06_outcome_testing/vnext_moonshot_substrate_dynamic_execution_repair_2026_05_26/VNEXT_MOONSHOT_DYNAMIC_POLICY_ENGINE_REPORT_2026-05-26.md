# vNext Moonshot Stage03 Dynamic Policy Engine Contract

Generated: `2026-05-26T03:33:46Z`

## Engine

- Module: `src/research/dynamic_execution_policy.py`
- Policy count: `9`
- Banned imports: `[]`
- Execution effect: `research_replay_only_default_off_no_runtime_flag_flip`
- First incomplete invariant: `STAGE_04_FULL_POLICY_DYNAMIC_REPLAY`

## Policies

- `ai_target`
- `be_after_trigger`
- `early_cut_if_no_progress`
- `legacy_fixed_1.5r`
- `live_current_j46_j49`
- `partial_be_runner`
- `path_aware_runner`
- `time_stop_only`
- `trailing_runner`

## Source Contract

- Stage03 consumes Stage02 source priority ordering, but does not claim broker lifecycle truth unless exact fields exist.
- Empty ordered paths return `not_replayable` rather than inferred R.
- Same-bar target/stop collisions can be conservative, optimistic, or explicitly ambiguous.
- Live-current J46/J49 is modeled as 3R TP1, move SL to BE, no partial, 6R target, and 12 M15-bar time stop.
