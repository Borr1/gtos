"""ATR basis foundation repair -- behavioural pins.

The defect these pin (measured, ops/receipts/ATR_FOUNDATION_V1.json): the key
``atr14`` carried no statement of what an ATR-14 *is* here, and two materially
different M15 estimators feed it depending on the origin family --
``M15|high_low_mean_14`` for the seven single-symbol families and
``M15|wilder_true_range_14`` for the three current-framework ones.  They
disagree outside +/-10 % on 41.8 % of decision-cells, which flips 5.28 % of
current-framework rows across a 0.75 threshold.

Every test below asserts BEHAVIOUR -- values produced by calling the production
functions -- never the presence of a substring in the source.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from src.components.broader_origin_generators import (
    ATR_BASIS_BY_SOURCE,
    ATR_BASIS_M15_HIGH_LOW_MEAN_14,
    ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
    ATR_COMMON_BASIS,
    ATR_SOURCE_MODULE_HIGH_LOW_MEAN,
    ATR_SOURCE_MSO_WILDER_TRUE_RANGE,
    Bar,
    BarSeries,
    _atr,
    _current_framework_atr_resolution,
    _current_framework_atr_with_source,
)
from src.components.poi_execution_lifecycle import (
    predecision_limit_fillability_from_geometry,
)
from src.research_infra.wave21_forward_shadow.feature_contract import (
    ATR_BASIS_UNAVAILABLE,
    DECLARED_COMMON_ATR_BASIS,
    PREDECISION_FEATURE_KEYS,
    resolve_atr_common_basis,
    shadow_feature_row,
)

UTC = timezone.utc
T0 = datetime(2026, 8, 12, 12, 15, tzinfo=UTC)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_series(n: int = 60, *, gap: float = 0.0) -> BarSeries:
    """M15 bars with a fixed high-low range and an optional close-to-close gap.

    With ``gap`` > 0 each bar opens away from the prior close, so TRUE range
    exceeds high-low and the two estimators must diverge.  With ``gap`` == 0
    they must agree, which is what makes the divergence attributable.
    """

    bars = []
    base = 100.0
    for i in range(n):
        base += gap
        bars.append(
            Bar(
                time=T0 - timedelta(minutes=15 * (n - i)),
                open=base,
                high=base + 1.0,
                low=base - 1.0,
                close=base,
                volume=100.0,
            )
        )
    return BarSeries(
        symbol="EURUSD",
        timeframe="M15",
        bars=tuple(bars),
        source_path_feature_status="raw_data_m15_asof_complete",
        session_windows=(),
        decision_time_utc=T0,
    )


class FakeTF:
    def __init__(self, atr_14):
        self.atr_14 = atr_14


class FakeMSO:
    def __init__(self, atr_14):
        self.timeframes = {"M15": FakeTF(atr_14)}


def make_raw(*, family: str, atr14: float, basis: str | None, common: float | None):
    features = {name: 0.5 for name in PREDECISION_FEATURE_KEYS}
    features["trend_state_m15"] = "UP"
    features["trend_transition_flag"] = "False"
    fillability = {"available": True, "atr14": atr14, "atr14_basis": basis}
    raw = {
        "decision_time_utc": T0.isoformat(),
        "limit_first_expiry_utc": (T0 + timedelta(minutes=120)).isoformat(),
        "decision_window_id": "w1",
        "trading_day": "2026-08-12",
        "symbol": "EURUSD",
        "side": "LONG",
        "origin_family": family,
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "predecision_features": features,
        "predecision_limit_fillability": fillability,
        "atr14": atr14,
        "atr14_basis": basis,
    }
    if common is not None:
        raw["atr14_common_basis"] = ATR_COMMON_BASIS
        raw["atr14_common_basis_value"] = common
    return raw


# ---------------------------------------------------------------------------
# 1. the two bases are real, and named
# ---------------------------------------------------------------------------


def test_the_two_estimators_diverge_on_gapping_bars_and_agree_without_gaps():
    """The reason a basis label is needed at all, demonstrated numerically."""

    flat = make_series(gap=0.0)
    # the gap must exceed the bar's own range for TRUE range to bind: each bar
    # spans 2.0, so a 1.5 drift puts |high - prev_close| at 2.5.
    gapped = make_series(gap=1.5)

    # module estimator is mean(high-low) -- blind to gaps by construction, so it
    # returns the same 2.0 whether or not price gaps between bars.
    assert _atr(flat, len(flat.bars) - 1, 14) == pytest.approx(2.0)
    assert _atr(gapped, len(gapped.bars) - 1, 14) == pytest.approx(2.0)

    # a true-range estimator sees the gap; that difference is exactly what the
    # unlabelled `atr14` key was hiding.
    from src.components.market_state import calculate_atr

    candles = [
        {"high": b.high, "low": b.low, "close": b.close} for b in gapped.bars
    ]
    wilder = calculate_atr(candles, period=14)
    assert wilder > 2.0


def test_basis_labels_cover_every_source_tag_and_name_the_timeframe():
    assert set(ATR_BASIS_BY_SOURCE) == {
        ATR_SOURCE_MSO_WILDER_TRUE_RANGE,
        ATR_SOURCE_MODULE_HIGH_LOW_MEAN,
    }
    for basis in ATR_BASIS_BY_SOURCE.values():
        timeframe, _, estimator = basis.partition("|")
        assert timeframe == "M15"
        assert estimator
    assert ATR_COMMON_BASIS == ATR_BASIS_M15_HIGH_LOW_MEAN_14


# ---------------------------------------------------------------------------
# 2. the resolver is behaviour-preserving and now also yields a common basis
# ---------------------------------------------------------------------------


def test_resolution_preserves_geometry_atr_exactly_in_both_branches():
    """Stop geometry must not move: the repair adds a field, it does not re-point."""

    series = make_series()
    idx = len(series.bars) - 1

    with_mso = FakeMSO(3.5)
    assert _current_framework_atr_with_source(
        series=series, index=idx, mso=with_mso
    ) == (3.5, ATR_SOURCE_MSO_WILDER_TRUE_RANGE)
    value, source, common = _current_framework_atr_resolution(
        series=series, index=idx, mso=with_mso
    )
    assert (value, source) == (3.5, ATR_SOURCE_MSO_WILDER_TRUE_RANGE)
    # the common-basis value is the OTHER estimator, available even though the
    # geometry used Wilder -- this is what makes restatement possible.
    assert common == pytest.approx(2.0)
    assert common != value

    no_mso = FakeMSO(None)
    value2, source2, common2 = _current_framework_atr_resolution(
        series=series, index=idx, mso=no_mso
    )
    assert source2 == ATR_SOURCE_MODULE_HIGH_LOW_MEAN
    assert value2 == pytest.approx(2.0)
    # on the fallback branch the geometry ATR IS the common basis
    assert common2 == value2


def test_resolution_returns_no_common_basis_when_series_cannot_supply_one():
    empty = BarSeries(
        symbol="EURUSD",
        timeframe="M15",
        bars=(),
        source_path_feature_status="raw_data_m15_asof_complete",
        session_windows=(),
    )
    value, source, common = _current_framework_atr_resolution(
        series=empty, index=-1, mso=FakeMSO(None)
    )
    assert (value, source, common) == (0.0, None, None)


# ---------------------------------------------------------------------------
# 3. the fillability contract carries the basis on both return shapes
# ---------------------------------------------------------------------------


def test_fillability_echoes_the_basis_on_the_available_shape():
    fill = predecision_limit_fillability_from_geometry(
        side="LONG",
        entry_price=100.0,
        stop_loss=99.0,
        current_price=100.5,
        atr14=2.0,
        atr14_basis=ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
    )
    assert fill["available"] is True
    assert fill["atr14"] == pytest.approx(2.0)
    assert fill["atr14_basis"] == ATR_BASIS_M15_WILDER_TRUE_RANGE_14


def test_fillability_echoes_the_basis_on_the_degraded_shape_too():
    """The unavailable branch carries no atr14 -- it must still say what basis
    was offered, or the degradation is indistinguishable from a basis change."""

    fill = predecision_limit_fillability_from_geometry(
        side="",  # forces the unavailable branch
        entry_price=100.0,
        stop_loss=99.0,
        current_price=100.5,
        atr14=2.0,
        atr14_basis=ATR_BASIS_M15_HIGH_LOW_MEAN_14,
    )
    assert fill["available"] is False
    assert fill["atr14_basis"] == ATR_BASIS_M15_HIGH_LOW_MEAN_14


def test_fillability_basis_is_none_when_unlabelled_never_guessed():
    fill = predecision_limit_fillability_from_geometry(
        side="LONG",
        entry_price=100.0,
        stop_loss=99.0,
        current_price=100.5,
        atr14=2.0,
    )
    assert fill["atr14_basis"] is None


# ---------------------------------------------------------------------------
# 4. the repaired feature is basis-consistent ACROSS families
# ---------------------------------------------------------------------------


def test_two_families_on_different_bases_share_one_v2_denominator():
    """The defect, and its repair, in one assertion.

    Same symbol, same bar, same 1.0 risk.  The single-symbol family is natively
    on basis A (2.0); the current-framework family's geometry used basis B (3.5)
    but carries the basis-A value alongside.  As shipped their `risk_over_atr`
    disagree; on the repaired feature they agree exactly.
    """

    broad = shadow_feature_row(
        make_raw(
            family="displacement_continuation",
            atr14=2.0,
            basis=ATR_BASIS_M15_HIGH_LOW_MEAN_14,
            common=2.0,
        )
    )
    poi = shadow_feature_row(
        make_raw(
            family="current_fvg_fill",
            atr14=3.5,
            basis=ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
            common=2.0,
        )
    )

    # as shipped: the same trade geometry reads 75 % smaller in one family
    assert broad["risk_over_atr"] == pytest.approx(0.5)
    assert poi["risk_over_atr"] == pytest.approx(1.0 / 3.5)
    assert broad["risk_over_atr"] != pytest.approx(poi["risk_over_atr"])

    # repaired: identical, and each row says which basis it is on
    assert broad["risk_over_atr_v2"] == pytest.approx(poi["risk_over_atr_v2"])
    assert broad["risk_over_atr_v2"] == pytest.approx(0.5)
    assert broad["risk_over_atr_v2_basis"] == DECLARED_COMMON_ATR_BASIS
    assert poi["risk_over_atr_v2_basis"] == DECLARED_COMMON_ATR_BASIS
    assert poi["risk_over_atr_basis"] == ATR_BASIS_M15_WILDER_TRUE_RANGE_14


def test_a_threshold_that_flips_as_shipped_does_not_flip_on_the_repaired_feature():
    """The measured consequence (5.28 % of rows), reproduced as behaviour."""

    threshold = 0.75
    broad = shadow_feature_row(
        make_raw(
            family="displacement_continuation",
            atr14=1.0,
            basis=ATR_BASIS_M15_HIGH_LOW_MEAN_14,
            common=1.0,
        )
    )
    poi = shadow_feature_row(
        make_raw(
            family="current_fvg_fill",
            atr14=1.5,
            basis=ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
            common=1.0,
        )
    )
    # identical geometry, opposite verdicts, purely from the estimator
    assert (broad["risk_over_atr"] >= threshold) is True
    assert (poi["risk_over_atr"] >= threshold) is False
    # repaired: same geometry, same verdict
    assert (broad["risk_over_atr_v2"] >= threshold) is True
    assert (poi["risk_over_atr_v2"] >= threshold) is True


# ---------------------------------------------------------------------------
# 5. fail-closed: an unlabelled ATR is never treated as common-basis
# ---------------------------------------------------------------------------


def test_unlabelled_atr_is_refused_not_assumed():
    row = shadow_feature_row(
        make_raw(family="current_ob_retest", atr14=3.5, basis=None, common=None)
    )
    assert math.isnan(row["risk_over_atr_v2"])
    assert row["risk_over_atr_v2_basis"] == ATR_BASIS_UNAVAILABLE
    assert row["risk_over_atr_basis"] == ATR_BASIS_UNAVAILABLE
    # the frozen feature still computes -- the repair adds a refusal, it does
    # not break the live lane
    assert row["risk_over_atr"] == pytest.approx(1.0 / 3.5)


def test_wrong_basis_label_is_refused():
    """A candidate labelled basis B with no common value must NOT be restated."""

    value, basis = resolve_atr_common_basis(
        {"atr14": 3.5, "atr14_basis": ATR_BASIS_M15_WILDER_TRUE_RANGE_14}, {}
    )
    assert math.isnan(value)
    assert basis == ATR_BASIS_UNAVAILABLE


def test_declared_common_basis_mismatch_is_refused():
    value, basis = resolve_atr_common_basis(
        {
            "atr14_common_basis": "H4|high_low_mean_14",
            "atr14_common_basis_value": 9.0,
        },
        {},
    )
    assert math.isnan(value)
    assert basis == ATR_BASIS_UNAVAILABLE


def test_common_basis_is_read_from_nested_source_fields():
    value, basis = resolve_atr_common_basis(
        {
            "source_fields": {
                "atr14_common_basis": DECLARED_COMMON_ATR_BASIS,
                "atr14_common_basis_value": 2.5,
            }
        },
        {},
    )
    assert value == pytest.approx(2.5)
    assert basis == DECLARED_COMMON_ATR_BASIS


# ---------------------------------------------------------------------------
# 6. the frozen model surface is untouched
# ---------------------------------------------------------------------------


def test_repaired_feature_is_not_a_model_input():
    """`risk_over_atr_v2` must be invisible to the live ridge until a refit."""

    from src.research_infra.wave21_forward_shadow.feature_contract import (
        CATEGORICAL_FEATURES,
        NUMERIC_FEATURES,
    )

    model_features = set(CATEGORICAL_FEATURES) | set(NUMERIC_FEATURES)
    for added in (
        "risk_over_atr_v2",
        "risk_over_atr_v2_basis",
        "risk_over_atr_basis",
    ):
        assert added not in model_features
    assert "risk_over_atr" in model_features


def test_frozen_risk_over_atr_still_divides_by_the_fillability_atr14():
    """Regression pin: the live feature's VALUE is unchanged by this repair."""

    row = shadow_feature_row(
        make_raw(
            family="current_fvg_fill",
            atr14=3.5,
            basis=ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
            common=2.0,
        )
    )
    assert row["risk_over_atr"] == pytest.approx(1.0 / 3.5)
