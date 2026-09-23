from __future__ import annotations

import json

import build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10 as builder
import verify_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10 as verifier


def _json(name: str) -> dict:
    return json.loads((builder.OUT_DIR / name).read_text(encoding="utf-8"))


def test_cat_v3_universe_recomputes_zero_sealed_rows() -> None:
    audit, blockers = builder.cat_v3_universe_zero_sealed_recomputation_audit()

    assert blockers == []
    assert audit["target_row_count"] == 298
    assert audit["target_family_counts"] == builder.EXPECTED_FAMILY_COUNTS
    assert audit["upstream_family_counts"] == builder.EXPECTED_FAMILY_COUNTS
    assert audit["sealed_validation_current_committed_nofill_rows_recomputed"] == 0
    assert audit["sealed_candidate_packet_row_ids"] == []
    assert audit["target_missing_upstream_ids"] == []
    assert audit["target_extra_ids_not_in_upstream"] == []


def test_source_binding_matrix_recomputes_55_and_20_counts() -> None:
    audit, blockers = builder.source_binding_matrix_reaudit()

    assert blockers == []
    assert audit["field_count_recomputed"] == 55
    assert audit["runtime_field_count_recomputed"] == 55
    assert audit["runtime_future_logger_field_count_recomputed"] == 20
    assert audit["design_terminal_status_counts_recomputed"] == builder.EXPECTED_DESIGN_COUNTS
    assert audit["binding_class_counts_recomputed"] == builder.EXPECTED_BINDING_CLASS_COUNTS
    assert audit["forbidden_rows_with_raw_route"] == []


def test_field_blocker_audit_recomputes_exact_20_future_requirements() -> None:
    audit, blockers = builder.field_blocker_exactness_audit()

    assert blockers == []
    assert audit["future_logger_or_source_extraction_requirement_count_recomputed"] == 20
    assert audit["field_blockers_missing_requirement_text"] == []
    assert audit["field_blockers_missing_matrix_support"] == []
    assert audit["field_blockers_missing_status_counts"] == []


def test_duplicate_and_split_controls_recompute_expected_counts() -> None:
    audit, blockers = builder.duplicate_purge_embargo_split_reaudit()

    assert blockers == []
    assert audit["accepted_row_count_recomputed"] == 225
    assert audit["primary_duplicate_key_unique_count_recomputed"] == 182
    assert audit["secondary_duplicate_group_unique_count_recomputed"] == 139
    assert audit["side_counts_recomputed"] == {"LONG": 107, "SHORT": 191}


def test_generated_completion_artifact_maps_prompt_requirements() -> None:
    completion = _json(builder.JSON_ARTIFACTS[13])

    assert completion["completion_standard_satisfied"] is True
    assert completion["terminal_decision"] == builder.ACCEPT_TERMINAL_DECISION
    assert completion["missing_incomplete_or_weak_requirements"] == []
    requirement_ids = {row["requirement_id"] for row in completion["prompt_to_artifact_checklist"]}
    assert {
        "cat_v3_totals",
        "zero_sealed_rows",
        "contamination",
        "field_55_counts",
        "future_20_requirements",
        "duplicate_purge_embargo",
        "local_heavy",
        "safe_flags",
    }.issubset(requirement_ids)


def test_verifier_accepts_current_g12_audit_package() -> None:
    result = verifier.verify()

    assert result["ok"] is True
    assert result["terminal_decision"] == builder.ACCEPT_TERMINAL_DECISION
    assert result["cat_v3_partition_rows"] == 298
    assert result["sealed_validation_current_committed_nofill_rows"] == 0
    assert result["field_count"] == 55
    assert result["future_requirement_count"] == 20
    assert result["exact_repair_source_blocker_count"] == 0
