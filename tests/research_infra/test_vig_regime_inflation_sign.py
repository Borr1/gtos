"""The sign defect in `regime_inflation.py`, and the property that closes it (B451).

`fwd_all_mean_ratio = mean_in_window / mean_all` is a MULTIPLE only when `mean_all > 0`.
Every threshold in the module was written as `ratio >= 1.5`, a positive test. Once the
full-history mean went negative the ratio went negative and the flag became structurally
unreachable — so the detector was defeated by making the concealed loss BIGGER, which is
the exact inverse of what a contamination detector is for.

These are behavioural tests, not source greps: each one constructs a series, calls the
production function, and asserts on the returned verdict. The load-bearing one is
`test_flag_is_monotone_in_the_concealed_loss` — it is the property, not an example, and it
fails on the pre-B451 code at every point on the sweep.

Deterministic alternating construction (same device as `test_vig_regime_inflation.py`) so
every sample mean is exact and no answer depends on a seed.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from research_infra.validation_integrity.regime_inflation import (  # noqa: E402
    regime_inflation_diagnostic,
)


def _year_block(year: int, mean: float, c: float, n: int = 120):
    assert n % 2 == 0
    base = _dt.date(year, 1, 1)
    return [(base + _dt.timedelta(days=i), mean + c if i % 2 == 0 else mean - c)
            for i in range(n)]


def _series(year_means, c=0.2, n=120):
    out = []
    for y, m in sorted(year_means.items()):
        out.extend(_year_block(y, m, c, n))
    return out


def test_negative_history_positive_window_is_flagged():
    """The attack, in its simplest form.

    Four losing years and one winning scored window. The old code computed
    ratio = +0.05 / -0.2375 = -0.2105, applied `>= 1.5`, and returned CLEAN.
    """
    series = _series({2019: -0.30, 2020: -0.30, 2021: -0.30, 2022: -0.30, 2023: +0.05})
    out = regime_inflation_diagnostic(series, _dt.date(2023, 1, 1), n_trials=128)

    assert out["mean_all"] < 0, "fixture must have a negative full-history mean"
    assert out["mean_in_window"] > 0, "fixture must have a positive scored window"
    assert out["fwd_all_mean_ratio"] < 0, "the ratio really is negative — that is the trap"

    assert out["contamination_flag"] is True
    assert out["sign_flip_contamination"] is True
    assert out["ratio_is_a_multiple"] is False
    assert out["inflation_basis"] == "sign_flip_window_positive_history_nonpositive"
    assert "CONTAMINATED" in out["verdict"]
    # ...and the haircut must not say "deploy the window magnitude in full".
    assert out["recommended_magnitude_haircut"] < 0.5


def test_flag_is_monotone_in_the_concealed_loss():
    """The property, not an example.

    Deepen the hidden history loss and the detector must not get QUIETER. On the pre-B451
    code the ratio walks from -0.07 toward 0 as the loss deepens, and the flag is False at
    every step — the concealment strictly improved with its own size.
    """
    verdicts = []
    for hidden in (-0.10, -0.30, -1.00, -3.00, -10.00):
        series = _series({2019: hidden, 2020: hidden, 2021: hidden, 2022: hidden,
                          2023: +0.05})
        out = regime_inflation_diagnostic(series, _dt.date(2023, 1, 1), n_trials=128)
        verdicts.append((hidden, out["contamination_flag"], out["fwd_all_mean_ratio"],
                         out["recommended_magnitude_haircut"]))

    assert all(flag for _h, flag, _r, _hc in verdicts), (
        f"flag must fire at every depth; got {verdicts}")
    # The ratio itself still walks toward zero — the point is that nothing keys off it now.
    ratios = [r for _h, _f, r, _hc in verdicts]
    assert all(r < 0 for r in ratios)
    assert ratios == sorted(ratios), (
        "sanity: the ratio rises monotonically toward 0 as the hidden loss deepens, so a "
        f"`>= 1.5` test moves FURTHER from firing the worse the sleeve gets: {ratios}")
    # And the haircut never rewards a deeper concealment.
    haircuts = [hc for _h, _f, _r, hc in verdicts]
    assert max(haircuts) < 0.5, haircuts


def test_positive_history_path_is_unchanged():
    """The regression guard: where the module was already right, it must be identical.

    3x window over a positive history — the case `test_vig_regime_inflation.py` pins.
    """
    series = _series({2019: 0.10, 2020: 0.10, 2021: 0.10, 2022: 0.10, 2023: 0.50})
    out = regime_inflation_diagnostic(series, _dt.date(2023, 1, 1), n_trials=128)
    assert out["ratio_is_a_multiple"] is True
    assert out["inflation_basis"] == "ratio_of_positive_means"
    assert out["sign_flip_contamination"] is False
    assert out["contamination_flag"] is True
    assert abs(out["fwd_all_mean_ratio"] - (0.50 / 0.18)) < 1e-4


def test_nonpositive_window_reports_clean_vacuously_and_says_so():
    """A losing window is not contamination, and the verdict must not imply a clean sleeve.

    This is the branch a reader is most likely to misread: `contamination_flag False` here
    means "no OPTIMISTIC inflation to detect", not "this sleeve is fine".
    """
    series = _series({2019: -0.05, 2020: -0.05, 2021: -0.05, 2022: -0.05, 2023: -0.20})
    out = regime_inflation_diagnostic(series, _dt.date(2023, 1, 1), n_trials=128)
    assert out["mean_all"] <= 0 and out["mean_in_window"] <= 0
    assert out["contamination_flag"] is False
    assert out["sign_flip_contamination"] is False
    assert out["inflation_basis"] == "window_nonpositive_no_optimistic_inflation"
    assert "vacuously" in out["verdict"]


def test_a_losing_window_over_a_winning_history_is_labelled_honestly():
    """The fourth sign regime, closed by Session AE (B873) while verifying FOURTH_REVIEW section 4.3.

    `mean_all > 0` with `mean_win <= 0`: the old branch order labelled this
    `ratio_of_positive_means` — true of the denominator only — and its verdict read "CLEAN:
    selection window is representative" of a window 145 % below the history it is measured against.
    No verdict moves (there is no optimistic magnitude to haircut); a published label stops lying.
    """
    series = _series({2019: 0.30, 2020: 0.30, 2021: 0.30, 2022: 0.30, 2023: -0.10})
    out = regime_inflation_diagnostic(series, _dt.date(2023, 1, 1), n_trials=128)
    assert out["mean_all"] > 0 and out["mean_in_window"] < 0
    assert out["inflation_basis"] == "window_nonpositive_no_optimistic_inflation"
    assert out["contamination_flag"] is False           # nothing to inflate
    assert out["recommended_magnitude_haircut"] == 1.0  # ...and nothing to haircut
    assert "vacuously" in out["verdict"]
    assert "UNDERPERFORMS" in out["verdict"]
    assert "selection window is representative" not in out["verdict"]


def test_the_label_change_moved_no_flag_and_no_haircut():
    """The regression guard on the amendment itself: only the LABEL and the prose may have moved.

    Swept over the whole sign plane, the flag and the haircut must be exactly what the two
    sign predicates imply — which is what they were before the branch order changed.
    """
    for hist in (-0.30, -0.05, 0.0, 0.05, 0.30):
        for win in (-0.20, -0.01, 0.0, 0.01, 0.50):
            out = regime_inflation_diagnostic(
                _series({2019: hist, 2020: hist, 2021: hist, 2022: hist, 2023: win}),
                _dt.date(2023, 1, 1), n_trials=128)
            ma, mw = out["mean_all"], out["mean_in_window"]
            sign_flip = (mw > 0) and (ma <= 0)
            assert out["sign_flip_contamination"] is sign_flip, (hist, win)
            assert out["ratio_is_a_multiple"] is (ma > 0), (hist, win)
            if sign_flip:
                assert out["contamination_flag"] is True, (hist, win)
                assert out["recommended_magnitude_haircut"] < 0.5, (hist, win)
            if mw <= 0:
                assert out["inflation_basis"] == "window_nonpositive_no_optimistic_inflation"


def test_gate_call_site_guard_now_agrees_with_the_module():
    """`walkforward/gate.py` guarded this defect locally. The guard is now redundant.

    Redundant is the right state — it cross-checks — but it must not DISAGREE, because a
    guard that fires where the module does not is a second source of truth.
    """
    from research_infra.walkforward.gate import _regime_inflation  # noqa: PLC0415
    from research_infra.walkforward.spec import GateSpec  # noqa: PLC0415

    spec = GateSpec(spec_id="t", authored_utc="2026-07-29T00:00:00+00:00")
    series = _series({2019: -0.30, 2020: -0.30, 2021: -0.30, 2022: -0.30, 2023: +0.05})
    got = _regime_inflation(dict(series), _dt.date(2023, 1, 1), spec)
    assert got["available"] is True
    assert got["contamination_flag"] is True
    # the module now flags it upstream, so the local override is no longer what carries it
    assert got["contamination_flag_upstream"] is True


if __name__ == "__main__":  # pragma: no cover
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)


# ------------------------------------------------- Session AU (B1560): the CLEAN verdict's prose

def _clean_series(n_days=1400, mu=0.02, sd=1.0, seed=7):
    """A representative window with a REALISTIC daily Sharpe: positive drift buried in noise, so
    `fwd_all_mean_ratio` ~ 1 (the CLEAN branch) and `sr_window` is ~0.04 rather than the ~10 a
    noiseless ramp would give. The magnitude of `sr_window` is the whole point — the
    selection-surface penalty is `1 - E[max-of-N Sharpe]/sr_window`, so a fixture with an
    unrealistically clean equity curve cannot reach the floor no matter what variance is injected.
    Seeded `random.Random`, so the verdict is reproducible without numpy."""
    import datetime as dt
    import random
    rnd = random.Random(seed)
    d0 = dt.date(2020, 1, 1)
    return [(d0 + dt.timedelta(days=i), mu + rnd.gauss(0.0, sd)) for i in range(n_days)]


def test_a_clean_window_whose_haircut_is_the_floor_no_longer_calls_it_one_point_oh():
    """The defect: the CLEAN branch printed a HARDCODED `(~1.0)` beside an INTERPOLATED value, so an
    arm at the 0.05 floor published `recommended magnitude haircut x0.050 (~1.0)` — a 20x
    misstatement inside the sentence that quotes the number.

    It was not hypothetical. It landed on the estate's standing admission: `mx_btcusd @ target_5R`
    on RECORDED/mid reads `haircut 0.05` with `selection_surface_penalty 0.0`, because the expected
    max-of-128 Sharpe (0.551) exceeds the arm's own window Sharpe (0.323). Session AU was the first
    receipt in the programme to publish this field beside a headline (AR handoff item 2) and found it
    misreported on the first read.

    Driven by forcing the selection-surface penalty to zero through `sr_variance`, which is the
    documented injection point, rather than by reaching for a fixture that happens to collapse it.
    """
    ds = _clean_series()
    out = regime_inflation_diagnostic(ds, ds[len(ds) // 3][0], 128, sr_variance=0.05)
    assert out["contamination_flag"] is False and out["verdict"].startswith("CLEAN:")
    assert out["selection_surface_penalty"] == 0.0
    assert out["recommended_magnitude_haircut"] == 0.05
    assert out["haircut_at_floor"] is True
    assert out["haircut_binding_term"] == "selection_surface"
    assert "(~1.0)" not in out["verdict"], "the floor must not be described as no haircut at all"
    assert "FLOOR" in out["verdict"] and "not a measurement" in out["verdict"]
    #: and it must not invite the opposite error either
    assert "shrink 20x" in out["verdict"]


def test_a_genuinely_unhaircut_clean_window_still_says_so():
    """The fix must not turn every CLEAN verdict into a warning. A window that really is
    representative, with a real SR variance small enough to leave the penalty at 1.0, keeps `(~1.0)`."""
    ds = _clean_series()
    out = regime_inflation_diagnostic(ds, ds[len(ds) // 3][0], 128, sr_variance=0.0)
    assert out["verdict"].startswith("CLEAN:") and "(~1.0)" in out["verdict"]
    assert out["haircut_at_floor"] is False
    assert out["haircut_binding_term"] in ("none", "regime_basis")
    assert out["recommended_magnitude_haircut"] >= 0.95


def test_the_selection_surface_resolution_is_published():
    """The penalty is computed from a cross-period SR variance. Estimated from two full years it is a
    2-point dispersion, which is the same class of caveat AO made binding for permutation p near its
    resolution floor. The VALUE is untouched — only its evaluability is stated."""
    ds = _clean_series(n_days=420)                      # ~1.2 years -> at most 1 full year
    out = regime_inflation_diagnostic(ds, ds[len(ds) // 3][0], 128)
    det = out["selection_surface_detail"]
    assert det["sr_variance_source"] == "estimated_from_per_year_dispersion"
    assert out["selection_surface_evaluable"] is False
    #: an injected variance is a measurement the caller vouches for, so it IS evaluable
    inj = regime_inflation_diagnostic(ds, ds[len(ds) // 3][0], 128, sr_variance=0.01)
    assert inj["selection_surface_evaluable"] is True
