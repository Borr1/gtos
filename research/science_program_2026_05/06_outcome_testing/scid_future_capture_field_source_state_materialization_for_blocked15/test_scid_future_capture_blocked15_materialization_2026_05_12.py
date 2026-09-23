from __future__ import annotations

import json
from pathlib import Path

import build_scid_future_capture_blocked15_materialization_2026_05_12 as builder
import verify_scid_future_capture_blocked15_materialization_2026_05_12 as verifier

from src.research_infra.forward_capture import SCID_CAPTURE_GROUPS


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_blocked15_subset_is_exact_from_upstream_ledger():
    cards = builder.load_blocked15()

    assert len(cards) == 15
    assert {card["assigned_next_route"] for card in cards} == {builder.ROUTE_ID}
    assert {card["accepted_readiness"] for card in cards} == {"BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS"}


def test_all_ten_capture_groups_remain_visible_in_matrix_and_contract():
    matrix = read_json(builder.OUTPUTS["matrix"])
    contract = read_json(builder.OUTPUTS["prospective_contract"])

    assert set(matrix["accepted_capture_groups"]) == set(SCID_CAPTURE_GROUPS)
    assert {row["field_group"] for row in contract["contracts"]} == set(SCID_CAPTURE_GROUPS)
    assert len(matrix["card_field_group_matrix"]) == 15


def test_recovered_rows_are_valid_scid_rows_without_forbidden_surfaces():
    rows = read_jsonl(builder.OUTPUTS["recovered_rows"])
    report = verifier.verify()

    assert rows
    assert report["recovered_row_validation"]["ok"] is True
    payload = "\n".join(json.dumps(row, sort_keys=True).lower() for row in rows)
    for fragment in builder.FORBIDDEN_TEXT_FRAGMENTS:
        assert fragment not in payload


def test_unblocking_keeps_recovered_rows_outside_result_denominator():
    unblocking = read_json(builder.OUTPUTS["unblocking"])

    assert unblocking["card_count"] == 15
    for card in unblocking["criteria_by_card"]:
        assert card["may_score_results_now"] is False
        assert card["validation_safe"] is False
        assert card["outcome_review_opened"] is False
        for group in card["required_capture_groups"]:
            assert group["does_recovery_unblock_card_now"] is False


def test_completion_audit_and_verifier_allow_goal_close():
    completion = read_json(builder.OUTPUTS["completion"])
    report = verifier.verify()

    assert completion["can_mark_goal_complete"] is True
    assert completion["historical_intent_order_lifecycle_inferred_from_price"] is False
    assert completion["no_validation_or_result_scoring_opened"] is True
    assert report["ok"] is True
    assert report["can_mark_goal_complete"] is True
