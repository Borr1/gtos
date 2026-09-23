# Historical OHLC GTOS Replay Branch Next-Compute Scoring Packet

Generated UTC: `2026-05-16T09:55:35Z`

Branch next-compute scoring packet only. It converts the full 386-branch outcome synthesis into same-resource proxy score vectors and family score ledgers for source stress, M15 interval, M1 support conflict, positive replay, and entry/adverse redesign. Scores are mechanical triage/proxy metrics, not broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live behavior claims.

## Counts

- `input_full_branch_rows`: `386`
- `input_full_action_rows`: `1930`
- `input_full_next_rows`: `386`
- `input_source_stress_branch_rows`: `138`
- `input_source_stress_support_rows`: `257`
- `input_m15_branch_rows`: `186`
- `input_m15_proxy_rows`: `744`
- `input_m1_branch_rows`: `110`
- `input_m1_proxy_rows`: `660`
- `input_positive_replay_rows`: `243`
- `input_entry_branch_rows`: `386`
- `input_adverse_branch_rows`: `386`
- `branch_score_rows`: `386`
- `action_family_score_rows`: `1930`
- `source_risk_router_rows`: `138`
- `m15_interval_score_rows`: `186`
- `m1_conflict_score_rows`: `110`
- `positive_replay_score_rows`: `243`
- `entry_adverse_score_rows`: `386`
- `bucket_rows`: `85`
- `question_rows`: `5`
- `source_manifest_rows`: `14`

## Score Distributions

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

### score_direction_class
- `CONSERVATIVE_NEGATIVE_PROXY`: `83`
- `CONSERVATIVE_POSITIVE_PROXY`: `243`
- `MIDPOINT_NEGATIVE_INTERVAL_RISK`: `42`
- `MIDPOINT_POSITIVE_INTERVAL_RISK`: `16`
- `NO_SCALAR_BINDING_SCOPE`: `2`

### source_risk_score_class
- `SOURCE_STRESS_FLIP_BUT_CONSERVATIVE_POSITIVE`: `87`
- `SOURCE_STRESS_FLIP_CONSERVATIVE_NEGATIVE`: `31`
- `SOURCE_STRESS_FLIP_CONSERVATIVE_NEGATIVE_OR_STRADDLE`: `20`

### m15_interval_score_class
- `M15_BOUNDS_ROUTER_SCORE`: `37`
- `M15_STOP_FIRST_AVOID_SCORE`: `58`
- `M15_TARGET_FIRST_CHALLENGER_SCORE`: `91`

### m1_conflict_score_class
- `M1_SUPPORT_AND_BRANCH_TARGET_STABLE`: `70`
- `M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT`: `40`

### positive_replay_score_class
- `POSITIVE_REPLAYABLE_CONSERVATIVE_POSITIVE_PROXY`: `156`
- `POSITIVE_STRESS_OR_SOURCE_REPAIR_FIRST`: `87`

### entry_adverse_score_class
- `ENTRY_ADVERSE_NO_REDESIGN_SCORE_SCOPE`: `82`
- `ENTRY_AND_ADVERSE_REDESIGN_BOTH_ACTIVE`: `153`
- `ENTRY_REDESIGN_ACTIVE`: `151`

## Continuation

This packet is the next execution/scoring layer, not completion. It routes every branch to concrete same-resource score vectors that can be consumed by source-stress routers, M15/M1 interval splitters, positive challenger replay scoring, and entry/adverse redesign scoring.
