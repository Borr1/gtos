"""Focused tests for the Blocked17 LTF as-of path attachment G12 audit."""

from __future__ import annotations

import json

import build_g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_2026_05_13 as builder


def load_json(name: str) -> dict:
    return json.loads((builder.ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_denominator_and_source_exists_subset_are_exact() -> None:
    source = load_json(builder.JSON_OUTPUTS["source_status"])
    noleak = load_json(builder.JSON_OUTPUTS["denominator_noleak"])

    assert source["ok"] is True
    assert source["source_exists_card_count"] == 13
    assert source["source_exists_field_row_count"] == 78
    assert set(source["source_exists_card_ids"]) == builder.EXPECTED_SOURCE_EXISTS_CARD_IDS
    assert set(source["source_exists_fields"]) == builder.REQUIRED_LTF_FIELDS

    assert noleak["ok"] is True
    assert noleak["included_blocked17_count"] == 17
    assert noleak["source_exists_card_count"] == 13
    assert noleak["ready8_overlap_count"] == 0
    assert noleak["expansion_overlap_count"] == 0
    assert noleak["blocked15_overlap_count"] == 0


def test_parser_hash_asof_rows_are_attached_and_fail_closed() -> None:
    audit = load_json(builder.JSON_OUTPUTS["parser_hash_asof"])

    assert audit["ok"] is True
    assert audit["attachment_row_count"] == 78
    assert audit["source_exists_card_count"] == 13
    assert audit["all_rows_parser_bound_hash_asof_and_fail_closed"] is True
    assert set(audit["required_parser_binding_families"]) == builder.REQUIRED_BINDING_FAMILIES
    assert audit["candidate_rowset_recompute"]["sha256_matches_manifest"] is True
    assert audit["candidate_rowset_recompute"]["row_count"] == 3014
    assert audit["candidate_rowset_recompute"]["duplicate_key_collision_count"] == 0
    assert audit["candidate_rowset_recompute"]["forbidden_field_names"] == []
    rules = " ".join(audit["decision_window_asof_rules"])
    assert "decision_asof_utc is the hard upper bound" in rules
    assert "decision_minus_window_start_utc must be present" in rules
    assert "fails closed" in rules


def test_missing_requirements_are_exact_and_g12_requirement_is_closed() -> None:
    audit = load_json(builder.JSON_OUTPUTS["missing_exact"])

    assert audit["ok"] is True
    assert audit["vague_blocker_count"] == 0
    assert audit["source_exists_rows_left_as_unreduced_blocker"] == 0
    assert audit["exact_requirement_count"] == 4
    assert audit["g12_audit_requirement_closed_count"] == 1
    assert audit["downstream_exact_requirement_count"] == 3
    assert {row["requirement_id"] for row in audit["exact_requirements"]} == {
        "REQ-LTF-HASH-001",
        "REQ-LTF-HASH-002",
        "REQ-LTF-WINDOW-003",
        "REQ-G12-AUDIT-004",
    }


def test_decision_completion_and_safe_flags() -> None:
    decision = load_json(builder.JSON_OUTPUTS["decision"])
    completion = load_json(builder.JSON_OUTPUTS["completion"])
    saturation = load_json(builder.JSON_OUTPUTS["saturation"])

    for payload in (decision, completion, saturation):
        for key, expected in builder.SAFE_FLAGS.items():
            assert payload[key] == expected
        assert payload["route_id"] == builder.ROUTE_ID
        assert payload["evidence_class"] == builder.EVIDENCE_CLASS

    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["terminal_blockers"] == []
    assert completion["completion_standard_satisfied"] is True
    assert completion["missing_incomplete_or_weakly_verified_requirements"] == []
    assert saturation["ok"] is True
    assert saturation["same_evidence_class_gaps_remaining"] == []
