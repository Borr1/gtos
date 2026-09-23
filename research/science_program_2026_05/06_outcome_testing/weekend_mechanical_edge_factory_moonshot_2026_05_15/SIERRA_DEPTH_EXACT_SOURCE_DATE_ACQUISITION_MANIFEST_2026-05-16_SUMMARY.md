# Sierra Depth Exact Source-Date Acquisition Manifest

Generated UTC: `2026-05-16T05:00:17Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: exact local `.depth` source-date file discovery/acquisition routing only. No paid/vendor calls were made.

## Counts

- `source_artifacts_considered`: `7`
- `source_artifacts_existing`: `7`
- `source_input_rows_total`: `12438`
- `extracted_requirement_rows`: `13052`
- `unique_source_date_requirements`: `1181`
- `search_root_rows`: `4`
- `unique_depth_files_seen`: `242`
- `permission_denied_or_walk_error_rows`: `29`
- `candidate_rows`: `548`
- `exact_candidate_rows`: `78`
- `exact_candidate_rows_sha256_hashed`: `78`
- `delayed_candidate_rows`: `40`
- `same_date_suffix_candidate_rows`: `2`
- `near_date_candidate_rows`: `463`
- `classification_rows`: `1181`
- `question_rows`: `5`

## Classifications

- `DELAYED_NEAR_MATCH_ONLY_NOT_SUBSTITUTABLE`: `3`
- `EXACT_LOCAL_PROOF_HASHED`: `77`
- `NEAR_DATE_MATCH_ONLY_NOT_SUBSTITUTABLE`: `13`
- `NO_LOCAL_PROOF`: `1088`

## Candidate Relations

- `exact_filename_match`: `78`
- `same_symbol_date_delayed_suffix_match`: `5`
- `same_symbol_date_suffix_match`: `2`
- `same_symbol_near_date_match_plusminus_3d`: `463`

## Boundary

- Exact matches were SHA-256 hashed and recorded as local source-date proof only.
- Near, suffix, and delayed files were preserved as leads/proxies only and are not substitutions.
- Permission errors are preserved in the permission ledger and not hidden.
- Shared `OUTPUT_MANIFEST`, `SPRINT_OPERATING_LEDGER`, verifier files, and `.context` were not edited.
