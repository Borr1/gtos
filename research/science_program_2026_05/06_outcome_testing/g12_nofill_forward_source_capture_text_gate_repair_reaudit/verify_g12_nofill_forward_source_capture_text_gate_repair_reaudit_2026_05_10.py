#!/usr/bin/env python3
"""Verify the independent G12 text-gate repair reaudit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
RESULT_JSON = OUT_DIR / builder.VERIFICATION_RESULT_NAME

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)

ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_text_gate_repair_reaudit/",
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return sorted(paths)


def verify_control_flags(name: str, payload: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": name, "value": payload.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_required_flag", "file": name, "flag": flag, "value": payload.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_route_flag", "file": name, "flag": flag, "value": payload.get(flag)})


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_files = (
        builder.AUDIT_JSON
        + builder.AUDIT_MD
        + [
            "build_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10.py",
            "verify_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10.py",
            "test_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10.py",
        ]
    )
    missing = [name for name in required_files if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_audit_artifacts", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in builder.AUDIT_JSON:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        if isinstance(payload, dict):
            verify_control_flags(name, payload, failures)

    for name in builder.AUDIT_MD:
        path = OUT_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})
        for literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if literal in text:
                failures.append({"check": "forbidden_closed_flag_literal", "file": name, "literal": literal})

    decision = parsed.get(builder.AUDIT_JSON[1], {})
    terminal = decision.get("terminal_verdict")
    if terminal not in builder.ALLOWED_TERMINAL_VERDICTS:
        failures.append({"check": "terminal_verdict_not_allowed", "value": terminal})
    if terminal != builder.ACCEPT_TERMINAL_VERDICT:
        failures.append({"check": "expected_text_gate_acceptance_verdict_after_d2bd8cac", "value": terminal})
    if decision.get("target_repair_closed") is not True:
        failures.append({"check": "target_repair_not_closed", "value": decision.get("target_repair_closed")})
    if decision.get("validation_or_promotion_opened") is not False:
        failures.append({"check": "decision_validation_or_promotion_boundary"})
    if decision.get("future_live_logger_wiring_still_requires_owner_approval") is not True:
        failures.append({"check": "future_live_wiring_gate_boundary"})

    repair = parsed.get(builder.AUDIT_JSON[2], {})
    if repair.get("status") != "PASS":
        failures.append({"check": "repair_audit_status", "status": repair.get("status"), "failed": repair.get("failed_checks")})
    package_result = repair.get("package_verifier_result", {})
    if package_result.get("returncode") != 0 or package_result.get("ok") is not True or package_result.get("failures") != []:
        failures.append({"check": "package_verifier_rerun_not_clean", "package_result": package_result})
    for flag, expected in builder.CONTROL_FLAGS.items():
        if package_result.get("route_flags", {}).get(flag) != expected:
            failures.append({"check": "package_route_flag_opened", "flag": flag, "value": package_result.get("route_flags", {}).get(flag)})
    for required_check, value in repair.get("source_status_checks", {}).items():
        if value is not True:
            failures.append({"check": "repair_required_check", "name": required_check, "value": value})

    adversarial = parsed.get(builder.AUDIT_JSON[3], {})
    if adversarial.get("status") != "PASS":
        failures.append({"check": "adversarial_status", "status": adversarial.get("status")})
    expected_adversarial_true = (
        "strict_text_lf_portability_accepted_only_through_bounded_text_fallback",
        "strict_text_true_mutation_rejected",
        "strict_binary_non_text_raw_sha_mismatch_rejected_despite_synthetic_lf_match",
        "mutable_context_raw_drift_warning_only",
        "mutable_context_does_not_mask_strict_source_failure",
        "cleanup_verified",
        "committed_source_artifacts_unchanged",
    )
    for key in expected_adversarial_true:
        if adversarial.get(key) is not True:
            failures.append({"check": "adversarial_required_bool", "name": key, "value": adversarial.get(key)})
    cases = {case.get("case_id"): case for case in adversarial.get("cases", [])}
    binary = cases.get("STRICT_BINARY_NON_TEXT_RAW_SHA_DRIFT_REJECTED_EVEN_WITH_SYNTHETIC_LF_MATCH", {})
    if (
        binary.get("target_package_verifier_accepts") is not False
        or binary.get("target_entry_allows_lf_normalized_fallback") is not False
        or binary.get("target_lf_normalized") is not None
        or binary.get("synthetic_lf_normalized_hash_matches_manifest") is not True
    ):
        failures.append({"check": "binary_non_text_adversarial_case_not_proven", "case": binary})
    text = cases.get("STRICT_TEXT_EOL_PORTABILITY_ACCEPTED_ONLY_BY_TEXT_FALLBACK", {})
    if text.get("accepted_only_through_bounded_text_fallback") is not True:
        failures.append({"check": "text_portability_not_bounded_to_text_fallback", "case": text})

    hashes = parsed.get(builder.AUDIT_JSON[4], {})
    if hashes.get("status") != "PASS":
        failures.append({"check": "source_hash_audit_status", "status": hashes.get("status")})
    if hashes.get("content_hash_failure_count") != 0 or hashes.get("missing_manifest_path_count") != 0:
        failures.append({"check": "source_hash_content_or_missing_failure", "hashes": hashes})
    no_leak = parsed.get(builder.AUDIT_JSON[5], {})
    if no_leak.get("status") != "PASS":
        failures.append({"check": "no_leak_control_regression", "status": no_leak.get("status")})
    if no_leak.get("prototype_row_count") != 298:
        failures.append({"check": "prototype_row_count", "value": no_leak.get("prototype_row_count")})
    if no_leak.get("family_counts") != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        failures.append({"check": "family_counts", "value": no_leak.get("family_counts")})
    if (
        no_leak.get("row_level_accepted_denominator"),
        no_leak.get("primary_duplicate_key_denominator"),
        no_leak.get("secondary_duplicate_group_denominator"),
    ) != (225, 182, 139):
        failures.append({"check": "accepted_denominators", "values": [
            no_leak.get("row_level_accepted_denominator"),
            no_leak.get("primary_duplicate_key_denominator"),
            no_leak.get("secondary_duplicate_group_denominator"),
        ]})
    if no_leak.get("forbidden_key_hits_in_prototype_rows") or no_leak.get("prototype_rows_with_open_flags") or no_leak.get("raw_value_hits_in_projection_rows"):
        failures.append({"check": "no_leak_or_closed_flag_regression"})
    if no_leak.get("source_cost_execution_separation_status") != "PASS":
        failures.append({"check": "source_cost_execution_separation"})

    blocker = parsed.get(builder.AUDIT_JSON[6], {})
    if blocker.get("target_blocker_closed") is not True:
        failures.append({"check": "blocker_closure_state", "value": blocker.get("target_blocker_closed")})
    if blocker.get("remaining_repair_blocker_count") != 0 or blocker.get("remaining_blockers") != []:
        failures.append({"check": "remaining_repair_blockers", "value": blocker.get("remaining_blockers")})

    completion = parsed.get(builder.AUDIT_JSON[7], {})
    if completion.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "completion_status", "value": completion.get("can_mark_goal_complete_after_verification_and_commit")})
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append({"check": "completion_weak_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})
    if completion.get("target_repair_closed") is not True:
        failures.append({"check": "completion_target_repair_closed"})
    if completion.get("validation_or_promotion_opened") is not False:
        failures.append({"check": "completion_validation_or_promotion_boundary"})

    dirty_paths = git_status_paths()
    forbidden_live_dirty = [path for path in dirty_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_allowed_dirty = [
        path
        for path in dirty_paths
        if not any(path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES)
    ]
    if forbidden_live_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_live_dirty})
    if outside_allowed_dirty:
        warnings.append({"check": "outside_allowed_dirty_informational", "paths": outside_allowed_dirty})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.CONTROL_FLAGS,
        "terminal_verdict": terminal,
        "target_repair_closed": decision.get("target_repair_closed"),
        "remaining_repair_blocker_count": blocker.get("remaining_repair_blocker_count"),
        "failures": failures,
        "warnings": warnings,
        "json_files_parsed": sorted(parsed),
        "dirty_paths_reviewed": dirty_paths,
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "validation_or_promotion_opened": False,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
