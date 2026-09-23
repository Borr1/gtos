from __future__ import annotations

from src.components.candidate_geometry import canonicalize_candidate_geometry


def test_canonical_geometry_does_not_recompute_target_for_invalid_side() -> None:
    row = canonicalize_candidate_geometry(
        {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "risk_reward_ratio": 2.0,
            "side": "UNKNOWN",
            "take_profit_1": 101.25,
        },
        source="unit_test",
    )

    assert row["take_profit_1"] == 101.25
    assert row["target_reference"] == 101.25
    assert row["canonical_geometry_target_recomputed"] is False
    assert (
        row["canonical_geometry_status"]
        == "canonicalized_from_available_fields_invalid_side_no_target_recompute"
    )


def test_canonical_geometry_recomputes_target_for_valid_side() -> None:
    row = canonicalize_candidate_geometry(
        {
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "risk_reward_ratio": 2.0,
            "side": "LONG",
            "take_profit_1": 101.25,
        },
        source="unit_test",
    )

    assert row["take_profit_1"] == 102.0
    assert row["canonical_geometry_target_recomputed"] is True
    assert row["canonical_geometry_status"] == "canonicalized"
