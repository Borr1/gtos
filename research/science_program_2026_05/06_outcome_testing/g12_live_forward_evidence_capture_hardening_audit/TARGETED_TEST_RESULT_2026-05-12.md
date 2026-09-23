# Targeted Test Result - 2026-05-12

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Command:

```powershell
python -m pytest tests/test_forward_capture_shadow_loggers.py tests/test_fvg_ob_confluence_audit.py tests/test_fvg_ob_confluence_source_geometry_backfill.py tests/test_daily_monitoring_checklist.py tests/test_verify_shadow_log_integrity.py tests/test_live_shadow_gap_closure.py tests/test_decision_layer_diagnostics_join.py tests/test_exit_management_no_event_audit.py tests/test_opportunity_lifecycle_audit.py tests/test_pending_limit_lifecycle_audit.py tests/test_v2_structural_selector_readiness.py tests/test_tick_capture.py tests/test_mt5_daemon_runtime.py tests/test_orchestrator.py tests/test_missed_fill_opportunity_study.py -q -p no:cacheprovider --basetemp .pytest_tmp
```

Result: `287 passed in 13.84s`

Exit code: `0`

Notes:

- The run used repo-local pytest temp path `.pytest_tmp`.
- Pytest emitted a production-path snapshot warning because live processes wrote runtime state concurrently under `knowledge_base/`, `shadow_logs/`, and `pipeline_state/`.
- This warning is not a target-commit blocker. The test write guard still treats pytest-process writes to protected production paths as failures.
