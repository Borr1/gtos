# Historical OHLC GTOS Replay Branch Score Export Packet

Generated UTC: `2026-05-16T10:06:32Z`

Branch score export packet only. It materializes next-compute proxy scores into branch-local research export queues and implementation-scoring specs. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live effect.

## Counts

- `input_branch_score_rows`: `386`
- `input_action_family_score_rows`: `1930`
- `input_source_risk_router_rows`: `138`
- `input_m15_interval_score_rows`: `186`
- `input_m1_conflict_score_rows`: `110`
- `input_positive_replay_score_rows`: `243`
- `input_entry_adverse_score_rows`: `386`
- `branch_export_rows`: `386`
- `export_action_rows`: `1930`
- `source_router_export_rows`: `138`
- `m15_interval_export_rows`: `186`
- `m1_conflict_export_rows`: `110`
- `positive_replay_export_rows`: `243`
- `entry_adverse_export_rows`: `386`
- `bucket_rows`: `73`
- `question_rows`: `5`
- `source_manifest_rows`: `9`

## Export Distributions

### primary_export_class
- `BINDING_OR_PRESERVE_NO_SCALAR_EXPORT`: `2`
- `ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE`: `5`
- `ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE`: `1`
- `M15_EXPORT_INTERVAL_BOUNDS_ROUTER`: `25`
- `M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN`: `36`
- `M15_EXPORT_TARGET_FIRST_CHALLENGER`: `58`
- `M1_EXPORT_SUPPORT_AND_BRANCH_TARGET_STABLE`: `47`
- `M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT`: `23`
- `POSITIVE_EXPORT_REPLAYABLE_CONSERVATIVE_POSITIVE`: `51`
- `SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE`: `31`
- `SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP`: `87`
- `SOURCE_ROUTER_STRADDLE_BOUNDS_ACQUIRE_OR_COST_SPLIT`: `20`

### source_export_class
- `SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE`: `31`
- `SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP`: `87`
- `SOURCE_ROUTER_STRADDLE_BOUNDS_ACQUIRE_OR_COST_SPLIT`: `20`

### m15_export_class
- `M15_EXPORT_INTERVAL_BOUNDS_ROUTER`: `37`
- `M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN`: `58`
- `M15_EXPORT_TARGET_FIRST_CHALLENGER`: `91`

### m1_export_class
- `M1_EXPORT_SUPPORT_AND_BRANCH_TARGET_STABLE`: `70`
- `M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT`: `40`

### positive_export_class
- `POSITIVE_EXPORT_REPLAYABLE_CONSERVATIVE_POSITIVE`: `156`
- `POSITIVE_EXPORT_SOURCE_REPAIR_OR_STRESS_FIRST`: `87`

### entry_adverse_export_class
- `ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE`: `153`
- `ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE`: `151`
- `ENTRY_ADVERSE_EXPORT_NO_REDESIGN_SCOPE_PRESERVE`: `82`
