# vNext Replacement Demo/Shadow Activation Runbook - 2026-05-26

## Scope

This is repo-local and demo-shadow only. It does not start `run_agent.py`, connect to an account, mutate broker state, place orders, modify orders, close positions, or read account/deal/history state.

## Demo Shadow Overlay

```yaml
gtos_vnext_runtime:
  ai_policy_apply_to_ai_call: false
  ai_policy_follow_no_ai_enabled: false
  apply_to_execution: false
  enabled: true
  exit_management_residue_apply_to_execution: false
  ltf_path_execution_apply_to_execution: false
  mode: demo_shadow_vnext_replacement
  moonshot_dynamic_execution_router_apply_to_execution: false
  moonshot_dynamic_execution_router_condition_challenger_enabled: false
  moonshot_dynamic_execution_router_enabled: true
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

## Activation Sequence

1. Apply only the demo-shadow overlay from `VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_2026-05-26.yaml`.
2. Run the Stage05, Stage06, Stage10, and Stage11 verifiers.
3. Run the focused monitoring tests.
4. Inspect `shadow_logs/gtos_vnext_replacement_monitoring.jsonl` for the required snapshot fields after a safe shadow/demo runtime has been started by an owner-approved external handoff.
5. Keep all broker-verified eligible symbols in capture/monitoring mode: AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NAS100, NZDUSD, SPX500, UK100, US30_cash, USDCAD, USDCHF, USDJPY, XAGUSD, XAUUSD.
6. Do not treat pending replay markets as unavailable. Pending broker-contract verification symbols are: -.

## Commands

- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage05_full_activated_replay.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage06_legacy_vs_vnext_delta.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage10_ml_monitoring_integration.py`
- `python research\science_program_2026_05\06_outcome_testing\vnext_moonshot_production_replacement_activation_2026_05_26\verify_vnext_replacement_stage11_activation_dossier.py`
- `python -m pytest tests\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces tests\test_gtos_vnext_runtime.py::test_vnext_replacement_monitoring_flags_old_live_fallback_leakage -q`

## External Handoff Required Before Runtime Startup

Owner must provide explicit permission and account details before any account-connected runtime process starts. Required fields: account type, account id, broker server, symbol alias map, allowed symbols, max risk, start/stop time, rollback operator, and confirmation that order/deal/position/history mutation is allowed for the selected demo/live surface.
