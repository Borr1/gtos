# Repaired Proxy Repair Work Execution

Generated UTC: `2026-05-17T14:16:58Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `blocked_repair_rows`: `188`
- `bucket_rows`: `7`
- `execution_batch_rows`: `2`
- `field_coverage_rows`: `7`
- `input_repair_batch_rows`: `2`
- `input_repair_work_order_rows`: `188`
- `input_rerun_plan_rows`: `4`
- `repair_execution_rows`: `188`
- `rerun_eligible_rows`: `0`
- `rerun_gate_rows`: `1`
- `source_manifest_rows`: `9`
- `system_action_rows`: `1`

## Continuation

Acquire missing identifier and scope fields, rerun repair execution, and only then rerun exact/proxy bridge with eligible repaired rows.
