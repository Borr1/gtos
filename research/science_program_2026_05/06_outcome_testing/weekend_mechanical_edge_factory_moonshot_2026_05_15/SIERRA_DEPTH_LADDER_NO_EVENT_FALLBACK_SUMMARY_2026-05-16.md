# Sierra Depth Ladder No-Event Fallback Probe

Generated UTC: `2026-05-15T21:21:34Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: local Sierra `.depth` record-level fallback for Route C rows where END_OF_BATCH boundary60 sampling produced no event samples. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `join_input_rows`: `10382`
- `target_no_event_rows`: `26`
- `target_depth_files`: `12`
- `fallback_feature_rows`: `26`
- `fallback_sample_rows`: `39954`
- `fallback_blocker_rows`: `26`
- `fallback_file_rows`: `12`
- `fallback_bucket_rows`: `10`
- `question_rows`: `9`
- `event15_proxy_rows`: `10`
- `repaired_from_no_event_rows`: `0`

## Fallback Buckets

- `FALLBACK_RECORD_LEVEL_NO_EVENT_SAMPLES`: `26`

## Event15 Proxy Buckets

- `FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_BALANCED_PROXY`: `8`
- `FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_IMBALANCED_PROXY`: `2`
- `FALLBACK_RECORD_LEVEL_EVENT15_IMBALANCE_MISSING`: `3`
- `FALLBACK_RECORD_LEVEL_EVENT15_NO_SAMPLES`: `13`

## Command/Fallback Relation Buckets

- `COMMAND_FALLBACK_AGREE_AND_ROUTE_ALIGNED_DESCRIPTOR`: `4`
- `COMMAND_FALLBACK_AGREE_BUT_ROUTE_NOT_ALIGNED_WEAKENING_DESCRIPTOR`: `3`
- `COMMAND_FALLBACK_DIVERGE_BUT_ROUTE_ALIGNED_SPLIT_REQUIRED`: `3`
- `COMMAND_OR_FALLBACK_SIGN_UNKNOWN`: `16`

## Interpretation Boundary

- Boundary60 remains exact: the run proves whether final-minute command records exist after removing the END_OF_BATCH filter.
- Full-M15 event-window record-level summaries are a proxy only when boundary60 is empty; they are not substituted as the exact final-minute descriptor.
- It does not repair exact missing `.depth` files, earlier-book-history/no-prior-clear requirements, or any outcome/validation class.
- Every sampled command record is preserved in the sample ledger; feature rows are per request and bucket rows are aggregate descriptors.

## Next Same-Resource Work

- Join fallback relation and full-M15 event proxy buckets into same-source intraday neighbor controls.
- Recompute source/capture requirements after preserving true boundary60-empty rows and adding full-event15 proxy splits.
- Continue source search for exact missing `.depth` files and split imbalanced descriptors by command-ladder sign.
