# VPS V3 FTMO Rollback And Activation Plan

Route: `vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02`
Generated: `2026-06-02T01:00:59.627263Z`

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

## Active Now

- redacted_account: active existing live `run_agent.py --profile redacted_account` process group on `C:\Program Files\MetaTrader 5\terminal64.exe`.
- FTMO: terminal open at `C:\MT5\FTMO\terminal64.exe /portable`, no FTMO `run_agent.py` process group.
- V3 packages: present and default-off; no live activation.

## Owner-Approved redacted_account Reload Command Shape

```powershell
$env:GTOS_PROFILE = "redacted_account"
$env:GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003"
$env:GTOS_MT5_TERMINAL_PATH = "C:\Program Files\MetaTrader 5\terminal64.exe"
python run_agent.py --symbol XAUUSD --mode live --profile redacted_account --runtime-namespace redacted_account_live_bee34003 --terminal-path "C:\Program Files\MetaTrader 5\terminal64.exe"
```

Use the existing 24-symbol launcher/supervisor pattern for all symbols after the route verifier, broker profile verifier, and supervisor verifier pass. Do not reload from this plan without owner command.

## Owner-Approved FTMO Start Command Shape

```powershell
$env:GTOS_PROFILE = "operator_profile"
$env:GTOS_RUNTIME_NAMESPACE = "operator_profile"
$env:GTOS_MT5_TERMINAL_PATH = "C:\MT5\FTMO\terminal64.exe"
python run_agent.py --symbol XAUUSD --mode live --profile operator_profile --runtime-namespace operator_profile --terminal-path "C:\MT5\FTMO\terminal64.exe"
```

Run only after the owner confirms FTMO stage/add-ons/dashboard constraints and explicitly authorizes activation.

## Namespace-Specific Stop Patterns

redacted_account-only stop filter:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like "*run_agent.py*" -and ($_.CommandLine -like "*--runtime-namespace redacted_account_live_bee34003*" -or $_.CommandLine -like "*--profile redacted_account*") } |
  ForEach-Object { Stop-Process -Id $_.ProcessId }
```

FTMO-only stop filter:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like "*run_agent.py*" -and ($_.CommandLine -like "*--runtime-namespace operator_profile*" -or $_.CommandLine -like "*--profile operator_profile*" -or $_.CommandLine -like "*--profile ftmo*") } |
  ForEach-Object { Stop-Process -Id $_.ProcessId }
```

The redacted_account filter must never match the FTMO namespace, and the FTMO filter must never match the redacted_account namespace. These commands are rollback plans only; this route did not run them.
