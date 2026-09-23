# vNext Replacement Rollback Runbook - 2026-05-26

## Purpose

Restore the current GTOS shadow/default-off behavior if Stage12 fails, monitoring detects leakage, or the owner stops the demo/prod activation sequence.

## Rollback Overlay

```yaml
gtos_vnext_runtime:
  ai_policy_apply_to_ai_call: false
  ai_policy_follow_no_ai_enabled: false
  apply_to_execution: false
  enabled: true
  exit_management_residue_apply_to_execution: false
  ltf_path_execution_apply_to_execution: false
  mode: shadow
  moonshot_dynamic_execution_router_apply_to_execution: false
  moonshot_dynamic_execution_router_condition_challenger_enabled: false
  moonshot_dynamic_execution_router_enabled: false
  moonshot_dynamic_execution_router_policy: be_after_trigger
  pending_policy_enabled: true
  pre_ai_apply_to_ai_call: false
  prop_safe_selector_apply_to_execution: false
  ready8_failure_control_residue_apply_to_execution: false
  replacement_ml_apply_to_execution: false
  replacement_monitoring_enabled: true
  replacement_monitoring_log_enabled: true
  replacement_monitoring_log_path: shadow_logs/gtos_vnext_replacement_monitoring.jsonl
```

## Required Checks

- Confirm `gtos_vnext_runtime.apply_to_execution=false`.
- Confirm `moonshot_dynamic_execution_router_apply_to_execution=false`.
- Confirm `moonshot_dynamic_execution_router_enabled=false`.
- Confirm `ltf_path_execution_apply_to_execution=false`.
- Confirm `prop_safe_selector_apply_to_execution=false`.
- Confirm `replacement_ml_apply_to_execution=false`.
- Confirm monitoring remains enabled at `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`.

## Verification Commands

- `python -m py_compile src\components\gtos_vnext_runtime.py src\components\orchestrator.py src\components\execution.py`
- `python -m pytest tests\test_gtos_vnext_runtime.py::test_agent_config_wires_vnext_runtime_shadow_execution_path -q`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage11_activation_dossier.py`

## Stop Conditions

Do not restart an account-connected runtime from this runbook. Broker/account/order/deal/position/history mutation is an owner external surface. If a live/demo process exists outside this route, stop it first through the owner-approved operator path, then apply this config overlay and rerun the verification commands.
