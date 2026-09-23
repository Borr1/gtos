# Syntax Compile Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "syntax_compile_audit",
  "ast_fallback": [
    {
      "ast_parse_ok": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
    },
    {
      "ast_parse_ok": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
    },
    {
      "ast_parse_ok": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
    }
  ],
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "ast_fallback_passed_if_needed": true,
    "py_compile_passed": false
  },
  "credentials_touched": false,
  "files": [
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
  ],
  "generated_at_utc": "2026-05-10T06:17:09Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "py_compile_run": {
    "command": [
      "C:\\Python313\\python.exe",
      "-m",
      "py_compile",
      "C:\\tmp\\gtos_otb\\G12NOFILLHASHREPAIR\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
      "C:\\tmp\\gtos_otb\\G12NOFILLHASHREPAIR\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py",
      "C:\\tmp\\gtos_otb\\G12NOFILLHASHREPAIR\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py"
    ],
    "completed_at_utc": "2026-05-10T06:17:09Z",
    "returncode": 1,
    "started_at_utc": "2026-05-10T06:17:08Z",
    "stderr_tail": "[Errno 2] No such file or directory: 'C:\\\\tmp\\\\gtos_otb\\\\G12NOFILLHASHREPAIR\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\g12_nofill_historical_source_expansion_hash_repair_reaudit\\\\__pycache__\\\\build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.cpython-313.pyc.2695534147280'",
    "stdout_tail": ""
  },
  "remaining_blockers": [],
  "validation_safe": false
}
```
