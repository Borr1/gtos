# Repaired Proxy Replay Score Rerun

Generated UTC: `2026-05-17T13:33:31Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `avoid_comparator_rerun_rows`: `2932`
- `bucket_rows`: `23`
- `control_context_rows`: `6`
- `default_off_score_rerun_rows`: `1719`
- `input_control_numeric_event_rows`: `173`
- `input_replay_numeric_event_rows`: `5324`
- `repair_context_rerun_rows`: `673`
- `score_rerun_rows`: `5324`
- `source_manifest_rows`: `8`
- `symbol_summary_rows`: `7`
- `system_action_rows`: `1`

## Continuation

Rebuild the exact/proxy bridge with replay rerun score fields, carry repair-context rows into identifier/geometry repair, and route scorer/comparator actions to the next branch-local packet.
