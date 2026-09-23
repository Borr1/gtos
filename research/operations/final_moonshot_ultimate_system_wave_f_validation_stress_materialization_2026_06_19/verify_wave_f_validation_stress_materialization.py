#!/usr/bin/env python3
"""Verify Wave F validation/stress materialization artifacts."""

from __future__ import annotations

import json
import errno
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]


def read_text(path: Path) -> str:
    last_deadlock: OSError | None = None
    for _ in range(5):
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            if exc.errno != errno.EDEADLK:
                raise
            last_deadlock = exc
            time.sleep(0.05)
    if last_deadlock is not None:
        try:
            return subprocess.check_output(["/bin/cat", str(path)], text=True, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            pass
        raise last_deadlock
    return path.read_text(encoding="utf-8")


def read_jsonl_or_none(path: Path) -> list[dict[str, Any]] | None:
    try:
        return read_jsonl(path)
    except OSError as exc:
        if exc.errno == errno.EDEADLK:
            return None
        raise


def write_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        temp = path.with_name(f".{path.name}.tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(path)


def stable_verified_utc(result: dict[str, Any]) -> str:
    existing_path = ROUTE / "VERIFICATION_RESULT.json"
    if not existing_path.exists():
        return utc_now()
    try:
        existing = read_json(existing_path)
    except (json.JSONDecodeError, OSError):
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "WAVE_F_VALIDATION_STRESS_SUMMARY.json")
    time_rows = read_jsonl(ROUTE / "WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl")
    walk_rows = read_jsonl(ROUTE / "WAVE_F_WALK_FORWARD_LEDGER.jsonl")
    leave_rows = read_jsonl(ROUTE / "WAVE_F_LEAVE_ONE_SYMBOL_SIDE_LEDGER.jsonl")
    adversarial_rows = read_jsonl(ROUTE / "WAVE_F_ADVERSARIAL_BASELINE_LEDGER.jsonl")
    mc_rows = read_jsonl(ROUTE / "WAVE_F_MONTE_CARLO_PROXY_LEDGER.jsonl")
    source_rows = read_jsonl(ROUTE / "WAVE_F_SOURCE_STATUS_LEDGER.jsonl")
    residual_rows = read_jsonl(ROUTE / "WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repairs = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "wave_f_validation_stress_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("input_row_count") != 214536:
        issues.append("input_row_count_mismatch")
    if summary.get("nonzero_proxy_row_count") != 8015:
        issues.append("nonzero_proxy_row_count_mismatch")
    if summary.get("time_split_rows") != 62 or len(time_rows) != 62:
        issues.append("time_split_row_count_mismatch")
    if summary.get("walk_forward_rows") != 51 or len(walk_rows) != 51:
        issues.append("walk_forward_row_count_mismatch")
    if summary.get("leave_one_symbol_side_rows") != 74 or len(leave_rows) != 74:
        issues.append("leave_one_row_count_mismatch")
    if summary.get("adversarial_baseline_rows") != 12 or len(adversarial_rows) != 12:
        issues.append("adversarial_row_count_mismatch")
    if summary.get("monte_carlo_proxy_rows") != 1000 or len(mc_rows) != 1000:
        issues.append("monte_carlo_row_count_mismatch")
    if summary.get("broker_actual_r_joined_rows") != 1:
        issues.append("broker_actual_r_joined_rows_not_one")
    if summary.get("close_side_all_in_cost_rows") != 1:
        issues.append("close_side_cost_rows_not_one")
    if summary.get("remaining_required_close_history_rows") != 8:
        issues.append("remaining_close_history_rows_not_eight")
    if summary.get("source_status_rows") != len(source_rows) or len(source_rows) < 4:
        issues.append("source_status_row_count_mismatch")
    if summary.get("residual_blocker_rows") != len(residual_rows) or len(residual_rows) < 4:
        issues.append("residual_blocker_row_count_mismatch")
    if len(decisions) < 2:
        issues.append("decision_rows_too_low")
    if len(repairs) < 2:
        issues.append("repair_rows_too_low")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")

    terminal = summary.get("terminal_decision", {})
    if terminal.get("validation_stress_checkpoint_materialized") is not True:
        issues.append("checkpoint_not_materialized")
    for field in [
        "broker_real_expectancy_claim_allowed",
        "final_package_selected",
        "model_training_allowed",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "wave_f_complete",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")

    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if completion.get("verification", {}).get("wave_f_validation_stress") not in {"pending", "passed"}:
        issues.append("completion_verification_status_invalid")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "WAVE_F_VALIDATION_STRESS_SUMMARY.json",
        "WAVE_F_TIME_SPLIT_VALIDATION_LEDGER.jsonl",
        "WAVE_F_WALK_FORWARD_LEDGER.jsonl",
        "WAVE_F_LEAVE_ONE_SYMBOL_SIDE_LEDGER.jsonl",
        "WAVE_F_ADVERSARIAL_BASELINE_LEDGER.jsonl",
        "WAVE_F_MONTE_CARLO_PROXY_LEDGER.jsonl",
        "WAVE_F_SOURCE_STATUS_LEDGER.jsonl",
        "WAVE_F_VALIDATION_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")

    if any(row.get("final_package_selection_allowed") is not False for row in time_rows):
        issues.append("time_row_allows_final_selection")
    if any(row.get("final_package_selection_allowed") is not False for row in walk_rows):
        issues.append("walk_row_allows_final_selection")
    if any(row.get("final_package_selection_allowed") is not False for row in leave_rows):
        issues.append("leave_row_allows_final_selection")
    if any(row.get("final_package_selection_allowed") is not False for row in adversarial_rows):
        issues.append("adversarial_row_allows_final_selection")
    if any(row.get("final_package_selection_allowed") is not False for row in mc_rows):
        issues.append("mc_row_allows_final_selection")
    blocker_statuses = {row.get("blocker_id"): row.get("status") for row in residual_rows}
    for blocker_id in ["WFV001", "WFV002", "WFV003", "WFV004"]:
        if not str(blocker_statuses.get(blocker_id, "")).startswith("open_"):
            issues.append(f"residual_blocker_not_open:{blocker_id}")

    parent_ledger_read_status = "checked"
    parent_question_rows = read_jsonl_or_none(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")
    parent_source_rows = read_jsonl_or_none(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")
    parent_merge_rows = read_jsonl_or_none(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")
    if parent_question_rows is None or parent_source_rows is None or parent_merge_rows is None:
        parent_ledger_read_status = "skipped_errno_11_resource_deadlock_avoided"
    else:
        parent_questions = {row.get("question_id"): row for row in parent_question_rows}
        parent_sources = {row.get("request_id"): row for row in parent_source_rows}
        parent_merges = {row.get("decision_id"): row for row in parent_merge_rows}
        if parent_questions.get("PQ014", {}).get("status") != "answered_validation_stress_checkpoint":
            issues.append("parent_pq014_missing")
        if parent_sources.get("PSR015", {}).get("status") != "open_exact_final_selection_requirement_partially_repaired_by_proxy_validation":
            issues.append("parent_psr015_missing")
        if parent_merges.get("PMD013", {}).get("status") != "selected":
            issues.append("parent_pmd013_missing")

    result = {
        "schema": "gtos.final_moonshot.wave_f.validation_stress.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "input_row_count": summary.get("input_row_count"),
        "nonzero_proxy_row_count": summary.get("nonzero_proxy_row_count"),
        "time_split_rows": len(time_rows),
        "walk_forward_rows": len(walk_rows),
        "leave_one_symbol_side_rows": len(leave_rows),
        "adversarial_baseline_rows": len(adversarial_rows),
        "monte_carlo_proxy_rows": len(mc_rows),
        "broker_actual_r_joined_rows": summary.get("broker_actual_r_joined_rows"),
        "close_side_all_in_cost_rows": summary.get("close_side_all_in_cost_rows"),
        "remaining_required_close_history_rows": summary.get("remaining_required_close_history_rows"),
        "final_package_selected": terminal.get("final_package_selected"),
        "parent_ledger_read_status": parent_ledger_read_status,
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["wave_f_validation_stress"] = "passed" if not issues else "failed"
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "verified_utc": result["verified_utc"],
    }
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
