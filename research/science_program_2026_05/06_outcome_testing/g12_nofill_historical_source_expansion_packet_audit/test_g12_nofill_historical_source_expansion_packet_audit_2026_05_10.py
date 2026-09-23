from __future__ import annotations

import json

import build_g12_nofill_historical_source_expansion_packet_audit_2026_05_10 as builder
import verify_g12_nofill_historical_source_expansion_packet_audit_2026_05_10 as verifier


def _json(name: str) -> dict:
    return json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))


def test_packet_rows_recompute_to_exact_two_admitted_rows() -> None:
    audit, blockers = builder.source_packet_row_recomputation_audit()

    assert blockers == []
    assert audit["packet_row_count_recomputed"] == 2
    assert audit["checks"]["packet_sha_matches_manifest"] is True
    assert [(row["symbol"], row["decision_time_utc"]) for row in audit["observed_rows"]] == builder.EXPECTED_PACKET_ROWS
    assert audit["checks"]["all_rows_have_55_fields"] is True
    assert audit["checks"]["all_rows_have_future20_fields"] is True


def test_source_hash_audit_has_no_strict_parser_tick_or_committed_hash_blockers() -> None:
    audit, blockers = builder.source_hash_parser_hash_audit()

    assert audit["strict_hash_blocker_count"] == len(blockers) == 3
    assert {blocker["role"] for blocker in blockers} == {
        "parser_or_verifier:builder",
        "parser_or_verifier:focused_tests",
        "parser_or_verifier:verifier",
    }
    assert all(blocker["exact_repair_requirement"] for blocker in blockers)
    assert audit["checks"]["parser_manifest_matches_current_target_builder"] is False
    assert audit["checks"]["packet_rows_bind_same_parser_hash"] is False
    assert audit["checks"]["target_builder_verifier_tests_committed"] is True


def test_contamination_embargo_and_duplicate_controls_remain_closed() -> None:
    contamination, contamination_blockers = builder.contamination_purge_embargo_audit()
    duplicate, duplicate_blockers = builder.duplicate_denominator_audit()

    assert contamination_blockers == []
    assert contamination["audit_passed"] is True
    assert contamination["admitted_row_count"] == 2
    assert duplicate_blockers == []
    assert duplicate["row_level_count"] == 2
    assert duplicate["primary_duplicate_denominator"]["unique_count"] == 2
    assert duplicate["secondary_duplicate_denominator"]["unique_count"] == 2


def test_55_field_and_future20_controls_match_runtime_contract() -> None:
    field, field_blockers = builder.field_55_binding_audit()
    future20, future_blockers = builder.future20_extraction_fail_closed_audit()

    assert field_blockers == []
    assert field["runtime_field_count"] == 55
    assert field["binding_class_counts"] == builder.EXPECTED_BINDING_CLASS_COUNTS
    assert future_blockers == []
    assert future20["runtime_future20_field_count"] == 20
    assert future20["status_counts"] == builder.EXPECTED_FUTURE20_STATUS_COUNTS


def test_forbidden_noleak_and_blocker_reject_exactness_audits_pass() -> None:
    noleak, noleak_blockers = builder.forbidden_redacted_noleak_audit()
    blocker, blocker_issues = builder.blocker_reject_exactness_audit()

    assert noleak_blockers == []
    assert noleak["audit_passed"] is True
    assert blocker_issues == []
    assert blocker["blocked_candidate_count"] == 37
    assert blocker["rejected_candidate_count"] == 9
    assert blocker["audit_passed"] is True


def test_completion_audit_maps_prompt_requirements_after_build() -> None:
    completion = _json(f"{builder.OUTPUT_PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json")

    assert completion["completion_standard_satisfied"] is True
    assert completion["terminal_decision"] == builder.BLOCKER_TERMINAL_DECISION
    assert completion["exact_repair_source_requirement_count"] == 3
    assert completion["missing_incomplete_or_weak_requirements"] == []
    requirement_ids = {row["requirement_id"] for row in completion["prompt_to_artifact_checklist"]}
    assert {
        "two_admitted_rows",
        "source_hash_parser_hash",
        "contamination_embargo",
        "field_55_binding",
        "future20",
        "forbidden_noleak",
        "duplicates",
        "blocked_rejected",
        "saturation",
        "future_route",
    }.issubset(requirement_ids)


def test_verifier_accepts_current_g12_packet_audit_package() -> None:
    result = verifier.verify()

    assert result["ok"] is True
    assert result["terminal_decision"] == builder.BLOCKER_TERMINAL_DECISION
    assert result["packet_row_count"] == 2
    assert result["blocked_candidate_count"] == 37
    assert result["rejected_candidate_count"] == 9
    assert result["field_count"] == 55
    assert result["future20_field_count"] == 20
    assert result["exact_repair_source_requirement_count"] == 3
