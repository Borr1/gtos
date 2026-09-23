# Historical OHLC GTOS Replay Branch Full Outcome Implementation Synthesis

Generated UTC: `2026-05-16T09:44:53Z`

Full-denominator branch outcome and implementation synthesis only. The packet preserves all 386 historical OHLC/MT5/Sierra proxy branches and joins sealed/proxy R-style outcome, expectancy-style proxy, target/stop, pass-control, cost, duplicate/effective-N, concentration, source confidence, ambiguity, source-stress, M15/M1 interval, code/replay, implementation, and failure/success-cause fields. It does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live behavior change.

## Counts

- `input_rstyle_branch_rows`: `386`
- `input_control_delta_rows`: `386`
- `input_cause_rows`: `386`
- `input_duplicate_effective_n_rows`: `386`
- `input_implementation_branch_rows`: `386`
- `input_local_branch_rows`: `386`
- `input_code_branch_rows`: `386`
- `input_replay_branch_rows`: `386`
- `input_source_ordering_rows`: `386`
- `input_source_stress_branch_rows`: `138`
- `input_m15_interval_branch_rows`: `186`
- `input_m1_fill_interval_branch_rows`: `110`
- `branch_synthesis_rows`: `386`
- `layer_join_rows`: `6562`
- `action_matrix_rows`: `1930`
- `conflict_rows`: `386`
- `next_compute_rows`: `386`
- `concentration_rows`: `90`
- `bucket_rows`: `102`
- `question_rows`: `6`
- `source_manifest_rows`: `18`

## Key Distributions

### next_computation_class
- `ENTRY_GEOMETRY_REDESIGN_SCORE_NEXT`: `6`
- `M15_INTERVAL_BOUNDS_ROUTER_NEXT`: `25`
- `M15_INTERVAL_STOP_FIRST_AVOID_REDESIGN_NEXT`: `36`
- `M15_INTERVAL_TARGET_FIRST_CHALLENGER_SCORE_NEXT`: `58`
- `M1_FILL_BAR_SUPPORT_BRANCH_CONFLICT_SPLIT_NEXT`: `23`
- `M1_FILL_BAR_TARGET_STABLE_CHALLENGER_SCORE_NEXT`: `47`
- `POSITIVE_CHALLENGER_REPLAY_SCORE_NEXT`: `51`
- `PRESERVE_CURRENT_PROXY_AND_ROUTE_BY_BUCKET`: `2`
- `SOURCE_STRESS_RISK_ROUTER_OR_ACQUISITION_NEXT`: `138`

### branch_result_class
- `AMBIGUOUS_INTERVAL_STRADDLES_ZERO`: `58`
- `NEGATIVE_RSTYLE_PROXY_MIDPOINT`: `83`
- `NO_RSTYLE_PROXY_INTERVAL_AVAILABLE`: `2`
- `POSITIVE_RSTYLE_PROXY_MIDPOINT`: `243`

### target_stop_result
- `NO_FILL_OR_UNFILLED_DOMINANT`: `46`
- `NO_TARGET_STOP_RESULT_ENTRY_PROVENANCE_ONLY`: `2`
- `NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT`: `5`
- `ORDERING_AMBIGUITY_DOMINANT`: `1`
- `STOP_FIRST_PROXY_DOMINANT`: `153`
- `TARGET_FIRST_PROXY_DOMINANT`: `179`

### source_execution_class
- `SOURCE_BINDING_ONLY_NO_SCALAR`: `2`
- `SOURCE_EXACT_CLEAN_COMPUTABLE_NOW`: `16`
- `SOURCE_EXACT_REPAIR_COMPUTABLE_NOW`: `59`
- `SOURCE_EXACT_UNAVAILABLE_STRESS_OR_ACQUIRE`: `138`
- `SOURCE_M1_SPREAD_PROXY_COMPUTABLE_NOW`: `171`

### ordering_execution_class
- `ORDERING_ALREADY_COLLAPSED_OR_NOT_REQUIRED`: `44`
- `ORDERING_BINDING_ONLY_NO_SCALAR`: `2`
- `ORDERING_M15_INTERVAL_BOUND`: `186`
- `ORDERING_M1_CHRONOLOGY_COMPUTABLE_NOW`: `43`
- `ORDERING_M1_FILL_BAR_INTERVAL_BOUND`: `110`
- `ORDERING_RECOVERED_PROXY_REQUIRES_KEY_REPAIR`: `1`

### source_stress_status
- `NO_SOURCE_STRESS_LAYER_SCOPE`: `248`
- `SOURCE_STRESS_DESCRIPTOR_FLIPS_TARGET_STOP`: `138`

### m15_interval_status
- `INTERVAL_ALL_NEGATIVE`: `58`
- `INTERVAL_ALL_POSITIVE`: `91`
- `INTERVAL_STRADDLES_ZERO`: `37`
- `NO_M15_INTERVAL_LAYER_SCOPE`: `200`

### m1_support_vs_branch_status
- `M1_SUPPORT_ALL_POSITIVE_BUT_BRANCH_AMBIGUOUS_INTERVAL_STRADDLES_ZERO`: `21`
- `M1_SUPPORT_ALL_POSITIVE_BUT_BRANCH_NEGATIVE_RSTYLE_PROXY_MIDPOINT`: `19`
- `M1_SUPPORT_AND_BRANCH_AGGREGATE_ALL_POSITIVE`: `70`
- `NO_M1_FILL_BAR_LAYER_SCOPE`: `276`

### metric_coverage_status
- `ALL_REQUIRED_BRANCH_METRICS_PRESENT`: `386`

## Continuation

This packet is not completion. It is the all-branch routing layer for the next same-resource computations: source-stress risk routing/acquisition, M15 interval avoid/challenger scoring, M1 fill-bar support-vs-branch conflict splitting, positive challenger replay scoring, and entry/adverse redesign scoring.
