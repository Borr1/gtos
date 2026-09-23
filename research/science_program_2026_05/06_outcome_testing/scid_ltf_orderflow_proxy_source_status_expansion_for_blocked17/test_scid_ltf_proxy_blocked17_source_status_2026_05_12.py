"""Focused tests for the SCID blocked-17 LTF/proxy source-status packet."""

from __future__ import annotations

import json
from pathlib import Path

import build_scid_ltf_proxy_blocked17_source_status_2026_05_12 as builder
import verify_scid_ltf_proxy_blocked17_source_status_2026_05_12 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-12"


def read_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_recomputed_blocked17_card_set_matches_g0_ledger():
    blocked32 = builder.read_json(builder.BLOCKED_32_PATH)
    decision = builder.read_json(builder.DECISION_PATH)
    card_set, included, excluded = builder.build_card_set(blocked32, decision)

    assert card_set["included_card_count"] == 17
    assert len(included) == 17
    assert len(excluded) == 15
    assert card_set["duplicate_denominator_boundaries"]["accepted_40_card_denominator_count"] == 40
    assert card_set["duplicate_denominator_boundaries"]["ready_8_count"] == 8
    assert card_set["duplicate_denominator_boundaries"]["blocked_32_count"] == 32
    assert card_set["duplicate_denominator_boundaries"]["all_expansion_candidates_outside_accepted_denominator"] is True
    assert "MIC-005" in card_set["included_card_ids"]
    assert "ADV-004" in card_set["excluded_blocked15_card_ids"]


def test_status_classifier_covers_required_dependency_families():
    cases = {
        "candidate_input_row_id": "RECOVERED_SOURCE_BOUND",
        "ltf_source_hash": "SOURCE_EXISTS_NEEDS_PARSER",
        "proxy_instrument": "PROXY_VALIDITY_REQUIRES_CONTRACT",
        "entry_reference_price": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
        "baseline_assignment_seed": "PROSPECTIVE_CAPTURE_REQUIRED",
    }
    for field, expected in cases.items():
        status, reason, source_paths, next_requirement = builder.dependency_field_status(field)
        assert status == expected
        assert reason
        assert source_paths
        assert next_requirement


def test_generated_status_matrix_preserves_no_scoring_and_exact_statuses():
    matrix = read_json(f"SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_{DATE}.json")
    assert matrix["card_count"] == 17
    assert matrix["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert matrix["validation_safe"] is False
    statuses = set()
    for row in matrix["rows"]:
        assert row["may_score_results_now"] is False
        assert row["accepted_denominator_inclusion"] is True
        assert row["expansion_denominator_inclusion"] is False
        for field_row in row["field_status_rows"]:
            statuses.add(field_row["status"])
            assert field_row["next_requirement"]
            assert "needs more data" not in json.dumps(field_row).lower()
    assert {
        "RECOVERED_SOURCE_BOUND",
        "SOURCE_EXISTS_NEEDS_PARSER",
        "PROXY_VALIDITY_REQUIRES_CONTRACT",
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
        "PROSPECTIVE_CAPTURE_REQUIRED",
    }.issubset(statuses)


def test_source_inventory_and_proxy_matrix_are_context_only():
    inventory = read_json(f"SCID_LTF_PROXY_SOURCE_INVENTORY_{DATE}.json")
    proxy = read_json(f"SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_{DATE}.json")

    assert inventory["source_inventory_count"] >= 100
    assert inventory["raw_market_blob_commits_added"] == 0
    assert inventory["forbidden_broker_account_order_history_deal_position_sources_consumed"] == 0
    assert inventory["source_category_counts"]["BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"] >= 1
    assert inventory["source_category_counts"]["SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"] >= 1
    assert proxy["broker_native_cfd_truth_claims"] == 0
    assert proxy["proxy_rows_context_only"] >= 1
    assert all(row["broker_cfd_truth_allowed"] is False for row in proxy["equivalence_rows"])
    assert all(row["equivalence_status"] == "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY" for row in proxy["equivalence_rows"])


def test_route_verifier_accepts_current_packet():
    result = verifier.verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["summary"]["included_card_count"] == 17
