"""Verifier for the G12 SCID read-only alignment expansion audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
AUDIT_DIR = Path(__file__).resolve().parent
PREFIX = "G12_SCID_RO_ALIGN_EXP_AUDIT"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY"
ACCEPT_DECISION = (
    "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY"
)
REPAIR_DECISION = "REPAIR_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_BEFORE_USE"

EXPECTED_STEMS = [
    "CONTEXT_AND_INPUT_INVENTORY",
    "SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT",
    "COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT",
    "FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT",
    "CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT",
    "VERIFIER_TEST_SCOPED_DIRTY_AUDIT",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
    "OUTPUT_MANIFEST",
]
FILE_STEMS = {
    "CONTEXT_AND_INPUT_INVENTORY": "CONTEXT_INPUTS",
    "SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT": "ROOT_RECOMP",
    "COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT": "COVERAGE_BOUNDARY",
    "FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT": "FORBIDDEN_FINGERPRINTS",
    "CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT": "CAPTURE_SATURATION",
    "VERIFIER_TEST_SCOPED_DIRTY_AUDIT": "VERIFIER_DIRTY",
    "DECISION_LEDGER": "DECISION",
    "COMPLETION_AUDIT": "COMPLETION",
    "CLOSEOUT_VERIFICATION": "CLOSEOUT",
    "OUTPUT_MANIFEST": "MANIFEST",
    "VERIFICATION_RESULT": "VERIFICATION_RESULT",
}
EXPECTED_GROUPS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
}


def output_path(stem: str, suffix: str = "json") -> Path:
    return AUDIT_DIR / f"{PREFIX}_{FILE_STEMS.get(stem, stem)}_2026-05-12.{suffix}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_status() -> str:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (proc.stdout + proc.stderr).strip()


def add_check(checks: list[dict[str, Any]], name: str, condition: bool, detail: Any = None) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def verify_required_files(checks: list[dict[str, Any]]) -> None:
    missing = []
    for stem in EXPECTED_STEMS:
        for suffix in ("json", "md"):
            path = output_path(stem, suffix)
            if not path.exists():
                missing.append(str(path))
    add_check(checks, "required_audit_files_exist", not missing, missing)


def verify_decision_completion(checks: list[dict[str, Any]]) -> None:
    decision = load_json(output_path("DECISION_LEDGER"))
    completion = load_json(output_path("COMPLETION_AUDIT"))
    terminal = decision["terminal_decision"]
    add_check(
        checks,
        "terminal_decision_exact_enum",
        terminal in {ACCEPT_DECISION, REPAIR_DECISION},
        terminal,
    )
    add_check(
        checks,
        "completion_matches_decision_status",
        completion["terminal_decision"] == terminal
        and completion["completion_standard_met"] == (terminal == ACCEPT_DECISION),
        {"decision": terminal, "completion_standard_met": completion["completion_standard_met"]},
    )
    add_check(checks, "no_blocking_failures_for_accept", terminal != ACCEPT_DECISION or not completion["blocking_failures"], completion["blocking_failures"])
    checklist_failures = [row for row in completion["prompt_to_artifact_checklist"] if row["status"] != "PASS"]
    add_check(checks, "prompt_to_artifact_checklist_all_pass", not checklist_failures, checklist_failures)


def verify_context_inventory(checks: list[dict[str, Any]]) -> None:
    context = load_json(output_path("CONTEXT_AND_INPUT_INVENTORY"))
    missing_preflight = [row for row in context["mandatory_preflight_files"] if not row["exists"]]
    add_check(checks, "mandatory_preflight_files_hashed", not missing_preflight, missing_preflight)
    add_check(
        checks,
        "input_route_manifest_artifacts_exist_and_checked",
        context["input_route_manifest_existing_artifact_count"] == context["input_route_manifest_artifact_count"]
        and not [row for row in context["input_route_manifest_artifacts_checked"] if row["raw_market_blob"]],
        {
            "route_dir_from_disk": context["input_route_artifact_count_from_disk"],
            "manifest": context["input_route_manifest_artifact_count"],
            "manifest_existing": context["input_route_manifest_existing_artifact_count"],
        },
    )
    add_check(
        checks,
        "upstream_offline_artifacts_hashed",
        context["accepted_g12_offline_schema_audit_file_count"] > 0
        and context["original_offline_schema_package_file_count"] > 0,
        {
            "g12_count": context["accepted_g12_offline_schema_audit_file_count"],
            "package_count": context["original_offline_schema_package_file_count"],
        },
    )


def verify_roots_and_coverage(checks: list[dict[str, Any]]) -> None:
    roots = load_json(output_path("SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT"))
    coverage = load_json(output_path("COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT"))
    add_check(checks, "root_recomputation_passed", roots["status"] == "PASS", roots["failures"])
    add_check(checks, "searched_more_than_twelve_and_external_roots", roots["searched_more_than_accepted_twelve_targets"] and roots["absolute_or_prior_worktree_roots"], roots)
    add_check(checks, "coverage_boundary_passed", coverage["status"] == "PASS", coverage["failures"])
    add_check(checks, "coverage_groups_exact_ten", set(coverage["coverage_groups"]) == EXPECTED_GROUPS, coverage["coverage_groups"])
    add_check(
        checks,
        "candidate_and_duplicate_boundaries_3014_control_only",
        coverage["candidate_rows_boundary"] == 3014
        and coverage["duplicate_proxy_denominator_key_boundary"] == 3014
        and coverage["boundary_is_source_control_expectation_only"],
        {
            "candidate": coverage["candidate_rows_boundary"],
            "duplicate": coverage["duplicate_proxy_denominator_key_boundary"],
            "control_only": coverage["boundary_is_source_control_expectation_only"],
        },
    )


def verify_forbidden_capture_saturation(checks: list[dict[str, Any]]) -> None:
    forbidden = load_json(output_path("FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT"))
    capture = load_json(output_path("CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT"))
    dirty = load_json(output_path("VERIFIER_TEST_SCOPED_DIRTY_AUDIT"))
    add_check(checks, "forbidden_and_fingerprint_audit_passed", forbidden["status"] == "PASS", forbidden["failures"])
    add_check(
        checks,
        "content_hashes_recomputed_with_no_blocking_mismatch",
        forbidden["content_hashes_recomputed_from_disk"] == forbidden["content_hashes_recorded_count_reported"]
        and forbidden["blocking_content_hash_mismatch_count"] == 0,
        forbidden,
    )
    add_check(checks, "forbidden_categories_excluded", forbidden["forbidden_file_exclusion_count"] > 0 and forbidden["forbidden_examples_bad_disposition_count"] == 0, forbidden)
    add_check(checks, "capture_saturation_passed", capture["status"] == "PASS", capture["failures"])
    add_check(checks, "missing_fields_have_exact_capture_requirements", capture["capture_requirements_include_required_controls"] and capture["capture_requirements_name_every_missing_field"], capture)
    add_check(checks, "input_route_verifier_and_tests_passed", dirty["status"] == "PASS", dirty["failures"])


def verify_manifest_and_git_scope(checks: list[dict[str, Any]]) -> None:
    manifest = load_json(output_path("OUTPUT_MANIFEST"))
    artifact_paths = {row["path"] for row in manifest["artifacts"]}
    add_check(checks, "manifest_has_no_raw_market_blobs", not [row for row in manifest["artifacts"] if row.get("raw_market_blob")], manifest)
    add_check(
        checks,
        "manifest_includes_verifier_and_tests",
        any(path.endswith("verify_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py") for path in artifact_paths)
        and any(path.endswith("test_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py") for path in artifact_paths),
        sorted(artifact_paths),
    )
    status = git_status()
    forbidden_dirty = [
        line
        for line in status.splitlines()
        if len(line) > 3
        and line[3:].startswith(
            (
                "src/components/",
                "src/safety/",
                "prompts/",
                "config/",
                "scripts/canary",
                "data/",
                "knowledge_base/trade_records/",
            )
        )
    ]
    add_check(checks, "no_forbidden_dirty_surfaces", not forbidden_dirty, {"status": status, "forbidden_dirty": forbidden_dirty})


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    verify_required_files(checks)
    verify_decision_completion(checks)
    verify_context_inventory(checks)
    verify_roots_and_coverage(checks)
    verify_forbidden_capture_saturation(checks)
    verify_manifest_and_git_scope(checks)
    failed = [check for check in checks if check["status"] != "PASS"]
    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "ok": not failed,
        "terminal_decision": (
            "VERIFIED_G12_SCID_READONLY_ALIGNMENT_EXPANSION_AUDIT_ACCEPTED"
            if not failed
            else "VERIFY_G12_SCID_READONLY_ALIGNMENT_EXPANSION_AUDIT_REPAIR_REQUIRED"
        ),
        "check_count": len(checks),
        "failed_check_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
    }
    write_json(output_path("VERIFICATION_RESULT"), result)
    return result


def main() -> int:
    result = verify()
    print(json.dumps({"ok": result["ok"], "failed_check_count": result["failed_check_count"]}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
