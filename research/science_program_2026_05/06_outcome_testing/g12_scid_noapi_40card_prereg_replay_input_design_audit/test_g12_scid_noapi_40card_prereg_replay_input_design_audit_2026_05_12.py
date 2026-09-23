from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NOAPI_PREREG_AUDIT"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_card_domain_readiness_recomputation_matches_prompt_denominator():
    audit = load_json("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER")

    assert audit["accepted_card_count_recomputed"] == 40
    assert audit["accepted_unique_card_count_recomputed"] == 40
    assert audit["domain_count_recomputed"] == 8
    assert set(audit["domain_counts_recomputed"].values()) == {5}
    assert audit["readiness_split_recomputed"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }
    assert audit["outside_current_gtos_ob_framing_count_recomputed"] == 33
    assert audit["all_40_accepted_cards_appear_once_in_source_mapping"] is True
    assert audit["all_40_accepted_cards_appear_once_in_terminal_status"] is True
    assert audit["ok"] is True


def test_packet_blocked_and_expansion_ledgers_preserve_denominator_separation():
    packets = load_json("REPLAY_INPUT_PACKET_AUDIT_LEDGER")
    blocked = load_json("BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT")
    expansion = load_json("EXPANSION_CANDIDATE_QUARANTINE_AUDIT")

    assert packets["replay_packet_count"] == 8
    assert packets["packets_only_for_preregisterable_now_cards"] is True
    assert all(row["has_eligibility_denominator_asof_noleak_baseline_future_gate"] for row in packets["packet_rows"])
    assert blocked["blocked_card_count"] == 32
    assert blocked["blocked_rows_only_for_blocked_cards"] is True
    assert blocked["blocked_readiness_split"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    }
    assert all(row["exact_dependency_row_ok"] for row in blocked["blocked_rows"])
    assert expansion["expansion_candidate_count"] == 8
    assert expansion["expansion_candidates_entered_accepted_denominator"] is False
    assert all(row["quarantine_ok"] for row in expansion["rows"])


def test_blocker_pursuit_noleak_hash_and_fairness_audits_pass():
    pursuit = load_json("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT")
    noleak = load_json("NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT")
    hashes = load_json("HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT")
    fairness = load_json("SATURATION_FAIRNESS_LEDGER")

    assert pursuit["pursued_group_count"] == 10
    assert pursuit["resolved_inside_this_prompt_count"] == 8
    assert pursuit["remaining_exact_dependency_blocker_count"] == 2
    assert pursuit["ok"] is True
    assert noleak["suspicious_forbidden_reference_count"] == 0
    assert noleak["ok"] is True
    assert hashes["blocking_hash_mismatches"] == []
    assert hashes["missing_manifest_artifacts"] == []
    assert len(hashes["nonblocking_manifest_self_hash_mismatches"]) == 1
    assert hashes["target_verifier_and_tests_passed"] is True
    assert hashes["ok"] is True
    assert fairness["did_not_reject_novelty_or_outside_current_edge"] is True
    assert fairness["did_not_accept_silent_denominator_expansion"] is True
    assert fairness["ok"] is True


def test_decision_accepts_with_exact_nonblocking_followup_and_next_g0_prompt():
    decision = load_json("DECISION_LEDGER")
    completion = load_json("COMPLETION_AUDIT")

    assert decision["terminal_decision"] == "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
    assert decision["terminal_blockers"] == []
    assert len(decision["exact_nonblocking_followups"]) == 1
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert decision["accepted_promotion"] is False
    assert completion["terminal_decision"] == "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
    assert (ROUTE_DIR / "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_STARTER_2026-05-12.txt").exists()


def test_standalone_verifier_passes_after_marking_focused_tests():
    result = verify(mark_focused_tests_ok=True)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["card_count_verified"] == 40
    assert result["domain_count_verified"] == 8
    assert result["replay_packet_count_verified"] == 8
    assert result["blocked_dependency_count_verified"] == 32
    assert result["expansion_candidate_count_verified"] == 8
