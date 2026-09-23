# Sierra Depth Ladder Route C Controls After In-Window Clear Repair

Generated UTC: `2026-05-15T22:38:46Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: repaired Route C/Sierra ladder source-control descriptors only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `after_repair_join_input_rows`: `10382`
- `effective_join_rows`: `10382`
- `effective_ladder_feature_join_rows`: `831`
- `effective_ladder_blocker_join_rows`: `77`
- `effective_source_gap_ladder_rows`: `9500`
- `pre_repair_no_prior_clear_rows`: `393`
- `effective_old_no_prior_clear_rows`: `0`
- `remaining_no_in_window_clear_rows`: `8`
- `remaining_in_window_event_no_sample_rows`: `43`
- `prior_boundary60_no_event_sample_rows`: `26`
- `bucket_control_rows`: `182`
- `neighbor_pair_rows`: `10215`
- `neighbor_bucket_rows`: `60`
- `control_delta_rows`: `49`
- `question_rows`: `16`

## Ladder Control Buckets

- `IN_WINDOW_CLEAR_EVENT_NO_SAMPLE_DOMINATES_CONTEXT`: `6`
- `LADDER_BUCKET_ABOVE_DENOMINATOR_DESCRIPTIVE`: `11`
- `LADDER_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR`: `6`
- `LADDER_BUCKET_MIXED_SMALL_DESCRIPTOR_DIFFERENCE`: `20`
- `LADDER_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT`: `18`
- `NO_DIRECTIONAL_DESCRIPTOR_AVAILABLE`: `2`
- `SOURCE_GAP_DOMINATES_LADDER_CONTEXT`: `41`
- `UNDERPOWERED_LADDER_GROUP_N_LT_20`: `78`

## Neighbor Control Buckets

- `NEIGHBOR_BUCKET_CONTAINS_LADDER_BLOCKER`: `3`
- `SAME_SOURCE_NEARBY_ALIGNMENT_CLUSTERS`: `1`
- `SAME_SOURCE_NEIGHBOR_ALIGNMENT_UNSTABLE`: `7`
- `SAME_SOURCE_NEIGHBOR_GENERIC_CONTEXT`: `14`
- `UNDERPOWERED_NEIGHBOR_PAIR_BUCKET_N_LT_20`: `35`

## Same-Resource Continuation

- Split and repair the `51` remaining blockers immediately: exact event-boundary no-sample rows versus no in-window clear before canonical.
- Use the effective `831` feature-row denominator for mutation-context work instead of the stale `489`-row prior-clear denominator.
- Keep exact missing `.depth` source-date acquisition active while building best-available same-source proxies.
