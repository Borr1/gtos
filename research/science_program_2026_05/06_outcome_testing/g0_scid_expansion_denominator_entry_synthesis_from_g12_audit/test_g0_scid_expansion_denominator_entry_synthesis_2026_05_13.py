from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_expansion_denominator_entry_synthesis_2026_05_13 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_decision_ledger_reconciles_g12_facts_and_safe_flags():
    decision = load_json("DECISION_LEDGER")
    facts = decision["accepted_audit_facts"]

    assert decision["terminal_decision"] == (
        "ACCEPT_AS_G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_WITH_QUARANTINED_ROUTE_PLAN"
    )
    assert facts["total_quarantined_expansion_candidates"] == 24
    assert facts["original_8"] == 8
    assert facts["g0_4"] == 4
    assert facts["r4_12"] == 12
    assert facts["accepted_40_overlap"] == 0
    assert facts["accepted_40_count"] == 40
    assert decision["route_family_decision_counts"] == {"accepted": 24, "deferred": 0, "rejected": 0}
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["opens_result_scoring"] is False


def test_route_family_ledger_covers_all_24_once_with_exact_prompts():
    ledger = load_json("ROUTE_FAMILY_LEDGER")
    rows = ledger["rows"]
    ids = [row["candidate_id"] for row in rows]

    assert ledger["candidate_count"] == 24
    assert ledger["accepted_count"] == 24
    assert ledger["deferred_count"] == 0
    assert ledger["rejected_count"] == 0
    assert len(ids) == len(set(ids)) == 24
    assert all(row["accepted_40_card_denominator_inclusion"] is False for row in rows)
    assert all(row["may_open_results_now"] is False for row in rows)
    assert all(row["same_evidence_class_blocker_status"] == "REDUCED_TO_EXACT_RUNNABLE_SOURCE_CONTROL_PROMPT" for row in rows)
    assert all((ROOT / row["exact_next_prompt"]).exists() for row in rows)
    assert all((ROOT / row["exact_next_starter"]).exists() for row in rows)


def test_ranked_plan_assigns_all_candidates_to_six_route_packs():
    plan = load_json("RANKED_ROUTE_PLAN")
    packs = plan["ranked_route_packs"]
    covered = [cid for pack in packs for cid in pack["candidate_ids"]]

    assert plan["route_pack_count"] == 6
    assert plan["accepted_24_candidate_count"] == 24
    assert plan["accepted_overflow_support_count"] >= 12
    assert len(covered) == len(set(covered)) == 24
    assert plan["immediate_result_execution_allowed"] is False
    assert all(pack["route_decision"] == "ACCEPTED_NEXT_SOURCE_CONTROL_ROUTE_PACK" for pack in packs)
    assert all(pack["may_open_results_now"] is False for pack in packs)


def test_prompt_packs_are_runnable_and_boundary_hardened():
    prompt_manifest = load_json("PROMPT_PACKS")

    assert prompt_manifest["prompt_pack_count"] == 6
    for row in prompt_manifest["prompt_packs"]:
        prompt_text = (ROOT / row["prompt_path"]).read_text(encoding="utf-8")
        starter_text = (ROOT / row["starter_path"]).read_text(encoding="utf-8").strip()

        assert starter_text.startswith("/goal Follow the full controlling prompt")
        assert "\n" not in starter_text
        assert len(starter_text) < 4000
        for phrase in [
            "Do not rely on chat memory",
            "accepted-40 denominator quarantine",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            assert phrase in prompt_text or phrase in starter_text


def test_quarantine_overflow_and_blocker_pursuit_are_explicit():
    quarantine = load_json("DENOMINATOR_QUARANTINE_PROOF")
    overflow = load_json("EXPANSION_OVERFLOW_LEDGER")
    blocker = load_json("BLOCKER_PURSUIT_LEDGER")

    assert quarantine["accepted_40_count_recomputed_from_g12"] == 40
    assert quarantine["candidate_overlap_count"] == 0
    assert quarantine["all_route_family_rows_denominator_inclusion_false"] is True
    assert quarantine["all_overflow_rows_denominator_inclusion_false"] is True
    assert quarantine["accepted_40_unchanged"] is True

    assert overflow["overflow_count"] == 40
    assert overflow["accepted_support_count"] >= 12
    assert overflow["deferred_to_existing_child_sequencing_count"] > 0
    assert all(row["overflow_candidate_id"].startswith("OVF-ANTI-") for row in overflow["rows"])
    assert all(row["accepted_40_card_denominator_inclusion"] is False for row in overflow["rows"])

    assert len(blocker["candidate_blocker_rows"]) == 24
    assert all(row["source_materialization_status"] == "EXACT_RUNNABLE_PROMPT_EMITTED" for row in blocker["candidate_blocker_rows"])
    assert all(row["access_status"] == "NO_RUNTIME_ACCESS_REQUIRED_FOR_G0_SYNTHESIS" for row in blocker["candidate_blocker_rows"])


def test_saturation_and_parallelization_do_not_box_the_next_wave():
    saturation = (ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md").read_text(encoding="utf-8")
    parallel = load_json("PARALLELIZATION_PLAN")

    for phrase in ["OB-only", "accepted 40", "anti-boxing", "blocker classification"]:
        assert phrase in saturation
    assert len(parallel["wave_1_parallelizable_route_packs"]) == 3
    assert len(parallel["wave_2_parallelizable_route_packs_after_wave_1_source_hash_contracts"]) == 3
    assert any("Any future result-scoring or validation route" in row for row in parallel["do_not_parallelize"])


def test_standalone_verifier_passes_and_marks_focused_tests_ok():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["candidate_count_verified"] == 24
    assert result["route_pack_count_verified"] == 6
    assert result["overflow_count_verified"] == 40
    assert result["accepted_40_overlap_verified"] == 0
