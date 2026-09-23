from __future__ import annotations

import json

import build_ready8_adversarial_control_placebo_drift_audit_2026_05_15 as b


def test_classify_adjustment_full_weak_residual_and_underpowered() -> None:
    assert b.classify_adjustment(0.10, 0.11, False, 1) == "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT"
    assert b.classify_adjustment(0.10, 0.06, False, 1) == "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT"
    assert b.classify_adjustment(0.10, 0.04, False, 1) == "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE"
    assert b.classify_adjustment(0.10, 0.04, True, 1) == "UNDERPOWERED_PRESERVED_NOT_DECISION"
    assert b.classify_adjustment(0.10, None, False, 0) == "CONTROL_MATCH_MISSING_BOUNDED_TO_G12_REVIEW"


def test_stress_pair_key_removes_partition_only() -> None:
    record = {
        "branch_family": "card_symbol_target_family_horizon",
        "branch_key": {
            "card_id": "HAZ-001",
            "symbol": "NAS100_NQ",
            "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
            "horizon_m15_bars": "16",
            "target_family_id": "neutral_close_to_close_return_m15_horizons_v1",
        },
    }
    family, key_json = b.stress_pair_key(record)
    key = json.loads(key_json)
    assert family == "card_symbol_target_family_horizon"
    assert key["symbol"] == "NAS100_NQ"
    assert "partition_assignment" not in key


def test_axis_from_branch_covers_required_baseline_axes() -> None:
    families = {
        "card_symbol_target_family_horizon": "symbol",
        "card_economic_group_target_family_horizon": "canonical_economic_group",
        "card_session_target_family_horizon": "session",
        "card_source_segment_target_family_horizon": "source_segment_sha256",
        "card_partition_target_family_horizon": "partition_assignment",
        "card_denominator_role_target_family_horizon": "denominator_role",
        "card_duplicate_hash_bucket_target_family_horizon": "duplicate_hash_bucket",
    }
    for family, axis in families.items():
        value = "VALUE"
        record = {"branch_family": family, "branch_key": {axis: value}}
        assert b.axis_from_branch(record) == (axis, value)
