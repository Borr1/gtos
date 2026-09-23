# Repaired Proxy Runtime Replay Spec Execution

Generated UTC: `2026-05-17T17:18:53Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `bucket_rows`: `8`
- `comparator_avoid_score_rows`: `107`
- `comparator_spec_execution_rows`: `368`
- `comparator_strong_avoid_score_rows`: `212`
- `comparator_weak_or_positive_score_rows`: `49`
- `input_avoid_rerun_rows`: `2932`
- `input_comparator_spec_rows`: `368`
- `input_default_off_rerun_rows`: `1719`
- `input_scorer_spec_rows`: `689`
- `input_spec_materialization_result_ok`: `1`
- `input_system_spec_materialization_rows`: `1`
- `scorer_negative_replay_score_rows`: `0`
- `scorer_positive_replay_score_rows`: `675`
- `scorer_spec_execution_rows`: `689`
- `scorer_weak_positive_replay_score_rows`: `14`
- `source_manifest_rows`: `11`
- `spec_execution_exact_join_rows`: `1057`
- `spec_execution_result_rows`: `1057`
- `spec_execution_scope_rollup_rows`: `33`
- `spec_execution_unmatched_rows`: `0`
- `system_spec_execution_rows`: `1`

## Continuation

Convert every executed scorer/comparator spec into row-level and aggregate historical replay/simulated-R performance tables. Use simulated historical/replay geometry, with proxy-R only where exact simulated trade geometry is unavailable, and preserve every row without a top-N cutoff.
