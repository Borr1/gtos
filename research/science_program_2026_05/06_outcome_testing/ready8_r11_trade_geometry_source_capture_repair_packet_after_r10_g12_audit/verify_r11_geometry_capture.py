"""Verify R11 READY8 trade-geometry source-capture repair packet artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_r11_geometry_capture as builder


DATE = builder.DATE
ROUTE_DIR = Path(__file__).resolve().parent


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
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())


def check_safe(record: dict[str, Any], label: str, errors: list[str]) -> None:
    for key, expected in builder.SAFE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")
    for key, expected in builder.FORBIDDEN_FALSE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")


def expected_files() -> list[str]:
    return [
        "build_r11_geometry_capture.py",
        "verify_r11_geometry_capture.py",
        "test_r11_geometry_capture.py",
        f"R11_CONTEXT_ANCHOR_{DATE}.json",
        f"R11_ROW_UNIVERSE_RECONCILIATION_{DATE}.json",
        f"R11_SOURCE_ROOT_EXPANSION_LEDGER_{DATE}.jsonl",
        f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl",
        f"R11_REPAIRED_GEOMETRY_RESULT_LEDGER_{DATE}.jsonl",
        f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl",
        f"R11_CAPTURE_SCHEMA_CONTRACT_{DATE}.json",
        f"R11_FORWARD_RETEST_EXECUTION_PACKET_{DATE}.jsonl",
        f"R11_FAILURE_INTELLIGENCE_PRESERVATION_LEDGER_{DATE}.jsonl",
        f"R11_QUESTION_AMBIGUITY_DOOR_LEDGER_{DATE}.jsonl",
        f"R11_DECISION_LEDGER_{DATE}.json",
        f"R11_COMPLETION_AUDIT_{DATE}.json",
        f"R11_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"R11_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"R11_METRIC_SUMMARY_{DATE}.json",
        f"R11_SOURCE_HASH_LEDGER_{DATE}.json",
        f"R11_OUTPUT_MANIFEST_{DATE}.json",
        f"R11_VERIFICATION_RESULT_{DATE}.json",
        f"R11_SYNTHESIS_{DATE}.md",
        f"G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md",
        f"G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_STARTER_{DATE}.txt",
    ]


def verify(
    *,
    update: bool = False,
    focused_tests_ok: bool = False,
    focused_tests_summary: str | None = None,
    artifact_audit_ok: bool | None = None,
    artifact_audit_summary: str | None = None,
    prompt_hardening_ok: bool | None = None,
    starter_hardening_ok: bool | None = None,
    require_focused_tests: bool = True,
    require_artifact_audit: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    missing = [name for name in expected_files() if not route_file(name).exists()]
    checks["expected_files_exist"] = not missing
    if missing:
        errors.append(f"missing expected files: {missing}")

    source_rows = list(iter_jsonl(route_file(f"R11_SOURCE_ROOT_EXPANSION_LEDGER_{DATE}.jsonl")))
    binding_rows = list(iter_jsonl(route_file(f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl")))
    repaired_rows = list(iter_jsonl(route_file(f"R11_REPAIRED_GEOMETRY_RESULT_LEDGER_{DATE}.jsonl")))
    capture_rows = list(iter_jsonl(route_file(f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl")))
    forward_rows = list(iter_jsonl(route_file(f"R11_FORWARD_RETEST_EXECUTION_PACKET_{DATE}.jsonl")))
    failure_rows = list(iter_jsonl(route_file(f"R11_FAILURE_INTELLIGENCE_PRESERVATION_LEDGER_{DATE}.jsonl")))
    question_rows = list(iter_jsonl(route_file(f"R11_QUESTION_AMBIGUITY_DOOR_LEDGER_{DATE}.jsonl")))

    source_type_counts = Counter(row.get("source_row_type") for row in binding_rows)
    weak_rows = sum(1 for row in binding_rows if row.get("weak_shadow_or_live_symbol_time_match_count"))
    root_counts_per_row = Counter(len(row.get("all_source_roots_searched", [])) for row in binding_rows)
    exact_r_rows = sum(1 for row in repaired_rows if row.get("exact_r_expectancy_computed") is True)
    target_hit_rows = sum(1 for row in repaired_rows if row.get("target_hit") is not None or row.get("stop_hit") is not None)

    checks.update(
        {
            "source_root_count": len(source_rows),
            "binding_row_count": len(binding_rows),
            "repaired_result_row_count": len(repaired_rows),
            "capture_requirement_row_count": len(capture_rows),
            "forward_packet_row_count": len(forward_rows),
            "failure_intelligence_row_count": len(failure_rows),
            "question_door_row_count": len(question_rows),
            "source_type_counts": dict(source_type_counts),
            "weak_shadow_symbol_time_matched_rows": weak_rows,
            "root_counts_per_row": dict(root_counts_per_row),
            "exact_r_rows": exact_r_rows,
            "target_or_stop_hit_rows": target_hit_rows,
        }
    )
    if len(source_rows) < 50:
        errors.append(f"source roots {len(source_rows)} < expected expanded minimum 50")
    if len(binding_rows) != 5502:
        errors.append(f"binding rows {len(binding_rows)} != 5502")
    if len(repaired_rows) != 5502:
        errors.append(f"repaired result rows {len(repaired_rows)} != 5502")
    if len(capture_rows) != 5502:
        errors.append(f"capture requirement rows {len(capture_rows)} != 5502")
    if len(forward_rows) != 5502:
        errors.append(f"forward packet rows {len(forward_rows)} != 5502")
    if len(failure_rows) != 2641:
        errors.append(f"failure intelligence rows {len(failure_rows)} != 2641")
    if source_type_counts.get("packet_row", 0) != 182:
        errors.append(f"packet rows {source_type_counts.get('packet_row', 0)} != 182")
    if source_type_counts.get("repaired_target_row", 0) != 5320:
        errors.append(f"repaired target rows {source_type_counts.get('repaired_target_row', 0)} != 5320")
    if len(root_counts_per_row) != 1 or next(iter(root_counts_per_row or {0: 0})) != len(source_rows):
        errors.append("not every binding row lists every source root")
    if weak_rows <= 0:
        errors.append("expanded shadow search did not preserve any weak symbol-time geometry matches")
    if exact_r_rows != 0:
        errors.append(f"exact R rows computed {exact_r_rows} != 0")
    if target_hit_rows != 0:
        errors.append(f"target/stop hit rows {target_hit_rows} != 0")

    for path in ROUTE_DIR.glob("R11_*.jsonl"):
        for row in iter_jsonl(path):
            check_safe(row, f"{path.name}:{row['_source_line_number']}", errors)
    for name in [
        f"R11_CONTEXT_ANCHOR_{DATE}.json",
        f"R11_ROW_UNIVERSE_RECONCILIATION_{DATE}.json",
        f"R11_CAPTURE_SCHEMA_CONTRACT_{DATE}.json",
        f"R11_DECISION_LEDGER_{DATE}.json",
        f"R11_COMPLETION_AUDIT_{DATE}.json",
        f"R11_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"R11_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"R11_METRIC_SUMMARY_{DATE}.json",
        f"R11_SOURCE_HASH_LEDGER_{DATE}.json",
        f"R11_OUTPUT_MANIFEST_{DATE}.json",
    ]:
        check_safe(read_json(route_file(name)), name, errors)

    row_universe = read_json(route_file(f"R11_ROW_UNIVERSE_RECONCILIATION_{DATE}.json"))
    decision = read_json(route_file(f"R11_DECISION_LEDGER_{DATE}.json"))
    completion = read_json(route_file(f"R11_COMPLETION_AUDIT_{DATE}.json"))
    instruction = read_json(route_file(f"R11_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json"))
    metrics = read_json(route_file(f"R11_METRIC_SUMMARY_{DATE}.json"))
    manifest = read_json(route_file(f"R11_OUTPUT_MANIFEST_{DATE}.json"))

    checks["row_universe_counts_match"] = row_universe.get("all_counts_match") is True
    checks["terminal_decision_ok"] = decision.get("terminal_decision") == builder.TERMINAL_DECISION
    checks["completion_standard_met"] = completion.get("completion_standard_met") is True
    checks["same_class_remaining_zero"] = completion.get("same_evidence_class_repairable_intelligence_remaining") == 0
    checks["instruction_coverage_ok"] = instruction.get("all_requirements_satisfied") is True
    checks["metrics_exact_r_zero"] = metrics.get("exact_r_expectancy_rows_computed") == 0
    checks["metrics_target_stop_zero"] = metrics.get("target_stop_hit_miss_rows_computed") == 0
    checks["metrics_ambiguous_5502"] = metrics.get("target_stop_ambiguous_rows") == 5502
    checks["manifest_files_present"] = len(manifest.get("files", [])) >= 20

    for key, ok in [
        ("row_universe_counts_match", checks["row_universe_counts_match"]),
        ("terminal_decision_ok", checks["terminal_decision_ok"]),
        ("completion_standard_met", checks["completion_standard_met"]),
        ("same_class_remaining_zero", checks["same_class_remaining_zero"]),
        ("instruction_coverage_ok", checks["instruction_coverage_ok"]),
        ("metrics_exact_r_zero", checks["metrics_exact_r_zero"]),
        ("metrics_target_stop_zero", checks["metrics_target_stop_zero"]),
        ("metrics_ambiguous_5502", checks["metrics_ambiguous_5502"]),
        ("manifest_files_present", checks["manifest_files_present"]),
    ]:
        if not ok:
            errors.append(f"{key} failed")

    if require_focused_tests and not focused_tests_ok:
        errors.append("focused tests not recorded as passed")
    if require_artifact_audit and artifact_audit_ok is not True:
        errors.append("artifact audit not recorded as passed")
    if prompt_hardening_ok is not True:
        errors.append("emitted G12 prompt hardening not recorded as passed")
    if starter_hardening_ok is not True:
        errors.append("emitted G12 starter hardening not recorded as passed")
    checks["focused_tests_ok"] = focused_tests_ok
    checks["focused_tests_summary"] = focused_tests_summary
    checks["artifact_audit_ok"] = artifact_audit_ok
    checks["artifact_audit_summary"] = artifact_audit_summary
    checks["prompt_hardening_ok"] = prompt_hardening_ok
    checks["starter_hardening_ok"] = starter_hardening_ok

    result = {
        **builder.safe_base(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
    if update:
        builder.write_json(route_file(f"R11_VERIFICATION_RESULT_{DATE}.json"), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary")
    parser.add_argument("--mark-artifact-audit-ok", action="store_true")
    parser.add_argument("--artifact-audit-summary")
    parser.add_argument("--mark-prompt-hardening-ok", action="store_true")
    parser.add_argument("--mark-starter-hardening-ok", action="store_true")
    parser.add_argument("--no-require-focused-tests", action="store_true")
    parser.add_argument("--no-require-artifact-audit", action="store_true")
    args = parser.parse_args()
    result = verify(
        update=args.update,
        focused_tests_ok=args.mark_focused_tests_ok,
        focused_tests_summary=args.focused_tests_summary,
        artifact_audit_ok=True if args.mark_artifact_audit_ok else None,
        artifact_audit_summary=args.artifact_audit_summary,
        prompt_hardening_ok=True if args.mark_prompt_hardening_ok else None,
        starter_hardening_ok=True if args.mark_starter_hardening_ok else None,
        require_focused_tests=not args.no_require_focused_tests,
        require_artifact_audit=not args.no_require_artifact_audit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
