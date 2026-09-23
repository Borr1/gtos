from __future__ import annotations

import json
from pathlib import Path

import build_g12_nofill_forward_source_capture_acceptance_audit_2026_05_09 as builder
import verify_g12_nofill_forward_source_capture_acceptance_audit_2026_05_09 as verifier


def test_package_rows_preserve_frozen_equation() -> None:
    package = builder.load_package()
    audit = builder.audit_denominators(package)
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


def test_hash_audit_classifies_line_ending_drift_without_content_failure() -> None:
    package = builder.load_package()
    audit = builder.audit_hash_manifest(package)
    assert audit["content_hash_failure_count"] == 0
    assert audit["missing_manifest_path_count"] == 0
    assert audit["text_eol_only_raw_sha_drift_count"] + audit["raw_sha_text_portability_risk_count"] > 0
    assert audit["package_self_verifier_portability_blocker"] is True


def test_schema_and_no_leak_audits_keep_routes_closed() -> None:
    package = builder.load_package()
    schema = builder.audit_schema_fields(package)
    no_leak = builder.audit_no_leak(package)
    assert schema["status"] == "PASS"
    assert schema["contract_field_count"] == 55
    assert schema["schema_field_count"] == 55
    assert schema["fields_opening_result_or_live_wiring"] == []
    assert no_leak["status"] == "PASS"
    assert no_leak["forbidden_key_hits_in_prototype_rows"] == []
    assert no_leak["result_or_cost_label_creep_hits"] == []


def test_builder_outputs_terminal_verdict_and_completion_audit() -> None:
    result = builder.build_artifacts()
    assert result["ok"] is True
    assert result["terminal_verdict"] == builder.TERMINAL_VERDICT
    completion_path = builder.OUT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["can_mark_goal_complete_after_verification_and_commit"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []


def test_verifier_accepts_generated_audit_artifacts() -> None:
    builder.build_artifacts()
    result = verifier.verify()
    assert result["ok"] is True
    assert result["terminal_verdict"] == builder.TERMINAL_VERDICT
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False

