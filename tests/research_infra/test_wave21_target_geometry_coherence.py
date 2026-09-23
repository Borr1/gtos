"""The model frame's take-profit must be the take-profit the order carries.

WHAT THIS PINS, and why each test exists rather than a source grep.

`target_distance_atr` is a predecision feature the generator computes at emission from its
own take-profit (`broader_origin_generators.py:3833-3834`, target = entry +/- `risk.min_rr`
* risk).  The submitted order's take-profit is then rewritten by the selected dynamic
execution policy -- `momentum_exhaustion`, `dynamic_execution_policy.py:167-186`,
`final_target_r = 2.0` -- and the predecision block is never recomputed.  The labeler
follows the ORDER (`candidate_funnel_analysis._lifecycle_row` reads `take_profit_1`), so the
model was trained to predict the outcome of a contract different from the one its own inputs
describe.

Measured on the five-month cached population: frame 1.5 on 632,934/632,934 rows, order 2.0
on 81,968/81,968.

`test_incoherent_row_is_detected` and `test_as_traded_basis_restates_the_target` FAIL against
the pre-repair implementation (there was no basis argument and no detector at all).  That is
deliberate -- a test that passes against the old code proves the change is different, not
that it is a fix.

`test_default_basis_is_bit_identical_to_the_frozen_frame` is the inertness proof: the
default path still emits the as-generated value, so `SHADOW_RIDGE_MODEL_V1` -- which was fit
on it -- keeps seeing exactly what it was fit on, and every sealed read reproduces.
"""

from __future__ import annotations

import math

import pytest

from src.research_infra.wave21_forward_shadow.feature_contract import (
    TARGET_GEOMETRY_AS_GENERATED,
    TARGET_GEOMETRY_AS_TRADED,
    TARGET_GEOMETRY_BASES,
    FeatureContractError,
    PREDECISION_FEATURE_KEYS,
    shadow_feature_row,
    target_geometry_coherence,
    traded_reward_to_risk,
    traded_target_distance_atr,
)


def _raw(*, min_rr: float = 1.5, traded_rr: float = 2.0, side: str = "LONG"):
    """A decision-time row whose frame carries `min_rr` and whose order carries `traded_rr`.

    This is the exact shape the defect takes on the cached population: the predecision
    feature block was computed at the generator's target, the order was rewritten to the
    execution policy's.
    """

    entry, stop = 100.0, 99.0
    risk = abs(entry - stop)
    direction = 1.0 if side == "LONG" else -1.0
    atr14 = 0.5
    predecision = {key: 0.0 for key in PREDECISION_FEATURE_KEYS}
    predecision["stop_distance_atr"] = risk / atr14
    predecision["target_distance_atr"] = (min_rr * risk) / atr14
    predecision["trend_state_m15"] = "up"
    predecision["trend_transition_flag"] = "False"
    return {
        "decision_time_utc": "2026-02-02T09:15:00+00:00",
        "limit_first_expiry_utc": "2026-02-02T11:15:00+00:00",
        "decision_window_id": "timewarp:2026-02-02T09:15:00+00:00",
        "trading_day": "2026-02-02",
        "symbol": "EURUSD",
        "side": side,
        "origin_family": "liquidity_sweep_reclaim",
        "session_bucket": "london",
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": entry + direction * traded_rr * risk,
        "cost_r": 0.05,
        "spread_r": 0.02,
        "expected_slippage_r": 0.01,
        "swap_cost_r": 0.0,
        "commission_r": 0.02,
        "predecision_features": predecision,
        "predecision_limit_fillability": {"atr14": atr14},
    }


# ------------------------------------------------------------------ the inertness proof


def test_default_basis_is_bit_identical_to_the_frozen_frame():
    """Default path still emits the generator's value -- the fitted model is untouched."""

    raw = _raw(min_rr=1.5, traded_rr=2.0)
    row = shadow_feature_row(raw)
    frame = raw["predecision_features"]
    assert row["target_distance_atr"] == frame["target_distance_atr"]
    assert row["stop_distance_atr"] == frame["stop_distance_atr"]
    assert row["target_distance_atr"] / row["stop_distance_atr"] == pytest.approx(1.5)
    assert shadow_feature_row(raw, target_geometry_basis=TARGET_GEOMETRY_AS_GENERATED) == row


def test_default_basis_leaves_every_other_feature_alone():
    """The basis switch moves exactly one column and nothing else."""

    raw = _raw()
    generated = shadow_feature_row(raw, target_geometry_basis=TARGET_GEOMETRY_AS_GENERATED)
    traded = shadow_feature_row(raw, target_geometry_basis=TARGET_GEOMETRY_AS_TRADED)
    assert set(generated) == set(traded)

    def same(a, b):
        # NaN is a legitimate feature value here (absent poi/fillability inputs), and
        # NaN != NaN would make every missing column look like a difference.
        if isinstance(a, float) and isinstance(b, float):
            return (math.isnan(a) and math.isnan(b)) or a == b
        return a == b

    differing = [k for k in generated if not same(generated[k], traded[k])]
    assert differing == ["target_distance_atr"]


# --------------------------------------------------- the tests that FAIL against old code


def test_as_traded_basis_restates_the_target():
    """The repaired feature describes the order the labeler resolves."""

    raw = _raw(min_rr=1.5, traded_rr=2.0)
    row = shadow_feature_row(raw, target_geometry_basis=TARGET_GEOMETRY_AS_TRADED)
    assert row["target_distance_atr"] / row["stop_distance_atr"] == pytest.approx(2.0)
    # and it is exactly traded_rr * stop_distance_atr, on the frame's own atr14
    assert row["target_distance_atr"] == pytest.approx(2.0 * row["stop_distance_atr"])


def test_incoherent_row_is_detected():
    """The 1.5-vs-2.0 disagreement is named, not silent."""

    verdict = target_geometry_coherence(_raw(min_rr=1.5, traded_rr=2.0))
    assert verdict["verdict"] == "INCOHERENT_ORDER_TARGET_WIDER_THAN_FRAME"
    assert verdict["generated_reward_to_risk"] == pytest.approx(1.5)
    assert verdict["traded_reward_to_risk"] == pytest.approx(2.0)


def test_coherent_row_is_reported_coherent():
    """min_rr == the policy's final_target_r is the Oct/Nov/Jan case -- no false alarm."""

    verdict = target_geometry_coherence(_raw(min_rr=2.0, traded_rr=2.0))
    assert verdict["verdict"] == "COHERENT"


def test_tighter_order_target_is_named_separately():
    verdict = target_geometry_coherence(_raw(min_rr=3.0, traded_rr=2.0))
    assert verdict["verdict"] == "INCOHERENT_ORDER_TARGET_TIGHTER_THAN_FRAME"


def test_missing_geometry_is_not_evaluable_never_coherent():
    """A silent default is how the 1.5 got here; absence must not read as agreement."""

    raw = _raw()
    raw.pop("take_profit_1")
    assert target_geometry_coherence(raw)["verdict"] == "NOT_EVALUABLE"
    assert math.isnan(traded_reward_to_risk(raw))

    no_frame = _raw()
    no_frame.pop("predecision_features")
    assert target_geometry_coherence(no_frame)["verdict"] == "NOT_EVALUABLE"


# ------------------------------------------------------------------------- the mechanics


def test_short_side_uses_absolute_distances():
    """A SHORT's take-profit is below entry; the RR is still positive."""

    row = shadow_feature_row(
        _raw(traded_rr=2.0, side="SHORT"), target_geometry_basis=TARGET_GEOMETRY_AS_TRADED
    )
    assert row["target_distance_atr"] / row["stop_distance_atr"] == pytest.approx(2.0)


def test_degenerate_risk_is_nan_not_a_default():
    raw = _raw()
    raw["stop_loss"] = raw["entry_price"]
    assert math.isnan(traded_reward_to_risk(raw))
    assert math.isnan(traded_target_distance_atr(raw, stop_distance_atr=2.0))


def test_unknown_basis_fails_loud():
    with pytest.raises(FeatureContractError):
        shadow_feature_row(_raw(), target_geometry_basis="whatever_seems_reasonable")


def test_bases_tuple_is_exactly_the_two_named_bases():
    assert TARGET_GEOMETRY_BASES == (
        TARGET_GEOMETRY_AS_GENERATED,
        TARGET_GEOMETRY_AS_TRADED,
    )


# ------------------------------------------------- the property that decides the refit
#
# On a population generated at a SINGLE min_rr, target_distance_atr is an exact positive
# scalar multiple of stop_distance_atr under BOTH bases.  StandardScaler maps x2 = c*x1
# (c > 0) to the identical standardised column, so the feature carries zero incremental
# information either way and repairing it cannot move a prediction.  This is why the refit
# in section 3 of the report is a no-op, and it is a property of the frame, not a claim
# about markets -- so it is pinned here rather than argued in prose.


def test_target_is_an_exact_multiple_of_stop_under_both_bases():
    rows = [_raw(min_rr=1.5, traded_rr=2.0) for _ in range(5)]
    for i, raw in enumerate(rows):
        raw["predecision_features"]["stop_distance_atr"] = 1.0 + i
        raw["predecision_features"]["target_distance_atr"] = 1.5 * (1.0 + i)

    for basis, expected in (
        (TARGET_GEOMETRY_AS_GENERATED, 1.5),
        (TARGET_GEOMETRY_AS_TRADED, 2.0),
    ):
        built = [shadow_feature_row(r, target_geometry_basis=basis) for r in rows]
        ratios = {
            round(b["target_distance_atr"] / b["stop_distance_atr"], 12) for b in built
        }
        assert ratios == {expected}, f"{basis} is not a single exact multiple"
