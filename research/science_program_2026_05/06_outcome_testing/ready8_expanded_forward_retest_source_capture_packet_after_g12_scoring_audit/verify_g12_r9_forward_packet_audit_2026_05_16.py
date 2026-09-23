"""Verify G12 READY8 R9 packet audit artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_g12_r9_forward_packet_audit_2026_05_16 as builder


DATE = builder.DATE
ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def check_safe_flags(record: dict[str, Any], label: str, errors: list[str]) -> None:
    for key, expected in builder.SAFE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")
    for key, expected in builder.FORBIDDEN_FALSE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")


def required_files() -> list[str]:
    return [
        f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_COMPLETION_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_R9_MANIFEST_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl",
        f"G12_R9_PACKET_AUDIT_SOURCE_HASH_{DATE}.json",
        f"G12_R9_PACKET_AUDIT_SYNTHESIS_{DATE}.md",
        "build_g12_r9_forward_packet_audit_2026_05_16.py",
        "verify_g12_r9_forward_packet_audit_2026_05_16.py",
        "test_g12_r9_forward_packet_audit_2026_05_16.py",
    ]


def verify(mark_focused_tests_ok: bool = False, focused_tests_summary: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}

    missing = [name for name in required_files() if not route_file(name).exists()]
    if missing:
        errors.append(f"missing required G12 R9 audit files: {missing}")
    checks["required_files_exist"] = not missing

    expected_counts = {
        "material_rows": 10668,
        "json_artifacts": 20,
        "packet_coverage": 182,
        "failure_intel": 2641,
        "repaired_target": 5320,
        "blockers": 22,
        "sequence": 182,
        "source_drift": 74,
        "r9_manifest": 41,
    }
    count_files = {
        "material_rows": f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl",
        "json_artifacts": f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl",
        "packet_coverage": f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl",
        "failure_intel": f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl",
        "repaired_target": f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl",
        "blockers": f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl",
        "sequence": f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl",
        "source_drift": f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl",
        "r9_manifest": f"G12_R9_PACKET_AUDIT_R9_MANIFEST_{DATE}.jsonl",
    }
    counts = {key: count_jsonl(route_file(name)) for key, name in count_files.items() if route_file(name).exists()}
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"{key} count {counts.get(key)} != {expected}")
    checks["audit_row_counts"] = counts
    checks["audit_row_counts_match_expected"] = all(counts.get(key) == expected for key, expected in expected_counts.items())

    decision = read_json(route_file(f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json"))
    completion = read_json(route_file(f"G12_R9_PACKET_AUDIT_COMPLETION_{DATE}.json"))
    recomputation = read_json(route_file(f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json"))
    source_hash = read_json(route_file(f"G12_R9_PACKET_AUDIT_SOURCE_HASH_{DATE}.json"))
    instruction = read_json(route_file(f"G12_R9_PACKET_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json"))
    for label, doc in [
        ("decision", decision),
        ("completion", completion),
        ("recomputation", recomputation),
        ("source_hash", source_hash),
        ("instruction_coverage", instruction),
    ]:
        check_safe_flags(doc, label, errors)

    checks["terminal_decision_ok"] = decision.get("terminal_decision") == builder.ACCEPT_DECISION
    if not checks["terminal_decision_ok"]:
        errors.append(f"terminal decision is {decision.get('terminal_decision')}")
    checks["completion_standard_met"] = completion.get("completion_standard_met") is True
    if not checks["completion_standard_met"]:
        errors.append("completion standard is not met")
    checks["same_g12_issue_count"] = completion.get("same_g12_issue_count")
    if completion.get("same_g12_issue_count") != 0:
        errors.append(f"same_g12_issue_count={completion.get('same_g12_issue_count')}")
    checks["recomputation_issue_count"] = len(recomputation.get("all_issues", []))
    if recomputation.get("all_issues"):
        errors.append("recomputation ledger has issues")

    bad_packet = [
        row["packet_row_id"]
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"))
        if row.get("audit_status") != "PACKET_ROW_FULLY_COVERED_AND_R8_G12_TRACEABLE"
    ]
    checks["packet_coverage_all_ok"] = not bad_packet
    if bad_packet:
        errors.append(f"packet coverage failures: {bad_packet[:10]}")

    bad_failure = [
        row.get("source_line_number")
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl"))
        if row.get("audit_status") != "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED"
    ]
    checks["failure_intelligence_preserved"] = not bad_failure
    if bad_failure:
        errors.append(f"failure-intelligence weak rows: {bad_failure[:10]}")

    bad_repaired = [
        row.get("source_line_number")
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl"))
        if row.get("audit_status") != "REPAIRED_TARGET_CONSUMPTION_VERIFIED"
    ]
    checks["repaired_target_consumption_verified"] = not bad_repaired
    if bad_repaired:
        errors.append(f"repaired target weak rows: {bad_repaired[:10]}")

    bad_blockers = [
        row.get("source_line_number")
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl"))
        if row.get("audit_status") != "BLOCKER_EXACTLY_BOUNDED_OR_REPAIRED"
    ]
    checks["blockers_exact_or_repaired"] = not bad_blockers
    if bad_blockers:
        errors.append(f"blocker weak rows: {bad_blockers[:10]}")

    bad_sequence = [
        row.get("packet_row_id")
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl"))
        if row.get("audit_status") != "PACKET_SEQUENCE_BOUNDARY_VERIFIED"
    ]
    checks["sequence_rows_verified"] = not bad_sequence
    if bad_sequence:
        errors.append(f"sequence weak rows: {bad_sequence[:10]}")

    real_drift = [
        row["source_path"]
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"))
        if row.get("blocking") is True
    ]
    checks["real_immutable_source_drift_count"] = len(real_drift)
    if real_drift:
        errors.append(f"real immutable source drift: {real_drift[:10]}")

    manifest_bad = [
        row.get("manifest_path")
        for row in iter_jsonl(route_file(f"G12_R9_PACKET_AUDIT_R9_MANIFEST_{DATE}.jsonl"))
        if row.get("audit_status") != "R9_MANIFEST_HASH_MATCH"
    ]
    checks["r9_manifest_hashes_match"] = not manifest_bad
    if manifest_bad:
        errors.append(f"R9 manifest hash mismatch: {manifest_bad[:10]}")

    manifest = read_json(route_file(f"G12_R9_PACKET_AUDIT_OUTPUT_MANIFEST_{DATE}.json"))
    check_safe_flags(manifest, "output_manifest", errors)
    manifest_errors: list[str] = []
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if not path.exists():
            manifest_errors.append(f"manifest path missing {item['path']}")
            continue
        current = builder.sha256_file(path)
        if current != item["sha256"]:
            if not item["path"].endswith(
                (
                    f"G12_R9_PACKET_AUDIT_VERIFICATION_RESULT_{DATE}.json",
                    f"G12_R9_PACKET_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json",
                )
            ):
                manifest_errors.append(f"manifest hash drift {item['path']}")
    checks["output_manifest_hashes_match_before_refresh"] = not manifest_errors
    errors.extend(manifest_errors)

    source_hash_errors: list[str] = []
    source_hash_warnings: list[str] = []
    for source in source_hash.get("sources", []):
        path = ROOT / source["path"]
        if not path.exists():
            source_hash_errors.append(f"missing source {source['path']}")
            continue
        current_raw = builder.sha256_file(path)
        current_lf = builder.sha256_file_canonical_lf(path)
        expected_hashes = {source.get("sha256"), source.get("sha256_canonical_lf")}
        if current_raw not in expected_hashes and current_lf not in expected_hashes:
            if source["path"] in builder.MUTABLE_COORDINATION_PATHS:
                source_hash_warnings.append(source["path"])
            else:
                source_hash_errors.append(f"source hash drift {source['path']}")
    checks["g12_source_hashes_match_current_disk"] = not source_hash_errors
    checks["g12_mutable_coordination_source_hash_drift_paths"] = source_hash_warnings
    errors.extend(source_hash_errors)

    jsonl_rows_checked = 0
    for path in ROUTE_DIR.glob(f"G12_R9_PACKET_AUDIT_*_{DATE}.jsonl"):
        for idx, row in enumerate(iter_jsonl(path), 1):
            check_safe_flags(row, f"{path.name}:{idx}", errors)
            jsonl_rows_checked += 1
    checks["g12_jsonl_safe_rows_checked"] = jsonl_rows_checked

    if mark_focused_tests_ok:
        focused = {
            **builder.safe_base(),
            "generated_at_utc": builder.utc_now(),
            "focused_tests_ok": True,
            "status": "PASSED",
            "command": f"py -3 -m pytest {rel(ROUTE_DIR / 'test_g12_r9_forward_packet_audit_2026_05_16.py')} -q",
            "summary": focused_tests_summary or "focused pytest passed",
        }
        builder.write_json(route_file(f"G12_R9_PACKET_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json"), focused)
    elif route_file(f"G12_R9_PACKET_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json").exists():
        focused = read_json(route_file(f"G12_R9_PACKET_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json"))
        checks["focused_tests_ok"] = bool(focused.get("focused_tests_ok"))
    else:
        checks["focused_tests_ok"] = False

    result = {
        **builder.safe_base(),
        "generated_at_utc": builder.utc_now(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "checks": checks,
        "errors": errors,
    }
    builder.write_json(route_file(f"G12_R9_PACKET_AUDIT_VERIFICATION_RESULT_{DATE}.json"), result)
    builder.write_output_manifest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary", default=None)
    args = parser.parse_args()
    result = verify(args.mark_focused_tests_ok, args.focused_tests_summary)
    print(json.dumps({"ok": result["ok"], "can_mark_goal_complete": result["can_mark_goal_complete"], "errors": result["errors"]}, indent=2))
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
