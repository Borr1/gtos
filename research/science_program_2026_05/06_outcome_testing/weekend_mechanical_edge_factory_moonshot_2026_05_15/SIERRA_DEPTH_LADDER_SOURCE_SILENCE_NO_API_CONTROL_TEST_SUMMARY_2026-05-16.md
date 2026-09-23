# Sierra Depth Ladder Source Silence No-API Control Tests

Generated UTC: `2026-05-15T23:20:08Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source-control and mutation-design tests only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `source_join_input_rows`: `10382`
- `exact_feature_control_rows`: `831`
- `target_control_input_rows`: `51`
- `design_target_input_rows`: `153`
- `split_control_input_rows`: `69`
- `target_test_rows`: `51`
- `design_test_rows`: `153`
- `control_comparison_rows`: `110`
- `acquisition_rows`: `8`
- `bucket_rows`: `5`
- `question_rows`: `9`

## No-API Control Verdicts

- `NO_API_CONTROL_MIXED_OR_DESCRIPTIVE_CONTEXT`: `17`
- `NO_API_CONTROL_POSSIBLE_AVOID_DUPLICATE_AWARE_RETEST_REQUIRED`: `1`
- `NO_API_CONTROL_SOURCE_ACQUISITION_NOT_SIGNAL`: `5`
- `NO_API_CONTROL_UNDERPOWERED_N_LT_20`: `38`
- `NO_API_CONTROL_UNDERPOWERED_N_LT_5`: `49`

## Same-Resource Continuation

- Convert surviving possible-avoid descriptor tests into a dedicated challenger packet before any promotion claim.
- Treat no-clear source-silence rows as exact acquisition/earlier-history repair requirements, not future-data waiting.
- Treat strong-neighbor source-silence rows as neutral/timing-context candidates and continue queue-level controls.
