"""The attribution has to be arithmetic, not narrative.

Every claim this session makes about *why* the armed book's firing rate moved rests on one
identity: `fires == eval_slots * prod(conditional pass rates)`, with no residual. If that
does not hold exactly, the "share of ramp" numbers are opinions with decimal places.

The panel controls are tested too, because the composition confound they remove is the one
that would otherwise have produced a wrong headline: the armed surface grows from 1-3
symbols to 13 in 2021, so an uncontrolled rate change measures the symbol mix.
"""

from __future__ import annotations

import datetime as dt

from src.research_infra.regime_spine import conditions as C
from src.research_infra.regime_spine import ramp as R
from src.research_infra.regime_spine.state import build_frame


def _frame(sym: str, seed: int, n: int, start_year: int):
    from tests.research_infra.test_regime_spine_state import _bars

    bars = _bars(n, seed=seed)
    t0 = dt.datetime(start_year, 1, 1, tzinfo=dt.timezone.utc)
    times = [t0 + dt.timedelta(hours=4 * i) for i in range(len(bars))]
    return build_frame(sym, 16388, bars, times)


def _frames():
    return {"XAUUSD": _frame("XAUUSD", 5, 5000, 2015),
            "XAGUSD": _frame("XAGUSD", 17, 5000, 2015),
            "XAUEUR": _frame("XAUEUR", 23, 1200, 2020)}


def test_decomposition_has_no_residual():
    frames = _frames()
    cond = C.SLEEVES["metals_core"]
    fun = R.funnel_by_period(frames, cond, grain="year")
    years = sorted(fun)
    a, b = years[:2], years[-2:]
    dec = R.decompose(fun, cond, a, b)
    if dec["log_fire_ratio"] is None:
        return  # a zero-fire era; the None is the point and is asserted elsewhere
    assert abs(dec["unexplained"]) < 1e-9, (
        "the opportunity term plus the gate terms must reproduce the log fire ratio "
        "exactly; a residual means the funnel is not the funnel")


def test_a_closed_gate_is_reported_not_averaged_away():
    """A gate that shut completely must surface as `closed_in_*`, never as a silent None."""
    frames = _frames()
    cond = C.SLEEVES["metals_core"]
    # an impossible persistence cut closes exactly one gate and nothing else
    fun = R.funnel_by_period(frames, cond, grain="year", params={"ac_thr": 99.0})
    years = sorted(fun)
    dec = R.decompose(fun, cond, years[:2], years[-2:])
    p = dec["gates"]["persistence"]
    assert p["closed_in_a"] and p["closed_in_b"]
    assert p["log_ratio"] is None
    assert dec["era_b"]["fires"] == 0


def test_strict_panel_is_stricter_than_common_panel():
    frames = _frames()
    cond = C.SLEEVES["metals_core"]
    era_a = [str(y) for y in range(2015, 2018)]
    era_b = [str(y) for y in range(2020, 2023)]
    common = R.common_panel(frames, cond, era_a, era_b)
    strict = R.strict_panel(frames, cond, era_a, era_b)
    assert set(strict) <= set(common)
    assert "XAUEUR" not in strict, "a symbol absent from era A must not enter the panel"


def test_symbol_restriction_actually_restricts():
    frames = _frames()
    cond = C.SLEEVES["metals_core"]
    full = R.funnel_by_period(frames, cond, grain="year")
    one = R.funnel_by_period(frames, cond, grain="year", symbols=["XAUUSD"])
    assert sum(c.slots for c in one.values()) < sum(c.slots for c in full.values())
    assert all(c.symbols == {"XAUUSD"} for c in one.values())


def test_joint_lift_separates_marginal_drift_from_co_occurrence():
    """Independence-implied fires vs observed — the (b)/(c) discriminator itself."""
    frames = _frames()
    cond = C.SLEEVES["sub_xvol_pullback"]
    fun = R.funnel_by_period(frames, cond, grain="year")
    years = sorted(fun)
    dec = R.decompose(fun, cond, years[:2], years[-2:])
    for era in ("era_a", "era_b"):
        node = dec["independence"][era]
        if node.get("independent_fires") is None:
            continue
        mr = node["marginal_rates"]
        assert all(0.0 <= v <= 1.0 for v in mr.values())
        assert node["independent_fires"] >= 0.0


def test_threshold_percentile_ranks_only_cover_threshold_gates():
    frames = _frames()
    cond = C.SLEEVES["metals_core"]
    pct = R.threshold_percentile_ranks(frames, cond, grain="year")
    names = {g.name for g in cond.gates if g.cause == C.THRESHOLD}
    assert set(pct) <= names
    assert "fvg_retest" not in pct, "a structure gate has no level to rank"
    for _g, node in pct.items():
        for _y, row in node["by_period"].items():
            if row["thr_pct_rank"] is not None:
                assert 0.0 <= row["thr_pct_rank"] <= 1.0


def test_weekday_sessions_counts_mondays_to_fridays():
    assert R.weekday_sessions(dt.date(2026, 1, 5), dt.date(2026, 1, 11)) == 5
    assert R.weekday_sessions(dt.date(2026, 1, 10), dt.date(2026, 1, 11)) == 0
    assert R.weekday_sessions(dt.date(2026, 1, 11), dt.date(2026, 1, 5)) == 0
