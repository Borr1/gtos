"""Focused tests for the G12 SCID read-only alignment expansion audit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILD_PATH = HERE / "build_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py"
VERIFY_PATH = HERE / "verify_g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit_2026_05_12.py"
PREFIX = "G12_SCID_RO_ALIGN_EXP_AUDIT"
FILE_STEMS = {
    "CONTEXT_AND_INPUT_INVENTORY": "CONTEXT_INPUTS",
    "SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT": "ROOT_RECOMP",
    "COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT": "COVERAGE_BOUNDARY",
    "FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT": "FORBIDDEN_FINGERPRINTS",
    "CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT": "CAPTURE_SATURATION",
    "VERIFIER_TEST_SCOPED_DIRTY_AUDIT": "VERIFIER_DIRTY",
    "DECISION_LEDGER": "DECISION",
    "COMPLETION_AUDIT": "COMPLETION",
}
ACCEPT_DECISION = (
    "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("g12_scid_readonly_alignment_audit_builder", BUILD_PATH)
verifier = load_module("g12_scid_readonly_alignment_audit_verifier", VERIFY_PATH)


def artifact(stem: str):
    return json.loads(
        (HERE / f"{PREFIX}_{FILE_STEMS.get(stem, stem)}_2026-05-12.json").read_text(encoding="utf-8")
    )


def test_coverage_boundary_preserves_exact_ten_groups_and_3014_counts():
    audit = artifact("COVERAGE_BOUNDARY_AND_GROUP_MATRIX_AUDIT")
    assert audit["status"] == "PASS"
    assert len(audit["coverage_groups"]) == 10
    assert set(audit["coverage_groups"]) == builder.EXPECTED_GROUPS
    assert audit["candidate_rows_boundary"] == 3014
    assert audit["duplicate_proxy_denominator_key_boundary"] == 3014
    assert audit["boundary_is_source_control_expectation_only"] is True


def test_root_recomputation_exceeds_twelve_targets_and_includes_absolute_roots():
    audit = artifact("SEARCHED_EXCLUDED_ROOT_RECOMPUTATION_AUDIT")
    assert audit["status"] == "PASS"
    assert audit["searched_more_than_accepted_twelve_targets"] is True
    assert audit["recomputed_from_root_rows"]["parsed_shape_file_count_from_rows"] == 2551
    assert audit["absolute_or_prior_worktree_roots"]
    assert audit["dynamic_exclusions_match_forbidden_ledger"] is True


def test_forbidden_keys_and_fingerprints_are_recomputed_from_disk():
    audit = artifact("FORBIDDEN_KEY_AND_SHAPE_FINGERPRINT_AUDIT")
    assert audit["status"] == "PASS"
    assert audit["blocking_content_hash_mismatch_count"] == 0
    assert audit["content_hash_missing_path_count"] == 0
    assert audit["forbidden_file_exclusion_count"] > 0
    assert audit["forbidden_examples_bad_disposition_count"] == 0
    for category in [
        "broker_account_order_deal_position",
        "credential_or_api",
        "post_outcome_or_validation",
        "result_performance_outcome",
    ]:
        assert category in audit["forbidden_key_category_counts"]


def test_capture_requirements_are_exact_and_do_not_authorize_live_wiring():
    audit = artifact("CAPTURE_REQUIREMENT_AND_SOURCE_SATURATION_AUDIT")
    assert audit["status"] == "PASS"
    assert audit["gate_row_count"] == 10
    assert audit["missing_producer_field_group_count"] == 5
    assert audit["capture_requirements_include_required_controls"] is True
    assert audit["capture_requirements_name_every_missing_field"] is True
    assert audit["historical_truth_inference_allowed_rows"] == []


def test_completion_decision_is_acceptance_only_with_safe_flags():
    decision = artifact("DECISION_LEDGER")
    completion = artifact("COMPLETION_AUDIT")
    assert decision["terminal_decision"] == ACCEPT_DECISION
    assert completion["completion_standard_met"] is True
    assert completion["blocking_failures"] == []
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_standalone_verifier_accepts_generated_audit_artifacts():
    result = verifier.verify()
    assert result["ok"] is True
    assert result["failed_checks"] == []
