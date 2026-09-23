# Sierra Depth Ladder Imbalanced Split After Fallback

Generated UTC: `2026-05-15T21:46:04Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: imbalanced ladder descriptor/control split only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.

## Counts

- `input_imbalanced_rows`: `9`
- `split_row_rows`: `9`
- `input_imbalanced_neighbor_context_rows`: `103`
- `split_neighbor_rows`: `103`
- `input_imbalanced_bucket_rows`: `24`
- `route_c_join_input_rows`: `10382`
- `fallback_target_input_rows`: `26`
- `fallback_context_rows`: `9`
- `requirement_after_fallback_input_rows`: `9919`
- `bucket_rows`: `42`
- `question_rows`: `7`
- `rows_with_same_source_fallback_targets`: `3`
- `rows_without_same_source_neighbor_context`: `1`
- `rows_with_command_ladder_divergence`: `2`
- `rows_with_route_alignment_unknown`: `3`

## Combined Split Buckets

- `AGREEING_COMMAND_LADDER_BUT_ROUTE_OR_CONTROL_WEAKENED`: `1`
- `AGREEING_IMBALANCE_WITH_NO_NEIGHBOR_SUPPORT`: `1`
- `AGREEING_IMBALANCE_WITH_UNDERPOWERED_CONTEXT`: `4`
- `AGREEING_ROUTE_ALIGNED_IMBALANCE_WITH_NEIGHBOR_SUPPORT`: `1`
- `DIVERGENT_COMMAND_LADDER_SPLIT_REQUIRED`: `2`

## Interpretation Boundary

- All `9` imbalanced ladder rows are preserved in the row ledger.
- All `103` existing imbalanced neighbor-context rows are preserved in the neighbor ledger.
- Same-source no-event fallback context is joined only as descriptor/control context; it does not replace exact boundary60 ladder truth.

## Next Same-Resource Work

- Search/acquire exact missing `.depth` source-date files where owned/current/free routes exist.
- Repair or proxy earlier-book-history rows where same-source depth history can be recovered.
- Feed split buckets into mutation rows without promoting any branch.
