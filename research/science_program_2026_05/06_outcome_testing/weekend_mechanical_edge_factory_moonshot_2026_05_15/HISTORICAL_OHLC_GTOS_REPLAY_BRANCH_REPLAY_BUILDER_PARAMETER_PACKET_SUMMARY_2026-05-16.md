# Historical OHLC GTOS Replay Branch Replay-Builder Parameter Packet

Generated UTC: `2026-05-16T11:30:04Z`

Branch replay-builder parameter packet only. It converts decision-matrix work units into executable research-builder parameter rows for source, M15, M1, positive, and entry/adverse families. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, live-readiness, promotion, or live effect.

## Counts

- `input_matrix_branch_rows`: `386`
- `input_matrix_family_rows`: `1930`
- `input_matrix_source_rows`: `138`
- `input_matrix_m15_rows`: `186`
- `input_matrix_m1_rows`: `110`
- `input_matrix_positive_rows`: `243`
- `input_matrix_entry_adverse_rows`: `386`
- `input_matrix_binding_rows`: `2`
- `input_matrix_work_unit_rows`: `386`
- `branch_parameter_rows`: `386`
- `family_parameter_rows`: `1930`
- `source_parameter_rows`: `138`
- `m15_parameter_rows`: `186`
- `m1_parameter_rows`: `110`
- `positive_parameter_rows`: `243`
- `entry_adverse_parameter_rows`: `386`
- `binding_parameter_rows`: `2`
- `bucket_rows`: `110`
- `question_rows`: `4`
- `source_manifest_rows`: `10`

## Key Distributions

### primary_export_family
- `BINDING`: `2`
- `ENTRY_ADVERSE`: `6`
- `M1`: `70`
- `M15`: `119`
- `POSITIVE`: `51`
- `SOURCE`: `138`

### primary_builder_policy
- `AVOID_UNTIL_EXACT_SOURCE_REPAIR`: `31`
- `BINDING_PROVENANCE_PRESERVE_NO_PARAMETERS`: `2`
- `ENTRY_AND_ADVERSE_REDESIGN_PRESSURE_SELECTOR`: `5`
- `ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR`: `1`
- `REPLAY_NOW_WITH_MODIFIER_PENALTIES`: `51`
- `SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_SOURCE`: `20`
- `STOP_FIRST_AVOID_OR_REDESIGN_SELECTOR`: `36`
- `SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT`: `23`
- `SUPPORT_STABLE_CHALLENGER_SELECTOR`: `47`
- `TARGET_FIRST_CONSERVATIVE_BOUND_SELECTOR`: `58`
- `TARGET_STOP_BOUNDS_SPLIT_SELECTOR`: `25`
- `USE_COST_CAP_LOWER_BOUND_AND_ACQUIRE_EXACT_SOURCE`: `87`

### source_builder_policy
- `AVOID_UNTIL_EXACT_SOURCE_REPAIR`: `31`
- `SOURCE_NOT_IN_SCOPE`: `248`
- `SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_SOURCE`: `20`
- `USE_COST_CAP_LOWER_BOUND_AND_ACQUIRE_EXACT_SOURCE`: `87`

### m15_builder_policy
- `M15_NOT_IN_SCOPE`: `200`
- `M15_SIDE_CAR_CONTEXT_SELECTOR`: `55`
- `STOP_FIRST_AVOID_OR_REDESIGN_SELECTOR`: `36`
- `TARGET_FIRST_CONSERVATIVE_BOUND_SELECTOR`: `58`
- `TARGET_STOP_BOUNDS_SPLIT_SELECTOR`: `37`

### m1_builder_policy
- `M1_NOT_IN_SCOPE`: `276`
- `M1_SIDE_CAR_CONTEXT_SELECTOR`: `40`
- `SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT`: `23`
- `SUPPORT_STABLE_CHALLENGER_SELECTOR`: `47`

### positive_builder_policy
- `POSITIVE_NOT_IN_SCOPE`: `143`
- `POSITIVE_SIDE_CAR_REPLAY_CONTEXT`: `105`
- `REPAIR_SOURCE_OR_STRESS_BEFORE_REPLAY`: `87`
- `REPLAY_NOW_WITH_MODIFIER_PENALTIES`: `51`

### entry_adverse_builder_policy
- `ENTRY_ADVERSE_PRESERVE_CONTEXT`: `82`
- `ENTRY_AND_ADVERSE_REDESIGN_PRESSURE_SELECTOR`: `153`
- `ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR`: `151`
