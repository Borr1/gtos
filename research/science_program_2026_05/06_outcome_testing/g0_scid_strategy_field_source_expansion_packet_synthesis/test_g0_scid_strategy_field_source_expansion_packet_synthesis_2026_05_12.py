from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_g12_reconciliation_and_source_field_readiness_are_exact():
    reconciliation = load_json("ACCEPTED_G12_AUDIT_RECONCILIATION")
    readiness = load_json("SOURCE_FIELD_READINESS_SYNTHESIS")
    checks = {row["check_id"]: row for row in reconciliation["exact_reconciliation_checks"]}

    assert reconciliation["terminal_decision_from_g12"] == (
        "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY"
    )
    assert checks["candidate_rows"]["actual"] == 3014
    assert checks["closure_rows"]["actual"] == 3014
    assert checks["closed_field_families"]["actual"] == 3
    assert checks["fail_closed_field_families"]["actual"] == 7
    assert checks["prospective_capture_field_families"]["actual"] == 2
    assert checks["forbidden_field_families"]["actual"] == 1
    assert checks["forbidden_result_key_hits"]["actual"] == 0
    assert checks["forbidden_broker_key_hits"]["actual"] == 0
    assert all(row["status"] == "PASS" for row in checks.values())

    assert readiness["accepted_packet_row_count"] == 3014
    assert readiness["result_design_ready"] is False
    assert set(readiness["direction_aware_result_design_blockers"]) == {
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
    }
    assert readiness["representative_closure_row_count"] == 3014


def test_route_ranking_scores_required_options_and_emits_bundle():
    ranking = load_json("ROUTE_OPTION_RANKING_LEDGER")
    route_ids = {row["route_id"] for row in ranking["routes"]}

    assert {
        "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
        "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
        "SCID_DIRECTION_AWARE_RESULT_DESIGN",
        "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
        "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
    }.issubset(route_ids)
    assert ranking["rank_1_route"] == "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE"
    assert len(ranking["routes"]) >= 10
    assert len(ranking["selected_route_bundle"]) == 3
    assert ranking["selected_route_bundle"][0]["prompt_path"].endswith(
        "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md"
    )
    totals = [row["weighted_total_score"] for row in ranking["routes"]]
    assert totals == sorted(totals, reverse=True)


def test_anti_boxing_and_capture_spec_go_beyond_current_frameworks():
    anti = load_json("ANTI_BOXING_ROUTE_DISCOVERY_LEDGER")
    capture = load_json("CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION")
    noleak = load_json("FORBIDDEN_SURFACE_NO_LEAK_CONTINUITY_AUDIT")

    assert anti["anti_boxing_applied_from_prompt"] is True
    assert "current GTOS OB/FVG/breaker frameworks" in anti["not_treated_as_limits"]
    assert "single source modality" in anti["not_treated_as_limits"]
    assert len(anti["outside_current_edge_route_families_considered"]) >= 12
    assert "orderflow/depth/proxy market-context fields" in anti["outside_current_edge_route_families_considered"]
    assert "path hazard and first-passage descriptors" in anti["outside_current_edge_route_families_considered"]

    groups = {row["field_group"] for row in capture["required_capture_field_groups"]}
    assert "intended_side_direction" in groups
    assert "lifecycle_fill_cancel_expiry_source_status" in groups
    assert "future_orderflow_depth_proxy_requirements" in groups
    assert "adversarial_baseline_assignment" in groups
    assert capture["capture_route_is_ranked_first"] is True
    assert noleak["current_route_opened_forbidden_surfaces"] is False


def test_prompt_bundle_is_hardened_and_control_only():
    ranking = load_json("ROUTE_OPTION_RANKING_LEDGER")

    for item in ranking["selected_route_bundle"]:
        prompt_path = ROOT / item["prompt_path"]
        text = prompt_path.read_text(encoding="utf-8")
        assert "Mandatory Preflight" in text
        assert "Required Saturation And Self-Red-Team" in text
        assert "NO_PROMOTION_VERDICT" in text
        assert "validation_safe=false" in text
        assert "outcome_review_opened=false" in text
        assert "live_effect=false" in text
        assert "Do not open validation execution" in text
        assert "broker account/order/history/deal/position evidence" in text
        assert "prompt/config/risk/safety/execution/canary/selector changes" in text


def test_completion_audit_and_standalone_verifier_pass():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    assert completion["terminal_decision"] == "ACCEPT_AS_G0_STRATEGY_FIELD_PACKET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"
    assert completion["can_mark_goal_complete"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
