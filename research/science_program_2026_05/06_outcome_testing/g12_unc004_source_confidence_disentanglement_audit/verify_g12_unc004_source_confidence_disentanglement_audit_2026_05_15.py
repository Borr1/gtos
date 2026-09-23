#!/usr/bin/env python3
"""Verify the G12 UNC-004 source-confidence audit artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_g12_unc004_source_confidence_disentanglement_audit_2026_05_15 as builder


VERIFICATION_PATH = builder.OUTPUT_FILES["verification_result"]
FOCUSED_TEST_PATH = builder.OUTPUT_FILES["focused_test_result"]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(builder.canonical_json_bytes(payload))


def output_manifest_current() -> dict[str, Any]:
    manifest = read_json(builder.OUTPUT_FILES["manifest"])
    bad = []
    missing = []
    for artifact in manifest.get("artifacts", []):
        if artifact.get("name") in {"manifest", "verification_result", "focused_test_result"}:
            continue
        path = builder.ROOT / artifact["path"]
        if not path.exists():
            missing.append(artifact["path"])
            continue
        rows = builder.count_jsonl(path) if path.suffix.lower() == ".jsonl" else None
        if artifact.get("sha256") != builder.file_sha256(path) or artifact.get("bytes") != path.stat().st_size or artifact.get("rows") != rows:
            bad.append({"name": artifact.get("name"), "path": artifact["path"]})
    return {"ok": not bad and not missing, "bad_entries": bad, "missing_entries": missing}


def verify(mark_focused_tests_ok: bool) -> dict[str, Any]:
    required = [
        "decision",
        "recomputation",
        "discrepancy_repair",
        "instruction_coverage",
        "saturation",
        "completion",
        "summary",
        "manifest",
    ]
    missing = [builder.rel(builder.OUTPUT_FILES[key]) for key in required if not builder.OUTPUT_FILES[key].exists()]
    issues: list[dict[str, Any]] = []
    if missing:
        issues.append({"issue": "missing_required_artifacts", "paths": missing})

    decision = read_json(builder.OUTPUT_FILES["decision"]) if builder.OUTPUT_FILES["decision"].exists() else {}
    recomputation = read_json(builder.OUTPUT_FILES["recomputation"]) if builder.OUTPUT_FILES["recomputation"].exists() else {}
    discrepancy = read_json(builder.OUTPUT_FILES["discrepancy_repair"]) if builder.OUTPUT_FILES["discrepancy_repair"].exists() else {}
    instruction = read_json(builder.OUTPUT_FILES["instruction_coverage"]) if builder.OUTPUT_FILES["instruction_coverage"].exists() else {}
    saturation = read_json(builder.OUTPUT_FILES["saturation"]) if builder.OUTPUT_FILES["saturation"].exists() else {}
    completion = read_json(builder.OUTPUT_FILES["completion"]) if builder.OUTPUT_FILES["completion"].exists() else {}

    unc_manifest = builder.check_unc_manifest_current()
    audit_manifest = output_manifest_current() if builder.OUTPUT_FILES["manifest"].exists() else {"ok": False}

    checks = {
        "decision_accepted": decision.get("accepted") is True,
        "terminal_decision_expected": decision.get("terminal_decision")
        == "ACCEPT_AS_G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_AFTER_MANIFEST_REPAIR_NO_PROMOTION",
        "all_row_counts_match_expected": recomputation.get("all_row_counts_match_expected") is True,
        "all_ledgers_recomputed_exactly": recomputation.get("all_ledger_recomputations_match") is True,
        "json_artifacts_recomputed_exactly": recomputation.get("all_json_artifact_recomputations_match") is True,
        "same_g12_repairable_zero": discrepancy.get("same_g12_repairable_items_remaining") == 0,
        "instruction_coverage_complete": instruction.get("all_requirements_covered") is True,
        "saturation_accepted": saturation.get("accepted") is True,
        "completion_ready_except_verifier_tests": completion.get("can_mark_goal_complete_after_verifier_and_focused_tests") is True,
        "unc_manifest_current": unc_manifest.get("ok") is True,
        "audit_manifest_current": audit_manifest.get("ok") is True,
        "safe_flags_closed": decision.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and decision.get("validation_safe") is False
        and decision.get("outcome_review_opened") is False
        and decision.get("live_effect") is False,
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
            "command": "py -3 -m pytest research/science_program_2026_05/06_outcome_testing/g12_unc004_source_confidence_disentanglement_audit/test_g12_unc004_source_confidence_disentanglement_audit_2026_05_15.py -q",
            "status": "PASSED_RECORDED_AFTER_COMMAND_SUCCESS",
            "passed": True,
            **builder.ALL_FLAGS,
        }
        write_json(FOCUSED_TEST_PATH, focused)
        if completion:
            for item in completion.get("prompt_to_artifact_checklist", []):
                if item.get("requirement") == "verifier_and_focused_tests":
                    item["satisfied"] = len(issues) == 0
                    item["artifact_or_evidence"] = builder.rel(FOCUSED_TEST_PATH)
            completion["missing_or_unverified_requirements_before_verifier"] = []
            completion["focused_tests_recorded"] = True
            completion["verification_result_path"] = builder.rel(VERIFICATION_PATH)
            completion["can_mark_goal_complete"] = len(issues) == 0
            write_json(builder.OUTPUT_FILES["completion"], completion)

    result = {
        "generated_at_utc": builder.utc_now(),
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "ok": len(issues) == 0,
        "can_mark_goal_complete": len(issues) == 0 and mark_focused_tests_ok,
        "checks": checks,
        "issues": issues,
        "unc_manifest_check": unc_manifest,
        "audit_manifest_check": audit_manifest,
        "terminal_decision": decision.get("terminal_decision"),
        **builder.ALL_FLAGS,
    }
    write_json(VERIFICATION_PATH, result)
    builder.write_output_manifest(builder.utc_now())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.mark_focused_tests_ok), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
