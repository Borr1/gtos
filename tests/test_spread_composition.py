"""Session AH -- the era x hour composition repair, tested behaviourally.

AF filed the defect: ``spread_model_v1`` multiplies an era ratio by an hour-of-week
multiplier, each validated alone, and the product reaches 198x-880x the modern base on
pre-2010 FX -- charging up to 178 % of the risk unit as spread. The repair damps the hour
PREMIUM by ``era_ratio ** (b - 1)`` with ``b = 0.5041`` measured on three axes.

Every test here asserts a property of the composition rather than a number from the fit, so
re-measuring ``b`` on better data changes the constant and not this file. The two that DO
pin numbers pin the ones that must never move: v1 reproducibility, and exactness in the
reference window.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from src.costs.spread_model import (
    COMPOSITIONS,
    DEFAULT_COMPOSITION,
    ERA_HOUR_EXPONENT,
    ERA_HOUR_EXPONENT_ENVELOPE,
    PREMIUM_FLOOR,
    SpreadModelError,
    damped_intraweek_mult,
    load_spread_model,
    spread_price,
)
from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

REPO = Path(__file__).resolve().parents[1]
MODEL = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
RULE = resolve_rule("FTMO-Server3")

pytestmark = pytest.mark.skipif(
    not MODEL.is_file(),
    reason="SPREAD_MODEL_V1.json absent; build with scripts/build_spread_model.py",
)


def at_broker_wall(y: int, m: int, d: int, hour: int) -> dt.datetime:
    """The UTC instant whose FTMO wall clock is `hour`:30 on that date.

    Hour-of-week is defined on the broker's wall clock, so a test that wants "the rollover"
    has to ask for it there. Building the instant in UTC and hoping is how a test ends up
    measuring hour 21 and passing for the wrong reason -- which is what the first draft of
    this file did.
    """
    return broker_naive_to_utc(dt.datetime(y, m, d, hour, 30), RULE)


@pytest.fixture(scope="module")
def model():
    return load_spread_model()


# ------------------------------------------------------------- the pure function


def test_an_hour_without_a_material_premium_is_left_alone():
    """Below `PREMIUM_FLOOR` the multiplier is session structure, not a rollover spike, and
    the fitted exponent was never measured on it. Both directions matter: a cheap era
    (ratio < 1) would otherwise have a 1.14x metals multiplier rescaled UPWARD."""
    for m in (0.5, 0.9, 1.0, 1.14, PREMIUM_FLOOR - 1e-9):
        for ratio in (0.178, 0.2, 1.0, 5.0, 50.0):
            assert damped_intraweek_mult(m, ratio, 0.5) == m


def test_the_reference_era_is_reproduced_exactly():
    """era_ratio == 1 is the window the hour term was measured in, so v1 is right there."""
    for m in (1.0, 1.14, 2.0, 13.0, 35.0):
        assert damped_intraweek_mult(m, 1.0, ERA_HOUR_EXPONENT) == pytest.approx(m)


def test_exponent_one_is_v1_exactly():
    for m in (2.0, 13.0, 35.0):
        for ratio in (0.18, 2.0, 13.0, 50.0):
            assert damped_intraweek_mult(m, ratio, 1.0) == pytest.approx(m)


def test_the_premium_is_monotone_decreasing_in_the_era_ratio():
    """A wider era pays a smaller MULTIPLE -- that is the whole content of b < 1."""
    prev = None
    for ratio in (1.0, 2.0, 5.0, 13.0, 50.0):
        m = damped_intraweek_mult(35.0, ratio, ERA_HOUR_EXPONENT)
        if prev is not None:
            assert m < prev
        prev = m


def test_the_multiplier_never_falls_below_one():
    """No book ever quoted a rollover TIGHTER than its own era's calm level."""
    for ratio in (1e3, 1e6):
        assert damped_intraweek_mult(35.0, ratio, 0.1) >= 1.0


def test_a_cheaper_era_pays_a_larger_multiple_but_only_on_a_real_premium():
    """The same physics run the other way: a thinner base makes a fixed premium a bigger
    ratio. XAUUSD's 2022 era ratio is 0.178x, so this direction is not hypothetical -- and it
    is the direction that made this repair briefly INCREASE the metals charge, which is why
    it is gated on `PREMIUM_FLOOR`."""
    assert (damped_intraweek_mult(35.0, 0.178, ERA_HOUR_EXPONENT)
            > damped_intraweek_mult(35.0, 1.0, ERA_HOUR_EXPONENT))
    # ...and the metals case that broke AG's test is now untouched in that direction.
    assert damped_intraweek_mult(1.14, 0.178, ERA_HOUR_EXPONENT) == 1.14


# ------------------------------------------------------------ through the model


def test_default_composition_is_the_measured_one():
    assert DEFAULT_COMPOSITION == "v2_damped"
    assert set(COMPOSITIONS) == {"v2_damped", "v1_multiplicative"}
    lo, hi = ERA_HOUR_EXPONENT_ENVELOPE
    assert 0.0 < lo <= ERA_HOUR_EXPONENT <= hi < 1.0, (
        "the fitted exponent must sit inside its own envelope and strictly below 1.0, "
        "which is the composition AF refuted")


def test_a_bad_composition_name_refuses(model):
    with pytest.raises(SpreadModelError):
        model.estimate("EURUSD", "FTMO", at_broker_wall(2013, 6, 12, 0),
                       composition="whatever_i_like")


def test_the_repair_shrinks_the_af_defect_case_by_a_lot(model):
    """AF's own numbers: NZDUSD in the 2000s composed to 198x and charged 178 % of the stop.

    Asserted as a ratio between compositions rather than as a level, so the artifact can be
    rebuilt without breaking the test -- what must hold is that the product falls a long way
    and that it falls on the FX rollover specifically.
    """
    t = at_broker_wall(2005, 6, 14, 0)
    v1 = model.estimate("NZDUSD", "FTMO", t, band="mid", composition="v1_multiplicative")
    v2 = model.estimate("NZDUSD", "FTMO", t, band="mid", composition="v2_damped")
    assert v1.era_ratio == v2.era_ratio, "the repair must not touch the era term"
    assert v2.spread_price < v1.spread_price / 2.0
    assert v2.intraweek_mult >= 1.0


def test_nothing_moves_where_there_is_no_rollover_premium(model):
    """Fourteen instruments do not quote at the rollover at all (AG §5), so their hour
    multiplier is 1.00 and the repair must be a no-op on them -- byte-identical, not close.
    """
    t = at_broker_wall(2022, 6, 14, 0)
    for sym in ("XAUUSD", "XAGUSD", "US30_cash", "BTCUSD"):
        v1 = model.estimate(sym, "FTMO", t, band="mid", composition="v1_multiplicative")
        v2 = model.estimate(sym, "FTMO", t, band="mid", composition="v2_damped")
        assert v1.spread_price == v2.spread_price, sym


def test_a_calm_hour_is_unaffected_in_any_era(model):
    """Broker hour 12 carries multiplier ~1.0 on every class, so an era-wide change there
    would mean the damping had leaked out of the premium it is supposed to be about."""
    t = at_broker_wall(2002, 6, 12, 12)
    v1 = model.estimate("EURUSD", "FTMO", t, band="mid", composition="v1_multiplicative")
    v2 = model.estimate("EURUSD", "FTMO", t, band="mid", composition="v2_damped")
    assert v1.spread_price == pytest.approx(v2.spread_price)


def test_the_envelope_is_ordered_and_brackets_v1(model):
    t = at_broker_wall(2002, 6, 12, 0)
    lo, hi = ERA_HOUR_EXPONENT_ENVELOPE
    a = model.estimate("EURUSD", "FTMO", t, band="mid", era_exponent=lo).spread_price
    b = model.estimate("EURUSD", "FTMO", t, band="mid").spread_price
    c = model.estimate("EURUSD", "FTMO", t, band="mid", era_exponent=hi).spread_price
    d = model.estimate("EURUSD", "FTMO", t, band="mid",
                       composition="v1_multiplicative").spread_price
    assert a < b < c < d, (a, b, c, d)


def test_the_estimate_carries_its_composition_and_both_multipliers(model):
    t = at_broker_wall(2002, 6, 12, 0)
    e = model.estimate("EURUSD", "FTMO", t, band="mid")
    assert e.composition == "v2_damped"
    assert e.detail["hour_mult_reference"] > e.detail["hour_mult_effective"]
    assert e.detail["era_hour_exponent"] == pytest.approx(ERA_HOUR_EXPONENT)
    assert "AH composition repair" in e.provenance
    assert e.as_dict()["composition"] == "v2_damped"
    v1 = model.estimate("EURUSD", "FTMO", t, band="mid", composition="v1_multiplicative")
    assert v1.detail["era_hour_exponent"] is None


def test_spread_price_helper_passes_the_composition_through():
    t = at_broker_wall(2002, 6, 12, 0)
    assert (spread_price("EURUSD", "FTMO", t, band="mid").spread_price
            < spread_price("EURUSD", "FTMO", t, band="mid",
                           composition="v1_multiplicative").spread_price)


# ------------------------------------------------------------- through cost_r


def test_cost_r_charges_the_repaired_composition():
    from src.costs import cost_r

    t = at_broker_wall(2005, 6, 14, 0)
    base = dict(holding_hours=5.0, sl_distance_price=0.004, entry_price=0.70,
                entry_utc=t, spread_band="mid")
    v1 = cost_r("NZDUSD", "FTMO", **base, spread_composition="v1_multiplicative")
    v2 = cost_r("NZDUSD", "FTMO", **base, spread_composition="v2_damped")
    dflt = cost_r("NZDUSD", "FTMO", **base)
    assert v2.total_r.value < v1.total_r.value
    assert dflt.total_r.value == pytest.approx(v2.total_r.value), (
        "the default must be the measured one")
    assert dflt.detail["spread"]["composition"] == "v2_damped"
    assert "v2_damped" in dflt.detail["spread"]["source"]


def test_cost_r_is_untouched_when_no_band_is_requested():
    """The snapshot path must not learn about compositions -- it has no era term to damp."""
    from src.costs import cost_r

    t = at_broker_wall(2005, 6, 14, 0)
    a = cost_r("NZDUSD", "FTMO", 5.0, sl_distance_price=0.004, entry_price=0.70, entry_utc=t)
    b = cost_r("NZDUSD", "FTMO", 5.0, sl_distance_price=0.004, entry_price=0.70, entry_utc=t,
               spread_composition="v1_multiplicative")
    assert a.total_r.value == b.total_r.value
    assert a.detail["spread"].get("composition") is None


# ------------------------------------------------------------ through the gate


def test_gate_spec_carries_the_composition_and_the_note_reports_it():
    from src.research_infra.walkforward.gate import _cost_window_note
    from src.research_infra.walkforward.options import OPTIONS

    spec = OPTIONS["C_exploratory"].with_(spread_band="mid")
    note = _cost_window_note(spec)
    assert note["composition"] == "v2_damped"
    assert note["era_hour_exponent"] == pytest.approx(ERA_HOUR_EXPONENT)
    assert "198x-880x" in note["composition_note"]

    v1spec = spec.with_(spread_composition="v1_multiplicative")
    n1 = _cost_window_note(v1spec)
    assert n1["composition"] == "v1_multiplicative"
    assert n1["era_hour_exponent"] is None
    assert "UNVALIDATED" in n1["composition_note"]
    assert spec.seal() != v1spec.seal(), (
        "the composition changes what a verdict means, so it must change the spec seal")


# --------------------------------------------------- the evidence behind the fit


def test_the_bar_spread_column_semantics_receipt_says_minimum():
    """The repair rests on the bar column being a MINIMUM, which is why the era term could
    never have validated the hour term at H4. If that receipt is ever regenerated and says
    something else, this file's reasoning needs revisiting -- so assert it."""
    p = (REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
         / "AH_BAR_SPREAD_SEMANTICS.json")
    if not p.is_file():
        pytest.skip("AH_BAR_SPREAD_SEMANTICS.json absent (ah_spread_scan.py bar-semantics)")
    doc = json.loads(p.read_text())
    assert doc["verdict"] == "min"
    assert doc["median_exact_match_rate"]["min"] > 0.95
    assert len(doc["symbols"]) >= 20


def test_the_fit_receipt_rejects_the_multiplicative_composition():
    p = (REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
         / "AH_COMPOSITION_TESTS.json")
    if not p.is_file():
        pytest.skip("AH_COMPOSITION_TESTS.json absent (ah_spread_compose.py validate)")
    fit = json.loads(p.read_text())["fit"]
    assert fit["depart_from_v1"] is True
    assert fit["v1_multiplicative_rejected_by"], "b=1 must be rejected somewhere"
    # The shipped constant must be the receipt's own point estimate, and inside its envelope.
    # Asserted as "inside the envelope and within one SE of the point" rather than as equality
    # to 4 dp: re-measuring b on better data should not force a re-ship of every downstream
    # artifact to change a 4th decimal, but a constant that drifts outside the measured
    # envelope IS a defect and this catches it.
    lo, hi = fit["b_envelope"]
    assert lo <= ERA_HOUR_EXPONENT <= hi, (ERA_HOUR_EXPONENT, fit["b_envelope"])
    se = fit["b_se_of_point"] or 0.05
    assert abs(fit["b_point"] - ERA_HOUR_EXPONENT) <= se, (
        f"shipped {ERA_HOUR_EXPONENT} is more than one SE ({se:.4f}) from the receipt's "
        f"fitted {fit['b_point']:.4f} -- re-ship or re-fit")
    assert [round(x, 3) for x in fit["b_envelope"]] == \
        [round(x, 3) for x in ERA_HOUR_EXPONENT_ENVELOPE]
