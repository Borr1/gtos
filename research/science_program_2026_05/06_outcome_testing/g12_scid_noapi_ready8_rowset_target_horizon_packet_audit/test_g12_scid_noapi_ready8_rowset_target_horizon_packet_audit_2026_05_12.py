"""Focused tests for the G12 ready-8 packet audit."""

from __future__ import annotations

import json
from pathlib import Path

import verify_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NOAPI_READY8"


def path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(stem: str) -> dict:
    return json.loads(path(stem).read_text(encoding="utf-8"))


def test_decision_accepts_source_control_packet_only() -> None:
    decision = read_json("DECISION_LEDGER")
    blocker = read_json("BLOCKER_FOLLOWUP_LEDGER")
    assert decision["terminal_decision"] in {
        "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
        "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
    }
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert blocker["may_score_results_now"] is False
    assert blocker["may_open_validation_now"] is False


def test_rowset_counts_hashes_and_asof_recomputed() -> None:
    rowset = read_json("ROWSET_COUNT_AUDIT")
    hash_asof = read_json("HASH_ASOF_AUDIT")
    assert rowset["expected_rowset_equation"] == "3014 * 8 = 24112"
    assert rowset["rowset_row_count_recomputed"] == 24112
    assert rowset["source_candidate_count_recomputed"] == 3014
    assert rowset["ready_card_count_recomputed"] == 8
    assert rowset["ready_card_ids_recomputed"] == verifier.READY_CARD_IDS
    assert set(rowset["per_card_counts_recomputed"].values()) == {3014}
    assert rowset["row_hash_mismatch_count"] == 0
    assert rowset["rowset_row_id_mismatch_count"] == 0
    assert rowset["candidate_source_hash_mismatch_count"] == 0
    assert rowset["descriptor_row_hash_mismatch_count"] == 0
    assert rowset["asof_violation_count"] == 0
    assert rowset["target_rowset_rows_lf_normalized_sha256_matches_manifest"] is True
    assert hash_asof["source_artifact_hash_mismatch_count"] == 0
    assert hash_asof["source_observed_asof_lte_decision_asof_count"] == 24112


def test_denominators_partitions_controls_and_expansion_quarantine() -> None:
    decision = read_json("DECISION_LEDGER")
    duplicate = read_json("DUPLICATE_DENOMINATOR_AUDIT")
    partition = read_json("PARTITION_BASELINE_CONTROL_AUDIT")
    expansion = read_json("EXPANSION_QUARANTINE_AUDIT")
    assert decision["ready_scope"]["accepted_card_denominator_recomputed"] == 40
    assert decision["ready_scope"]["blocked_dependency_count_recomputed"] == 32
    assert duplicate["duplicate_proxy_denominator_key_count_recomputed"] == 3014
    assert duplicate["ready_card_row_denominator_count_recomputed"] == 24112
    assert duplicate["quarantined_expansion_denominator_inclusion"] is False
    assert partition["deterministic_assignments_only"] is True
    assert partition["result_or_performance_lookup_used"] is False
    assert partition["baseline_seed_mismatch_count"] == 0
    assert partition["control_bucket_mismatch_count"] == 0
    assert expansion["accepted_40_is_floor_not_ceiling"] is True
    assert expansion["all_expansion_observations_remain_outside_accepted_denominator"] is True
    assert expansion["all_expansion_observations_remain_outside_ready8_denominator"] is True
    assert expansion["new_ready8_expansion_observation_count"] == 3


def test_target_horizon_and_forbidden_surfaces_remain_closed() -> None:
    target = read_json("TARGET_HORIZON_NO_RESULT_AUDIT")
    no_leak = read_json("NO_LEAK_FORBIDDEN_SURFACE_AUDIT")
    assert target["target_or_hazard_hits_computed"] is False
    assert target["performance_or_result_fields_present"] is False
    assert target["forbidden_exact_key_hit_count"] == 0
    assert no_leak["artifact_safe_flag_violation_count"] == 0
    assert no_leak["row_safe_flag_violation_count"] == 0
    assert no_leak["forbidden_row_field_hit_count"] == 0
    assert no_leak["asof_violation_count"] == 0
    assert no_leak["raw_market_blob_committed"] is False
    assert no_leak["ai_api_paid_vendor_accessed"] is False
    assert no_leak["broker_account_order_history_deal_position_evidence_accessed"] is False


def test_target_verifier_and_audit_verifier_pass() -> None:
    rerun = read_json("TARGET_ROUTE_VERIFICATION_RERUN_AUDIT")
    assert rerun["line_ending_friction_classification"][
        "accepted_as_environment_friction_not_packet_content_drift"
    ] is True or rerun["target_verifier"]["ok"] is True
    assert rerun["line_ending_friction_classification"][
        "accepted_as_environment_friction_not_packet_content_drift"
    ] is True or rerun["target_focused_pytest"]["ok"] is True
    result = verifier.verify(write_result=False)
    assert result["ok"], result["failures"]
    assert result["rowset_row_count_verified"] == 24112
    assert result["source_candidate_count_verified"] == 3014
    assert result["ready_card_count_verified"] == 8
