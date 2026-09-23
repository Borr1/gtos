"""Unit tests for the R-denominated broad-origin emission contract.

These pin the PREDICATES.  The generator-level behaviour they govern is pinned
separately in ``tests/test_broad_origin_emission_repairs.py``; nothing here
asserts on source strings.
"""

from __future__ import annotations

import math

import pytest

from src.components.broad_origin_emission_contract import (
    BIN_MARKETABLE,
    BIN_PAST_STOP,
    BIN_RESTING,
    BIN_TARGET_THROUGH,
    DEFAULT_MAX_ADMISSION_GAP_R,
    DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS,
    DEFAULT_MIN_ADMISSION_GAP_R,
    DEFAULT_REFUSE_PAST_STOP,
    LEGACY_EMISSION_POLICY,
    MAX_ADMISSION_GAP_R_KEY,
    MAX_SELECTED_BAR_AGE_PERIODS_KEY,
    MIN_ADMISSION_GAP_R_KEY,
    REASON_MAX_GAP_R,
    REASON_MIN_GAP_R,
    REASON_OK,
    REASON_PAST_STOP,
    REFUSE_PAST_STOP_KEY,
    RUNTIME_SECTION,
    BroadOriginEmissionPolicy,
    admission_bin,
    evaluate_poi_admission,
    fill_gap_r,
    resolve_emission_policy,
    selected_bar_age_admissible,
)


def _runtime(**kwargs) -> dict:
    return {RUNTIME_SECTION: dict(kwargs)}


# --------------------------------------------------------------- fill_gap_r


def test_fill_gap_r_is_signed_by_side_and_scaled_by_the_trades_own_risk() -> None:
    # LONG: entry 100, stop 99 -> risk 1.0.  Market at 98.5 is 1.5 risk units
    # BELOW the entry, i.e. half a risk unit beyond the stop.
    assert fill_gap_r(
        side="LONG", entry_price=100.0, stop_loss=99.0, current_price=98.5
    ) == pytest.approx(-1.5)
    # SHORT is the exact mirror.
    assert fill_gap_r(
        side="SHORT", entry_price=100.0, stop_loss=101.0, current_price=101.5
    ) == pytest.approx(-1.5)
    # a wider stop makes the SAME price displacement a smaller number of R
    assert fill_gap_r(
        side="LONG", entry_price=100.0, stop_loss=95.0, current_price=98.5
    ) == pytest.approx(-0.3)


def test_fill_gap_r_is_none_when_the_geometry_cannot_define_a_risk_unit() -> None:
    assert fill_gap_r(side="LONG", entry_price=100.0, stop_loss=100.0,
                      current_price=99.0) is None
    assert fill_gap_r(side="LONG", entry_price=None, stop_loss=99.0,
                      current_price=99.0) is None
    assert fill_gap_r(side="LONG", entry_price=float("nan"), stop_loss=99.0,
                      current_price=99.0) is None


@pytest.mark.parametrize("side,sign", [("LONG", 1.0), ("SHORT", -1.0)])
def test_gap_r_thresholds_are_the_stop_and_the_target_in_price_terms(side, sign) -> None:
    """``gap_r < -1`` IS "price beyond the stop"; ``gap_r >= rr`` IS "price at or
    past the target".  The whole gate is therefore ``stop < price < target``."""

    entry, risk, rr = 100.0, 1.0, 1.5
    stop = entry - sign * risk
    target = entry + sign * rr * risk
    for price in (90.0, 98.5, 99.0, 99.5, 100.0, 101.0, 101.5, 110.0):
        gap = fill_gap_r(side=side, entry_price=entry, stop_loss=stop,
                         current_price=price)
        beyond_stop = price < stop if side == "LONG" else price > stop
        at_or_past_target = price >= target if side == "LONG" else price <= target
        assert (gap < -1.0) is beyond_stop, (side, price, gap)
        assert (gap >= rr) is at_or_past_target, (side, price, gap)


def test_a_past_stop_candidate_has_its_stop_on_the_wrong_side_of_the_market() -> None:
    """This is why refusing is not a strategy preference.

    For a LONG whose ``gap_r < -1`` the market sits BELOW the stop, and a buy
    limit above the market fills at once - so the position would open with its
    stop-loss ABOVE the achievable fill price.  That is a malformed order under
    any fill convention, not a trade with poor odds.
    """

    entry, stop = 100.75, 100.25
    market = 100.0
    gap = fill_gap_r(side="LONG", entry_price=entry, stop_loss=stop,
                     current_price=market)
    assert gap < -1.0
    assert market < stop < entry  # stop-loss on the wrong side of the fill


# ------------------------------------------------------------- admission_bin


def test_admission_bins_partition_the_line_exhaustively_and_disjointly() -> None:
    rr = 1.5
    seen = {}
    for gap in (-9.0, -1.0001, -1.0, -0.5, -1e-12, 0.0, 0.75, 1.4999, 1.5, 9.0):
        seen[gap] = admission_bin(gap, rr)
    assert seen[-9.0] == seen[-1.0001] == BIN_PAST_STOP
    assert seen[-1.0] == seen[-0.5] == seen[-1e-12] == BIN_MARKETABLE
    assert seen[0.0] == seen[0.75] == seen[1.4999] == BIN_RESTING
    assert seen[1.5] == seen[9.0] == BIN_TARGET_THROUGH
    assert admission_bin(None, rr) is None


def test_admission_bin_boundary_moves_with_the_candidates_own_rr() -> None:
    assert admission_bin(2.0, 1.5) == BIN_TARGET_THROUGH
    assert admission_bin(2.0, 4.0) == BIN_RESTING


# ------------------------------------------------------- evaluate_poi_admission


def _long(price: float, policy: BroadOriginEmissionPolicy) -> dict:
    return evaluate_poi_admission(
        side="LONG", entry_price=100.0, stop_loss=99.0, current_price=price,
        target_rr=1.5, policy=policy,
    )


def test_default_policy_refuses_only_the_born_past_stop_population() -> None:
    policy = BroadOriginEmissionPolicy()
    assert policy.refuse_past_stop is True
    assert policy.max_admission_gap_r is None
    assert policy.min_admission_gap_r is None

    refused = _long(98.5, policy)
    assert refused["admit"] is False
    assert refused["reason"] == REASON_PAST_STOP
    assert refused["admission_bin"] == BIN_PAST_STOP
    assert refused["fill_gap_r"] == pytest.approx(-1.5)

    for price, bucket in ((99.5, BIN_MARKETABLE), (100.5, BIN_RESTING),
                          (105.0, BIN_TARGET_THROUGH)):
        verdict = _long(price, policy)
        assert verdict["admit"] is True, (price, verdict)
        assert verdict["reason"] == REASON_OK
        assert verdict["admission_bin"] == bucket


def test_legacy_policy_admits_everything_the_pre_repair_gate_admitted() -> None:
    for price in (90.0, 98.5, 99.5, 100.5, 105.0, 1000.0):
        verdict = _long(price, LEGACY_EMISSION_POLICY)
        assert verdict["admit"] is True, price
        assert verdict["reason"] == REASON_OK


def test_far_side_radius_is_denominated_in_R_not_percent_of_price() -> None:
    policy = BroadOriginEmissionPolicy(max_admission_gap_r=1.5)
    assert _long(101.4, policy)["admit"] is True          # gap 1.4 R
    refused = _long(101.5, policy)                        # gap 1.5 R
    assert refused["admit"] is False
    assert refused["reason"] == REASON_MAX_GAP_R
    # the SAME price displacement on a wider stop is a smaller gap in R and is
    # admitted - which is the whole point of the repair.
    wide = evaluate_poi_admission(
        side="LONG", entry_price=100.0, stop_loss=90.0, current_price=101.5,
        target_rr=1.5, policy=policy,
    )
    assert wide["admit"] is True
    assert wide["fill_gap_r"] == pytest.approx(0.15)


def test_near_side_radius_refuses_already_marketable_limits_when_set() -> None:
    policy = BroadOriginEmissionPolicy(min_admission_gap_r=0.0)
    refused = _long(99.5, policy)
    assert refused["admit"] is False
    assert refused["reason"] == REASON_MIN_GAP_R
    assert _long(100.0, policy)["admit"] is True


def test_past_stop_refusal_outranks_the_radius_so_the_reason_is_never_masked() -> None:
    policy = BroadOriginEmissionPolicy(refuse_past_stop=True, min_admission_gap_r=0.0)
    assert _long(98.5, policy)["reason"] == REASON_PAST_STOP


def test_degenerate_geometry_is_refused_rather_than_admitted_by_default() -> None:
    verdict = evaluate_poi_admission(
        side="LONG", entry_price=100.0, stop_loss=100.0, current_price=99.0,
        target_rr=1.5, policy=BroadOriginEmissionPolicy(),
    )
    assert verdict["admit"] is False
    assert verdict["fill_gap_r"] is None


# --------------------------------------------------------- policy resolution


def test_absent_keys_resolve_to_the_shipped_defaults() -> None:
    for config in ({}, None, {"gtos_vnext_runtime": {}}, {"risk": {"min_rr": 1.5}}):
        policy = resolve_emission_policy(config)
        assert policy.refuse_past_stop is DEFAULT_REFUSE_PAST_STOP is True
        assert policy.max_admission_gap_r is DEFAULT_MAX_ADMISSION_GAP_R is None
        assert policy.min_admission_gap_r is DEFAULT_MIN_ADMISSION_GAP_R is None
        assert (
            policy.max_selected_bar_age_periods
            == DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS
            == 1.0
        )


def test_the_escape_hatch_reconstructs_the_legacy_contract_exactly() -> None:
    policy = resolve_emission_policy(_runtime(**{
        REFUSE_PAST_STOP_KEY: False,
        MAX_ADMISSION_GAP_R_KEY: None,
        MIN_ADMISSION_GAP_R_KEY: None,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: None,
    }))
    assert policy == LEGACY_EMISSION_POLICY


def test_unreadable_values_fall_back_to_the_repair_not_to_the_defect() -> None:
    policy = resolve_emission_policy(_runtime(**{
        REFUSE_PAST_STOP_KEY: "no",          # not a bool
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: "soon",
    }))
    assert policy.refuse_past_stop is True
    assert policy.max_selected_bar_age_periods == 1.0
    # a non-positive age budget is meaningless and must not disable the check
    assert resolve_emission_policy(
        _runtime(**{MAX_SELECTED_BAR_AGE_PERIODS_KEY: 0})
    ).max_selected_bar_age_periods == 1.0
    assert resolve_emission_policy(
        _runtime(**{MAX_ADMISSION_GAP_R_KEY: -3})
    ).max_admission_gap_r is None


def test_policy_round_trips_through_its_own_receipt_dict() -> None:
    policy = BroadOriginEmissionPolicy(
        refuse_past_stop=True, max_admission_gap_r=1.5,
        min_admission_gap_r=0.0, max_selected_bar_age_periods=2.0,
    )
    assert resolve_emission_policy({RUNTIME_SECTION: policy.to_dict()}) == policy


# ------------------------------------------------------------ bar-age budget


def test_bar_age_budget_is_measured_in_that_timeframes_own_periods() -> None:
    policy = BroadOriginEmissionPolicy()  # 1.0 period
    for tf in (1, 15, 60, 240, 1440):
        period = tf * 60.0
        assert selected_bar_age_admissible(
            age_seconds=0.0, timeframe_minutes=tf, policy=policy) is True
        assert selected_bar_age_admissible(
            age_seconds=period - 1, timeframe_minutes=tf, policy=policy) is True
        # exactly one missing bar is already refused
        assert selected_bar_age_admissible(
            age_seconds=period, timeframe_minutes=tf, policy=policy) is False


def test_bar_age_budget_scales_and_can_be_disabled() -> None:
    two = BroadOriginEmissionPolicy(max_selected_bar_age_periods=2.0)
    assert selected_bar_age_admissible(
        age_seconds=15 * 60, timeframe_minutes=15, policy=two) is True
    assert selected_bar_age_admissible(
        age_seconds=30 * 60, timeframe_minutes=15, policy=two) is False
    assert selected_bar_age_admissible(
        age_seconds=7 * 24 * 3600, timeframe_minutes=15,
        policy=LEGACY_EMISSION_POLICY) is True


def test_a_slightly_early_bar_close_is_not_treated_as_stale() -> None:
    # the selector tolerates a bar closing up to 2 s after ``now``; a negative
    # age must never read as stale.
    assert selected_bar_age_admissible(
        age_seconds=-2.0, timeframe_minutes=15,
        policy=BroadOriginEmissionPolicy()) is True
