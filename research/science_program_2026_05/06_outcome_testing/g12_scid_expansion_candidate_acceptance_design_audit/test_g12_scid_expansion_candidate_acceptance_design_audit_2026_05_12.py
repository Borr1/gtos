from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_expansion_candidate_acceptance_design_audit_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_EXPANSION_AUDIT"


def load(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_candidate_counts_are_exact_and_quarantined():
    counts = load("CANDIDATE_COUNT_AUDIT")
    quarantine = load("DENOMINATOR_QUARANTINE_AUDIT")

    assert counts["candidate_count_recomputed"] == 24
    assert counts["unique_candidate_count_recomputed"] == 24
    assert counts["candidate_origin_counts_recomputed"] == {
        "preserved_original_8_from_target_input_design": 8,
        "preserved_g0_discovered_4_from_g0_synthesis": 4,
        "r4_artifact_search_discovered_additional_family": 12,
    }
    assert counts["all_candidates_denominator_inclusion_false"] is True
    assert counts["accepted_40_is_floor_not_ceiling"] is True
    assert quarantine["candidate_overlap_count"] == 0
    assert quarantine["candidate_result_label_key_hits"] == []
    assert quarantine["safe_flag_failures"] == []
    assert counts["ok"] is True
    assert quarantine["ok"] is True


def test_source_design_and_criteria_cover_every_candidate():
    source = load("SOURCE_FIELD_DESIGN_AUDIT")

    assert source["inventory_candidate_count"] == 24
    assert source["source_matrix_row_count"] == 24
    assert source["criteria_row_count"] == 24
    assert source["matrix_covers_inventory_exactly"] is True
    assert source["criteria_covers_inventory_exactly"] is True
    assert source["matrix_missing_required_controls"] == []
    assert source["weak_criteria_candidate_ids"] == []
    assert source["novelty_guard_row_count"] == 24
    assert source["novelty_guard_covers_all_candidates"] is True
    assert source["ok"] is True


def test_denominator_floor_and_accepted_40_are_recomputed_from_upstream():
    quarantine = load("DENOMINATOR_QUARANTINE_AUDIT")

    assert quarantine["accepted_40_count_recomputed_from_source_mapping"] == 40
    assert quarantine["accepted_40_count_recomputed_from_terminal_status"] == 40
    assert quarantine["accepted_mapping_and_terminal_card_ids_match"] is True
    assert quarantine["accepted_domain_count_recomputed"] == 8
    assert set(quarantine["accepted_domain_counts_recomputed"].values()) == {5}
    assert quarantine["candidate_overlap_with_accepted_40_card_ids"] == []
    assert quarantine["no_candidate_inherits_result_labels_or_accepted_status"] is True


def test_anti_boxing_source_search_and_negative_evidence_pass():
    novelty = load("NOVELTY_ANTI_BOXING_AUDIT")
    source_search = load("SOURCE_SEARCH_AUDIT")
    negative = load("NEGATIVE_EVIDENCE_AUDIT")

    assert novelty["ok"] is True
    assert all(novelty["anti_boxing_checks"].values())
    assert len(novelty["r4_required_family_ids_present"]) == 12
    assert source_search["ok"] is True
    assert all(source_search["checks"].values())
    assert source_search["source_inventory_count"] >= 1
    assert negative["ok"] is True
    assert negative["negative_evidence_row_count"] >= 6


def test_decision_followups_and_next_prompt_are_safe():
    decision = load("DECISION_LEDGER")
    followup = load("BLOCKER_FOLLOWUP_LEDGER")

    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_CONTROL_EVIDENCE_ONLY"
    assert decision["terminal_blockers"] == []
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert decision["accepted_promotion"] is False
    assert followup["terminal_blockers"] == []
    assert followup["target_verifier_ok"] is True
    assert followup["ok"] is True
    assert (ROUTE_DIR / "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_STARTER_2026-05-12.txt").exists()


def test_standalone_verifier_passes_after_marking_focused_tests():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["candidate_count_verified"] == 24
    assert result["origin_counts_verified"] == {
        "preserved_original_8_from_target_input_design": 8,
        "preserved_g0_discovered_4_from_g0_synthesis": 4,
        "r4_artifact_search_discovered_additional_family": 12,
    }
    assert result["accepted_40_count_verified"] == 40
    assert result["candidate_overlap_count_verified"] == 0
