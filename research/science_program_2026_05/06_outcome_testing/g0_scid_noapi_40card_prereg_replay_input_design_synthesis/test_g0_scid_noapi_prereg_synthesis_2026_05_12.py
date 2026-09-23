from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_noapi_prereg_synthesis_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_NOAPI_PREREG_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_decision_reconciles_g12_counts_and_safe_flags():
    decision = load_json("DECISION_LEDGER")
    facts = decision["accepted_facts"]

    assert decision["terminal_decision"] == "ACCEPT_AS_G0_SCID_NOAPI_PREREG_SYNTHESIS_WITH_RANKED_NEXT_ROUTE_BUNDLE"
    assert facts["accepted_card_count"] == 40
    assert facts["science_domain_count"] == 8
    assert set(facts["cards_per_domain"].values()) == {5}
    assert facts["readiness_split"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }
    assert facts["outside_current_gtos_ob_framing_count"] == 33
    assert facts["replay_input_packet_design_count"] == 8
    assert facts["blocked_dependency_row_count"] == 32
    assert facts["quarantined_expansion_candidate_count"] == 8
    assert facts["same_evidence_class_capture_groups_pursued"] == 10
    assert facts["capture_groups_resolved_inside_packet_design_scope"] == 8
    assert facts["remaining_exact_dependency_blockers"] == 2
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["opens_result_scoring"] is False


def test_route_ranking_selects_ready8_materialization_before_scoring():
    ranking = load_json("ROUTE_RANKING_MATRIX")
    rows = {row["route_id"]: row for row in ranking["routes"]}

    assert ranking["rank_1_route"] == "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"
    assert ranking["rank_1_is_fastest_valid_noapi_path_toward_result_evidence"] is True
    assert ranking["immediate_result_execution_is_allowed_now"] is False
    assert "target horizons" in ranking["immediate_result_execution_blocker"]
    assert ranking["accepted_40_is_floor_not_ceiling"] is True
    assert len(rows) == 7
    assert rows["SCID_DORMANT_SEALED_RESULT_GATE_AFTER_PACKET_SOURCE_COMPLETION"]["run_state"] == (
        "DO_NOT_RUN_UNTIL_PACKET_AND_SOURCE_DEPENDENCIES_ACCEPTED"
    )
    assert rows["SCID_TARGET_MANIFEST_SELF_HASH_POLICY_MAINTENANCE"]["run_state"] == "OPTIONAL_NONBLOCKING_MAINTENANCE"
    assert all(row["may_open_outcomes_or_results_in_this_route"] is False for row in rows.values())


def test_ready_blocked_expansion_and_followup_ledgers_are_exactly_routed():
    ready = load_json("READY_8_ROUTE_LEDGER")
    blocked = load_json("BLOCKED_32_ROUTE_LEDGER")
    expansion = load_json("EXPANSION_CANDIDATE_LEDGER")
    followup = load_json("NONBLOCKING_FOLLOWUP_LEDGER")

    assert ready["ready_card_count"] == 8
    assert ready["ready_cards_all_routed_to_rank_1"] is True
    assert {row["assigned_next_route"] for row in ready["ready_cards"]} == {
        "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"
    }
    assert all(row["may_score_results_now"] is False for row in ready["ready_cards"])

    assert blocked["blocked_card_count"] == 32
    assert blocked["blocked_readiness_split"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    }
    assert blocked["assigned_route_counts"] == {
        "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15": 15,
        "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17": 17,
    }
    assert blocked["blocked_is_exact_dependency_not_passive_waiting"] is True

    assert expansion["preserved_target_expansion_candidate_count"] == 8
    assert expansion["g0_discovered_additional_candidate_count"] >= 1
    assert expansion["accepted_40_card_denominator_unchanged"] is True
    assert expansion["all_expansion_candidates_remain_outside_accepted_denominator"] is True

    assert followup["nonblocking_followup_count"] == 1
    assert followup["self_hash_issue_is_nonblocking"] is True
    assert followup["fake_blocker_rejected"] is True
    assert followup["nonblocking_followups"][0]["blocks_rank_1"] is False


def test_prompt_packs_and_starters_are_runnable_and_bounded():
    ranking = load_json("ROUTE_RANKING_MATRIX")
    for row in ranking["routes"]:
        prompt_text = (ROOT / row["prompt_path"]).read_text(encoding="utf-8")
        starter_text = (ROOT / row["starter_path"]).read_text(encoding="utf-8").strip()

        assert starter_text.startswith("/goal Follow the full controlling prompt")
        assert "\n" not in starter_text
        assert len(starter_text) < 4000
        for phrase in [
            "Do not rely on chat memory",
            "Current GTOS OB/retest logic is not the research horizon",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            assert phrase in prompt_text, (row["route_id"], phrase)


def test_parallelization_and_saturation_preserve_boundaries():
    parallel = load_json("PARALLELIZATION_PLAN")
    saturation = (ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md").read_text(encoding="utf-8")

    assert "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION" in parallel[
        "run_now_parallel_routes"
    ]
    assert parallel["do_not_run_until_dependency_valid"] == [
        "SCID_DORMANT_SEALED_RESULT_GATE_AFTER_PACKET_SOURCE_COMPLETION"
    ]
    assert parallel["optional_nonblocking_parallel_routes"] == ["SCID_TARGET_MANIFEST_SELF_HASH_POLICY_MAINTENANCE"]
    for phrase in ["OB-only", "passive waiting", "self-hash mismatch as a fake blocker", "No outcome/result"]:
        assert phrase in saturation


def test_standalone_verifier_passes_and_marks_focused_tests_ok():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["card_count_verified"] == 40
    assert result["domain_count_verified"] == 8
    assert result["readiness_split_verified"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }
    assert result["outside_current_gtos_ob_framing_count_verified"] == 33
    assert result["ready_packet_count_verified"] == 8
    assert result["blocked_dependency_count_verified"] == 32
    assert result["preserved_expansion_candidate_count_verified"] == 8
