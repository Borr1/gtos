"""Focused tests for the SCID expansion candidate acceptance/design route."""

from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_EXPANSION"

ORIGINAL_8_IDS = {
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001",
}
G0_4_IDS = {
    "G0-EXP-PARTITION-001",
    "G0-EXP-DOMAIN-MISSINGNESS-001",
    "G0-EXP-NEGCTRL-001",
    "G0-EXP-ROWSET-001",
}


def load(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_inventory_preserves_floor_and_expands_beyond_first_twelve():
    inventory = load(f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json")
    ids = {row["candidate_id"] for row in inventory["rows"]}

    assert inventory["accepted_40_is_floor_not_ceiling"] is True
    assert inventory["preserved_original_8_count"] == 8
    assert inventory["preserved_g0_discovered_4_count"] == 4
    assert inventory["r4_discovered_additional_count"] >= 8
    assert len(inventory["rows"]) >= 20
    assert ORIGINAL_8_IDS.issubset(ids)
    assert G0_4_IDS.issubset(ids)
    assert all(row["accepted_40_card_denominator_inclusion"] is False for row in inventory["rows"])


def test_source_matrix_and_criteria_cover_every_candidate_with_no_novelty_reject():
    inventory = load(f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json")
    matrix = load(f"{PREFIX}_SOURCE_FIELD_DESIGN_MATRIX_{DATE_TAG}.json")
    criteria = load(f"{PREFIX}_ACCEPTANCE_REJECTION_CRITERIA_{DATE_TAG}.json")

    assert len(matrix["rows"]) == len(inventory["rows"])
    assert len(criteria["rows"]) == len(inventory["rows"])
    assert criteria["novelty_alone_is_never_rejection_reason"] is True
    for row in matrix["rows"]:
        assert row["source_fields_or_groups"]
        assert row["as_of_rules"]
        assert row["duplicate_policy"]
        assert row["forbidden_fields"]
        assert row["no_leak_requirements"]
    for row in criteria["rows"]:
        assert row["novelty_alone_is_rejection_reason"] is False
        assert len(row["acceptance_criteria"]) >= 4
        assert len(row["rejection_criteria"]) >= 4


def test_denominator_quarantine_is_exact_and_no_overlap_with_accepted_40():
    quarantine = load(f"{PREFIX}_DENOMINATOR_QUARANTINE_PROOF_{DATE_TAG}.json")

    assert quarantine["accepted_40_card_denominator_count"] == 40
    assert quarantine["accepted_40_card_denominator_unchanged"] is True
    assert quarantine["accepted_40_is_floor_not_ceiling"] is True
    assert quarantine["candidate_overlap_count"] == 0
    assert quarantine["candidate_overlap_with_accepted_40_card_ids"] == []
    assert quarantine["all_candidates_denominator_inclusion_false"] is True
    assert set(quarantine["preserved_original_8_ids"]) == ORIGINAL_8_IDS
    assert set(quarantine["preserved_g0_4_ids"]) == G0_4_IDS


def test_ranking_prompts_and_negative_evidence_are_not_compact_only():
    ranking = load(f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json")
    negative = load(f"{PREFIX}_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_{DATE_TAG}.json")

    totals = [row["total_score"] for row in ranking["rows"]]
    assert totals == sorted(totals, reverse=True)
    assert len(ranking["prompt_packs"]) >= 3
    assert ranking["top_candidate_ids"]
    for pack in ranking["prompt_packs"]:
        assert pack["starter_one_physical_line"] is True
        assert Path(ROUTE_DIR.parents[3] / pack["prompt_path"]).exists()
        assert Path(ROUTE_DIR.parents[3] / pack["starter_path"]).exists()

    search = negative["searched_artifacts_proof"]
    assert len(search["artifact_search_scopes"]) >= 6
    assert len(search["local_heavy_roots_checked"]) >= 5
    assert search["source_inventory_summary"]["source_inventory_count"]
    assert "floor" in negative["anti_boxing_conclusion"].lower()


def test_completion_audit_and_saturation_bind_prompt_requirements():
    completion = load(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json")
    saturation = (ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md").read_text(encoding="utf-8")

    assert completion["all_checklist_items_pass"] is True
    requirements = {row["requirement"] for row in completion["prompt_to_artifact_checklist"]}
    assert any("preserve original 8" in requirement for requirement in requirements)
    assert any("preserve G0" in requirement for requirement in requirements)
    assert any("source-field design matrix" in requirement for requirement in requirements)
    assert "Original 8 preserved exactly" in saturation
    assert "G0 4 preserved exactly" in saturation
    assert "R4 additional families added" in saturation
    assert "Deliberately Not Answered" in saturation
