# Repaired Proxy Runtime Replay Implementation Steps

Generated UTC: `2026-05-17T17:03:41Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `avoid_redesign_comparator_action_rows`: `368`
- `bucket_rows`: `11`
- `context_carry_comparator_rows`: `78`
- `context_carry_scorer_rows`: `32`
- `context_comparator_batch_rows`: `114`
- `context_scorer_batch_rows`: `232`
- `default_off_scorer_action_rows`: `689`
- `implementation_action_rows`: `1057`
- `implementation_next_step_rows`: `1057`
- `implementation_scope_rollup_rows`: `40`
- `input_next_branch_local_packet_rows`: `1057`
- `input_ranked_advance_packet_rows`: `1057`
- `input_ranked_packet_result_ok`: `1`
- `input_system_ranked_packet_rows`: `1`
- `ready_comparator_batch_rows`: `176`
- `ready_scorer_batch_rows`: `425`
- `source_manifest_rows`: `9`
- `system_implementation_step_rows`: `1`

## Continuation

Materialize implementation-step batches into concrete scorer/comparator specs.
