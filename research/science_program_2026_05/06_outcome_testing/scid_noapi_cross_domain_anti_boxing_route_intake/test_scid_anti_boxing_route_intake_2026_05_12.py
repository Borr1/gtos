from __future__ import annotations

import json
from pathlib import Path

from verify_scid_anti_boxing_route_intake_2026_05_12 import REQUIRED_DOMAINS, verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "SCID_ANTI_BOXING"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_upstream_reconstruction_preserves_denominators():
    inventory = load_json("ROUTE_FAMILY_INVENTORY")
    upstream = inventory["upstream_reconstruction"]

    assert inventory["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert inventory["validation_safe"] is False
    assert inventory["outcome_review_opened"] is False
    assert inventory["live_effect"] is False
    assert inventory["accepted_40_is_floor_not_ceiling"] is True
    assert upstream["accepted_card_count"] == 40
    assert upstream["ready_card_count"] == 8
    assert upstream["blocked_card_count"] == 32
    assert upstream["preserved_target_expansion_candidate_count"] == 8
    assert upstream["g0_discovered_expansion_candidate_count"] == 4
    assert upstream["all_expansion_candidates_denominator_inclusion_false"] is True


def test_route_families_cover_required_domains_and_stay_broad():
    inventory = load_json("ROUTE_FAMILY_INVENTORY")
    families = inventory["route_families"]
    domains = {row["science_domain"] for row in families}

    assert len(families) >= 40
    assert REQUIRED_DOMAINS.issubset(domains)
    assert inventory["current_gtos_ob_retest_logic_is_not_research_horizon"] is True
    assert all(row["may_open_outcomes_or_results_in_this_route"] is False for row in families)
    assert all(row["why_not_current_gtos_ob_framing"] for row in families)
    assert any(row["science_domain"] == "failure_anatomy_derived_hypotheses" for row in families)
    assert any(row["science_domain"] == "auction_microstructure_orderflow_liquidity" for row in families)
    assert any(row["science_domain"] == "macro_calendar_cross_asset" for row in families)


def test_source_contracts_and_negative_evidence_are_auditable():
    contracts = load_json("SOURCE_CONTRACT_TEMPLATES")
    negative = load_json("NEGATIVE_EVIDENCE_LEDGER")
    criteria = load_json("CANDIDATE_ACCEPTANCE_REJECTION_CRITERIA")

    assert contracts["template_count"] >= 10
    assert all(template["required_fields"] for template in contracts["templates"])
    assert all(template["as_of_rule"] for template in contracts["templates"])
    assert all(template["searched_root_expectations"] for template in contracts["templates"])
    assert all(template["hash_deferral_policy"] for template in contracts["templates"])
    assert all(template["no_leak_rules"] for template in contracts["templates"])
    assert all(template["fail_closed_statuses"] for template in contracts["templates"])
    assert negative["negative_evidence_count"] >= 6
    assert any(row["status"] == "REJECTED_AS_BOXED" for row in negative["negative_evidence_rows"])
    assert any("broker" in " ".join(criteria["rejection_criteria"]) for _ in [0])


def test_ranking_and_prompt_packs_are_complete_and_bounded():
    ranking = load_json("ROUTE_RANKING_MATRIX")
    manifest = load_json("PROMPT_PACK_MANIFEST")
    ranked = ranking["ranked_route_families"]

    scores = [row["rank_score"] for row in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranking["route_family_count"] == len(ranked)
    assert manifest["prompt_pack_count"] >= len(REQUIRED_DOMAINS)
    assert manifest["all_required_domains_have_prompt_pack"] is True

    for pack in manifest["prompt_packs"]:
        prompt = (ROOT / pack["prompt_path"]).read_text(encoding="utf-8")
        starter = (ROOT / pack["starter_path"]).read_text(encoding="utf-8").strip()
        assert prompt.startswith("# ")
        assert "Do not rely on chat memory" in prompt
        assert "Current GTOS OB/retest logic is not the research horizon" in prompt
        assert "NO_PROMOTION_VERDICT" in prompt
        assert "validation_safe=false" in prompt
        assert "outcome_review_opened=false" in prompt
        assert "live_effect=false" in prompt
        assert starter.startswith("/goal Follow the full controlling prompt")
        assert "\n" not in starter


def test_completion_audit_answers_prompt_closure_questions():
    audit = load_json("COMPLETION_AUDIT")
    questions = audit["completion_questions"]

    assert audit["all_checklist_items_satisfied"] is True
    assert questions["stayed_open_beyond_current_ob_gtos_framing"] is True
    assert set(questions["new_domains_or_mechanisms_found"]) == REQUIRED_DOMAINS
    assert questions["rejected_with_evidence"]
    assert questions["preserved_for_future_g12_g0_filtering"] >= len(REQUIRED_DOMAINS)
    assert questions["immediate_parallel_routes_that_can_run_next"]


def test_standalone_verifier_passes_and_marks_focused_tests_ok():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["accepted_card_count_verified"] == 40
    assert result["ready_card_count_verified"] == 8
    assert result["blocked_card_count_verified"] == 32
    assert result["route_family_count_verified"] >= 40
    assert result["required_domain_count_verified"] == len(REQUIRED_DOMAINS)
    assert result["prompt_pack_count_verified"] >= len(REQUIRED_DOMAINS)
