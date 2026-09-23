# Branch M15 Interval Collapse Packet

Generated UTC: `2026-05-16T09:02:45Z`

## Boundary

Branch M15 interval collapse packet only. It preserves M15 same-bar ambiguity rows and emits bounded proxy variants for M15-only target/stop ordering. It does not assert exact chronology, change live behavior, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion.

## Counts

- input_replay_execution_branch_rows: 386
- input_m15_only_branch_rows: 186
- input_path_ambiguity_rows: 9185
- m15_interval_branch_rows: 186
- m15_interval_ambiguity_support_rows: 9185
- m15_interval_proxy_variant_rows: 744
- m15_interval_requirement_rows: 186
- bucket_rows: 13
- question_rows: 3
- source_manifest_rows: 4

## interval_sign_class

- INTERVAL_ALL_NEGATIVE: 58
- INTERVAL_ALL_POSITIVE: 91
- INTERVAL_STRADDLES_ZERO: 37

## support_match_status

- MATCHED_ACTIVE_M15_INTERVAL_BRANCH: 4639
- UNMATCHED_TO_ACTIVE_186_M15_INTERVAL_QUEUE: 4546

## proxy_variant

- CLOSE_DIRECTION_PROXY: 186
- MIDPOINT: 186
- STOP_FIRST_BOUND: 186
- TARGET_FIRST_BOUND: 186

## target_stop_result

- NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT: 1
- STOP_FIRST_PROXY_DOMINANT: 82
- TARGET_FIRST_PROXY_DOMINANT: 103
