from __future__ import annotations

import json

import build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10 as builder
import verify_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10 as verifier


def _json(name: str) -> dict:
    return json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))


def test_runtime_contract_recomputes_55_fields_from_code() -> None:
    audit, blockers = builder.runtime_55_field_contract_audit()

    assert blockers == []
    assert audit["runtime_field_count"] == 55
    assert audit["runtime_unique_field_count"] == 55
    assert audit["runtime_validator_result"]["ok"] is True
    assert audit["status_counts_recomputed_from_coverage"] == builder.EXPECTED_STATUS_COUNTS


def test_future_logger_field_audit_recomputes_20_fields() -> None:
    audit, blockers = builder.future_logger_field_audit()

    assert blockers == []
    assert audit["runtime_future_logger_field_count"] == 20
    assert audit["future_fields_subset_of_55"] is True
    assert audit["future_fields_match_coverage_ledger"] is True
    assert all(row["emits_or_fail_closes"] for row in audit["per_field"])


def test_no_leak_audit_blocks_secret_marker_and_raw_hash_leaks() -> None:
    audit, blockers = builder.forbidden_redaction_no_leak_audit()

    assert blockers == []
    assert audit["secret_marker_leaks"] == []
    assert audit["forbidden_output_keys"] == []
    assert audit["raw_value_hash_hits"] == []
    assert audit["raw_value_hashing_opened"] is False


def test_failopen_audit_proves_ignored_writer_return() -> None:
    audit, blockers = builder.failopen_no_live_behavior_audit()

    assert blockers == []
    assert audit["normal_writer_return_value"] is None
    assert audit["forced_failure_return_value"] is None
    assert audit["forced_failure_exception_escaped"] is False
    assert audit["nofill_writer_call_consumed_count"] == 0


def test_diff_scope_allows_only_target_source_and_test_surface() -> None:
    audit, blockers = builder.diff_scope_call_path_audit()

    assert blockers == []
    assert audit["forbidden_live_surface_paths"] == []
    assert audit["unexpected_code_or_test_paths"] == []
    assert audit["call_path_additive_only"] is True


def test_generated_completion_artifact_maps_prompt_requirements() -> None:
    completion = _json(builder.JSON_ARTIFACTS[12])

    assert completion["completion_standard_satisfied"] is True
    assert completion["terminal_decision"] == builder.ACCEPT_TERMINAL_DECISION
    assert completion["exact_repair_blocker_count"] == 0
    requirement_ids = {row["requirement_id"] for row in completion["prompt_to_artifact_checklist"]}
    assert {
        "runtime_55_fields",
        "future_20_fields",
        "no_raw_leak",
        "fail_open_ignored_return",
        "diff_scope",
        "repair_blockers",
        "safe_flags",
    }.issubset(requirement_ids)


def test_verifier_accepts_current_audit_package() -> None:
    result = verifier.verify()

    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_decision"] == builder.ACCEPT_TERMINAL_DECISION
    assert result["exact_repair_blocker_count"] == 0
