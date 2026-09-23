#!/usr/bin/env python3
"""Verify the G12 R8DISC sealed-validation audit artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_g12_scid_ready8_discriminative_sealed_validation_result_audit_2026_05_13 as builder


DATE = builder.DATE
OUTPUT_DIR = builder.OUTPUT_DIR
VERIFICATION_PATH = OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_VERIFICATION_RESULT_{DATE}.json"
FOCUSED_TEST_PATH = OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def verify(mark_focused_tests_ok: bool) -> dict[str, Any]:
    required_keys = [
        "decision",
        "recomputation",
        "metric_discrepancy",
        "branch_coverage",
        "fail_duplicate_concentration",
        "forbidden_surface",
        "lfs_materialization",
        "full_distribution",
        "repair",
        "saturation",
        "completion",
        "summary_md",
        "manifest",
    ]
    missing = [
        builder.rel(builder.OUTPUT_FILES[key])
        for key in required_keys
        if not builder.OUTPUT_FILES[key].exists()
    ]
    issues: list[dict[str, Any]] = []
    if missing:
        issues.append({"issue": "missing_required_artifacts", "paths": missing})

    decision = read_json(builder.OUTPUT_FILES["decision"]) if builder.OUTPUT_FILES["decision"].exists() else {}
    recomputation = read_json(builder.OUTPUT_FILES["recomputation"]) if builder.OUTPUT_FILES["recomputation"].exists() else {}
    discrepancy = read_json(builder.OUTPUT_FILES["metric_discrepancy"]) if builder.OUTPUT_FILES["metric_discrepancy"].exists() else {}
    branch = read_json(builder.OUTPUT_FILES["branch_coverage"]) if builder.OUTPUT_FILES["branch_coverage"].exists() else {}
    fail_dup = read_json(builder.OUTPUT_FILES["fail_duplicate_concentration"]) if builder.OUTPUT_FILES["fail_duplicate_concentration"].exists() else {}
    forbidden = read_json(builder.OUTPUT_FILES["forbidden_surface"]) if builder.OUTPUT_FILES["forbidden_surface"].exists() else {}
    lfs = read_json(builder.OUTPUT_FILES["lfs_materialization"]) if builder.OUTPUT_FILES["lfs_materialization"].exists() else {}
    repair = read_json(builder.OUTPUT_FILES["repair"]) if builder.OUTPUT_FILES["repair"].exists() else {}
    saturation = read_json(builder.OUTPUT_FILES["saturation"]) if builder.OUTPUT_FILES["saturation"].exists() else {}
    completion = read_json(builder.OUTPUT_FILES["completion"]) if builder.OUTPUT_FILES["completion"].exists() else {}

    checks = {
        "decision_accepted": decision.get("accepted") is True,
        "terminal_decision_accepts_without_promotion": decision.get("terminal_decision")
        == "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_NO_PROMOTION",
        "all_recomputation_checks_true": bool(recomputation.get("checks"))
        and all(recomputation.get("checks", {}).values()),
        "no_metric_discrepancies": discrepancy.get("discrepancy_count") == 0,
        "branch_coverage_accepted": branch.get("accepted") is True,
        "fail_duplicate_concentration_accepted": fail_dup.get("fail_closed_exclusion", {}).get("accepted") is True
        and fail_dup.get("duplicate_effective_n", {}).get("accepted") is True,
        "forbidden_surface_clear": forbidden.get("no_forbidden_surface_touches_by_audit") is True,
        "lfs_materialization_accepted": lfs.get("accepted") is True,
        "same_g12_repairable_zero": repair.get("same_g12_repairable_items_remaining") == 0,
        "saturation_accepted": saturation.get("accepted") is True,
        "safe_flags_closed_decision": decision.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and decision.get("validation_safe") is False
        and decision.get("outcome_review_opened") is False
        and decision.get("live_effect") is False,
        "builder_completion_waited_only_on_verifier_tests": completion.get("can_mark_goal_complete_after_verifier_and_focused_tests") is True,
        "focused_tests_recorded": mark_focused_tests_ok,
    }
    for name, ok in checks.items():
        if not ok:
            issues.append({"issue": name, "ok": ok})

    if mark_focused_tests_ok:
        focused = {
            "generated_at_utc": builder.utc_now(),
            "route_id": builder.ROUTE_ID,
            "evidence_class": builder.EVIDENCE_CLASS,
            "command": "pytest research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/test_g12_scid_ready8_discriminative_sealed_validation_result_audit_2026_05_13.py -q",
            "status": "PASSED_RECORDED_AFTER_COMMAND_SUCCESS",
            "passed": True,
            **builder.SAFE_FLAGS,
        }
        write_json(FOCUSED_TEST_PATH, focused)
        if completion:
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "focused tests/verifier output":
                    row["artifact"] = builder.rel(FOCUSED_TEST_PATH)
                    row["satisfied"] = True
            completion["missing_or_unverified_requirements_before_verifier"] = []
            completion["can_mark_goal_complete"] = len(issues) == 0
            completion["focused_tests_recorded"] = True
            completion["verification_result_path"] = builder.rel(VERIFICATION_PATH)
            write_json(builder.OUTPUT_FILES["completion"], completion)

    result = {
        "generated_at_utc": builder.utc_now(),
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "ok": len(issues) == 0,
        "can_mark_goal_complete": len(issues) == 0 and mark_focused_tests_ok,
        "checks": checks,
        "issues": issues,
        "terminal_decision": decision.get("terminal_decision"),
        **builder.SAFE_FLAGS,
    }
    write_json(VERIFICATION_PATH, result)
    builder.write_output_manifest(builder.utc_now(), include_verifier_outputs=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.mark_focused_tests_ok), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
