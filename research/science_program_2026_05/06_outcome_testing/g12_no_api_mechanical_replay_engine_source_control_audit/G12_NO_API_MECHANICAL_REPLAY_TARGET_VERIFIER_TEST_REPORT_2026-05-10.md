# Target Verifier Test Report

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "target_verifier_focused_test_rerun_report",
  "changes_live_trading_behavior": false,
  "commands": [
    {
      "args": [
        "C:\\Python313\\python.exe",
        "-B",
        "-c",
        "import ast, pathlib, sys; bad=[]; \nfor p in sys.argv[1:]:\n    ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p)\n",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
      ],
      "name": "target_py_compile",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "args": [
        "C:\\Python313\\python.exe",
        "-B",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        "--quiet"
      ],
      "name": "target_verifier",
      "returncode": 0,
      "stderr": "",
      "stdout": "{\n  \"can_mark_goal_complete\": true,\n  \"candidate_row_count\": 13540033,\n  \"failures\": [],\n  \"ok\": true,\n  \"path_label_row_count\": 12852758\n}"
    },
    {
      "args": [
        "C:\\Python313\\python.exe",
        "-B",
        "-m",
        "pytest",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.tmp_pytest_target_qqbi9ik4"
      ],
      "name": "target_focused_pytest",
      "returncode": 0,
      "stderr": "",
      "stdout": "..                                                                       [100%]\n2 passed in 0.38s"
    }
  ],
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-10T21:10:29+00:00",
  "issues": [],
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
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "status": "PASS",
  "validation_safe": false
}
```
