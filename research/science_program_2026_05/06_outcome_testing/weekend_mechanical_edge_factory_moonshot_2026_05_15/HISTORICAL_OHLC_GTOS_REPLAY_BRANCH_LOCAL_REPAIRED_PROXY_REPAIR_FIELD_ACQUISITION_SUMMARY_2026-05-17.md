# Repaired Proxy Repair Field Acquisition

Generated UTC: `2026-05-17T14:23:21Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `acquisition_batch_rows`: `6`
- `acquisition_requirement_rows`: `564`
- `bucket_rows`: `12`
- `input_field_coverage_rows`: `7`
- `input_repair_execution_rows`: `188`
- `input_rerun_gate_rows`: `1`
- `source_candidate_rows`: `18`
- `source_manifest_rows`: `9`
- `system_action_rows`: `1`
- `unblock_plan_rows`: `3`

## Continuation

Run branch-local source lookups for acquisition requirements, rerun repair execution, then rerun exact/proxy bridge only if the repair gate has eligible rows.
