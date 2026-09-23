# Historical OHLC GTOS Replay Branch Local Implementation Candidate Packet

Generated UTC: `2026-05-16T07:57:59Z`

## Boundary

Branch-local implementation candidate specification only. The packet preserves all 386 historical OHLC/MT5/Sierra proxy branches and maps them to replay/spec/code-surface actions for source repair, ordering collapse, entry redesign, adverse avoid/redesign, and positive challenger comparison. It does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live behavior change.

## Counts

- input_branch_synthesis_rows: 386
- input_entry_synthesis_rows: 386
- input_adverse_synthesis_rows: 386
- input_positive_synthesis_rows: 386
- input_source_synthesis_rows: 386
- input_ordering_synthesis_rows: 386
- branch_candidate_rows: 386
- entry_redesign_spec_rows: 386
- adverse_avoid_redesign_spec_rows: 386
- positive_challenger_spec_rows: 386
- source_repair_spec_rows: 386
- ordering_collapse_spec_rows: 386
- code_surface_exploded_rows: 1428
- rule_card_rows: 25
- bucket_rows: 40
- question_rows: 5
- source_manifest_rows: 7

## branch_local_candidate_stage

- BINDING_SCOPE_ONLY: 2
- ENTRY_REDESIGN_REPLAY_SPEC_READY: 52
- ORDERING_COLLAPSE_OR_INTERVAL_FIRST: 190
- POSITIVE_CHALLENGER_SPEC_READY: 4
- SOURCE_ACQUISITION_OR_STRESS_FIRST: 138

## entry_local_impl_class

- ENTRY_FAR_MISS_AVOID_OR_MARKET_PROXY_SPEC_READY: 96
- ENTRY_FILLABILITY_SOURCE_SPLIT_ROUTER_REQUIRED: 128
- ENTRY_MARKET_AND_OFFSET_CHALLENGER_REPLAY_READY: 48
- ENTRY_NO_BRANCH_LOCAL_REDESIGN_SCOPE: 82
- ENTRY_WITHIN_RANGE_RETEST_ZONE_REDESIGN_SPEC_READY: 32

## adverse_local_impl_class

- ADVERSE_NO_STOP_FIRST_SCOPE: 233
- ADVERSE_STOP_FIRST_AVOID_OR_REDESIGN_REPLAY_READY: 5
- ADVERSE_STOP_FIRST_MIXED_POSITIVE_SPLIT_REQUIRED: 66
- ADVERSE_STOP_FIRST_ORDERING_COLLAPSE_PRECONDITION: 48
- ADVERSE_STOP_FIRST_SOURCE_REPAIR_PRECONDITION: 34

## positive_local_impl_class

- POSITIVE_EXACT_REPAIRED_CHALLENGER_COMPARISON_READY: 25
- POSITIVE_NO_CHALLENGER_SCOPE: 143
- POSITIVE_STRESS_ONLY_CHALLENGER_NOT_SCALAR_COLLAPSED: 87
- POSITIVE_ZERO_TO_SPREAD_M1_REPLAY_CHALLENGER_READY: 131

## source_local_impl_class

- SOURCE_CURRENT_EXACT_CLEAN_PRESERVE: 16
- SOURCE_EXACT_SPREAD_RECOMPUTED_DESCRIPTOR_READY: 59
- SOURCE_EXACT_SPREAD_UNAVAILABLE_ACQUIRE_OR_STRESS: 138
- SOURCE_TARGETSTOP_NA_BINDING_ONLY: 2
- SOURCE_ZERO_TO_SPREAD_SHIFT_USE_M1_REPLAY: 171

## ordering_local_impl_class

- ORDERING_M15_INTERVAL_ONLY_SOURCE_ROUTE_REQUIRED: 186
- ORDERING_M1_CHRONOLOGICAL_COLLAPSE_READY: 43
- ORDERING_M1_FILL_BAR_STRESS_INTERVAL_REQUIRED: 110
- ORDERING_NO_COLLAPSE_REQUIRED: 44
- ORDERING_RECOVERED_PROXY_NO_M1_KEY_REQUIREMENT: 1
- ORDERING_TARGETSTOP_NA_BINDING_ONLY: 2
