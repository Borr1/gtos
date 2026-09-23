from __future__ import annotations

import json

import build_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10 as builder
import verify_g12_nofill_forward_source_capture_text_gate_repair_reaudit_2026_05_10 as verifier


def test_source_inspection_finds_explicit_text_gate() -> None:
    inspection = builder.inspect_target_verifier_source()
    assert inspection["status"] == "PASS"
    checks = inspection["checks"]
    assert checks["text_suffix_allowlist_defined"] is True
    assert checks["sha256_lf_normalized_function_has_suffix_guard"] is True
    assert checks["entry_gate_function_present"] is True
    assert checks["fallback_branch_calls_entry_gate"] is True
    assert checks["raw_sha_recomputed_before_fallback"] is True
    assert checks["mutable_context_separated_before_lf_fallback"] is True
    assert checks["true_content_mismatch_fails_after_fallback_checks"] is True


def test_adversarial_hash_policy_cases_cover_text_gate_requirements() -> None:
    proof = builder.run_adversarial_hash_policy_probe()
    assert proof["status"] == "PASS"
    cases = {case["case_id"]: case for case in proof["cases"]}

    text_case = cases["STRICT_TEXT_EOL_PORTABILITY_ACCEPTED_ONLY_BY_TEXT_FALLBACK"]
    assert text_case["target_package_verifier_accepts"] is True
    assert text_case["accepted_only_through_bounded_text_fallback"] is True
    assert text_case["raw_sha_matches"] is False
    assert text_case["target_entry_allows_lf_normalized_fallback"] is True
    assert text_case["target_lf_normalized_hash_matches_manifest"] is True

    mutation_case = cases["STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED"]
    assert mutation_case["target_package_verifier_accepts"] is False
    assert mutation_case["target_lf_normalized_hash_matches_manifest"] is False

    binary_case = cases["STRICT_BINARY_NON_TEXT_RAW_SHA_DRIFT_REJECTED_EVEN_WITH_SYNTHETIC_LF_MATCH"]
    assert binary_case["target_package_verifier_accepts"] is False
    assert binary_case["target_entry_allows_lf_normalized_fallback"] is False
    assert binary_case["target_lf_normalized"] is None
    assert binary_case["synthetic_lf_normalized_hash_matches_manifest"] is True
    assert binary_case["raw_sha_matches"] is False

    mutable_case = cases["MUTABLE_CONTEXT_NON_STRICT_DRIFT_WARNING_ONLY"]
    assert mutable_case["strict_hash_recompute"] is False
    assert mutable_case["target_package_verifier_accepts"] is True
    assert mutable_case["target_package_verifier_decision"] == "ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING"

    assert proof["cleanup_verified"] is True
    assert proof["committed_source_artifacts_unchanged"] is True
    assert proof["temporary_probe_dir_exists_after_cleanup"] is False


def test_source_hash_and_control_regression_audits_pass() -> None:
    source_hash = builder.audit_source_hash_manifest()
    assert source_hash["status"] == "PASS"
    assert source_hash["content_hash_failure_count"] == 0
    assert source_hash["missing_manifest_path_count"] == 0

    no_leak = builder.audit_no_leak_control_regression()
    assert no_leak["status"] == "PASS"
    assert no_leak["prototype_row_count"] == 298
    assert no_leak["family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert no_leak["row_level_accepted_denominator"] == 225
    assert no_leak["primary_duplicate_key_denominator"] == 182
    assert no_leak["secondary_duplicate_group_denominator"] == 139
    assert no_leak["forbidden_key_hits_in_prototype_rows"] == []
    assert no_leak["prototype_rows_with_open_flags"] == []
    assert no_leak["source_cost_execution_separation_status"] == "PASS"


def test_builder_outputs_acceptance_completion() -> None:
    result = builder.build_artifacts()
    assert result["ok"] is True
    assert result["terminal_verdict"] == builder.ACCEPT_TERMINAL_VERDICT
    assert result["target_repair_closed"] is True
    assert result["remaining_repair_blocker_count"] == 0

    completion_path = builder.OUT_DIR / builder.AUDIT_JSON[7]
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["can_mark_goal_complete_after_verification_and_commit"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert completion["target_repair_closed"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False


def test_verifier_accepts_generated_text_gate_reaudit_artifacts() -> None:
    builder.build_artifacts()
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_verdict"] == builder.ACCEPT_TERMINAL_VERDICT
    assert result["target_repair_closed"] is True
    assert result["remaining_repair_blocker_count"] == 0
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
