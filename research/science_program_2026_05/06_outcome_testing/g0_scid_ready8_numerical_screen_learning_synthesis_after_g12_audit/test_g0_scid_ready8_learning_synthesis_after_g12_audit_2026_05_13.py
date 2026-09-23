from __future__ import annotations

import json

from build_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13 import (
    PROMPT_PATH,
    RANK1_ROUTE,
    STARTER_PATH,
    TERMINAL_DECISION,
    build_artifacts,
    output_path,
)
from verify_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13 import verify


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_builder_reconciles_accepted_facts_and_selects_non_audit_rank1():
    result = build_artifacts(write_outputs=False)
    assert result["terminal_decision"] == TERMINAL_DECISION
    assert result["rank1_route"] == RANK1_ROUTE
    assert result["same_evidence_class_learning_remaining"] == 0
    fact = result["outputs"]["FACT_RECONCILIATION_LEDGER"]
    accepted = fact["accepted_exact_facts"]
    assert accepted["source_candidates"] == 3014
    assert accepted["ready_cards"] == 8
    assert accepted["rowset_candidate_card_rows"] == 24112
    assert accepted["target_result_rows"] == 192896
    assert accepted["horizons"] == [1, 4, 16, 32]
    assert len(accepted["target_families"]) == 2
    assert fact["card_redundancy_reconciled"]["all_card_horizon_target_fingerprints_match_adv001"] is True
    assert "not_a_dead_end" in fact["card_redundancy_reconciled"]


def test_killed_preserved_and_route_ledgers_cover_required_learning():
    killed = read_json(output_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"))
    killed_ids = {row["finding_id"] for row in killed["killed_findings"]}
    assert "KILL001_CARD_LEVEL_MOVEMENT_EDGE_OR_RANKING_FROM_CURRENT_PACKET" in killed_ids
    assert "KILL007_ANOTHER_AUDIT_AS_RANK1_WITH_NO_NEW_ARTIFACT" in killed_ids
    preserved_ids = {row["finding_id"] for row in killed["preserved_findings"]}
    for required in [
        "PRES003_HORIZON_INTELLIGENCE",
        "PRES004_TARGET_FAMILY_INTELLIGENCE",
        "PRES006_FAIL_CLOSED_POLICY",
        "PRES007_DUPLICATE_CONCENTRATION_GUARD",
        "PRES008_CANDIDATE_LEVEL_ANATOMY_CATEGORIES",
    ]:
        assert required in preserved_ids

    ranking = read_json(output_path("ROUTE_RANKING_LEDGER"))
    assert ranking["rank1_selected"] == RANK1_ROUTE
    assert ranking["rank1_is_audit"] is False
    assert len(ranking["routes"]) >= 10
    assert ranking["routes"][0]["route_id"] == RANK1_ROUTE


def test_question_and_blocker_ledgers_leave_no_same_class_learning():
    questions = read_json(output_path("QUESTION_STACK_LEDGER"))
    assert questions["same_evidence_class_learning_remaining"] == 0
    assert len(questions["questions"]) >= 22
    assert all(row["same_evidence_class_remaining_after_answer"] is False for row in questions["questions"])

    blocker = read_json(output_path("BLOCKER_AND_REPAIR_LEDGER"))
    assert blocker["active_same_evidence_class_blockers"] == []
    assert blocker["same_evidence_class_learning_remaining"] == 0
    assert len(blocker["separate_evidence_class_handoffs"]) >= 3


def test_rank1_prompt_and_starter_are_hardened():
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    for phrase in [
        "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY",
        "Do not treat \"cards are redundant\" as a dead end",
        "per-card source-field map",
        "candidate predicate or descriptor-contrast design",
        "duplicate_proxy_denominator_key",
        "Target-opening prerequisites",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "live_effect=false",
    ]:
        assert phrase in prompt

    starter = STARTER_PATH.read_text(encoding="utf-8").strip()
    assert "\n" not in starter
    assert starter.startswith("/goal Follow the full controlling prompt")
    assert RANK1_ROUTE in starter
    assert "all 8 card-specific predicates" in starter
    assert "same-evidence-class repair/design remaining is 0" in starter


def test_verifier_dry_run_passes_without_forbidden_surfaces():
    result = verify(write_result=False, mark_focused_tests_ok=True, mark_context_refreshed=True)
    assert result["ok"] is True
    assert result["failure_count"] == 0
    assert result["opens_validation"] is False
    assert result["opens_ai_api"] is False
    assert result["opens_broker_account_order_history_deal_position_evidence"] is False
    assert result["opens_live_trading_behavior"] is False
    assert result["live_effect"] is False
