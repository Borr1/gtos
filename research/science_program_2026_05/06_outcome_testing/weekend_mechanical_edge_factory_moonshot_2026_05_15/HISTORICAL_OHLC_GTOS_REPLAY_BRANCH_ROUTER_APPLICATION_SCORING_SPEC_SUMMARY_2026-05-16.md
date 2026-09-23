# Historical OHLC GTOS Replay Branch Router-Application Scoring Spec

Generated UTC: `2026-05-16T10:53:26Z`

Branch router-application scoring spec only. It applies branch-local research router modules to all follow-up rows and computes same-resource proxy/spec metrics for source stress, M15 intervals, M1 support conflict, positive replay, and entry/adverse redesign. It does not change live behavior and does not claim broker R/PnL, realized expectancy, win-rate, live-readiness, promotion, or live effect.

## Counts

- `input_branch_followup_rows`: `386`
- `input_family_action_followup_rows`: `1930`
- `input_source_router_followup_rows`: `138`
- `input_m15_followup_rows`: `186`
- `input_m1_followup_rows`: `110`
- `input_positive_followup_rows`: `243`
- `input_entry_adverse_followup_rows`: `386`
- `input_binding_preserve_rows`: `2`
- `input_full_outcome_branch_rows`: `386`
- `branch_router_application_rows`: `386`
- `family_spec_rows`: `1930`
- `source_spec_rows`: `138`
- `m15_spec_rows`: `186`
- `m1_spec_rows`: `110`
- `positive_spec_rows`: `243`
- `entry_adverse_spec_rows`: `386`
- `binding_preserve_spec_rows`: `2`
- `bucket_rows`: `165`
- `question_rows`: `6`
- `source_manifest_rows`: `15`

## Key Distributions

### primary_export_family
- `BINDING`: `2`
- `ENTRY_ADVERSE`: `6`
- `M1`: `70`
- `M15`: `119`
- `POSITIVE`: `51`
- `SOURCE`: `138`

### branch_router_application_class
- `BINDING_PRESERVE_NO_SCALAR_APPLICATION`: `2`
- `ENTRY_ADVERSE_APPLICATION_NEGATIVE_SCORE_AVOID_OR_REDESIGN`: `1`
- `ENTRY_ADVERSE_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS`: `5`
- `M15_APPLICATION_NEGATIVE_SCORE_AVOID_OR_REDESIGN`: `53`
- `M15_APPLICATION_POSITIVE_SCORE_AND_SEALED_POSITIVE`: `58`
- `M15_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS`: `8`
- `M1_APPLICATION_POSITIVE_SCORE_AND_SEALED_POSITIVE`: `47`
- `M1_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS`: `23`
- `POSITIVE_APPLICATION_NEGATIVE_SCORE_AVOID_OR_REDESIGN`: `8`
- `POSITIVE_APPLICATION_POSITIVE_SCORE_AND_SEALED_POSITIVE`: `21`
- `POSITIVE_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS`: `22`
- `SOURCE_APPLICATION_NEGATIVE_SCORE_AVOID_OR_REDESIGN`: `45`
- `SOURCE_APPLICATION_POSITIVE_SCORE_AND_SEALED_POSITIVE`: `75`
- `SOURCE_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS`: `18`

### router_application_score_class
- `BINDING_NO_SCALAR_SCORE`: `2`
- `ENTRY_ADVERSE_REDESIGN_PRESSURE_SCORE`: `5`
- `ENTRY_REDESIGN_FILLABILITY_SCORE`: `1`
- `M15_STOP_FIRST_AVOID_BOUND_SCORE`: `36`
- `M15_STRADDLE_BOUNDS_ROUTER_SCORE`: `25`
- `M15_TARGET_FIRST_CONSERVATIVE_BOUND_SCORE`: `58`
- `M1_SUPPORT_BRANCH_HALFSTEP_CONFLICT_SCORE`: `23`
- `M1_SUPPORT_TARGET_STABLE_SCORE`: `47`
- `POSITIVE_REPLAY_CONSERVATIVE_ADJUSTED_SCORE`: `51`
- `SOURCE_COST_CAPPED_LOWER_BOUND_SCORE`: `87`
- `SOURCE_NEGATIVE_AVOID_SCORE`: `31`
- `SOURCE_STRADDLE_MIDPOINT_WITH_BOUNDS_SCORE`: `20`

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
