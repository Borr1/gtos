# Sierra Depth Ladder Source Silence Possible-Avoid Dedup Packet

Generated UTC: `2026-05-15T23:26:14Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: de-duplicated source-control/challenger design only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `source_join_input_rows`: `10382`
- `exact_feature_control_rows`: `831`
- `possible_avoid_design_rows`: `69`
- `dedup_target_rows`: `23`
- `duplicate_design_rows_removed`: `46`
- `control_rows`: `5`
- `stress_rows`: `14`
- `decision_rows`: `1`
- `question_rows`: `9`

## Decision

- `decision_status`: `POSSIBLE_AVOID_DEDUP_PARTIAL_CONTROL_SUPPORT_NEEDS_DEEPER_SPLIT`
- `next_same_resource_action`: split by queue, command bucket, source date, and source symbol; then rerun matched controls
