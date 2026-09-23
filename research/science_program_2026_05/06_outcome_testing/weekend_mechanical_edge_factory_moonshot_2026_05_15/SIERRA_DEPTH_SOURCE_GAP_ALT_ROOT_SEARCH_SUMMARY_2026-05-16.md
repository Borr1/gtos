# Sierra Depth Source-Gap Alternate-Root Search

Generated UTC: `2026-05-15T19:50:30Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: local file discovery and exact source-gap repair routing only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `searched_root_rows`: `4`
- `unique_depth_files_seen`: `233`
- `missing_source_gap_rows`: `1106`
- `gap_search_rows`: `1106`
- `candidate_rows`: `3`
- `exact_candidate_rows`: `0`
- `near_candidate_rows`: `3`
- `root_error_count`: `33`
- `question_rows`: `4`

## Recovery Buckets

- `NEAR_MATCH_SUFFIX_OR_DELAYED_FILE_ONLY`: `1`
- `NO_ALTERNATE_DEPTH_FILE_FOUND`: `1105`

## Interpretation

- Every missing depth source-date gap was searched against the accessible approved roots.
- Exact alternate files, if any, still require parser/source audit before use.
- Near delayed/suffix files are not substitutions for exact source-date truth.
- Access-denied roots are preserved in the root scan ledger.

## Next Same-Resource Work

- Convert unrecovered gaps into exact forward-capture/source-acquisition requirements.
- Use delayed/suffix files only for parser-fixture or provenance analysis after audit.
- Continue the independent ladder-snapshotter route for the locally available depth files.
