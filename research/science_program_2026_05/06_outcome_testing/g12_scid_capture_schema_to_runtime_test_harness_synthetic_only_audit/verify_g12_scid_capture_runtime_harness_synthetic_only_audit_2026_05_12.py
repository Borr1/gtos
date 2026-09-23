"""Standalone verifier for the G12 SCID synthetic harness audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


import build_g12_scid_capture_runtime_harness_synthetic_only_audit_2026_05_12 as audit


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(audit.REPO_ROOT).as_posix()


def verify() -> dict[str, Any]:
    failures: list[str] = []
    required = [
        audit.AUDIT_DIR / f"{audit.PREFIX}_REQUIRED_READS_LEDGER_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_RECOMPUTATION_AUDIT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_NOLEAK_AUDIT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_MANIFEST_BINDING_AUDIT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_VERIFIER_AND_TEST_RESULT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_SCOPED_DIRTY_STATE_AUDIT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_DECISION_LEDGER_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_COMPLETION_AUDIT_{audit.DATE_TAG}.json",
        audit.AUDIT_DIR / f"{audit.PREFIX}_OUTPUT_MANIFEST_{audit.DATE_TAG}.json",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing_audit_artifact:{rel(path)}")

    if failures:
        return {
            "route_id": audit.ROUTE_ID,
            "ok": False,
            "failures": failures,
        }

    reads = read_json(required[0])
    recomputation = read_json(required[1])
    noleak = read_json(required[2])
    manifest_binding = read_json(required[3])
    verifier_tests = read_json(required[4])
    dirty_state = read_json(required[5])
    decision = read_json(required[6])
    completion = read_json(required[7])
    output_manifest = read_json(required[8])

    if not all(item.get("exists") for item in reads.values()):
        failures.append("required_reads_not_all_present")
    if recomputation.get("filesystem_fixture_file_count") != 109:
        failures.append("fixture_file_count_not_109")
    if recomputation.get("filesystem_row_fixture_count") != 117:
        failures.append("fixture_row_count_not_117")
    if not recomputation.get("fixture_matrix_ok"):
        failures.append("fixture_matrix_not_ok")
    if not noleak.get("no_leak_ok"):
        failures.append("noleak_not_ok")
    if noleak.get("recomputed_deliberate_negative_forbidden_hit_count") != 10:
        failures.append("deliberate_negative_forbidden_count_not_10")
    if not manifest_binding.get("manifest_binding_policy_ok"):
        failures.append("manifest_binding_not_ok")
    if not verifier_tests.get("py_compile", {}).get("passed"):
        failures.append("py_compile_not_passed")
    if not verifier_tests.get("standalone_verifier", {}).get("passed"):
        failures.append("standalone_verifier_not_passed")
    if not verifier_tests.get("standalone_verifier_json", {}).get("ok"):
        failures.append("standalone_verifier_json_not_ok")
    if not verifier_tests.get("focused_tests", {}).get("passed"):
        failures.append("focused_tests_not_passed")
    if not dirty_state.get("surface_scope_ok"):
        failures.append("dirty_state_surface_scope_not_ok")
    if dirty_state.get("forbidden_surface_status_entries"):
        failures.append("forbidden_surface_status_entries_present")
    if decision.get("terminal_decision") != audit.TERMINAL_ACCEPT:
        failures.append("decision_not_accept")
    if decision.get("validation_safe") is not False:
        failures.append("validation_safe_not_false")
    if decision.get("outcome_review_opened") is not False:
        failures.append("outcome_review_opened_not_false")
    if decision.get("live_effect") is not False:
        failures.append("live_effect_not_false")
    if decision.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append("promotion_verdict_not_no_promotion")
    if not completion.get("can_mark_goal_complete_after_scoped_commit"):
        failures.append("completion_not_markable_after_scoped_commit")
    if any(not item.get("satisfied") for item in completion.get("completion_checklist", [])):
        failures.append("completion_checklist_has_unsatisfied_items")
    if output_manifest.get("terminal_decision") != audit.TERMINAL_ACCEPT:
        failures.append("output_manifest_not_accept")

    result = {
        "route_id": audit.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "terminal_decision": decision.get("terminal_decision"),
        "fixture_cases_verified": recomputation.get("filesystem_fixture_file_count"),
        "fixture_rows_verified": recomputation.get("filesystem_row_fixture_count"),
        "safe_flags_preserved_false": (
            decision.get("validation_safe") is False
            and decision.get("outcome_review_opened") is False
            and decision.get("live_effect") is False
        ),
        "forbidden_surfaces_opened": dirty_state.get("forbidden_surface_status_entries", []),
    }
    out_path = audit.AUDIT_DIR / f"{audit.PREFIX}_VERIFICATION_RESULT_{audit.DATE_TAG}.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
