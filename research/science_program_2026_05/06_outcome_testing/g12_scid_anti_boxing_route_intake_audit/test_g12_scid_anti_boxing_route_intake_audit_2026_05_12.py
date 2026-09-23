from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_anti_boxing_route_intake_audit_2026_05_12 import (
    REQUIRED_SOURCE_CONTRACT_FIELDS,
    TERMINAL_DECISION,
    verify,
)


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_ANTI_BOXING"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_route_family_recomputation_is_exact():
    audit = load_json("ROUTE_FAMILY_RECOMPUTATION_AUDIT")

    assert audit["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert audit["validation_safe"] is False
    assert audit["outcome_review_opened"] is False
    assert audit["live_effect"] is False
    assert audit["route_family_count"] == 40
    assert audit["route_family_count_exactly_40"] is True
    assert audit["domain_count"] == 10
    assert audit["all_required_domains_covered"] is True
    assert audit["exact_four_families_per_domain"] is True
    assert audit["upstream_reconstruction"]["accepted_card_count"] == 40
    assert audit["upstream_reconstruction"]["ready_card_count"] == 8
    assert audit["upstream_reconstruction"]["blocked_card_count"] == 32
    assert audit["failures"] == []


def test_prompt_packs_are_exact_and_one_line():
    audit = load_json("PROMPT_PACK_AUDIT")

    assert audit["prompt_pack_count"] == 12
    assert audit["prompt_pack_count_exactly_12"] is True
    assert audit["all_starters_one_physical_line"] is True
    assert audit["all_starters_bind_controlling_prompt"] is True
    assert audit["all_required_domains_have_prompt_pack"] is True
    assert audit["failures"] == []


def test_source_contract_repair_is_present_and_complete():
    audit = load_json("SOURCE_CONTRACT_AUDIT")

    assert audit["template_count"] == 10
    assert audit["template_count_exactly_10"] is True
    assert audit["same_evidence_class_repair_applied"]["status"] == "APPLIED_BEFORE_G12_CLOSEOUT"
    assert set(audit["required_contract_fields"]) == set(REQUIRED_SOURCE_CONTRACT_FIELDS)
    assert audit["failures"] == []
    assert all(row["has_all_required_contract_controls"] for row in audit["template_rows"])
    assert all(row["same_evidence_class_repair_fields_present"] for row in audit["template_rows"])


def test_negative_evidence_novelty_and_no_leak_are_closed():
    negative = load_json("NEGATIVE_EVIDENCE_TREATMENT_AUDIT")
    novelty = load_json("ANTI_BOXING_NOVELTY_AUDIT")
    no_leak = load_json("NO_LEAK_FORBIDDEN_SURFACE_AUDIT")

    assert negative["negative_evidence_count"] >= 8
    assert negative["all_negative_rows_preserve_learning"] is True
    assert negative["has_boxed_route_rejection"] is True
    assert novelty["all_40_have_non_ob_rationale"] is True
    assert novelty["breadth_verdict"] == "PASS_PRESERVE_CREATIVE_OUTSIDE_CURRENT_GTOS_BREADTH"
    assert no_leak["forbidden_surfaces_closed"] is True
    assert no_leak["json_artifact_safe_flag_failures"] == []
    assert no_leak["route_family_safe_flag_failures"] == []


def test_decision_completion_and_g0_prompt_are_bounded():
    decision = load_json("DECISION_LEDGER")
    completion = load_json("COMPLETION_AUDIT")
    starter = ROUTE_DIR / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_STARTER_2026-05-12.txt"
    prompt = ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md"

    assert decision["terminal_decision"] == TERMINAL_DECISION
    assert decision["child_routes_launched"] is False
    assert completion["all_checklist_items_satisfied"] is True
    assert prompt.exists()
    assert starter.exists()
    assert "\n" not in starter.read_text(encoding="utf-8").strip()


def test_standalone_verifier_passes_with_target_and_focused_flags():
    result = verify(mark_target_tests_ok=True, mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["target_verifier_ok"] is True
    assert result["target_focused_tests_ok"] is True
    assert result["g12_focused_tests_ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["route_family_count_verified"] == 40
    assert result["required_domain_count_verified"] == 10
    assert result["prompt_pack_count_verified"] == 12
    assert result["source_contract_template_count_verified"] == 10
