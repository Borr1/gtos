from __future__ import annotations

from copy import deepcopy

import pytest

from src.research_infra.current_ob_retest_geometry_candidate import (
    DEFAULT_ENABLED,
    ENABLE_SURFACE,
    REWARD_TO_RISK,
    TRANSFORM_ID,
    CurrentOBRetestGeometryCandidateError,
    apply_current_ob_retest_geometry_candidate,
)


def _candidate(*, side: str = "LONG") -> dict:
    return {
        "candidate_id": "broadorigin_original",
        "origin_family": "current_ob_retest",
        "symbol": "XAUUSD",
        "decision_time_utc": "2026-01-02T10:00:00+00:00",
        "side": side,
        "direction": side,
        "entry_price": 100.0,
        "stop_loss": 96.0 if side == "LONG" else 104.0,
        "take_profit_1": 106.0 if side == "LONG" else 94.0,
        "risk_reward_ratio": 1.5,
        "predecision_features": {"stop_distance_atr": 2.0},
        "source_fields": {"uses_outcome_fields": False},
        "trade_parameters": {
            "side": side,
            "direction": side,
            "entry_price": 100.0,
            "stop_loss": 96.0 if side == "LONG" else 104.0,
            "take_profit_1": 106.0 if side == "LONG" else 94.0,
            "risk_reward_ratio": 1.5,
        },
    }


def test_candidate_is_default_off_detached_and_input_is_unchanged() -> None:
    candidate = _candidate()
    original = deepcopy(candidate)

    disabled = apply_current_ob_retest_geometry_candidate(candidate)

    assert DEFAULT_ENABLED is False
    assert ENABLE_SURFACE == "explicit_research_argument_only"
    assert disabled == original
    assert disabled is not candidate
    assert disabled["predecision_features"] is not candidate["predecision_features"]
    assert candidate == original


@pytest.mark.parametrize(
    ("side", "expected_stop", "expected_target"),
    [("LONG", 99.0, 106.0), ("SHORT", 101.0, 94.0)],
)
def test_enabled_candidate_keeps_direction_and_applies_selected_geometry(
    side: str, expected_stop: float, expected_target: float
) -> None:
    repaired = apply_current_ob_retest_geometry_candidate(
        _candidate(side=side), enabled=True
    )

    assert repaired["side"] == repaired["direction"] == side
    assert repaired["entry_price"] == 100.0
    assert repaired["stop_loss"] == pytest.approx(expected_stop)
    assert repaired["take_profit_1"] == pytest.approx(expected_target)
    assert repaired["risk_reward_ratio"] == pytest.approx(REWARD_TO_RISK)
    assert repaired["candidate_transform_id"] == TRANSFORM_ID
    assert repaired["candidate_transform_default"] == "off"
    assert repaired["candidate_transform_enable_surface"] == ENABLE_SURFACE
    assert repaired["predecision_features"]["stop_distance_atr"] == pytest.approx(0.5)
    assert repaired["predecision_features"]["target_distance_atr"] == pytest.approx(3.0)
    assert repaired["trade_parameters"]["stop_loss"] == pytest.approx(expected_stop)
    assert repaired["trade_parameters"]["take_profit_1"] == pytest.approx(
        expected_target
    )


def test_enabled_candidate_id_is_stable_and_binds_time_symbol_and_geometry() -> None:
    candidate = _candidate()
    first = apply_current_ob_retest_geometry_candidate(candidate, enabled=True)
    second = apply_current_ob_retest_geometry_candidate(candidate, enabled=True)
    moved = apply_current_ob_retest_geometry_candidate(
        {**candidate, "decision_time_utc": "2026-01-02T10:15:00+00:00"},
        enabled=True,
    )

    assert first["candidate_id"] == second["candidate_id"]
    assert first["candidate_id"] != candidate["candidate_id"]
    assert moved["candidate_id"] != first["candidate_id"]


def test_enabled_candidate_fails_closed_when_outcome_fields_enter() -> None:
    with pytest.raises(
        CurrentOBRetestGeometryCandidateError, match="forbids outcome fields"
    ):
        apply_current_ob_retest_geometry_candidate(
            {**_candidate(), "opportunity_net_proxy_r": 1.0}, enabled=True
        )


def test_enabled_candidate_fails_closed_on_missing_composite_identity() -> None:
    candidate = _candidate()
    candidate.pop("symbol")

    with pytest.raises(CurrentOBRetestGeometryCandidateError, match="requires"):
        apply_current_ob_retest_geometry_candidate(candidate, enabled=True)


def test_other_family_is_exact_pass_through_even_when_enabled() -> None:
    candidate = {**_candidate(), "origin_family": "current_fvg_fill"}

    result = apply_current_ob_retest_geometry_candidate(candidate, enabled=True)

    assert result == candidate
    assert result is not candidate
    assert "candidate_transform_id" not in result
