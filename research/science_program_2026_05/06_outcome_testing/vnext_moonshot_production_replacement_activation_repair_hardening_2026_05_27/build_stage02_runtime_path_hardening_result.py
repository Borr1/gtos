from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"

STAGE02_RESULT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE02_RUNTIME_HARDENING_RESULT_{DATE}.json"
STAGE_SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _run_command(command_id: str, args: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc).replace(microsecond=0)
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    ended = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "command": " ".join(args),
        "duration_seconds": round((ended - started).total_seconds(), 3),
        "ended_at_utc": ended.isoformat().replace("+00:00", "Z"),
        "exit_code": proc.returncode,
        "id": command_id,
        "started_at_utc": started.isoformat().replace("+00:00", "Z"),
        "status": "passed" if proc.returncode == 0 else "failed",
        "stderr_tail": proc.stderr[-4000:],
        "stdout_tail": proc.stdout[-4000:],
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    commands = [
        _run_command(
            "execution_pending_fill_dynamic_policy_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_limit_order_flow.py",
                "tests/test_j46_j49_policy.py",
                "-q",
                "--basetemp=.pytest-tmp-vnext-execution-stage02-artifact",
                "-o",
                "cache_dir=.pytest-tmp-vnext-execution-stage02-artifact-cache",
            ],
        ),
        _run_command(
            "broader_origin_runtime_parity_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_vnext_broader_origin_orchestrator.py",
                "-q",
                "--basetemp=.pytest-tmp-vnext-broader-origin-stage02-artifact",
                "-o",
                "cache_dir=.pytest-tmp-vnext-broader-origin-stage02-artifact-cache",
            ],
        ),
    ]
    all_passed = all(row["exit_code"] == 0 for row in commands)

    changed_files = [
        REPO_ROOT / "src/components/orchestrator.py",
        REPO_ROOT / "src/components/execution.py",
        REPO_ROOT / "tests/test_vnext_broader_origin_orchestrator.py",
        REPO_ROOT / "tests/test_limit_order_flow.py",
        REPO_ROOT / "tests/test_j46_j49_policy.py",
    ]
    file_evidence = [
        {
            "path": _rel(path),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        for path in changed_files
    ]

    completed_gates = [
        {
            "evidence": [
                "src/components/orchestrator.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
            ],
            "gate_id": "vnext_native_prescreen_news_parity",
            "status": "closed_broader_origin_vnext_native_prescreen_news_calendar_gates",
        },
        {
            "evidence": [
                "src/components/orchestrator.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
            ],
            "gate_id": "fake_completion_dead_selector_gates",
            "status": "closed_production_replacement_consumes_when_activation_flags_disabled",
        },
        {
            "evidence": [
                "src/components/execution.py",
                "tests/test_limit_order_flow.py",
                "tests/test_j46_j49_policy.py",
            ],
            "gate_id": "dynamic_pending_fill_persistence",
            "status": "closed_pending_intent_persists_placement_time_be_params_source_identity_and_survives_config_drift",
        },
        {
            "evidence": [
                "src/components/execution.py",
                "tests/test_limit_order_flow.py",
            ],
            "gate_id": "execution_policy_support_matrix",
            "status": "closed_unsupported_dynamic_policy_fails_closed_before_order_send",
        },
    ]

    result = {
        "commands": commands,
        "completed_gates": completed_gates,
        "file_evidence": file_evidence,
        "generated_at_utc": generated_at,
        "remaining_open_gates": [
            "rollback_executable_proof",
            "broker_resolved_monitor_tick_parity",
            "broker_alias_repair_ger_oil",
            "pending_notification_parity",
            "redacted_account_risk_broker_geometry_current_specs",
            "cost_slippage_commission_fill_capture",
            "non_mutating_check_mode",
            "canonical_frequency_executable_trade_ledger",
            "prior_question_anatomy_consumption",
        ],
        "route_id": ROUTE_ID,
        "schema_version": "vnext_activation_repair_stage02_runtime_hardening_result_v1",
        "status": "completed_stage02_core_runtime_gates_route_open" if all_passed else "failed_stage02_tests",
    }
    _write_json(STAGE02_RESULT, result)

    spine = _read_json(STAGE_SPINE)
    completed_ids = {row["gate_id"] for row in completed_gates}
    spine["completed_gates"] = sorted(set(spine.get("completed_gates", [])) | completed_ids)
    spine["open_gates"] = [
        gate for gate in spine.get("open_gates", []) if gate not in completed_ids
    ]
    spine["current_stage"] = "stage_03_broker_risk_monitoring_alias_cost_capture"
    spine["latest_stage02_test_commands"] = commands
    spine["next_exact_action"] = (
        "Repair Stage03 broker/risk/monitoring gates: non-mutating GER30/UKOUSD/USOUSD alias verification, monitor/tick universe parity, redacted_account geometry, pending-notification parity, and cost/slippage/commission/fill capture."
    )
    spine.setdefault("stage_status", {})[
        "stage_02_runtime_path_hardening"
    ] = "completed_core_runtime_gates_route_open"
    spine.setdefault("stage_status", {})[
        "stage_03_broker_risk_monitoring_alias_cost_capture"
    ] = "in_progress"
    spine["generated_at_utc"] = generated_at
    _write_json(STAGE_SPINE, spine)

    manifest = _read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    for path in [Path(__file__).resolve(), STAGE02_RESULT, STAGE_SPINE]:
        rel_path = _rel(path)
        outputs[:] = [row for row in outputs if row.get("path") != rel_path]
        outputs.append(
            {
                "path": rel_path,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "stage": "stage_02",
                "status": "created_or_updated",
            }
        )
    manifest["last_updated_utc"] = generated_at
    manifest["status"] = "stage02_runtime_hardening_recorded_route_open"
    _write_json(OUTPUT_MANIFEST, manifest)

    _append_control(
        {
            "completed_gate_count": len(completed_gates),
            "event": "stage02_runtime_path_hardening_recorded",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "status": result["status"],
            "test_status": "passed" if all_passed else "failed",
        }
    )
    print(json.dumps({"status": result["status"], "test_status": "passed" if all_passed else "failed"}))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
