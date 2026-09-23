#!/usr/bin/env python3
"""Verify the independent G12 source-capture repair reaudit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_forward_source_capture_repair_reaudit_2026_05_09 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
RESULT_JSON = OUT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_VERIFICATION_RESULT_2026-05-09.json"

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)

ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_repair_reaudit/",
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

    missing = [name for name in builder.AUDIT_JSON + builder.AUDIT_MD if not (OUT_DIR / name).exists()]
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

    decision = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-09.json", {})
    if decision.get("terminal_verdict") != builder.TERMINAL_VERDICT:
        failures.append({"check": "terminal_verdict", "value": decision.get("terminal_verdict")})
    if decision.get("terminal_verdict") not in builder.ALLOWED_TERMINAL_VERDICTS:
        failures.append({"check": "terminal_verdict_not_allowed", "value": decision.get("terminal_verdict")})
    if decision.get("target_repair_closed") is not False:
        failures.append({"check": "target_repair_should_remain_open", "value": decision.get("target_repair_closed")})
    if decision.get("validation_or_promotion_opened") is not False:
        failures.append({"check": "decision_validation_or_promotion_boundary"})

    repair = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_VERIFICATION_AUDIT_2026-05-09.json", {})
    if repair.get("status") != "FAIL_REMAINING_REPAIR_BLOCKER":
        failures.append({"check": "repair_audit_status", "status": repair.get("status")})
    package_result = repair.get("package_verifier_result", {})
    if package_result.get("ok") is not True or package_result.get("failures") != []:
        failures.append({"check": "package_verifier_rerun_not_clean", "package_result": package_result})
    checks = repair.get("source_status_checks", {})
    for required_check in (
        "prior_decision_reconstructed",
        "prior_blocker_reconstructed",
        "package_verifier_ok",
        "package_verifier_can_mark_goal_complete",
        "package_verifier_zero_failures",
        "package_verifier_records_lf_fallback_warnings",
        "raw_sha_recomputed_before_fallback",
        "mutable_context_separated",
        "true_content_mismatch_fails",
        "strict_text_lf_fallback_accepts",
        "temporary_fixtures_cleaned",
        "source_artifacts_unchanged_after_probe",
    ):
        if checks.get(required_check) is not True:
            failures.append({"check": "repair_required_check", "name": required_check, "value": checks.get(required_check)})
    if checks.get("binary_non_text_raw_sha_required") is not False:
        failures.append({"check": "expected_binary_non_text_case_to_fail_current_repair", "value": checks.get("binary_non_text_raw_sha_required")})

    adversarial = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADVERSARIAL_HASH_POLICY_PROOF_2026-05-09.json", {})
    if adversarial.get("status") != "FAIL_BINARY_NON_TEXT_FALLBACK_WEAKENING":
        failures.append({"check": "adversarial_status", "status": adversarial.get("status")})
    if adversarial.get("strict_text_lf_portability_accepted") is not True:
        failures.append({"check": "strict_text_lf_portability_not_accepted"})
    if adversarial.get("strict_text_true_mutation_rejected") is not True:
        failures.append({"check": "strict_text_true_mutation_not_rejected"})
    if adversarial.get("strict_binary_or_non_text_raw_sha_required") is not False:
        failures.append({"check": "binary_non_text_raw_sha_requirement_not_exposed"})
    if adversarial.get("strict_binary_or_non_text_safe_policy_would_reject") is not True:
        failures.append({"check": "safe_policy_binary_expectation_absent"})
    if adversarial.get("mutable_context_non_strict_drift_allowed") is not True:
        failures.append({"check": "mutable_context_case_not_allowed"})
    if adversarial.get("cleanup_verified") is not True:
        failures.append({"check": "adversarial_cleanup_not_verified"})
    binary_cases = [
        case for case in adversarial.get("cases", [])
        if case.get("case_id") == "STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED"
    ]
    if not binary_cases or binary_cases[0].get("target_package_verifier_accepts") is not True or binary_cases[0].get("safe_policy_accepts") is not False:
        failures.append({"check": "binary_case_does_not_show_policy_divergence", "case": binary_cases})

    hashes = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.json", {})
    if hashes.get("status") != "PASS":
        failures.append({"check": "source_hash_audit_status", "status": hashes.get("status")})
    if hashes.get("content_hash_failure_count") != 0 or hashes.get("missing_manifest_path_count") != 0:
        failures.append({"check": "source_hash_content_or_missing_failure", "hashes": hashes})
    if hashes.get("strict_text_lf_normalized_accept_count_current_checkout", 0) <= 0:
        failures.append({"check": "current_checkout_lf_fallback_evidence_absent"})

    no_leak = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_CONTROL_REGRESSION_AUDIT_2026-05-09.json", {})
    if no_leak.get("status") != "PASS":
        failures.append({"check": "no_leak_control_regression", "status": no_leak.get("status")})
    if no_leak.get("prototype_row_count") != 298:
        failures.append({"check": "prototype_row_count", "value": no_leak.get("prototype_row_count")})
    if (no_leak.get("row_level_accepted_denominator"), no_leak.get("primary_duplicate_key_denominator"), no_leak.get("secondary_duplicate_group_denominator")) != (225, 182, 139):
        failures.append({"check": "accepted_denominators", "values": [
            no_leak.get("row_level_accepted_denominator"),
            no_leak.get("primary_duplicate_key_denominator"),
            no_leak.get("secondary_duplicate_group_denominator"),
        ]})
    if no_leak.get("forbidden_key_hits_in_prototype_rows") or no_leak.get("prototype_rows_with_open_flags"):
        failures.append({"check": "no_leak_or_closed_flag_regression"})

    blocker = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_CLOSURE_LEDGER_2026-05-09.json", {})
    if blocker.get("target_blocker_closed") is not False:
        failures.append({"check": "blocker_closure_state", "value": blocker.get("target_blocker_closed")})
    if blocker.get("remaining_repair_blocker_count") != 1:
        failures.append({"check": "remaining_repair_blocker_count", "value": blocker.get("remaining_repair_blocker_count")})
    blocker_ids = {item.get("blocker_id") for item in blocker.get("remaining_blockers", [])}
    if "G12-SRC-CAP-REPAIR-001" not in blocker_ids:
        failures.append({"check": "expected_repair_blocker_id", "ids": sorted(blocker_ids)})

    completion = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-09.json", {})
    if completion.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "completion_status", "value": completion.get("can_mark_goal_complete_after_verification_and_commit")})
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append({"check": "completion_weak_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})
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
        "terminal_verdict": decision.get("terminal_verdict"),
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
