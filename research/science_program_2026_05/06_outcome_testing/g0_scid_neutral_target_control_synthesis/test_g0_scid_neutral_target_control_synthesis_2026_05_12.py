from __future__ import annotations

import json
from pathlib import Path

from verify_g0_scid_neutral_target_control_synthesis_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_NEUTRAL_TARGET_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_exact_g12_reconciliation_counts_and_safe_boundary():
    reconciliation = load_json("ACCEPTED_EVIDENCE_RECONCILIATION")
    checks = {row["check_id"]: row for row in reconciliation["exact_reconciliation_checks"]}

    assert reconciliation["terminal_decision_from_g12"] == (
        "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY"
    )
    assert checks["candidate_rows"]["actual"] == 3014
    assert checks["sealed_rows"]["actual"] == 2432
    assert checks["stress_rows"]["actual"] == 582
    assert checks["terminal_statuses"]["actual"] == 24112
    assert checks["computable_rows"]["actual"] == 20292
    assert checks["fail_closed_not_computable_rows"]["actual"] == 3820
    assert checks["bounded_scid_segments_rehashed"]["actual"] == 9
    assert checks["target_row_hash_mismatches"]["actual"] == 0
    assert checks["target_value_mismatches"]["actual"] == 0
    assert all(row["status"] == "PASS" for row in checks.values())
    assert reconciliation["validation_safe"] is False
    assert reconciliation["outcome_review_opened"] is False
    assert reconciliation["live_effect"] is False


def test_neutral_behavior_synthesis_contains_required_slices_without_strategy_claims():
    neutral = load_json("NEUTRAL_BEHAVIOR_SYNTHESIS")

    assert len(neutral["availability_by_target_family_and_horizon"]) == 8
    assert neutral["matrix_excerpts"]["by_symbol"]
    assert neutral["matrix_excerpts"]["by_session_bucket"]
    assert len(neutral["matrix_excerpts"]["by_utc_hour"]) == 24
    assert neutral["matrix_excerpts"]["by_denominator_group"]
    assert neutral["matrix_excerpts"]["by_source_file"]
    assert "not a strategy edge" in neutral["interpretation_boundary"]
    assert "not win-rate" in neutral["interpretation_boundary"]
    assert neutral["opens_result_scoring"] is False
    assert neutral["opens_validation"] is False


def test_anti_boxing_source_fields_and_route_ranking_are_explicit():
    anti_boxing = load_json("ANTI_BOXING_MECHANISM_REVIEW")
    field_ledger = load_json("FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER")
    ranking = load_json("ROUTE_RANKING_LEDGER")

    families = {row["family"] for row in anti_boxing["mechanism_families"]}
    assert "session_hour_time_of_day_microstructure" in families
    assert "volatility_compression_expansion_range_state" in families
    assert "orderflow_depth_proxy_explanation" in families
    assert "adversarial_baseline_market_state_only" in families

    fields = {row["field_group"] for row in field_ledger["required_fields"]}
    assert {
        "direction_and_side",
        "entry_stop_target_references",
        "poi_type_bounds_and_setup_family",
        "lifecycle_fill_cancel_expiry_source_state",
        "orderflow_depth_proxy_context",
        "adversarial_baseline_assignment",
    }.issubset(fields)

    assert ranking["rank_1_route"] == "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET"
    assert ranking["routes"][0]["decision"] == "ACTIVE_NEXT_ROUTE"
    assert len(ranking["routes"]) >= 7
    assert ranking["parallel_route_needed_now"] is False


def test_rank_1_prompt_is_hardened_and_stays_source_field_only():
    ranking = load_json("ROUTE_RANKING_LEDGER")
    prompt_path = ROOT / ranking["rank_1_prompt_path"]
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY" in prompt_text
    assert "Every `3,014` candidate row" in prompt_text
    assert "CLOSED_FROM_SOURCE" in prompt_text
    assert "FAIL_CLOSED_MISSING_SOURCE_FIELD" in prompt_text
    assert "PROSPECTIVE_CAPTURE_REQUIRED" in prompt_text
    assert "FORBIDDEN_IN_THIS_EVIDENCE_CLASS" in prompt_text
    assert "NO_PROMOTION_VERDICT" in prompt_text
    assert "validation_safe=false" in prompt_text
    assert "broker account/order/history/deal/position evidence" in prompt_text
    assert "no validation/strategy-edge/R/PnL/win-rate/expectancy/performance" in prompt_text


def test_completion_audit_and_standalone_verifier_pass():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    assert completion["terminal_decision"] == "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"
    assert completion["can_mark_goal_complete"] is True
    assert completion["completion_standard_satisfied"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
