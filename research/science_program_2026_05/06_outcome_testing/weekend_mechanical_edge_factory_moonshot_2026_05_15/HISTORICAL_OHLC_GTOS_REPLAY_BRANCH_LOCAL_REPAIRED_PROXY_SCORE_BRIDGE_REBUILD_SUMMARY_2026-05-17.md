# Repaired Proxy Score Bridge Rebuild

Generated UTC: `2026-05-17T13:51:54Z`

Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.

## Counts

- `bucket_rows`: `17`
- `input_exact_proxy_bridge_rows`: `17916`
- `input_score_rerun_rows`: `5324`
- `missing_score_scope_rows`: `18`
- `rebuilt_exact_proxy_bridge_rows`: `17916`
- `repair_context_bridge_rows`: `170`
- `score_scope_joined_rows`: `17898`
- `score_scope_summary_rows`: `288`
- `source_manifest_rows`: `8`
- `symbol_summary_rows`: `8`
- `system_action_rows`: `1`

## Continuation

Aggregate score-bridge actions by symbol/scope/market, route repair-context rows into identifier and geometry repair, then materialize the next comparator packet.
