#!/usr/bin/env python3
"""Verify and finalize the G12 R11 geometry capture packet audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_r11_geometry_capture_packet_audit_2026_05_16 as build  # noqa: E402


REQUIRED_OUTPUTS = list(build.G12_OUTPUTS)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def safe_flag_violations(paths: list[Path]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    keys = [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "opens_live_trading_behavior",
        "opens_ai_api",
        "opens_paid_or_vendor_access",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
    ]
    for path in paths:
        if path.suffix not in {".json", ".jsonl"} or not path.exists():
            continue
        rows: list[Any]
        if path.suffix == ".json":
            rows = [read_json(path)]
        else:
            rows = read_jsonl(path)
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            for key in keys:
                if row.get(key) is True:
                    violations.append({"path": path.name, "row": index, "flag": key})
    return violations


def check(name: str, condition: bool, details: Any = None) -> dict[str, Any]:
    return {"check": name, "ok": bool(condition), "details": details}


def main() -> None:
    outputs = {filename: ROUTE_DIR / filename for filename in REQUIRED_OUTPUTS}
    existence = {filename: path.exists() for filename, path in outputs.items()}
    missing = [filename for filename, exists in existence.items() if not exists]

    decision = read_json(outputs["G12_R11_DECISION_LEDGER_2026-05-16.json"])
    recomputation = read_json(outputs["G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json"])
    completion = read_json(outputs["G12_R11_COMPLETION_AUDIT_2026-05-16.json"])
    downstream = read_json(outputs["G12_R11_DOWNSTREAM_FORK_DECISION_2026-05-16.json"])
    source_rows = read_jsonl(outputs["G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl"])
    weak_rows = read_jsonl(outputs["G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl"])
    capture_rows = read_jsonl(outputs["G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl"])
    discrepancy_rows = read_jsonl(outputs["G12_R11_DISCREPANCY_REPAIR_LEDGER_2026-05-16.jsonl"])
    focused = read_json(outputs["G12_R11_FOCUSED_TEST_RESULT_2026-05-16.json"])

    checks = [
        check("all_required_output_files_exist", not missing, missing),
        check(
            "terminal_decision_accepts_no_promotion",
            decision.get("terminal_decision") == "ACCEPT_R11_PACKET_AS_G12_AUDITED_NO_PROMOTION"
            and decision.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
            and decision.get("can_promote") is False,
        ),
        check("all_count_checks_pass", recomputation.get("all_count_checks_pass") is True),
        check("row_universe_5502", recomputation["recomputed_counts"].get("row_universe") == 5502),
        check("packet_rows_182", recomputation["recomputed_counts"].get("packet_rows") == 182),
        check("repaired_target_rows_5320", recomputation["recomputed_counts"].get("repaired_target_rows") == 5320),
        check("source_roots_51", len(source_rows) == 51),
        check("weak_overlap_rows_80", len(weak_rows) == 80),
        check("capture_requirements_5502", len(capture_rows) == 5502),
        check("discrepancy_repair_rows_zero", len(discrepancy_rows) == 0),
        check("exact_r_rows_zero", recomputation["recomputed_counts"].get("exact_r_rows") == 0),
        check(
            "target_stop_rows_zero",
            recomputation["recomputed_counts"].get("target_stop_hit_miss_rows") == 0,
        ),
        check(
            "all_capture_requirements_row_specific",
            all(row.get("row_identity_specific") is True for row in capture_rows),
        ),
        check(
            "weak_rows_rejected_for_exact_repair",
            all(
                row.get("g12_repair_decision")
                == "REJECTED_FOR_EXACT_R_REPAIR_NOT_SOURCE_BOUND_TO_ACCEPTED_SCID_CANDIDATE_INPUT_ROW"
                for row in weak_rows
            ),
        ),
        check(
            "source_roots_have_no_missed_same_evidence_repair",
            all(row.get("g12_missed_same_evidence_repair") is False for row in source_rows),
        ),
        check("completion_standard_met", completion.get("completion_standard_met") is True),
        check(
            "downstream_fork_exactly_one_and_executable",
            downstream.get("selected_fork") == "EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE"
            and downstream.get("not_g0_summary_blocker_ambiguity_or_capture_requirement_only") is True,
        ),
        check("focused_tests_passed", focused.get("ok") is True, focused),
    ]

    violations = safe_flag_violations([path for name, path in outputs.items() if name != "G12_R11_OUTPUT_MANIFEST_2026-05-16.json"])
    checks.append(check("safe_flags_closed", not violations, violations))

    artifact_rows = []
    for filename, path in sorted(outputs.items()):
        if filename == "G12_R11_OUTPUT_MANIFEST_2026-05-16.json":
            continue
        artifact_rows.append(
            {
                "path": path.relative_to(build.REPO_ROOT).as_posix(),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": build.sha256_file(path) if path.exists() and path.is_file() else None,
            }
        )
    artifact_audit = build.with_flags(
        {
            "ok": all(row["exists"] for row in artifact_rows),
            "artifact_audit_status": "PASS" if all(row["exists"] for row in artifact_rows) else "FAIL",
            "expected_file_count_excluding_manifest": len(artifact_rows),
            "missing_files": [row["path"] for row in artifact_rows if not row["exists"]],
            "artifacts": artifact_rows,
        }
    )
    write_json(outputs["G12_R11_ARTIFACT_AUDIT_RESULT_2026-05-16.json"], artifact_audit)

    ok = all(item["ok"] for item in checks) and artifact_audit["ok"]
    verification = build.with_flags(
        {
            "ok": ok,
            "verification_status": "PASS" if ok else "FAIL",
            "checks": checks,
            "same_evidence_class_repairable_issue_count": 0,
            "exact_r_expectancy_rows_computed": 0,
            "target_stop_hit_miss_rows_computed": 0,
            "downstream_fork_selected": downstream.get("selected_fork"),
        }
    )
    write_json(outputs["G12_R11_VERIFICATION_RESULT_2026-05-16.json"], verification)

    manifest = build.build_manifest([filename for filename in REQUIRED_OUTPUTS if filename != "G12_R11_OUTPUT_MANIFEST_2026-05-16.json"])
    write_json(outputs["G12_R11_OUTPUT_MANIFEST_2026-05-16.json"], manifest)

    print(json.dumps({"ok": ok, "checks": len(checks), "missing": missing}, sort_keys=True))
    if not ok:
        failed = [item for item in checks if not item["ok"]]
        raise SystemExit(json.dumps({"failed": failed}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
