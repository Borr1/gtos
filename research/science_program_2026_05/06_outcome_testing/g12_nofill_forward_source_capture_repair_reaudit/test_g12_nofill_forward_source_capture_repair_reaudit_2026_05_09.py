from __future__ import annotations

import json

import build_g12_nofill_forward_source_capture_repair_reaudit_2026_05_09 as builder
import verify_g12_nofill_forward_source_capture_repair_reaudit_2026_05_09 as verifier


def test_adversarial_hash_policy_cases_cover_prompt_requirements() -> None:
    proof = builder.run_adversarial_hash_policy_probe()
    cases = {case["case_id"]: case for case in proof["cases"]}

    text_case = cases["STRICT_TEXT_EOL_PORTABILITY_ACCEPTED"]
    assert text_case["target_package_verifier_accepts"] is True
    assert text_case["safe_policy_accepts"] is True
    assert text_case["actual_raw"] != text_case["expected_raw"]
    assert text_case["actual_lf_normalized"] == text_case["expected_lf_normalized"]

    mutation_case = cases["STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED"]
    assert mutation_case["target_package_verifier_accepts"] is False
    assert mutation_case["safe_policy_accepts"] is False
    assert mutation_case["actual_lf_normalized"] != mutation_case["expected_lf_normalized"]

    binary_case = cases["STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED"]
    assert binary_case["is_text_artifact_by_audit_policy"] is False
    assert binary_case["target_package_verifier_accepts"] is True
    assert binary_case["safe_policy_accepts"] is False
    assert binary_case["actual_raw"] != binary_case["expected_raw"]
    assert binary_case["actual_lf_normalized"] == binary_case["expected_lf_normalized"]

    mutable_case = cases["MUTABLE_CONTEXT_NON_STRICT_DRIFT_ALLOWED"]
    assert mutable_case["strict_hash_recompute"] is False
    assert mutable_case["target_package_verifier_accepts"] is True
    assert mutable_case["safe_policy_accepts"] is True

    assert proof["cleanup_verified"] is True
    assert proof["committed_source_artifacts_unchanged"] is True
    assert proof["temporary_probe_dir_exists_after_cleanup"] is False


def test_source_inspection_finds_raw_recompute_and_missing_text_gate() -> None:
    inspection = builder.inspect_repaired_verifier_source()
    assert inspection["raw_recompute_line"] is not None
    assert inspection["mutable_context_line"] is not None
    assert inspection["lf_fallback_line"] is not None
    assert inspection["lf_fallback_warning_line"] is not None
    assert inspection["content_failure_line"] is not None
    assert inspection["fallback_text_gate_present"] is False
    assert inspection["source_inspection_status"] == "FAIL_TEXT_GATE_ABSENT"


def test_package_invariants_and_no_leak_controls_are_unchanged() -> None:
    audit = builder.audit_no_leak_control_regression()
    assert audit["status"] == "PASS"
    assert audit["prototype_row_count"] == 298
    assert audit["family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert audit["row_level_accepted_denominator"] == 225
    assert audit["primary_duplicate_key_denominator"] == 182
    assert audit["secondary_duplicate_group_denominator"] == 139
    assert audit["forbidden_key_hits_in_prototype_rows"] == []
    assert audit["prototype_rows_with_open_flags"] == []
    assert audit["same_tick_ambiguity_fixture_present"] is True


def test_builder_outputs_remaining_exact_repair_blocker_completion() -> None:
    result = builder.build_artifacts()
    assert result["ok"] is True
    assert result["terminal_verdict"] == builder.TERMINAL_VERDICT
    assert result["target_repair_closed"] is False
    assert result["remaining_repair_blocker_count"] == 1

    completion_path = builder.OUT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-09.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["can_mark_goal_complete_after_verification_and_commit"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False


def test_verifier_accepts_generated_reaudit_artifacts() -> None:
    builder.build_artifacts()
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_verdict"] == builder.TERMINAL_VERDICT
    assert result["target_repair_closed"] is False
    assert result["remaining_repair_blocker_count"] == 1
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
