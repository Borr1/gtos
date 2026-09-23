# Historical OHLC GTOS Replay Branch Follow-Up Computation Packet

Generated UTC: `2026-05-16T10:25:56Z`

Branch follow-up computation packet only. It consumes score-export queues into source-router/acquisition, M15 interval action, M1 support-conflict, positive replay, and entry/adverse redesign computation ledgers. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live effect.

## Counts

- `input_branch_export_rows`: `386`
- `input_export_action_rows`: `1930`
- `input_source_router_export_rows`: `138`
- `input_m15_interval_export_rows`: `186`
- `input_m1_conflict_export_rows`: `110`
- `input_positive_replay_export_rows`: `243`
- `input_entry_adverse_export_rows`: `386`
- `input_full_outcome_branch_rows`: `386`
- `branch_followup_rows`: `386`
- `family_action_followup_rows`: `1930`
- `source_router_followup_rows`: `138`
- `m15_followup_rows`: `186`
- `m1_followup_rows`: `110`
- `positive_followup_rows`: `243`
- `entry_adverse_followup_rows`: `386`
- `binding_preserve_rows`: `2`
- `bucket_rows`: `157`
- `question_rows`: `6`
- `source_manifest_rows`: `9`

## Key Distributions

### branch_primary_followup_class
- `BINDING_OR_PRESERVE_NO_SCALAR_COMPUTATION`: `2`
- `ENTRY_AND_ADVERSE_REDESIGN_COMPUTED`: `5`
- `ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED`: `1`
- `M15_INTERVAL_BOUNDS_ROUTER_COMPUTED`: `25`
- `M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED`: `36`
- `M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED`: `58`
- `M1_SUPPORT_AND_BRANCH_TARGET_STABLE_CHALLENGER_COMPUTED`: `47`
- `M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED`: `23`
- `POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED`: `51`
- `SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE`: `31`
- `SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL`: `87`
- `SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL`: `20`

### source_router_followup_class
- `SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE`: `31`
- `SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL`: `87`
- `SOURCE_NOT_EXPORTED_PRESERVE_UPSTREAM_PROXY_OR_CLEAN_SOURCE`: `248`
- `SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL`: `20`

### m15_followup_class
- `M15_INTERVAL_BOUNDS_ROUTER_COMPUTED`: `37`
- `M15_NOT_EXPORTED_PRESERVE_NON_M15_ORDERING_ROUTE`: `200`
- `M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED`: `58`
- `M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED`: `91`

### m1_followup_class
- `M1_NOT_EXPORTED_PRESERVE_NON_M1_ORDERING_ROUTE`: `276`
- `M1_SUPPORT_AND_BRANCH_TARGET_STABLE_CHALLENGER_COMPUTED`: `70`
- `M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED`: `40`

### positive_followup_class
- `POSITIVE_NOT_EXPORTED_NO_CHALLENGER_SCOPE`: `143`
- `POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED`: `156`
- `POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY`: `87`

### entry_adverse_followup_class
- `ENTRY_ADVERSE_PRESERVE_NO_REDESIGN_SCOPE`: `82`
- `ENTRY_AND_ADVERSE_REDESIGN_COMPUTED`: `153`
- `ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED`: `151`
