# Sierra Depth Ladder Route C Controls

Generated UTC: `2026-05-15T20:48:25Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: ladder boundary60 descriptors joined to Route C/Sierra depth controls only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `command_join_input_rows`: `10382`
- `ladder_feature_input_rows`: `489`
- `ladder_blocker_input_rows`: `419`
- `joined_rows`: `10382`
- `ladder_feature_join_rows`: `489`
- `ladder_blocker_join_rows`: `419`
- `source_gap_ladder_rows`: `9500`
- `bucket_control_rows`: `134`
- `neighbor_pair_rows`: `5173`
- `neighbor_bucket_rows`: `9`
- `question_rows`: `11`

## Ladder Control Buckets

- `LADDER_BUCKET_ABOVE_DENOMINATOR_DESCRIPTIVE`: `13`
- `LADDER_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR`: `1`
- `LADDER_BUCKET_MIXED_SMALL_DESCRIPTOR_DIFFERENCE`: `11`
- `LADDER_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT`: `7`
- `NO_DIRECTIONAL_DESCRIPTOR_AVAILABLE`: `1`
- `NO_PRIOR_CLEAR_DOMINATES_LADDER_CONTEXT`: `27`
- `SOURCE_GAP_DOMINATES_LADDER_CONTEXT`: `41`
- `UNDERPOWERED_LADDER_GROUP_N_LT_20`: `33`

## Neighbor Control Buckets

- `NEIGHBOR_BUCKET_CONTAINS_LADDER_BLOCKER`: `3`
- `SAME_SOURCE_NEIGHBOR_GENERIC_CONTEXT`: `3`
- `UNDERPOWERED_NEIGHBOR_PAIR_BUCKET_N_LT_20`: `3`

## Next Same-Resource Work

- Convert no-prior-clear rows into earlier-book-history capture requirements.
- Inspect imbalanced ladder rows against command-flow and same-source pair ledgers.
- Use underpowered and source-gap buckets as acquisition/aggregation requirements, not stopping labels.
