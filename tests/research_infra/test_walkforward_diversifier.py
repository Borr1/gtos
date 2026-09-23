"""The guard layer must refuse every attack that reached CERTIFIED_DIVERSIFIER.

Each test reconstructs one adversarial refuter's attack in miniature and asserts the guard
that closes it. The shape of every attack is the same and it is the shape W's gate was
already hardened against: **put the losses where the scored statistic does not look.**

`certify_diversifier` receives two daily series, two booleans and one scalar, so it cannot
look. The guards supply what it cannot see and refuse on it.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.research_infra.walkforward.diversifier import (  # noqa: E402
    MAX_APPLIED_SCALE,
    MIN_CORR_OVERLAP,
    DiversifierEvidence,
    applied_vol_match_scale,
    certify_guarded,
)


def _series(n: int, mean: float, amp: float, start: dt.date = dt.date(2020, 1, 1),
            step: int = 1) -> dict:
    """Deterministic alternating series: exact sample mean, exact population std."""
    return {(start + dt.timedelta(days=i * step)).isoformat():
            mean + (amp if i % 2 == 0 else -amp) for i in range(n)}


def _book() -> dict:
    return _series(600, 0.004, 0.02)


def _good_evidence(**over) -> DiversifierEvidence:
    base = {"total_return_pct": 30.0, "max_drawdown_pct": 9.0, "book_daily_sharpe": 0.08}
    withc = {"total_return_pct": 40.0, "max_drawdown_pct": 8.5, "book_daily_sharpe": 0.11}
    kw = dict(
        sleeve="cand", gate_verdict="REJECT",
        gate_reasons=("REJECT significance: q=0.149",),
        coverage_frac=1.0, coverage_floor=0.95,
        blackout_r_gross=0.0, n_blackout_trades=0,
        lifetime_mean_r=0.05, n_trades_total=400, n_trades_priced=400,
        base_book_stats=base, with_candidate_book_stats=withc,
        with_candidate_rejections={},
    )
    kw.update(over)
    return DiversifierEvidence(**kw)


def _run(cand: dict, ev: DiversifierEvidence, **kw):
    return certify_guarded(
        _book(), cand, ev, standalone_edge_ok=True, regime_clean=True,
        sealed_start="2021-06-01", n_boot=400, **kw)


# ---------------------------------------------------------------------------------------
def test_a_clean_candidate_can_still_certify():
    """The positive control. A guard layer that refuses everything is as useless as none."""
    # a genuinely additive, low-correlation candidate on the book's own days
    cand = {d: (0.006 if i % 3 else -0.004)
            for i, d in enumerate(sorted(_book()))}
    got = _run(cand, _good_evidence())
    assert got.failed_guards == [], got.guards
    assert got.verdict in ("CERTIFIED_DIVERSIFIER", "NOT_CERTIFIED"), got.verdict
    assert got.verdict != "REFUSED_BY_GUARD"


def test_a_sleeve_the_gate_could_not_evaluate_is_refused():
    """Attack 1: `idxrev` at 6.3% cost coverage. The gate said NOT_EVALUABLE; this door said CERTIFIED."""
    cand = _series(300, 0.05, 0.02)
    got = _run(cand, _good_evidence(gate_verdict="NOT_EVALUABLE",
                                    gate_reasons=("cost_coverage_below_floor: ...",)))
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "gate_verdict" in got.failed_guards


def test_hidden_unpriceable_trades_are_refused_on_coverage():
    """Attack 1's mechanism: 4,638 of 7,148 trades unpriceable, -6,515.6 R, invisible."""
    cand = _series(300, 0.05, 0.02)
    got = _run(cand, _good_evidence(coverage_frac=0.0627, n_trades_total=7148,
                                    n_trades_priced=310, lifetime_mean_r=-0.91))
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "cost_coverage" in got.failed_guards
    assert "lifetime_expectancy" in got.failed_guards


def test_the_blackout_amount_is_a_guard_not_a_footnote():
    """Attack 2: 9,000 blackout trades carrying -8,820 R, at 100% cost coverage.

    `gate.py` already PUBLISHES `lifetime.blackout_removed.sum_r_gross` and no gate consumes
    it — W's "a count is not an amount" fix stopped one step short. This consumes it.
    """
    cand = _series(300, 0.05, 0.02)
    got = _run(cand, _good_evidence(blackout_r_gross=-8820.0, n_blackout_trades=9000,
                                    coverage_frac=1.0))
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "blackout_amount" in got.failed_guards


def test_a_near_constant_candidate_is_refused_before_it_is_levered():
    """Attack 3: `combine_vol_matched` applied 10,876,819x while reporting `weight: 0.5`."""
    days = sorted(_book())
    cand = {d: 0.05 + (1e-9 if i % 2 else -1e-9) for i, d in enumerate(days)}
    scale = applied_vol_match_scale([_book()[d] for d in days],
                                    [cand[d] for d in days], 0.5)
    assert scale > 1e6, f"the fixture must actually explode the scale; got {scale}"
    got = _run(cand, _good_evidence())
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "vol_match_scale" in got.failed_guards
    assert got.guards["vol_match_scale"]["applied_scale"] > MAX_APPLIED_SCALE
    # ...and the applied multiple is PUBLISHED, which the raw module never did
    assert got.guards["vol_match_scale"]["requested_weight"] == 0.5


def test_a_thin_overlap_cannot_carry_a_correlation_ceiling():
    """Attack 5: 7 overlapping days, corr +0.14, CI [-0.159, +0.525] — and CERTIFIED."""
    days = sorted(_book())
    cand = {d: 0.05 for d in days[:7]}
    got = _run(cand, _good_evidence())
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "correlation_sample" in got.failed_guards
    assert got.guards["correlation_sample"]["n_overlap"] < MIN_CORR_OVERLAP


def test_a_candidate_that_displaces_a_better_sleeve_is_refused_on_RETURN():
    """Attack 4: cannibalised 100% of `metals_core`, halved return and Sharpe, PASSED.

    `no_risk_regression` reads drawdown only, and reducing exposure reduces drawdown.
    """
    cand = {d: (0.006 if i % 3 else -0.004) for i, d in enumerate(sorted(_book()))}
    got = _run(cand, _good_evidence(
        base_book_stats={"total_return_pct": 34.94, "max_drawdown_pct": 9.660,
                         "book_daily_sharpe": 0.08072},
        with_candidate_book_stats={"total_return_pct": 17.73, "max_drawdown_pct": 7.683,
                                   "book_daily_sharpe": 0.04122},
        with_candidate_rejections={"same_broker_symbol_open_position_lifecycle_guard": 310}))
    assert got.verdict == "REFUSED_BY_GUARD"
    assert "book_return" in got.failed_guards
    assert got.guards["book_return"]["n_placements_displaced"] == 310
    # the drawdown check the raw module runs would have PASSED it
    assert got.guards["book_return"]["max_drawdown_delta_pp"] < 0
    # ...and the two Sharpe estimates disagree in sign, which is its own refusal
    assert "prediction_agrees_with_the_measured_book" in got.failed_guards


def test_the_guards_never_relax_the_raw_certification():
    """The second door must be a second question, never a lower bar.

    Property, not an example: for any input, a guarded verdict is CERTIFIED only if the raw
    module also said CERTIFIED.
    """
    for mean in (-0.02, -0.001, 0.0, 0.001, 0.02):
        cand = _series(600, mean, 0.02)
        got = _run(cand, _good_evidence())
        if got.verdict == "CERTIFIED_DIVERSIFIER":
            assert got.raw["verdict"] == "CERTIFIED_DIVERSIFIER", (
                f"guarded said CERTIFIED where the raw module did not, at mean {mean}")


def test_every_guard_carries_the_measurement_that_motivated_it():
    """A guard with no stated reason is a magic constant waiting to be relaxed."""
    got = _run(_series(600, 0.005, 0.02), _good_evidence())
    for name, g in got.guards.items():
        assert "why" in g and len(g["why"]) > 40, f"{name} has no readable justification"
        assert "pass" in g


def test_evidence_has_no_defaults_for_anything_load_bearing():
    """A default here is a silent assumption about a sleeve nobody measured."""
    with pytest.raises(TypeError):
        DiversifierEvidence(sleeve="x", gate_verdict="ADMIT", gate_reasons=())
