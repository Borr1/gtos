# Historical OHLC GTOS Replay Branch Parameter Execution Scoring Packet

Generated UTC: `2026-05-16T11:50:38Z`

Branch parameter execution/scoring packet only. It consumes replay-builder parameter rows, instantiates deterministic same-resource research builders for source, M15, M1, positive, and entry/adverse families, and emits accepted/rejected branch-builder results plus proxy score deltas. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, live-readiness, promotion, or live effect.

## Decisive System Recommendation

EXECUTE_ACCEPTED_BUILDER_BRANCHES_NOW_AND_REJECT_OR_REPAIR_THE_REST: run accepted source cost-cap/source-repair, M15 bounds, M1 support, positive replay, and entry/adverse redesign builders as branch-local research; do not carry rejected branches forward except through their explicit repair/avoid recommendations.

## Counts

- `input_parameter_branch_rows`: `386`
- `input_parameter_family_rows`: `1930`
- `input_parameter_source_rows`: `138`
- `input_parameter_m15_rows`: `186`
- `input_parameter_m1_rows`: `110`
- `input_parameter_positive_rows`: `243`
- `input_parameter_entry_adverse_rows`: `386`
- `input_parameter_binding_rows`: `2`
- `branch_selector_rows`: `386`
- `family_selector_rows`: `1930`
- `source_selector_rows`: `138`
- `m15_selector_rows`: `186`
- `m1_selector_rows`: `110`
- `positive_selector_rows`: `243`
- `entry_adverse_selector_rows`: `386`
- `binding_selector_rows`: `2`
- `bucket_rows`: `128`
- `question_rows`: `4`
- `source_manifest_rows`: `9`

## Selector Distributions

### primary_selector_execution_status
- `BINDING_PROVENANCE_ONLY_NO_SELECTOR_EXECUTION`: `2`
- `ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED`: `5`
- `ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED`: `1`
- `M15_STOP_FIRST_AVOID_REDESIGN_BOUND_EXECUTED`: `36`
- `M15_TARGET_FIRST_CONSERVATIVE_LOWER_BOUND_EXECUTED`: `58`
- `M15_TARGET_STOP_BOUNDS_SPLIT_EXECUTED`: `25`
- `M1_SUPPORT_BRANCH_CONFLICT_SPLIT_EXECUTED`: `23`
- `M1_SUPPORT_STABLE_CHALLENGER_EXECUTED`: `47`
- `POSITIVE_REPLAY_NOW_SELECTOR_EXECUTED`: `51`
- `SOURCE_AVOID_EXECUTED_EXACT_SOURCE_REPAIR_QUEUED`: `31`
- `SOURCE_COST_CAP_LOWER_BOUND_EXECUTED_EXACT_SOURCE_QUEUED`: `87`
- `SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED`: `20`

### source_selector_execution_status
- `NO_SOURCE_SELECTOR_EXECUTION`: `248`
- `SOURCE_AVOID_EXECUTED_EXACT_SOURCE_REPAIR_QUEUED`: `31`
- `SOURCE_COST_CAP_LOWER_BOUND_EXECUTED_EXACT_SOURCE_QUEUED`: `87`
- `SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED`: `20`

### m15_selector_execution_status
- `M15_SIDE_CAR_CONTEXT_EXECUTED`: `55`
- `M15_STOP_FIRST_AVOID_REDESIGN_BOUND_EXECUTED`: `36`
- `M15_TARGET_FIRST_CONSERVATIVE_LOWER_BOUND_EXECUTED`: `58`
- `M15_TARGET_STOP_BOUNDS_SPLIT_EXECUTED`: `37`
- `NO_M15_SELECTOR_EXECUTION`: `200`

### m1_selector_execution_status
- `M1_SIDE_CAR_CONTEXT_EXECUTED`: `40`
- `M1_SUPPORT_BRANCH_CONFLICT_SPLIT_EXECUTED`: `23`
- `M1_SUPPORT_STABLE_CHALLENGER_EXECUTED`: `47`
- `NO_M1_SELECTOR_EXECUTION`: `276`

### positive_selector_execution_status
- `NO_POSITIVE_SELECTOR_EXECUTION`: `143`
- `POSITIVE_REPAIR_STRESS_FIRST_SELECTOR_EXECUTED`: `87`
- `POSITIVE_REPLAY_NOW_SELECTOR_EXECUTED`: `51`
- `POSITIVE_SIDE_CAR_REPLAY_CONTEXT_EXECUTED`: `105`

### entry_adverse_selector_execution_status
- `ENTRY_ADVERSE_PRESERVE_CONTEXT_EXECUTED`: `82`
- `ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED`: `153`
- `ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED`: `151`
