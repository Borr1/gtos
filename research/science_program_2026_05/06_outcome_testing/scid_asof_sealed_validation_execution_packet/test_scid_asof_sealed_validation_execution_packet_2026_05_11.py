"""Focused tests for the SCID as-of sealed-validation execution packet."""

from __future__ import annotations

import json
from pathlib import Path

import build_scid_asof_sealed_validation_execution_packet_2026_05_11 as builder
from verify_scid_asof_sealed_validation_execution_packet_2026_05_11 import verify


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_builder_emits_exact_blocked_packet_without_result_rows():
    completion = builder.build()
    assert completion["terminal_decision"] == "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
    assert completion["can_mark_goal_complete"], completion["failed_checks"]

    freeze = load_json(
        builder.ROUTE_DIR
        / f"{builder.PREFIX}_PREOUTCOME_FREEZE_PACKET_{builder.DATE_TAG}.json"
    )
    assert freeze["freeze_packet_emitted_before_any_result_row"] is True
    assert freeze["result_rows_read_derived_or_written"] is False
    assert freeze["outcome_target_definitions"]["status"] == "MISSING_SPEC"
    assert freeze["sealed_rowset_count"] == 2432
    assert freeze["stress_rowset_count"] == 582
    assert freeze["discovery_exclusion_count"] == 365
    assert freeze["candidate_denominator_group_count"] == 7

    for name in builder.RESULT_ARTIFACT_NAMES:
        assert not (builder.ROUTE_DIR / name).exists(), name
    assert builder.REPAIR_PROMPT.exists()


def test_rowset_manifest_covers_all_rows_and_keeps_stress_separate():
    builder.build()
    rowset = load_json(
        builder.ROUTE_DIR / f"{builder.PREFIX}_FROZEN_ROWSET_MANIFEST_{builder.DATE_TAG}.json"
    )
    assert rowset["candidate_input_row_count"] == 3014
    assert rowset["row_partition_ledger_row_count"] == 3014
    assert rowset["all_candidate_rows_covered_once"] is True
    assert len(rowset["sealed_rowset"]) == 2432
    assert len(rowset["stress_rowset"]) == 582
    assert {row["partition_assignment"] for row in rowset["sealed_rowset"]} == {
        "SEALED_VALIDATION_CANDIDATE_DESIGN"
    }
    assert {row["partition_assignment"] for row in rowset["stress_rowset"]} == {
        "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
    }
    assert all(
        row["row_block_reason"] == "MISSING_FROZEN_OUTCOME_TARGET_AND_HORIZON_SPEC"
        for row in rowset["sealed_rowset"] + rowset["stress_rowset"]
    )


def test_variant_registry_addresses_every_known_family_with_exact_blocker():
    builder.build()
    registry = load_json(
        builder.ROUTE_DIR / f"{builder.PREFIX}_VARIANT_FAMILY_REGISTRY_{builder.DATE_TAG}.json"
    )
    assert registry["all_known_families_addressed"] is True
    assert registry["known_family_count"] == 11
    assert registry["executable_family_count"] == 0
    assert registry["control_only_family_count"] == 4
    assert {row["family_id"] for row in registry["families"]} == set(builder.KNOWN_FAMILIES)
    assert all(
        row["execution_status"] == "NOT_EXECUTABLE_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
        for row in registry["families"]
    )
    assert all(row["missing_fields_or_specs"] for row in registry["families"])


def test_verifier_passes_and_preserves_safe_flags():
    builder.build()
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"]
    assert result["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
    assert result["result_artifacts_absent"] is True
