# Sierra Depth Ladder Gap Requirements And Imbalanced Inspection

Generated UTC: `2026-05-15T20:58:47Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source/capture requirements plus imbalanced ladder row inspection only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `join_input_rows`: `10382`
- `neighbor_pair_input_rows`: `5173`
- `alt_gap_input_rows`: `1106`
- `alt_candidate_input_rows`: `3`
- `requirement_rows`: `9919`
- `requirement_group_rows`: `1264`
- `missing_depth_file_requirement_rows`: `9500`
- `earlier_book_history_requirement_rows`: `393`
- `event_window_alignment_requirement_rows`: `26`
- `near_match_requirement_rows`: `9`
- `imbalanced_ladder_rows`: `9`
- `imbalanced_neighbor_context_rows`: `103`
- `imbalanced_bucket_rows`: `24`
- `question_rows`: `11`

## Requirement Types

- `EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT`: `393`
- `EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT`: `26`
- `MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT`: `9500`

## Requirement Statuses

- `LOCAL_FILE_PRESENT_BUT_EVENT_WINDOW_EMPTY_OR_MISALIGNED`: `26`
- `LOCAL_FILE_PRESENT_BUT_PRIOR_BOOK_STATE_INSUFFICIENT`: `393`
- `UNRECOVERED_EXACT_DEPTH_FILE`: `9491`
- `UNRESOLVED_NEAR_MATCH_NOT_SUBSTITUTABLE`: `9`

## Imbalanced Route Descriptors

- `COMMAND_LADDER_AGREE_AND_ROUTE_ALIGNED_DESCRIPTOR`: `4`
- `COMMAND_LADDER_AGREE_BUT_ROUTE_NOT_ALIGNED_WEAKENING_DESCRIPTOR`: `1`
- `COMMAND_LADDER_DIVERGE_BUT_ROUTE_ALIGNED_SPLIT_REQUIRED`: `1`
- `IMBALANCED_ROW_ALIGNMENT_UNKNOWN_OR_MIXED`: `3`

## Next Same-Resource Work

- Search or request exact `.depth` source-date files for unrecovered missing-depth requirements.
- Audit delayed/suffixed near-match NQ depth samples before any substitution.
- Split the imbalanced rows by command-ladder sign relation and same-source neighbor context.
- Continue mutation work from current depth/SCID/tick data; this packet is not completion.
