"""Verify READY8 R9 forward-retest/source-capture packet artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_r9_forward_packet_2026_05_16 as builder


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
        "build_r9_forward_packet_2026_05_16.py",
        "verify_r9_forward_packet_2026_05_16.py",
        "test_r9_forward_packet_2026_05_16.py",
        f"R9_CONTEXT_{DATE}.json",
        f"R9_G12_PROVENANCE_{DATE}.json",
        f"R9_SOURCE_ROOTS_{DATE}.jsonl",
        f"R9_SOURCE_HASH_{DATE}.json",
        f"R9_METHOD_{DATE}.json",
        f"R9_NO_LEAK_POLICY_{DATE}.json",
        f"R9_PARTITION_POLICY_{DATE}.json",
        f"R9_DUP_EFFECTIVE_N_POLICY_{DATE}.json",
        f"R9_CONTROL_POLICY_{DATE}.json",
        f"R9_CONCENTRATION_POLICY_{DATE}.json",
        f"R9_FAIL_CLOSED_POLICY_{DATE}.json",
        f"R9_ROW_IDENTITY_{DATE}.jsonl",
        f"R9_HAZ001_PACKET_{DATE}.jsonl",
        f"R9_MAC_PACKET_{DATE}.jsonl",
        f"R9_HAZ005_PACKET_{DATE}.jsonl",
        f"R9_UNC004_CONTRACT_{DATE}.jsonl",
        f"R9_RESIDUAL_PACKET_{DATE}.jsonl",
        f"R9_REPAIRED_TARGETS_{DATE}.jsonl",
        f"R9_FAILURE_INTEL_{DATE}.jsonl",
        f"R9_SOURCE_CAPTURE_REQS_{DATE}.jsonl",
        f"R9_FORWARD_IMPLICATIONS_{DATE}.jsonl",
        f"R9_DOORS_{DATE}.jsonl",
        f"R9_QUESTIONS_{DATE}.jsonl",
        f"R9_BLOCKERS_{DATE}.jsonl",
        f"R9_SEQUENCE_{DATE}.jsonl",
        f"R9_SATURATION_{DATE}.json",
        f"R9_INSTRUCTION_COVERAGE_{DATE}.json",
        f"R9_COMPLETION_{DATE}.json",
        f"R9_completion_audit_{DATE}.json",
        f"R9_DECISION_{DATE}.json",
        f"R9_decision_ledger_{DATE}.json",
        f"R9_FOCUSED_TEST_{DATE}.json",
        f"R9_VERIFICATION_{DATE}.json",
        f"R9_verification_result_{DATE}.json",
        f"R9_OUTPUT_MANIFEST_{DATE}.json",
        f"R9_SYNTHESIS_{DATE}.md",
        f"G12_R9_PACKET_AUDIT_PROMPT_{DATE}.md",
        f"G12_R9_PACKET_AUDIT_STARTER_{DATE}.txt",
    ]


def verify(
    update: bool = False,
    focused_tests_ok: bool = False,
    focused_tests_summary: str | None = None,
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
        "row_identity": f"R9_ROW_IDENTITY_{DATE}.jsonl",
        "haz001": f"R9_HAZ001_PACKET_{DATE}.jsonl",
        "mac": f"R9_MAC_PACKET_{DATE}.jsonl",
        "haz005": f"R9_HAZ005_PACKET_{DATE}.jsonl",
        "unc004": f"R9_UNC004_CONTRACT_{DATE}.jsonl",
        "residual": f"R9_RESIDUAL_PACKET_{DATE}.jsonl",
        "repaired_target": f"R9_REPAIRED_TARGETS_{DATE}.jsonl",
        "failure_intel": f"R9_FAILURE_INTEL_{DATE}.jsonl",
        "source_capture": f"R9_SOURCE_CAPTURE_REQS_{DATE}.jsonl",
        "forward_implication": f"R9_FORWARD_IMPLICATIONS_{DATE}.jsonl",
        "open_closed": f"R9_DOORS_{DATE}.jsonl",
        "question": f"R9_QUESTIONS_{DATE}.jsonl",
        "sequence": f"R9_SEQUENCE_{DATE}.jsonl",
    }
    counts = {key: count_jsonl(route_file(name)) for key, name in count_names.items() if route_file(name).exists()}
    expected_counts = {
        "row_identity": 182,
        "haz001": 143,
        "mac": 32,
        "haz005": 5,
        "unc004": 1154,
        "residual": 1,
        "repaired_target": 5320,
        "failure_intel": 2641,
        "source_capture": 182,
        "forward_implication": 182,
        "open_closed": 364,
        "question": 182,
        "sequence": 182,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"{key} row count {counts.get(key)} != {expected}")
    checks["row_counts"] = counts
    checks["row_counts_match_expected"] = all(counts.get(key) == value for key, value in expected_counts.items())

    if route_file(count_names["row_identity"]).exists() and route_file(count_names["sequence"]).exists():
        identity_ids = {row["packet_row_id"] for row in iter_jsonl(route_file(count_names["row_identity"]))}
        sequence_ids = {row["packet_row_id"] for row in iter_jsonl(route_file(count_names["sequence"]))}
        source_capture_ids = {row["packet_row_id"] for row in iter_jsonl(route_file(count_names["source_capture"]))}
        if identity_ids != sequence_ids or identity_ids != source_capture_ids:
            errors.append("packet id coverage mismatch across identity/sequence/source-capture ledgers")
        checks["packet_id_coverage_match"] = identity_ids == sequence_ids == source_capture_ids

    decision = read_json(route_file(f"R9_DECISION_{DATE}.json"))
    check_safe(decision, "decision", errors)
    checks["terminal_decision_ok"] = decision.get("terminal_decision") == builder.TERMINAL_DECISION
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        errors.append(f"terminal decision mismatch: {decision.get('terminal_decision')}")

    completion = read_json(route_file(f"R9_COMPLETION_{DATE}.json"))
    check_safe(completion, "completion", errors)
    checks["same_evidence_class_remaining_zero"] = completion.get("same_evidence_class_intelligence_remaining") == 0
    if completion.get("same_evidence_class_intelligence_remaining") != 0:
        errors.append("completion audit does not have same_evidence_class_intelligence_remaining=0")

    instruction = read_json(route_file(f"R9_INSTRUCTION_COVERAGE_{DATE}.json"))
    check_safe(instruction, "instruction_coverage", errors)
    checks["instruction_coverage_ok"] = instruction.get("all_requirements_satisfied") is True
    if instruction.get("all_requirements_satisfied") is not True:
        errors.append("instruction coverage does not mark all requirements satisfied")

    source_hash = read_json(route_file(f"R9_SOURCE_HASH_{DATE}.json"))
    check_safe(source_hash, "source_hash", errors)
    source_hash_errors = []
    mutable_hash_warnings = []
    for source in source_hash.get("sources", []):
        source_path = ROOT / source["path"]
        if not source_path.exists():
            message = f"missing source {source['path']}"
            if source["path"] in builder.MUTABLE_COORDINATION_SOURCE_PATHS:
                mutable_hash_warnings.append(message)
            else:
                source_hash_errors.append(message)
            continue
        current = builder.sha256_file(source_path)
        current_lf = builder.sha256_file_canonical_lf(source_path)
        if current != source.get("sha256") and current_lf != source.get("sha256_canonical_lf"):
            message = f"source hash drift {source['path']}"
            if source["path"] in builder.MUTABLE_COORDINATION_SOURCE_PATHS:
                mutable_hash_warnings.append(message)
            else:
                source_hash_errors.append(message)
    if source_hash_errors:
        errors.extend(source_hash_errors)
    warnings.extend(mutable_hash_warnings)
    checks["source_hashes_match_current_disk"] = not source_hash_errors
    checks["mutable_coordination_source_hash_warnings"] = mutable_hash_warnings

    safe_rows_checked = 0
    for path in ROUTE_DIR.glob("R9_*.jsonl"):
        for row in iter_jsonl(path):
            check_safe(row, f"{path.name}:{row['_source_line_number']}", errors)
            safe_rows_checked += 1
    checks["jsonl_safe_rows_checked"] = safe_rows_checked

    for path in ROUTE_DIR.glob("R9_*.json"):
        if path.name.endswith(f"OUTPUT_MANIFEST_{DATE}.json") or path.name.endswith(f"VERIFICATION_RESULT_{DATE}.json"):
            continue
        data = read_json(path)
        if isinstance(data, dict) and "promotion_verdict" in data:
            check_safe(data, path.name, errors)
    checks["json_safe_flags_checked"] = True

    unc_rows = list(iter_jsonl(route_file(f"R9_UNC004_CONTRACT_{DATE}.jsonl")))
    checks["unc004_packet_scope_rows"] = sum(1 for row in unc_rows if row.get("contract_scope") == "packet_row")
    checks["unc004_full_implication_rows"] = sum(1 for row in unc_rows if row.get("contract_scope") == "accepted_full_row_implication")
    if checks["unc004_packet_scope_rows"] != 1 or checks["unc004_full_implication_rows"] != 1153:
        errors.append("UNC004 packet/full implication split mismatch")

    haz005_rows = list(iter_jsonl(route_file(f"R9_HAZ005_PACKET_{DATE}.jsonl")))
    if not all(row.get("exact_row_level_impossibility") for row in haz005_rows):
        errors.append("HAZ005 rows do not all carry exact row-level impossibility")
    checks["haz005_exact_impossibility_rows"] = sum(1 for row in haz005_rows if row.get("exact_row_level_impossibility"))

    failure_rows = list(iter_jsonl(route_file(f"R9_FAILURE_INTEL_{DATE}.jsonl")))
    unknown_class_rows = [row for row in failure_rows if row.get("unknown_doctrine_classifications")]
    if unknown_class_rows:
        errors.append(f"failure-intelligence rows have unknown doctrine classes: {len(unknown_class_rows)}")
    checks["failure_intel_unknown_class_rows"] = len(unknown_class_rows)

    if update and focused_tests_ok:
        focused = {
            **builder.safe_base(),
            "generated_at_utc": builder.utc_now(),
            "focused_tests_ok": True,
            "status": "PASSED",
            "command": f"py -3 -m pytest {builder.rel(ROUTE_DIR / 'test_r9_forward_packet_2026_05_16.py')}",
            "summary": focused_tests_summary or "focused pytest passed",
        }
        builder.write_json(route_file(f"R9_FOCUSED_TEST_{DATE}.json"), focused)
    else:
        focused = read_json(route_file(f"R9_FOCUSED_TEST_{DATE}.json"))
    checks["focused_tests_ok"] = bool(focused.get("focused_tests_ok"))
    if require_focused_tests and not focused.get("focused_tests_ok"):
        errors.append("focused tests are not recorded as passing")

    if update:
        result = {
            **builder.safe_base(),
            "generated_at_utc": builder.utc_now(),
            "ok": not errors,
            "can_mark_goal_complete": not errors,
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
        }
        builder.write_json(route_file(f"R9_VERIFICATION_{DATE}.json"), result)
        builder.write_json(route_file(f"R9_verification_result_{DATE}.json"), result)
        builder.write_output_manifest()
    else:
        manifest = read_json(route_file(f"R9_OUTPUT_MANIFEST_{DATE}.json"))
        check_safe(manifest, "output_manifest", errors)
        bad_manifest_hashes = []
        for item in manifest.get("files", []):
            path = ROOT / item["path"]
            if not path.exists():
                bad_manifest_hashes.append(f"missing manifest path {item['path']}")
                continue
            if builder.sha256_file(path) != item["sha256"]:
                bad_manifest_hashes.append(f"manifest hash drift {item['path']}")
        if bad_manifest_hashes:
            errors.extend(bad_manifest_hashes)
        checks["output_manifest_hashes_match"] = not bad_manifest_hashes

    return {
        **builder.safe_base(),
        "generated_at_utc": builder.utc_now(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary")
    args = parser.parse_args()
    result = verify(update=args.update, focused_tests_ok=args.mark_focused_tests_ok, focused_tests_summary=args.focused_tests_summary)
    if args.update:
        # Re-read after update so stdout matches the written artifact.
        result = read_json(route_file(f"R9_VERIFICATION_{DATE}.json"))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
