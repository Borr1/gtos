# VPS V3 FTMO Context Anchor

Route: `vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02`
Generated: `2026-06-02T01:00:59.626366Z`

## Status Fields

```json
{
  "branch_decision": "consume_origin_vnext_vps_ftmo_v3_clean_deploy_2026_06_02_preserve_vps_live_fixes",
  "broker_operation_status": "read_only_mt5_profile_and_process_inspection_only_no_broker_mutation",
  "evidence_class": "VPS production engineering, runtime integration, broker-profile verification, default-off package consumption, supervisor setup, rollback proof, and scoped deployment readiness",
  "exact_R_status": "not_applicable_to_this_production_engineering_goal_no_replay_scoring",
  "expectancy_status": "not_applicable_to_live_readiness_expectancy_values_are_package_provenance_only",
  "implementation_decision": "repair_profiles_add_default_off_v3_loader_verify_namespace_rollbacks",
  "live_trading_status": "redacted_account_live_continues_existing_processes_ftmo_staged_no_activation",
  "production_change_status": "scoped_code_config_profile_verifier_artifact_changes_authorized_by_goal",
  "proxy_R_status": "not_applicable_to_this_production_engineering_goal_v3_proxy_values_are_package_provenance_only",
  "remote_push_status": "pending_until_scoped_commit_is_pushed",
  "runtime_effect_boundary": "default_off_v3_package_consumption_no_live_process_reload_no_order_deal_position_mutation",
  "source_capture_status": "current_vps_disk_process_and_readonly_mt5_capture"
}
```

## Current Active/Staged State

- redacted_account remains the active live broker on the normal MetaTrader terminal.
- FTMO is bound to the separate portable terminal at `C:\MT5\FTMO\terminal64.exe` and remains staged.
- Selector V3, Scheduler V3, and Execution Policy V3 packages are loaded and hashed through `src/research/moonshot_v3_runtime_packages.py`; config keys remain default-off.
- No live process reload/start/stop and no order/deal/position mutation was performed by this route.

## Required Inputs

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- `research/science_program_2026_05/04_goal_prompts/VNEXT_VPS_V3_FULL_PROMOTION_AND_FTMO_SETUP_GOAL_PROMPT_2026-06-02.md`
- `research/science_program_2026_05/04_goal_prompts/VNEXT_VPS_V3_FULL_PROMOTION_AND_FTMO_SETUP_STARTER_2026-06-02.txt`
- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_HANDOFF.md`
- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_SCOPE_LEDGER.jsonl`
- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_VERIFICATION_RESULT.json`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/COMPLETION_AUDIT.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_VERIFICATION_RESULT.json`
- `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/VPS_SUPERVISOR_STATE.json`
- `config/profiles/redacted_account.yaml`
- `config/profiles/operator_profile.yaml`
- `config/profiles/ftmo.yaml`
- `config/agent_config.yaml`
- `run_agent.py`
- `scripts/verify_broker_profile.py`
- `src/utils/broker_profile.py`
- `src/components/broker_truth_cost_capture_v2.py`
- `src/research/moonshot_selector_v3_default_off.py`
- `src/research/moonshot_v3_runtime_packages.py`
- `tests/test_moonshot_v3_runtime_packages.py`
