# Branch-Local Numeric Shadow Scorer Compute

Generated UTC: `2026-05-17T11:13:24Z`

Branch-local numeric shadow scorer compute. This packet runs callable scorer/source-repair code over the current numeric result rows and router recommendation ledgers, producing exact-R compute attempts, proxy-R score rows, scope decisions, repair queues, and summaries. It is research-only and has no live behavior.

## Counts

- `input_numeric_result_rows`: `17916`
- `input_scorer_surface_rows`: `5341`
- `input_avoid_comparator_rows`: `4115`
- `input_source_repair_proof_rows`: `17753`
- `input_context_guard_rows`: `1513`
- `input_scope_system_rows`: `290`
- `numeric_event_score_rows`: `17916`
- `exact_r_compute_rows`: `17916`
- `exact_r_value_rows`: `0`
- `proxy_score_rows`: `10969`
- `source_repair_queue_rows`: `17753`
- `scope_score_decision_rows`: `290`
- `symbol_session_horizon_summary_rows`: `290`
- `source_component_summary_rows`: `13`
- `bucket_rows`: `25`
- `question_rows`: `4`
- `source_manifest_rows`: `12`

## Decisions

- `AVOID_INVERSE_OR_FAILURE_FILTER_FIRST`: `157`
- `DEFAULT_OFF_SCORER_WITH_AVOID_AND_SOURCE_GUARDS`: `95`
- `SOURCE_REPAIR_FIRST_NO_CURRENT_SCALAR`: `38`
