# vNext Moonshot Stage04 Full Policy Dynamic Replay

Generated: `2026-05-26T03:45:53Z`

## Scope

- Replay scope: `universal_bar_close_m15_first_pass_every_replayable_candidate`
- Replay mode: `bar_close_m15`
- Same-bar policy: `conservative`
- Replayable candidates: `214536`
- Input rows scanned: `1978947`
- First incomplete invariant: `STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER`

## Policy Expectancy

- `ai_target`: expectancy `0.3765151394122706`, total R `80776.05194895089`
- `be_after_trigger`: expectancy `0.3894716001928695`, total R `83555.67921897746`
- `early_cut_if_no_progress`: expectancy `0.37649490175465583`, total R `80771.71024283684`
- `legacy_fixed_1.5r`: expectancy `0.3765151394122706`, total R `80776.05194895089`
- `live_current_j46_j49`: expectancy `0.18021810925213155`, total R `38663.2722865153`
- `partial_be_runner`: expectancy `0.3145438404890228`, total R `67480.977363153`
- `path_aware_runner`: expectancy `0.18021810925213155`, total R `38663.2722865153`
- `time_stop_only`: expectancy `0.16728967698969646`, total R `35889.65814266152`
- `trailing_runner`: expectancy `0.2792544735975976`, total R `59910.137747734196`

## Source Note

M1/M5/tick/Sierra path-aware rows inventoried in Stage02 and preserved; Stage04 first pass uses complete M15 OHLC source to avoid sparse-source selection bias.

This is no longer a fixed target/stop label replay: each row contains all Stage03 policy outcomes from ordered source OHLC observations.
