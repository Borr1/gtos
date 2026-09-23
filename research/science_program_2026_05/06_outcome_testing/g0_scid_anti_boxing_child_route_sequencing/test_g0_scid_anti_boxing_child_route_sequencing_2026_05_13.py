from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_anti_boxing_child_route_sequencing_2026_05_13 import (
    REQUIRED_CHILD_ROUTES,
    REQUIRED_DOMAINS,
    TERMINAL_DECISION,
    verify,
)


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_ANTI_BOXING"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_ranking_covers_all_12_child_routes_and_all_domains():
    ranking = load_json("ROUTE_RANKING_LEDGER")
    rows = ranking["ranked_child_routes"]

    assert ranking["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert ranking["validation_safe"] is False
    assert ranking["outcome_review_opened"] is False
    assert ranking["live_effect"] is False
    assert ranking["child_routes_launched"] is False
    assert len(rows) == 12
    assert {row["route_family_id"] for row in rows} == REQUIRED_CHILD_ROUTES
    assert {row["science_domain"] for row in rows} == REQUIRED_DOMAINS
    assert [row["sequence_rank"] for row in rows] == list(range(1, 13))
    assert ranking["ranking_is_broad_not_ob_boxed"] is True
    assert all(row["starter_one_physical_line"] for row in rows)
    assert all(row["starter_binds_controlling_prompt"] for row in rows)


def test_parallel_wave_plan_is_staged_and_parallel_inside_waves():
    wave_plan = load_json("PARALLEL_WAVE_PLAN")
    waves = wave_plan["waves"]

    assert wave_plan["wave_count"] == 4
    assert sum(wave["route_count"] for wave in waves) == 12
    assert [wave["stage"] for wave in waves] == [0, 1, 2, 3]
    assert waves[0]["parallel"] is True
    assert waves[1]["parallel"] is True
    assert waves[2]["parallel"] is True
    assert waves[3]["parallel"] is False
    assert [route["route_family_id"] for route in waves[0]["routes"]] == [
        "ADV-002",
        "MISS-001",
        "ADV-004",
        "ADV-001",
    ]


def test_adjacent_followups_are_quarantined_and_not_in_child_denominator():
    adjacent = load_json("ADJACENT_ROUTE_FOLLOWUP_LEDGER")
    rows = adjacent["adjacent_followup_rows"]

    assert adjacent["adjacent_followup_count"] == 28
    assert adjacent["adjacent_followups_are_quarantined"] is True
    assert not (REQUIRED_CHILD_ROUTES & {row["route_family_id"] for row in rows})
    assert all(
        row["quarantine_status"] == "QUARANTINED_ADJACENT_FOLLOWUP_NOT_IN_12_CHILD_PROMPT_PACKS"
        for row in rows
    )
    assert all(row["validation_safe"] is False for row in rows)
    assert all(row["outcome_review_opened"] is False for row in rows)
    assert all(row["live_effect"] is False for row in rows)


def test_no_leak_audit_closes_forbidden_surfaces_and_no_child_launch():
    no_leak = load_json("NO_LEAK_FORBIDDEN_SURFACE_AUDIT")

    assert no_leak["forbidden_surfaces_closed"] is True
    assert no_leak["all_route_rows_safe"] is True
    assert no_leak["all_adjacent_rows_safe"] is True
    assert no_leak["child_routes_launched"] is False
    assert no_leak["no_outcome_result_scoring_or_validation_opened"] is True
    assert no_leak["no_ai_api_or_paid_vendor_opened"] is True
    assert no_leak["no_broker_account_order_history_deal_position_evidence_opened"] is True
    assert no_leak["no_trading_risk_safety_prompt_decision_change"] is True
    assert all(row["exists"] is False for row in no_leak["child_route_dirs_absent_or_not_launched"])


def test_starters_and_completion_audit_are_actionable():
    starters = load_json("ONE_LINE_STARTERS_AND_COMMANDS")
    completion = load_json("COMPLETION_AUDIT")

    assert starters["all_starters_one_physical_line"] is True
    assert starters["all_starters_bind_controlling_prompt"] is True
    assert sum(len(wave["routes"]) for wave in starters["wave_commands"]) == 12
    for wave in starters["wave_commands"]:
        for route in wave["routes"]:
            assert route["codex_command"].startswith("codex --enable goals -C ")
            assert route["one_line_starter"].startswith("/goal Follow the full controlling prompt in ")
            assert "NO_PROMOTION_VERDICT" in route["one_line_starter"]

    assert completion["all_checklist_items_satisfied_by_artifacts"] is True
    assert completion["ranked_child_route_count"] == 12
    assert completion["adjacent_followup_count"] == 28
    assert completion["may_mark_goal_complete_after_verifier_tests_and_commit"] is True


def test_standalone_verifier_passes_with_focused_tests_marked():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["focused_tests_ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["terminal_decision"] == TERMINAL_DECISION
    assert result["ranked_child_route_count_verified"] == 12
    assert result["adjacent_followup_count_verified"] == 28
