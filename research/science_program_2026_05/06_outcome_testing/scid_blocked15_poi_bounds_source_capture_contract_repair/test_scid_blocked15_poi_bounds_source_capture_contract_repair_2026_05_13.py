"""Focused tests for the SCID Blocked15 POI/bounds contract repair route."""

from __future__ import annotations

import json

import build_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13 as builder
import verify_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13 as verifier


def test_upstream_target_cards_are_exact_five() -> None:
    rows = builder.upstream_card_rows()
    assert [row["card_id"] for row in rows] == list(builder.TARGET_CARD_IDS)
    assert all("poi_type_bounds_source" in row["required_capture_groups"] for row in rows)
    assert all(row["may_score_results_now"] is False for row in rows)


def test_source_logger_contract_has_required_parser_hash_asof_redaction_fields() -> None:
    contract = builder.make_source_logger_contract()
    names = {field["name"] for field in contract["field_contracts"]}
    assert set(builder.REQUIRED_ROW_FIELDS) <= names
    assert contract["source_logger_id"] == "source_safe_mso_snapshot_and_poi_logger"
    assert contract["accepted_40_denominator_unblocked_now"] is False
    assert contract["parser_requirement"]["mso_snapshot_hash"].startswith("sha256")
    assert "source_bar_refs.bar_end_exclusive_utc" in contract["as_of_rule"]
    assert "broker" in contract["redaction_rule"]["policy_id"].lower()
    assert "geometry_envelope" in contract["poi_mechanism_families_v2"]


def test_valid_synthetic_fixtures_pass_and_bad_fixtures_fail() -> None:
    rows = builder.make_fixtures()
    registry: dict[str, str] = {}
    seen_pass = 0
    seen_fail = 0
    for row in rows:
        result = verifier.validate_poi_fixture_row(row, registry)
        if row["fixture_expected_status"] == "PASS":
            seen_pass += 1
            assert result["ok"], json.dumps(result, indent=2)
        else:
            seen_fail += 1
            assert not result["ok"], row["candidate_input_row_id"]
            assert set(row["fixture_expected_issue_codes"]) <= set(result["issues"])
    assert seen_pass >= 3
    assert seen_fail >= 7


def test_card_requirement_ledger_keeps_dependencies_fail_closed() -> None:
    ledger = builder.make_card_requirement_ledger(builder.upstream_card_rows())
    assert ledger["all_cards_remain_blocked_for_results"] is True
    assert ledger["accepted_40_denominator_unblocked_now"] is False
    by_card = {row["card_id"]: row for row in ledger["requirements"]}
    assert by_card["ADV-005"]["dependency_groups_that_remain_fail_closed"] == [
        "intended_entry_reference"
    ]
    assert by_card["BEH-002"]["dependency_groups_that_remain_fail_closed"] == [
        "lifecycle_fill_cancel_expiry_source_status"
    ]
    assert by_card["GEO-001"]["dependency_groups_that_remain_fail_closed"] == [
        "framework_setup_family"
    ]


def test_built_route_verifies_after_builder_run() -> None:
    assert builder.OUTPUTS["output_manifest_json"].exists(), "run builder before focused tests"
    result = verifier.verify()
    assert result["ok"], json.dumps(result["issues"], indent=2)
    assert result["target_cards_verified"] == list(builder.TARGET_CARD_IDS)
    assert result["safe_flags"]["promotion_verdict"] == builder.PROMOTION_VERDICT
    assert result["safe_flags"]["validation_safe"] is False
    assert result["safe_flags"]["outcome_review_opened"] is False
    assert result["safe_flags"]["live_effect"] is False
