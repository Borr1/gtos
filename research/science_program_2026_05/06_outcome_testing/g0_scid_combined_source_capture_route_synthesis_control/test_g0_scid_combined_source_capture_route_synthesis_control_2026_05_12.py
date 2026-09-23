from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_g12_reconciliation_preserves_accepted_counts_and_repair_boundary():
    reconciliation = load_json("ACCEPTED_G12_AUDIT_RECONCILIATION")
    repair = load_json("MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE")

    checks = {row["check_id"]: row for row in reconciliation["exact_reconciliation_checks"]}
    assert reconciliation["accepted_g12_terminal_decision"] == (
        "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR"
    )
    assert checks["candidate_rows"]["actual"] == 3014
    assert checks["unique_candidate_ids"]["actual"] == 3014
    assert checks["unique_duplicate_keys"]["actual"] == 3014
    assert checks["hash_binding_after_repair"]["actual"] is True
    assert all(row["status"] == "PASS" for row in checks.values())
    assert repair["blocking_unrepaired_hash_mismatches"] == []
    assert "SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING" in " ".join(repair["future_verifier_policy"])
    assert reconciliation["validation_safe"] is False
    assert reconciliation["outcome_review_opened"] is False
    assert reconciliation["live_effect"] is False


def test_capture_contract_and_non_generatable_families_are_carried_forward():
    ledger = load_json("CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER")

    required_groups = set(ledger["required_capture_groups"])
    assert {
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields",
    } == required_groups
    assert len(ledger["non_generatable_historical_strategy_intent_source_state_families"]) == 7
    assert ledger["candidate_rows_covered"] == 3014
    assert any("Do not infer historical side" in rule for rule in ledger["carry_forward_rules"])


def test_route_ranking_is_aggressive_and_emits_high_value_prompt_pack():
    ranking = load_json("ROUTE_OPTION_RANKING")
    prompt_pack = load_json("SELECTED_ROUTE_PROMPT_PACK_LEDGER")

    assert ranking["rank_1_route"] == "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE"
    route_ids = [row["route_id"] for row in ranking["routes"]]
    for required in ranking["required_route_options_evaluated"]:
        assert required in route_ids
    assert "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT" in ranking["same_class_routes_combined_now"]
    assert ranking["routes"][0]["decision"] == "SELECT_RANK_1_STARTER"
    assert ranking["routes"][0]["weighted_total_score"] > ranking["routes"][2]["weighted_total_score"]
    assert prompt_pack["prompt_count"] == 4
    assert prompt_pack["rank_1_prompt"]["embedded_g12_repair"] is True
    assert prompt_pack["rank_1_prompt"]["embedded_checkpoint_resume"] is True


def test_anti_boxing_saturation_keeps_wide_science_horizon_open():
    anti = load_json("ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER")

    families = set(anti["outside_current_edge_mechanism_families_kept_open"])
    assert "path geometry and topology" in families
    assert "volatility clustering, tails, hazard timing, and first-passage behavior" in families
    assert "orderflow, depth, proxy, liquidity provision/taking, and trapped-trader context" in families
    assert "ML/meta-labeling, uncertainty, model disagreement, and adversarial baselines" in families

    answers = " ".join(row["answer"] for row in anti["saturation_questions_answered"])
    assert "3,014" in answers
    assert "24,112" in answers
    assert "13,540,033" in answers
    assert "not strategy results" in answers


def test_prompt_packs_embed_boundaries_and_next_route_execution_detail():
    prompt_pack = load_json("SELECTED_ROUTE_PROMPT_PACK_LEDGER")

    for prompt_path in prompt_pack["all_prompt_paths"].values():
        text = (ROOT / prompt_path).read_text(encoding="utf-8")
        assert "Do not rely on chat memory" in text
        assert "G12 Repair Handoff" in text
        assert "NO_PROMOTION_VERDICT" in text
        assert "validation_safe=false" in text
        assert "outcome_review_opened=false" in text
        assert "live_effect=false" in text
        assert "raw-market-blob" in text
        assert "broker-account-order-history-deal-position" in text
        assert "current GTOS OB/retest logic" in text
        assert "13,540,033 FPB discovery substrate" in text
        assert "Create a dedicated route directory" in text


def test_decision_completion_and_standalone_verifier_pass():
    decision = load_json("DECISION_LEDGER")
    assert decision["terminal_decision"] == "ACCEPT_AS_G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_WITH_RANKED_ROUTE_BUNDLE"
    assert decision["result_design_ready"] is False
    assert len(decision["result_design_blocked_by"]) == 7

    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    assert completion["terminal_decision"] == decision["terminal_decision"]
    assert completion["completion_standard_satisfied"] is True
    assert completion["can_mark_goal_complete"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False

    closeout_path = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    closeout["focused_pytest"] = {
        "status": "PASSED",
        "command": (
            "python -m pytest -q -p no:cacheprovider "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_combined_source_capture_route_synthesis_control/"
            "test_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py"
        ),
        "observed_result": "6 passed",
    }
    closeout["status"] = "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
    closeout_path.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
