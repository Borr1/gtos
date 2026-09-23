# Sierra Depth Ladder Route C After In-Window CLEAR_BOOK Join

Generated UTC: `2026-05-15T22:28:19Z`

Evidence class: full Route C ladder denominator and mutation-design update after same-source in-window clear repair.

## Counts

- `input_route_c_join_rows`: `10382`
- `updated_route_c_join_rows`: `10382`
- `input_in_window_clear_rows`: `393`
- `input_in_window_clear_repaired_full_rows`: `342`
- `input_in_window_clear_remaining_blocker_rows`: `51`
- `old_no_prior_clear_rows_updated`: `393`
- `repaired_feature_join_rows`: `342`
- `remaining_blocker_rows`: `51`
- `mutation_input_rows`: `54`
- `mutation_context_rows`: `54`
- `mutation_repair_join_rows`: `1179`
- `bucket_rows`: `106`
- `question_rows`: `7`

## Updated Ladder Join Status

- `LADDER_BLOCKER_REFINED_AFTER_IN_WINDOW_CLEAR_REPAIR`: `51`
- `LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED`: `26`
- `LADDER_FEATURE_JOINED`: `463`
- `LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR`: `342`
- `LADDER_SOURCE_GAP_MISSING_DEPTH_FILE`: `9500`

## Repaired Feature Buckets

- `IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_BALANCED`: `324`
- `IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_IMBALANCED`: `18`

## Interpretation Boundary

- The full `10,382` Route C/Sierra depth request denominator is preserved.
- All `393` old no-prior-clear ladder blockers now carry in-window clear repair context.
- `342` rows become exact repaired boundary ladder descriptors and `51` remain exact source/sample blockers.
- Mutation context is preserved for every `54` mutation rows and all row-level mutation/repair joins.
- This packet is a current-data control/mutation update, not a terminal closeout.

## Next Same-Resource Work

- Recompute Route C controls with `831` exact ladder feature rows (`489` prior-clear plus `342` in-window-clear repaired).
- Split the `51` remaining blockers by no-clear/no-sample source routes and search/acquire/proxy immediately.
- Feed repaired ladder buckets into current-data mutation rows outside the prior imbalanced context.
