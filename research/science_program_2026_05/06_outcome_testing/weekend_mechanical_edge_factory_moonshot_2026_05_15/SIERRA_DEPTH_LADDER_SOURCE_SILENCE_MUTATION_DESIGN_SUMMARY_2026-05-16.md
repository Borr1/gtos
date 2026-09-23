# Sierra Depth Ladder Source Silence Mutation Design

Generated UTC: `2026-05-15T23:02:45Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: branch-local mutation design only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `mutation_context_input_rows`: `54`
- `mutation_source_silence_join_input_rows`: `153`
- `target_summary_input_rows`: `51`
- `design_rows`: `54`
- `affected_design_rows`: `24`
- `unaffected_design_rows`: `30`
- `evidence_join_rows`: `153`
- `queue_rows`: `18`
- `bucket_rows`: `60`
- `question_rows`: `60`

## Design Status Counts

- `MUTATION_DESIGN_UNAFFECTED_BY_SOURCE_SILENCE`: `30`
- `SOURCE_SILENCE_AVOID_FILTER_DESIGN_CANDIDATE`: `4`
- `SOURCE_SILENCE_COST_AND_SOURCE_QUALITY_DESIGN`: `4`
- `SOURCE_SILENCE_DECONCENTRATION_DESIGN`: `3`
- `SOURCE_SILENCE_ENTRY_TIMING_GUARD_DESIGN`: `3`
- `SOURCE_SILENCE_HORIZON_ROUTER_SPLIT_DESIGN`: `3`
- `SOURCE_SILENCE_MUTATION_SPLIT_DESIGN`: `3`
- `SOURCE_SILENCE_SOURCE_PROXY_ACQUISITION_DESIGN`: `4`

## Same-Resource Continuation

- Materialize affected design rows into source-silence split/control packets.
- Keep unaffected mutation rows in the denominator instead of dropping them.
- Treat the rules as branch-local proposals only until a separate validation/promotion dossier exists.
