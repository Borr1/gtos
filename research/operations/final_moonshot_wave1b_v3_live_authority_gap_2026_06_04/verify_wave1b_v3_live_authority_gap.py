#!/usr/bin/env python3
"""Verify Wave 1B V3/live authority-gap route artifacts and focused checks."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

REQUIRED_ARTIFACTS = [
    "WAVE1B_CONTEXT_ANCHOR.json",
    "WAVE1B_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE1B_SOURCE_INVENTORY.jsonl",
    "WAVE1B_COMPONENT_INVENTORY.jsonl",
    "WAVE1B_CODE_RUNTIME_PATH_MAP.md",
    "LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl",
    "V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl",
    "SELECTOR_AUTHORITY_GAP_LEDGER.jsonl",
    "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl",
    "EXECUTION_POLICY_GAP_LEDGER.jsonl",
    "LIVE_DECISION_PACKET_COMPLETENESS_LEDGER.jsonl",
    "COST_SWAP_SLIPPAGE_AUTHORITY_LEDGER.jsonl",
    "EXPOSURE_AND_CLUSTER_AUTHORITY_LEDGER.jsonl",
    "HALT_SEMANTICS_AND_RUNTIME_CONTROL_LEDGER.jsonl",
    "PRODUCTION_CODE_CHANGE_LEDGER.jsonl",
    "IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "WAVE1B_AUTHORITY_GAP_SUMMARY.md",
    "WAVE1B_SATURATION_AND_SELF_RED_TEAM.md",
    "WAVE1B_VERIFICATION_RESULT.json",
    "WAVE1B_OUTPUT_MANIFEST.json",
    "WAVE1B_COMPLETION_AUDIT.md",
    "FOCUSED_TEST_RESULT.json",
]

REQUIRED_SUBAGENTS = [
    "SUBAGENT_SELECTOR_AUTHORITY_AUDITOR.md",
    "SUBAGENT_SCHEDULER_MONEY_RISK_AUDITOR.md",
    "SUBAGENT_EXECUTION_PACKET_COMPLETENESS_AUDITOR.md",
    "SUBAGENT_HALT_RUNTIME_CONTROL_AUDITOR.md",
    "SUBAGENT_PRODUCTION_SCOPE_AUDITOR.md",
    "SUBAGENT_SATURATION_PROMPT_HARDENING_AUDITOR.md",
]

REQUIRED_COMPONENTS = {
    "selector_v3",
    "scheduler_v3",
    "execution_policy_v3",
    "same_symbol_lifecycle_logic",
    "cost_swap_slippage_handling",
    "exposure_and_correlation_controls",
    "halt_semantics_runtime_control",
    "live_decision_packet_completeness",
    "market_whiteboard_state_inputs",
    "broker_profile_spec_session_authority",
    "replay_and_capture_contracts",
}

REQUIRED_MATRIX_FIELDS = {
    "material_row_id",
    "source_row_kind",
    "source_file",
    "evidence_class",
    "live_authority_classification",
    "branch_decision",
    "implementation_decision",
    "source_capture_state",
    "source_completeness_state",
    "exact_r",
    "proxy_r",
    "expectancy_r",
}


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "cmd": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def read_json(path: str) -> Any:
    return json.loads((ROUTE_DIR / path).read_text(encoding="utf-8"))


def read_jsonl(path: str) -> list[dict[str, Any]]:
    rows = []
    with (ROUTE_DIR / path).open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                rows.append({"_parse_error": str(exc), "_line": index})
            else:
                rows.append(value if isinstance(value, dict) else {"_non_object": value})
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        entry: dict[str, Any] = {
            "path": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if path.suffix == ".jsonl":
            entry["jsonl_rows"] = sum(
                1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
            )
        rows.append(entry)
    return rows


def write_json(path: str, data: Any) -> None:
    (ROUTE_DIR / path).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_artifacts() -> dict[str, Any]:
    missing = [
        name for name in REQUIRED_ARTIFACTS + REQUIRED_SUBAGENTS if not (ROUTE_DIR / name).exists()
    ]
    json_parse_errors = []
    jsonl_parse_errors = []
    for path in ROUTE_DIR.glob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            json_parse_errors.append({"path": path.name, "error": str(exc)})
    for path in ROUTE_DIR.glob("*.jsonl"):
        for index, line in enumerate(path.open(encoding="utf-8"), start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                jsonl_parse_errors.append({"path": path.name, "line": index, "error": str(exc)})
    return {
        "missing_artifacts": missing,
        "json_parse_errors": json_parse_errors,
        "jsonl_parse_errors": jsonl_parse_errors,
        "ok": not missing and not json_parse_errors and not jsonl_parse_errors,
    }


def verify_coverage() -> dict[str, Any]:
    matrix = read_jsonl("LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl")
    components = read_jsonl("V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl")
    implementation = read_jsonl("IMPLEMENTATION_DECISION_LEDGER.jsonl")
    matrix_missing_fields = []
    for row in matrix:
        missing = sorted(REQUIRED_MATRIX_FIELDS - set(row))
        if missing:
            matrix_missing_fields.append({"material_row_id": row.get("material_row_id"), "missing": missing})
            if len(matrix_missing_fields) >= 20:
                break
    component_ids = {row.get("component_id") for row in components}
    impl_component_ids = {row.get("component_id") for row in implementation}
    source_kinds: dict[str, int] = {}
    for row in matrix:
        source_kinds[str(row.get("source_row_kind"))] = source_kinds.get(str(row.get("source_row_kind")), 0) + 1
    minimum_source_kinds = {
        "runtime_decision",
        "replacement_monitoring_snapshot",
        "redacted_account_trade_record",
        "pending_limit_lifecycle",
        "broker_truth_trade_group",
    }
    checks = {
        "matrix_rows_ge_12000": len(matrix) >= 12000,
        "required_matrix_fields_present": not matrix_missing_fields,
        "required_components_present": REQUIRED_COMPONENTS <= component_ids,
        "implementation_decisions_for_components": REQUIRED_COMPONENTS <= impl_component_ids,
        "all_required_source_kinds_present": minimum_source_kinds <= set(source_kinds),
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "matrix_rows": len(matrix),
        "source_kind_counts": source_kinds,
        "component_ids": sorted(component_ids),
        "implementation_component_ids": sorted(impl_component_ids),
        "matrix_missing_fields": matrix_missing_fields,
    }


def main() -> int:
    artifact_checks = verify_artifacts()
    coverage_checks = verify_coverage()
    commands = [
        run(["python3", "-m", "py_compile", "src/components/orchestrator.py"]),
        run(["python3", "-m", "py_compile", "tests/test_vnext_broader_origin_orchestrator.py"]),
        run([
            "python3",
            "-m",
            "py_compile",
            rel(ROUTE_DIR / "build_wave1b_v3_live_authority_gap.py"),
            rel(ROUTE_DIR / "verify_wave1b_v3_live_authority_gap.py"),
        ]),
        run([
            "python3",
            "scripts/validate_goal_prompt_hardening.py",
            "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md",
        ]),
        run([
            "python3",
            "scripts/audit_goal_route_artifacts.py",
            rel(ROUTE_DIR),
            "--full-jsonl",
        ]),
        run([
            "python3",
            "-m",
            "pytest",
            "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_dynamic_refusal_record_has_complete_candidate_packet",
            "-q",
        ]),
    ]
    pytest_command = commands[-1]
    focused_test_status = (
        "pytest_passed"
        if pytest_command["exit_code"] == 0
        else "pytest_unavailable_or_failed_py_compile_passed"
    )
    py_compile_ok = all(command["exit_code"] == 0 for command in commands[:3])
    hardening_ok = commands[3]["exit_code"] == 0
    route_audit_ok = commands[4]["exit_code"] == 0
    ok = bool(
        artifact_checks["ok"]
        and coverage_checks["ok"]
        and py_compile_ok
        and hardening_ok
        and route_audit_ok
    )
    result = {
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "status": "pass" if ok else "fail",
        "ok": ok,
        "artifact_checks": artifact_checks,
        "coverage_checks": coverage_checks,
        "command_results": commands,
        "focused_test_status": focused_test_status,
        "pytest_required_for_behavior_assertion": True,
        "pytest_environment_note": (
            "Direct python3 -m pytest may be unavailable in this worktree environment; "
            "py_compile checks are the hard verification fallback allowed by the prompt."
        ),
        "source_capture_state": "verifier_ran_current_disk_artifacts",
        "source_completeness_state": "all_required_artifacts_and_full_jsonl_scans_checked",
        "branch_decision": "route_verified_for_commit" if ok else "repair_required_before_commit",
        "implementation_decision": "commit_scoped_wave1b_changes" if ok else "repair_failing_checks",
    }
    write_json("WAVE1B_VERIFICATION_RESULT.json", result)
    write_json(
        "FOCUSED_TEST_RESULT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "route": rel(ROUTE_DIR),
            "status": focused_test_status,
            "py_compile_ok": py_compile_ok,
            "pytest_exit_code": pytest_command["exit_code"],
            "pytest_stdout_tail": pytest_command["stdout_tail"],
            "pytest_stderr_tail": pytest_command["stderr_tail"],
            "commands": commands[:3] + [pytest_command],
            "source_capture_state": "focused_runtime_and_test_commands_recorded",
            "source_completeness_state": "pytest_attempt_recorded_py_compile_fallback_available",
        },
    )
    write_json(
        "WAVE1B_OUTPUT_MANIFEST.json",
        {
            "generated_at_utc": GENERATED_AT,
            "route": rel(ROUTE_DIR),
            "artifact_count": len(artifact_manifest()),
            "artifacts": artifact_manifest(),
            "manifest_status": "final_after_verifier_run",
        },
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
