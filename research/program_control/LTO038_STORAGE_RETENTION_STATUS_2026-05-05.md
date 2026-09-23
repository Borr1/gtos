# LTO-038 Storage Retention Status - 2026-05-05

**Schema:** `lto038_storage_retention_status_v1`
**Generated:** `2026-06-03T00:03:20.770223+00:00`
**Status:** `OK_STORAGE_RETENTION_DRY_RUN`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Disk

- Total GB: `199.9004`
- Used GB: `143.4109`
- Free GB: `56.4895`
- Free %: `28.2588`
- Pressure codes: `[]`

## Counts

- Status rows available: `14`
- Status rows appended this run: `1`
- Scanned files: `30905`
- Dry-run cleanup candidates: `25`
- Temp/cache directories: `3`
- Deletion performed: `False`

## Large Sierra / Depth Files

| Path | Size MB | Class | Deletable |
|---|---:|---|---|
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_SCID_M15_TARGET_MOVEMENT_EVENT_LEDGER_2026-05-16.jsonl` | `562.2527` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_SCID_M15_PRIMITIVE_EVENT_LEDGER_2026-05-16.jsonl` | `289.0744` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_SCID_M15_SOURCE_BOUND_BAR_LEDGER_2026-05-16.jsonl` | `185.7425` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_SCID_M15_TARGET_MOVEMENT_FAIL_CLOSED_LEDGER_2026-05-16.jsonl` | `175.2457` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_GROUP_STRESS_LEDGER_2026-05-16.jsonl` | `137.1255` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_LEAVE_GROUP_LEDGER_2026-05-16.jsonl` | `101.3228` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_STATE_PROXY_LEDGER_2026-05-16.jsonl` | `66.3972` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_ROUTE_C_PROXY_JOIN_LEDGER_2026-05-16.jsonl` | `53.6736` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_SAMPLE_LEDGER_2026-05-16.jsonl` | `52.2912` | `REPORT_PROTECTED` | `False` |
| `research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_GROUP_LEDGER_2026-05-16.jsonl` | `42.1602` | `REPORT_PROTECTED` | `False` |

## Dry-Run Cleanup Candidates

| Path | Size MB | Class | Deletable |
|---|---:|---|---|
| `tests/__pycache__/test_gtos_vnext_runtime.cpython-313-pytest-9.0.3.pyc` | `3.0364` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `tests/__pycache__/test_gtos_vnext_runtime.cpython-313.pyc` | `0.9514` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `src/components/__pycache__/gtos_vnext_runtime.cpython-313.pyc` | `0.7009` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `src/components/__pycache__/orchestrator.cpython-313.pyc` | `0.5069` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `tests/__pycache__/test_execution.cpython-313-pytest-9.0.3.pyc` | `0.2457` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `src/components/__pycache__/execution.cpython-313.pyc` | `0.2359` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/__pycache__/build_vps_supervisor_artifacts.cpython-313.pyc` | `0.2199` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `tests/__pycache__/test_orchestrator.cpython-313-pytest-9.0.3.pyc` | `0.2194` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `tests/__pycache__/test_limit_order_flow.cpython-313-pytest-9.0.3.pyc` | `0.2112` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `tests/__pycache__/test_heartbeat_monitor.cpython-313-pytest-9.0.3.pyc` | `0.1878` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |

## Temp / Cache Directories

| Path | Size MB | Class | Deletable |
|---|---:|---|---|
| `.pytest_cache` | `0.0888` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `__pycache__` | `0.0047` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |
| `.codex` | `0.0001` | `TEMP_CACHE_DRY_RUN_DELETABLE` | `True` |

## Deletion Allowlist Policy

```json
{
  "allowed_classes": [
    "TEMP_CACHE_DRY_RUN_DELETABLE"
  ],
  "allowed_names": [
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__"
  ],
  "allowed_root_prefixes": [
    ".pytest",
    ".codex",
    "_codex",
    "_pytest",
    "pytest",
    "tmp",
    ".tmp",
    "codex_tmp",
    "tmp_pytest"
  ],
  "apply_mode_available": false,
  "evidence_log_delete_allowed": false,
  "raw_source_delete_allowed": false,
  "reports_delete_allowed": false
}
```

## Boundary

This row is a dry-run storage-retention classification only. It does not delete files and does not approve deletion of raw source data, Sierra/depth files, account history, shadow evidence logs, or research reports.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
