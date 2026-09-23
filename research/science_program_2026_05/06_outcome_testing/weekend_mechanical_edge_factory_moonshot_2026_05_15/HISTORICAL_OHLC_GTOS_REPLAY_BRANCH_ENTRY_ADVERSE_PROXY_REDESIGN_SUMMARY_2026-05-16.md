# Historical OHLC GTOS Replay Branch Entry/Adverse Proxy Redesign

Generated UTC: `2026-05-16T08:02:54Z`

## Boundary

Entry/adverse branch-local proxy redesign packet only. It preserves all 386 branch_queue_id rows and converts entry-geometry plus stop-first adverse path classes into same-resource replay/proxy/source/ordering actions. It does not claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live behavior change.

## Counts

- input_branch_synthesis_rows: 386
- input_entry_synthesis_rows: 386
- input_adverse_synthesis_rows: 386
- entry_geometry_branch_redesign_rows: 386
- entry_geometry_variant_exploded_rows: 786
- adverse_stop_first_branch_redesign_rows: 386
- adverse_stop_first_action_exploded_rows: 539
- entry_adverse_unified_branch_rows: 386
- crosstab_bucket_rows: 62
- source_manifest_rows: 18
- question_rows: 4

## entry_geometry_retest_class

- FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN: 96
- MIXED_FILLABILITY_SOURCE_SPLIT: 128
- NEAR_MISS_ENTRY_CHALLENGER: 48
- NOT_ENTRY_GEOMETRY_RETEST_SCOPE: 82
- WITHIN_RANGE_RETEST_REDESIGN: 32

## entry_redesign_action_class

- ENTRY_FAR_MISS_AVOID_AND_MARKET_PROXY_REDESIGN: 96
- ENTRY_MIXED_FILLABILITY_SOURCE_SPLIT_FIRST: 128
- ENTRY_NEAR_MISS_OFFSET_AND_MARKET_ENTRY_CHALLENGER: 48
- ENTRY_PRESERVE_NO_REDESIGN_SCOPE: 82
- ENTRY_WITHIN_RANGE_RETEST_ZONE_AND_OFFSET_REDESIGN: 32

## adverse_stop_first_class

- NOT_ADVERSE_STOP_FIRST_SCOPE: 233
- STOP_FIRST_AVOID_OR_REDESIGN_READY: 5
- STOP_FIRST_MIXED_POSITIVE_PROXY_REVIEW: 66
- STOP_FIRST_ORDERING_COLLAPSE_FIRST: 48
- STOP_FIRST_SOURCE_REPAIR_FIRST: 34

## adverse_redesign_action_class

- ADVERSE_PRESERVE_NO_STOP_FIRST_SCOPE: 233
- ADVERSE_STOP_FIRST_IMMEDIATE_AVOID_OR_REDESIGN: 5
- ADVERSE_STOP_FIRST_MIXED_POSITIVE_CONFLICT_REVIEW: 66
- ADVERSE_STOP_FIRST_ORDERING_COLLAPSE_FIRST: 48
- ADVERSE_STOP_FIRST_SOURCE_STRESS_FIRST: 34
