# Sierra Depth Ladder Source Silence Join

Generated UTC: `2026-05-15T22:56:46Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source-silence Route C/mutation/neighbor context only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `input_effective_join_rows`: `10382`
- `input_source_silence_rows`: `51`
- `updated_join_rows`: `10382`
- `target_rows`: `51`
- `neighbor_pair_rows`: `608`
- `target_summary_rows`: `51`
- `mutation_input_rows`: `54`
- `mutation_context_rows`: `54`
- `mutation_source_silence_join_rows`: `153`
- `bucket_rows`: `24`
- `question_rows`: `24`

## Source Silence Families

- `NO_CLEAR_AND_EVENT_BOUNDARY_SOURCE_SILENCE`: `8`
- `TRUE_EVENT_BOUNDARY_SOURCE_SILENCE_AFTER_CLEAR`: `43`

## Neighbor Buckets

- `SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT`: `6`
- `SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT`: `40`
- `SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT`: `1`
- `SOURCE_SILENCE_ONLY_HAS_OTHER_SOURCE_SILENCE_NEIGHBORS`: `4`

## Same-Resource Continuation

- Use true source-silence status in mutation design instead of stale no-sample labels.
- Source-silence rows with weak/underpowered neighbor context should feed acquisition and avoid-context tests.
- Continue exact missing `.depth` source-date search; source silence is a current-source fact, not a future-data excuse.
