"""Verify READY8 R10 sealed historical validation execution artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import build_ready8_r9_sealed_historical_validation_execution_2026_05_16 as builder


DATE = builder.DATE
ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_number"] = line_number
                yield row


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def check_safe(record: dict[str, Any], label: str, errors: list[str]) -> None:
    for key, expected in builder.SAFE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")
    for key, expected in builder.FORBIDDEN_FALSE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")


def expected_files() -> list[str]:
    return [
        ".gitattributes",
        "build_ready8_r9_sealed_historical_validation_execution_2026_05_16.py",
        "verify_ready8_r9_sealed_historical_validation_execution_2026_05_16.py",
        "test_ready8_r9_sealed_historical_validation_execution_2026_05_16.py",
        f"R10_CONTEXT_ANCHOR_{DATE}.json",
        f"R10_PREREQUISITE_ACCEPTANCE_G12_PROVENANCE_LEDGER_{DATE}.json",
        f"R10_SOURCE_HASH_LEDGER_{DATE}.json",
        f"R10_SOURCE_DRIFT_LEDGER_{DATE}.jsonl",
        f"R10_PARTITION_FREEZE_LEDGER_{DATE}.jsonl",
        f"R10_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json",
        f"R10_DUPLICATE_DENOMINATOR_EFFECTIVE_N_POLICY_{DATE}.json",
        f"R10_CONTROL_PLACEBO_GENERIC_MOVEMENT_ADJUSTMENT_POLICY_{DATE}.json",
        f"R10_FAIL_CLOSED_SOURCE_CAPTURE_POLICY_{DATE}.json",
        f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl",
        f"R10_SEALED_HISTORICAL_PRIMARY_VALIDATION_LEDGER_{DATE}.jsonl",
        f"R10_STRESS_ROBUSTNESS_LEDGER_{DATE}.jsonl",
        f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl",
        f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl",
        f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl",
        f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl",
        f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl",
        f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl",
        f"R10_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
        f"R10_REPAIRED_TARGET_CARRY_FORWARD_LEDGER_{DATE}.jsonl",
        f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl",
        f"R10_REPAIRED_TARGET_SPLIT_METRIC_SUMMARY_LEDGER_{DATE}.jsonl",
        f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
        f"R10_DUPLICATE_CONCENTRATION_EFFECTIVE_N_LEDGER_{DATE}.jsonl",
        f"R10_FAIL_CLOSED_ATTRITION_REPAIR_SENSITIVITY_LEDGER_{DATE}.jsonl",
        f"R10_QUESTION_AMBIGUITY_LEDGER_{DATE}.jsonl",
        f"R10_OPEN_CLOSED_DOOR_LEDGER_{DATE}.jsonl",
        f"R10_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
        f"R10_SOURCE_ROOT_SEARCHED_ROOT_LEDGER_{DATE}.jsonl",
        f"R10_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"R10_DECISION_LEDGER_{DATE}.json",
        f"R10_COMPLETION_AUDIT_{DATE}.json",
        f"R10_FOCUSED_TEST_RESULT_{DATE}.json",
        f"R10_VERIFICATION_RESULT_{DATE}.json",
        f"R10_SYNTHESIS_{DATE}.md",
        f"R10_OUTPUT_MANIFEST_{DATE}.json",
        f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md",
        f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_STARTER_{DATE}.txt",
    ]


def verify(
    update: bool = False,
    focused_tests_ok: bool = False,
    focused_tests_summary: str | None = None,
    artifact_audit_ok: bool | None = None,
    artifact_audit_summary: str | None = None,
    require_focused_tests: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    missing = [name for name in expected_files() if not route_file(name).exists()]
    if missing:
        errors.append(f"missing expected files: {missing}")
    checks["expected_files_exist"] = not missing

    count_names = {
        "partition": f"R10_PARTITION_FREEZE_LEDGER_{DATE}.jsonl",
        "admission": f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl",
        "haz001": f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl",
        "mac": f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl",
        "haz005": f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl",
        "unc004": f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl",
        "residual": f"R10_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
        "repaired_carry": f"R10_REPAIRED_TARGET_CARRY_FORWARD_LEDGER_{DATE}.jsonl",
        "repaired_neutral": f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl",
        "failure_intel": f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
        "geometry": f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl",
        "target_stop": f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl",
        "question": f"R10_QUESTION_AMBIGUITY_LEDGER_{DATE}.jsonl",
        "doors": f"R10_OPEN_CLOSED_DOOR_LEDGER_{DATE}.jsonl",
        "blockers": f"R10_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
    }
    counts = {key: count_jsonl(route_file(name)) for key, name in count_names.items() if route_file(name).exists()}
    expected_counts = {
        "partition": 182,
        "admission": 182,
        "haz001": 143,
        "mac": 32,
        "haz005": 5,
        "unc004": 1154,
        "residual": 1,
        "repaired_carry": 5320,
        "repaired_neutral": 5320,
        "failure_intel": 2641,
        "geometry": 5502,
        "target_stop": 5502,
        "question": 182,
        "doors": 364,
        "blockers": 22,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"{key} row count {counts.get(key)} != {expected}")
    checks["row_counts"] = counts
    checks["row_counts_match_expected"] = all(counts.get(key) == value for key, value in expected_counts.items())

    decision = read_json(route_file(f"R10_DECISION_LEDGER_{DATE}.json"))
    completion = read_json(route_file(f"R10_COMPLETION_AUDIT_{DATE}.json"))
    instruction = read_json(route_file(f"R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json"))
    source_hash = read_json(route_file(f"R10_SOURCE_HASH_LEDGER_{DATE}.json"))
    for label, artifact in [
        ("decision", decision),
        ("completion", completion),
        ("instruction", instruction),
        ("source_hash", source_hash),
    ]:
        check_safe(artifact, label, errors)

    checks["terminal_decision_ok"] = decision.get("terminal_decision") == builder.TERMINAL_DECISION
    if not checks["terminal_decision_ok"]:
        errors.append(f"terminal decision mismatch: {decision.get('terminal_decision')!r}")
    checks["completion_standard_met"] = completion.get("completion_standard_met") is True
    checks["same_evidence_class_remaining_zero"] = (
        completion.get("same_evidence_class_intelligence_remaining") == 0
    )
    checks["instruction_coverage_ok"] = instruction.get("all_requirements_satisfied") is True
    if not checks["completion_standard_met"]:
        errors.append("completion audit does not mark completion_standard_met=true")
    if not checks["same_evidence_class_remaining_zero"]:
        errors.append("same_evidence_class_intelligence_remaining is not zero")
    if not checks["instruction_coverage_ok"]:
        errors.append("instruction coverage does not mark all requirements satisfied")

    real_drift = source_hash.get("real_immutable_source_drift_count")
    checks["real_immutable_source_drift_count"] = real_drift
    if real_drift != 0:
        errors.append(f"real immutable source drift count is {real_drift}")

    jsonl_safe_rows_checked = 0
    invalid_status_rows = 0
    for path in ROUTE_DIR.glob("R10_*.jsonl"):
        for row in iter_jsonl(path):
            check_safe(row, f"{path.name}:{row['_source_line_number']}", errors)
            for status in row.get("execution_statuses", []):
                if status not in builder.EXECUTION_STATUSES:
                    invalid_status_rows += 1
            jsonl_safe_rows_checked += 1
    checks["jsonl_safe_rows_checked"] = jsonl_safe_rows_checked
    checks["invalid_execution_status_rows"] = invalid_status_rows
    if invalid_status_rows:
        errors.append(f"invalid execution status rows: {invalid_status_rows}")

    admission_statuses = Counter()
    for row in iter_jsonl(route_file(f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl")):
        for status in row.get("execution_statuses", []):
            admission_statuses[status] += 1
    checks["admission_execution_status_counts"] = dict(admission_statuses)
    for required_status in [
        "SEALED_HISTORICAL_VALIDATION_EXECUTABLE",
        "STRESS_ROBUSTNESS_EXECUTABLE",
        "FORWARD_SHADOW_CAPTURE_REQUIRED",
        "SOURCE_CONTROL_ONLY",
        "INVERSE_AVOID_FILTER_DIAGNOSTIC_ONLY",
        "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE_ONLY",
    ]:
        if admission_statuses.get(required_status, 0) == 0:
            errors.append(f"missing execution status coverage: {required_status}")

    neutral_numeric = sum(
        1
        for row in iter_jsonl(route_file(f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl"))
        if row.get("neutral_metric_status") == "SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_COMPUTED"
    )
    checks["repaired_target_neutral_metric_computed_rows"] = neutral_numeric
    if neutral_numeric != 5320:
        errors.append(f"repaired target neutral movement computed rows {neutral_numeric} != 5320")

    ambiguous_target_stop = sum(
        1
        for row in iter_jsonl(route_file(f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl"))
        if row.get("hit_miss_ambiguous_fail_closed") == "AMBIGUOUS"
    )
    checks["target_stop_ambiguous_rows"] = ambiguous_target_stop
    if ambiguous_target_stop != 5502:
        errors.append(f"target/stop ambiguous rows {ambiguous_target_stop} != 5502")

    if require_focused_tests and not focused_tests_ok:
        errors.append("focused tests not recorded as passed")
    checks["focused_tests_ok"] = focused_tests_ok
    checks["focused_tests_summary"] = focused_tests_summary
    checks["artifact_audit_ok"] = artifact_audit_ok
    checks["artifact_audit_summary"] = artifact_audit_summary

    result = {
        **builder.safe_base(),
        "generated_at_utc": builder.utc_now(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    if update:
        if focused_tests_ok:
            builder.write_json(
                route_file(f"R10_FOCUSED_TEST_RESULT_{DATE}.json"),
                {
                    **builder.safe_base(),
                    "generated_at_utc": builder.utc_now(),
                    "ok": True,
                    "summary": focused_tests_summary or "focused tests passed",
                },
            )
        builder.write_json(route_file(f"R10_VERIFICATION_RESULT_{DATE}.json"), result)
        builder.write_json(route_file(f"R10_OUTPUT_MANIFEST_{DATE}.json"), builder.output_manifest())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary")
    parser.add_argument("--artifact-audit-ok", action="store_true")
    parser.add_argument("--artifact-audit-summary")
    parser.add_argument("--no-require-focused-tests", action="store_true")
    args = parser.parse_args()
    result = verify(
        update=args.update,
        focused_tests_ok=args.focused_tests_ok,
        focused_tests_summary=args.focused_tests_summary,
        artifact_audit_ok=args.artifact_audit_ok if args.artifact_audit_ok else None,
        artifact_audit_summary=args.artifact_audit_summary,
        require_focused_tests=not args.no_require_focused_tests,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
