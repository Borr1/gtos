"""The fixing machine must produce the RIGHT repair, and must never move a verdict.

Two properties carry this file. First, no gate is relaxed: running with `diagnose=True`
must return byte-identical verdicts to running without it, or the diagnostic head is a
back door into the admission standard. Second, the prescription must be mechanistically
correct — a sleeve whose gross is positive and whose net is negative gets COST_GEOMETRY,
one with no excursion at all gets INVERSE_TEST, and one whose day-mean is fine but whose
per-trade mean is not gets PER_TRADE_QUALITY. Those are constructed here rather than
asserted about the estate, so the test says something even when the estate changes.
"""

from __future__ import annotations

import datetime as dt
import json
import random

import pytest

from src.research_infra.walkforward import TradeRecord, Verdict, run_gate
from src.research_infra.walkforward.diagnostics import (
    Prescription,
    _breadth_multiple,
    build_repair_queue,
    cost_decomposition,
    diagnose_sleeve,
    excursion_from_features,
)
from src.research_infra.walkforward.panel import PricedTrade
from src.research_infra.walkforward.spec import GateSpec

UTC = dt.timezone.utc
FAST = dict(n_bootstrap=400, n_permutation=400)


def _spec(**kw) -> GateSpec:
    base = dict(spec_id="t_diag", authored_utc="2026-07-29T00:00:00+00:00", **FAST)
    base.update(kw)
    return GateSpec(**base)


def _mk(sleeve, symbol, n, gen, *, rng, start=dt.date(2016, 1, 4), sl=1.0, px=100.0,
        hold_h=6.0, features=None):
    out, d = [], start
    for i in range(n):
        d += dt.timedelta(days=rng.choice((1, 1, 2, 3)))
        e = dt.datetime(d.year, d.month, d.day, 8, tzinfo=UTC)
        out.append(TradeRecord(
            sleeve=sleeve, symbol=symbol, entry_utc=e,
            exit_utc=e + dt.timedelta(hours=hold_h), direction=rng.choice([1, -1]),
            sl_distance_price=sl, entry_price=px, r_gross=gen(i, d),
            features=dict(features or {})))
    return out


def _priced(trades, *, cost=0.05, components=None, nights=0.0):
    return [
        PricedTrade(t, cost, None, "priced",
                    components=dict(components or {"commission_r": cost, "swap_r": 0.0,
                                                   "spread_r": 0.0, "slippage_r": 0.0}),
                    swap_nights=nights)
        for t in trades
    ]


# =====================================================================================
# 1. THE PROPERTY THAT MATTERS MOST: diagnose() cannot move a verdict
# =====================================================================================
def test_diagnose_changes_no_verdict_and_no_gate():
    rng = random.Random(7)
    trades = {
        "metals_core": _mk("metals_core", "XAUUSD", 400,
                           lambda i, d: rng.gauss(0.05, 1.0), rng=rng),
        "crypto": _mk("crypto", "BTCUSD", 260,
                      lambda i, d: rng.gauss(-0.02, 1.0), rng=rng),
    }
    spec = _spec()
    plain = run_gate(trades, spec)
    diag = run_gate(trades, spec, diagnose=True, server="FTMO-Server3")

    # `robustness.retention` is NaN whenever the headline expectancy is <= 0, and
    # NaN != NaN, so a bare dict comparison reports a difference where there is none.
    # Compare the serialised form, which is also what any downstream consumer reads.
    def _ser(x):
        return json.dumps(x, sort_keys=True, default=str)

    for s in plain.verdicts:
        assert plain.verdicts[s].verdict is diag.verdicts[s].verdict
        assert _ser(plain.verdicts[s].gates) == _ser(diag.verdicts[s].gates)
        assert _ser(plain.verdicts[s].q_value) == _ser(diag.verdicts[s].q_value)
        assert _ser(plain.verdicts[s].pooled_oos_mean_r) == _ser(
            diag.verdicts[s].pooled_oos_mean_r)
        assert plain.verdicts[s].reasons == diag.verdicts[s].reasons
    assert plain.spec.seal() == diag.spec.seal()
    assert diag.verdicts["metals_core"].diagnostics is not None
    assert plain.verdicts["metals_core"].diagnostics is None


def test_repair_queue_refuses_without_the_priced_population():
    rng = random.Random(3)
    trades = {"crypto": _mk("crypto", "BTCUSD", 120, lambda i, d: rng.gauss(0, 1), rng=rng)}
    res = run_gate(trades, _spec())
    with pytest.raises(ValueError, match="diagnose=True"):
        res.repair_queue()


# =====================================================================================
# 2. The prescriptions are mechanistically right
# =====================================================================================
def test_positive_gross_eaten_by_cost_prescribes_cost_geometry():
    """The §2.2 headline row: expectancy fails, gross > 0 => cost geometry, not a verdict."""
    rng = random.Random(11)
    # +0.04 R/trade gross, 0.09 R/trade cost => net negative, gross clearly positive.
    trades = _mk("fx_jpy", "USDJPY", 300, lambda i, d: rng.gauss(0.04, 0.3), rng=rng)
    priced = _priced(trades, cost=0.09,
                     components={"commission_r": 0.07, "swap_r": 0.01,
                                 "spread_r": 0.01, "slippage_r": 0.0})
    spec = _spec()
    res = run_gate({"fx_jpy": trades}, spec, diagnose=True)
    sv = res.verdicts["fx_jpy"]
    # Substitute the constructed cost population so the arithmetic is the test's, not the
    # broker artifact's — the gate's own verdict is irrelevant here, the mapping is not.
    d = diagnose_sleeve(sv, spec, priced=priced)
    exp = next(g for g in d.gates if g.gate == "expectancy_per_day")
    if not exp.passed:
        assert exp.prescription is Prescription.COST_GEOMETRY
        assert "commission" in exp.action
    assert d.cost_decomposition["largest_term"] == "commission_r"
    assert d.cost_decomposition["mean_gross_r"] > 0


def test_negative_with_excursion_prescribes_exit_repair():
    rng = random.Random(13)
    trades = _mk("mx_ger40", "GER40.cash", 200, lambda i, d: rng.gauss(-0.10, 0.4),
                 rng=rng, features={"mfe_r": 1.8, "mae_r": -0.6, "bars_to_mfe": 4,
                                    "exit_reason": "maxbars"})
    d = diagnose_sleeve(_stub_verdict("mx_ger40", day=-0.10), _spec(),
                        priced=_priced(trades, cost=0.02))
    exp = next(g for g in d.gates if g.gate == "expectancy_per_day")
    assert exp.prescription is Prescription.EXIT_REPAIR
    assert "excursion" in exp.action or "move" in exp.action


def test_negative_without_excursion_prescribes_inverse_test():
    rng = random.Random(17)
    trades = _mk("mx_us500", "US500.cash", 200, lambda i, d: rng.gauss(-0.20, 0.3),
                 rng=rng, features={"mfe_r": 0.12, "mae_r": -0.9, "bars_to_mfe": 1,
                                    "exit_reason": "stop"})
    d = diagnose_sleeve(_stub_verdict("mx_us500", day=-0.20), _spec(),
                        priced=_priced(trades, cost=0.02))
    exp = next(g for g in d.gates if g.gate == "expectancy_per_day")
    assert exp.prescription is Prescription.INVERSE_TEST
    assert "INVERSE" in exp.action


def test_day_mean_ok_but_per_trade_bad_prescribes_per_trade_quality():
    sv = _stub_verdict("clusterer", day=0.30, per_trade=-0.02, per_trade_pass=False)
    d = diagnose_sleeve(sv, _spec(), priced=[])
    pt = next(g for g in d.gates if g.gate == "expectancy_per_trade")
    assert pt.prescription is Prescription.PER_TRADE_QUALITY
    assert "intraday count" in pt.action


def test_coverage_failure_is_a_data_path_never_unjudgeable():
    sv = _stub_verdict("mx_cadjpy", coverage=0.0, coverage_pass=False,
                       unpriceable=["CADJPY"])
    d = diagnose_sleeve(sv, _spec(), priced=[])
    cov = next(g for g in d.gates if g.gate == "coverage")
    assert cov.prescription is Prescription.DATA_PATH
    assert "CADJPY" in cov.action
    assert "unjudgeable" in cov.action.lower()
    assert cov.margin == pytest.approx(-0.95)


def test_sample_failure_carries_what_would_make_it_evaluable():
    sv = _stub_verdict("thin", sample_pass=False, n_scored=12, min_trades=30,
                       n_folds=2, min_folds=3)
    d = diagnose_sleeve(sv, _spec(), priced=[])
    smp = next(g for g in d.gates if g.gate == "sample")
    assert smp.prescription is Prescription.SAMPLE_EXTENSION
    lacks = smp.evidence["what_would_make_it_evaluable"]
    assert any("18 more scored trades" in x for x in lacks)
    assert any("1 more evaluable folds" in x for x in lacks)


def test_fidelity_is_a_stamp_and_a_work_item_never_a_refusal():
    sv = _stub_verdict("asian_fade", fid_pass=False, fid_recall=0.073)
    d = diagnose_sleeve(sv, _spec(), priced=[])
    f = next(g for g in d.gates if g.gate == "fidelity")
    assert f.prescription is Prescription.FIDELITY_RECONCILIATION
    assert "unknowable" in f.action
    assert f.margin == pytest.approx(0.073 - 0.50)


# =====================================================================================
# 3. Breadth arithmetic — the significance repair carries a number
# =====================================================================================
def test_breadth_multiple_is_the_variance_ratio():
    """p=0.0124 at alpha=0.10 needs roughly (z_.10/z_.0124)^2 ~ 0.32 of the breadth.

    i.e. it ALREADY clears alpha raw and only fails the multiplicity bill — which is the
    exact shape of `mx_btcusd_d1_donchian_20` in FOURTH_REVIEW §3.3, and the reading must
    say the repair is the family pool, not more data.
    """
    b = _breadth_multiple(0.0124, 0.149, 0.10)
    assert b["available"]
    assert b["breadth_multiple_needed"] < 1.0
    assert "multiplicity bill" in b["reading"]

    # A genuinely weak p needs real breadth.
    b2 = _breadth_multiple(0.30, 0.60, 0.10)
    assert b2["breadth_multiple_needed"] > 2.0
    assert "pooling" in b2["reading"]


def test_breadth_refuses_on_a_left_tail_p():
    assert _breadth_multiple(0.999, 1.0, 0.10)["available"] is False
    assert _breadth_multiple(None, None, 0.10)["available"] is False


# =====================================================================================
# 4. Evidence builders
# =====================================================================================
def test_cost_decomposition_uses_abs_gross_so_a_zero_edge_sleeve_does_not_explode():
    """`idxrev` is +0.006 gross on n=6,473. Signed-sum denominators divide by ~0."""
    rng = random.Random(23)
    trades = _mk("idxrev", "US500.cash", 600, lambda i, d: rng.gauss(0.0, 1.0), rng=rng)
    dec = cost_decomposition(_priced(trades, cost=0.03))
    assert dec["available"]
    assert abs(dec["cost_pct_of_abs_gross"]) < 100.0  # sane, because |gross| is the base
    assert dec["terms"]["commission_r"]["share_of_cost"] == pytest.approx(1.0)


def test_excursion_says_what_would_supply_it_when_absent():
    rng = random.Random(29)
    trades = _mk("x", "XAUUSD", 20, lambda i, d: 0.1, rng=rng)
    exc = excursion_from_features(_priced(trades))
    assert exc["available"] is False
    assert "exits.replay" in exc["what_would_supply_it"]


def test_repair_queue_shape_and_admitted_rows():
    rng = random.Random(31)
    trades = {
        "good": _mk("good", "XAUUSD", 400, lambda i, d: rng.gauss(0.25, 0.6), rng=rng),
        "bad": _mk("bad", "BTCUSD", 400, lambda i, d: rng.gauss(-0.25, 0.6), rng=rng),
    }
    res = run_gate(trades, _spec(), diagnose=True, server="FTMO-Server3")
    q = res.repair_queue(server="FTMO-Server3", run_label="unit")
    assert q["schema"] == "gtos.walkforward.repair_queue.v1"
    assert q["spec_sha256"] == res.spec.seal()
    assert set(r["sleeve"] for r in q["rows"]) == {"good", "bad"}
    # every row names a component from the brief's vocabulary
    assert all(r["component"] for r in q["rows"])
    # a rejected sleeve must carry at least one actionable line
    bad_rows = [r for r in q["rows"] if r["sleeve"] == "bad"]
    if res.verdicts["bad"].verdict is not Verdict.ADMIT:
        assert any(r["action"] for r in bad_rows)


def test_session_buckets_are_stamped_with_their_clock_basis():
    rng = random.Random(37)
    trades = _mk("s", "XAUUSD", 60, lambda i, d: 0.1, rng=rng)
    d = diagnose_sleeve(_stub_verdict("s"), _spec(), priced=_priced(trades),
                        server="FTMO-Server3")
    assert d.by_session
    assert all("[" in row["session"] for row in d.by_session)
    d_utc = diagnose_sleeve(_stub_verdict("s"), _spec(), priced=_priced(trades))
    assert all("utc_hour" in row["session"] for row in d_utc.by_session)


# =====================================================================================
# stub verdict — lets the mapping be tested independently of any real gate run
# =====================================================================================
def _stub_verdict(sleeve, *, day=0.5, per_trade=0.1, per_trade_pass=True,
                  coverage=1.0, coverage_pass=True, unpriceable=None,
                  sample_pass=True, n_scored=100, min_trades=30, n_folds=5, min_folds=3,
                  fid_pass=True, fid_recall=0.96):
    from src.research_infra.walkforward.gate import SleeveVerdict

    sv = SleeveVerdict(sleeve=sleeve, verdict=Verdict.REJECT, n_trades=n_scored)
    sv.fidelity = {"class": "per_bar", "basis": "measured_direct", "live_recall": fid_recall,
                   "basis_n": 167, "basis_note": "", "ceiling_stamp": ""}
    sv.gates = {
        "fidelity": {"pass": fid_pass, "floor": 0.50, "live_recall": fid_recall},
        "cost_coverage": {"pass": coverage_pass, "coverage_frac": coverage, "floor": 0.95,
                          "policy": "refuse", "weakest_coverage": None,
                          **({"unpriceable_symbols": unpriceable,
                              "priceable_symbols": []} if unpriceable else {})},
        "sample": {"pass": sample_pass, "n_trades_in_scored_folds": n_scored,
                   "min_trades_total": min_trades, "n_folds_evaluable": n_folds,
                   "min_folds_evaluable": min_folds, "n_thin_folds": 0,
                   "thin_fold_frac": 0.0, "max_thin_fold_frac": 0.34, "fold_status": {},
                   "n_priced_trades_all_folds": n_scored},
        "expectancy": {"pass": day > 0 and per_trade_pass, "pooled_oos_mean_r": day,
                       "min_oos_mean_r": 0.0, "pooling_weights": "equal_by_fold",
                       "oos_mean_r_per_trade": per_trade, "min_oos_mean_r_per_trade": 0.0,
                       "per_trade_pass": per_trade_pass, "n_scored_oos_trades": n_scored},
        "lifetime": {"pass": True, "enabled": True,
                     "mean_r_net_per_trade_all_folds": 0.1, "min_lifetime_mean_r": 0.0,
                     "n_priced_trades_all_folds": n_scored},
        "stability": {"pass": True, "oos_positive_fold_frac": 0.8,
                      "min_oos_positive_fold_frac": 0.6, "fold_means": [0.1, 0.2, -0.1],
                      "n_thin_folds_counted_as_non_positive": 0, "denominator": 3},
        "robustness": {"pass": True, "enabled": True, "dropped_fold_id": 2,
                       "retention": 0.8, "retention_floor": 0.5},
        "significance": {"pass": True, "p_raw": 0.01, "q_value": 0.02, "alpha": 0.10,
                         "multiplicity": "benjamini_hochberg", "family_size": 12},
    }
    sv.folds = []
    sv.telemetry = {}
    sv.coverage = {}
    return sv


def test_zero_trade_sleeve_gets_a_generation_prescription_not_a_coverage_one():
    """Measured defect from this module's first run: it said "capture ticks for []".

    A sleeve with no trades has coverage 0/0. Handing it the coverage prescription names
    an empty symbol list and points a data-capture ceremony at nothing. The two failures
    are mechanistically different and the repairs are different, so they are separated.
    """
    sv = _stub_verdict("vp_euidx_pocgrav", coverage=0.0, coverage_pass=False,
                       unpriceable=[], n_scored=0)
    sv.n_trades = 0
    d = diagnose_sleeve(sv, _spec(), priced=[])
    assert d.primary is Prescription.GENERATION
    gen = next(g for g in d.gates if g.gate == "generation")
    # the register names the exact missing input and the fetch that supplies it
    assert "M1" in gen.action
    assert "GER40" in gen.action and "UK100" in gen.action
    assert "vp_euidx.py:70" in gen.action
    assert not any(g.gate == "coverage" for g in d.gates)


def test_an_unregistered_zero_trade_sleeve_is_told_to_read_the_guard():
    sv = _stub_verdict("some_new_sleeve", coverage=0.0, coverage_pass=False, n_scored=0)
    sv.n_trades = 0
    d = diagnose_sleeve(sv, _spec(), priced=[])
    assert d.primary is Prescription.GENERATION
    assert "fail-closed guards" in d.repair_paths[-1]


def test_capture_ratio_is_a_ratio_of_means_not_a_mean_of_ratios():
    """B615: the mean of per-trade `R / MFE` is unbounded below and read NEGATIVE for
    every sleeve in the estate — an artefact of near-zero denominators, not a capture
    ratio. Pooled is bounded and is what "share of the excursion the exit kept" means.
    """
    rng = random.Random(101)
    # 9 trades that kept most of a 2R excursion, and 1 that stopped out after a 0.02R one.
    good = _mk("s", "XAUUSD", 9, lambda i, d: 1.6, rng=rng,
               features={"mfe_r": 2.0, "mae_r": -0.3, "exit_reason": "target"})
    bad = _mk("s", "XAUUSD", 1, lambda i, d: -1.0, rng=rng,
              features={"mfe_r": 0.02, "mae_r": -1.0, "exit_reason": "stop"})
    exc = excursion_from_features(_priced(good + bad))
    # mean of ratios would be (9*0.8 + (-50)) / 10 = -4.28 — a nonsense "capture ratio".
    assert exc["capture_ratio_pooled"] == pytest.approx((9 * 1.6 - 1.0) / (9 * 2.0 + 0.02),
                                                        abs=1e-5)
    assert exc["capture_ratio_pooled"] > 0
    assert "capture_ratio_mean" not in exc
    assert "ratio of means" in exc["capture_ratio_note"] or "RATIO OF MEANS" in \
        exc["capture_ratio_note"] or "sum(realised R)" in exc["capture_ratio_note"]
