# vNext Moonshot Stage01 Static Primitive Assumption Audit

Generated: `2026-05-26T03:21:04Z`

## Result

- Ledger rows: `38415`
- Large row ledgers preserved/deferred for later streaming replay: `905`
- No arbitrary top-N sampling used: `True`
- Lossy sampling used: `False`
- First incomplete invariant: `STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY`

## Assumption Families

- `ai_ml_label_dependency`: `7518`
- `candidate_origin_boxing`: `12069`
- `dynamic_execution_gap`: `2879`
- `fixed_bracket_or_proxy_r`: `1279`
- `prop_governor_static_path`: `1247`
- `shadow_disabled_or_stale`: `2836`
- `source_proxy_or_gap`: `4163`
- `verifier_completion_semantics`: `6424`

## Required Bucket Coverage

- `activation_route_artifacts`: `True`
- `code`: `True`
- `config`: `True`
- `full_replay_route_artifacts`: `True`
- `moonshot_route_artifacts`: `True`
- `production_failure_route_artifacts`: `True`
- `prompts`: `True`
- `repaired_candidate_route_artifacts`: `True`
- `scripts`: `True`
- `shadow_logs`: `True`
- `tests`: `True`

## Actions

- `consume_as_dynamic_execution_policy_input`: `2879`
- `keep_default_off_until_corrected_replay_then_implementation_decision`: `2836`
- `rebuild_ai_budget_design_after_dynamic_labels`: `6017`
- `recompute_prop_ev_after_dynamic_labels`: `1247`
- `redesign_or_expand_universal_candidate_origin`: `12069`
- `relabel_ml_feasibility_after_dynamic_labels`: `1501`
- `replay_under_dynamic_execution_policy`: `1279`
- `semantic_verifier_hardening`: `6424`
- `source_repair_or_forward_capture`: `4163`

## Notes

- Code/config/prompts/tests/small artifacts were scanned at line level.
- JSONL artifacts below the scan limit were streamed fully and counted by assumption family.
- Huge activation ledgers were not sampled or reduced; they are preserved as exact source ledgers and explicitly queued for the dynamic replay and corrected branch-metric stages.
- Stage01 is an assumption inventory, not the dynamic replay result. It moves the first incomplete invariant to Stage02.
