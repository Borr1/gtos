# Branch M1 Fill-Bar Interval Collapse Packet

Generated UTC: `2026-05-16T09:17:54Z`

## Boundary

Branch M1 fill-bar interval collapse packet only. It preserves all M1 fill-bar ordering-stress support rows, scores the 110 active branch rows with branch aggregate and M1 support-component proxy bounds, and records remaining source/tick-ordering ambiguity without broker R/PnL, realized expectancy, win-rate, validation, live-readiness, promotion, or live behavior change claims.

## Counts

- input_replay_execution_branch_rows: 386
- input_m1_fill_bar_interval_branch_rows: 110
- input_m1_fill_bar_stress_signature_rows: 2256
- input_m1_fill_bar_stress_family_rows: 480
- m1_fill_bar_interval_branch_rows: 110
- m1_fill_bar_signature_support_rows: 2256
- m1_fill_bar_matched_signature_support_rows: 1308
- m1_fill_bar_unmatched_signature_support_rows: 948
- m1_fill_bar_family_support_rows: 480
- m1_fill_bar_matched_family_support_rows: 330
- m1_fill_bar_unmatched_family_support_rows: 150
- m1_fill_bar_matched_fill_bar_order_unresolved_rows: 176
- m1_fill_bar_matched_source_fail_closed_rows: 12
- m1_fill_bar_proxy_variant_rows: 660
- m1_fill_bar_requirement_rows: 110
- bucket_rows: 40
- question_rows: 4
- source_manifest_rows: 7

## branch_aggregate_interval_sign_class

- INTERVAL_ALL_NEGATIVE: 19
- INTERVAL_ALL_POSITIVE: 70
- INTERVAL_STRADDLES_ZERO: 21

## m1_support_resolution_class

- M1_FILL_BAR_STRESS_TARGET_STABLE_AFTER_NEXT_BAR: 28
- M1_SUPPORT_TARGET_STABLE_NO_FILL_BAR_RESIDUAL: 78
- M1_SUPPORT_TARGET_WITH_SOURCE_FAIL_CLOSED_RESIDUAL: 4

## signature_support_match_status

- MATCHED_ACTIVE_M1_FILL_BAR_INTERVAL_BRANCH: 1308
- UNMATCHED_TO_ACTIVE_110_M1_FILL_BAR_INTERVAL_QUEUE: 948

## support_row_match_status

- SUPPORT_ROWS_MATCH_UPSTREAM_COUNT: 110

## proxy_variant

- BRANCH_AGGREGATE_CONSERVATIVE_BOUND: 110
- BRANCH_AGGREGATE_MIDPOINT: 110
- BRANCH_AGGREGATE_OPTIMISTIC_BOUND: 110
- M1_SUPPORT_CONSERVATIVE_SCALAR_MEAN: 110
- M1_SUPPORT_MIDPOINT_SCALAR_MEAN: 110
- M1_SUPPORT_OPTIMISTIC_SCALAR_MEAN: 110

## target_stop_result

- NO_FILL_OR_UNFILLED_DOMINANT: 12
- NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT: 4
- ORDERING_AMBIGUITY_DOMINANT: 1
- STOP_FIRST_PROXY_DOMINANT: 38
- TARGET_FIRST_PROXY_DOMINANT: 55
