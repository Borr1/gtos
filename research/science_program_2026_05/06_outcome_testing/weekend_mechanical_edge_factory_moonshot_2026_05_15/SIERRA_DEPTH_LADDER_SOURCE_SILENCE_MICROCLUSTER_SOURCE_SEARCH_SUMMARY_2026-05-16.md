# Sierra Source-Silence Microcluster Source Search

Generated UTC: `2026-05-15T23:48:07Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: exact source-date/root search plus event-boundary replay. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `source_requirement_input_rows`: `14`
- `source_join_input_rows`: `10382`
- `searched_root_rows`: `4`
- `unique_depth_files_seen`: `233`
- `candidate_file_rows`: `14`
- `primary_exact_candidate_rows`: `14`
- `alternate_exact_candidate_rows`: `0`
- `same_symbol_date_variant_candidate_rows`: `0`
- `request_replay_rows`: `23`
- `repairing_replay_rows`: `0`
- `decision_rows`: `14`
- `bucket_rows`: `8`
- `question_rows`: `22`
- `root_error_count`: `33`

## Decision Buckets

- `CURRENT_FILE_TRUE_FINAL_MINUTE_SOURCE_SILENCE_NO_ALTERNATE`: `11`
- `SOURCE_SEARCH_NO_REPAIR_REQUIRES_PROXY_CONTROL`: `3`

## Replay Buckets

- `CANDIDATE_HAS_EVENT15_BUT_FINAL_MINUTE_SOURCE_SILENCE`: `18`
- `CANDIDATE_HAS_NO_EVENT15_RECORDS`: `5`

## Same-Resource Continuation

- Build source-safe proxy controls for unrepaired micro-clusters.
- Use variant/suffixed candidates only as source-semantics leads unless they repair event-boundary records and pass parser audit.
- Feed unrepaired source-search decisions into branch-local challenger boundaries only.
