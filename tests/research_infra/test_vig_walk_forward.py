"""Known-answer tests for the purged/embargoed walk-forward degradation module.

Module under test:
    src/research_infra/validation_integrity/walk_forward_oos.py

Why these are KNOWN-ANSWER tests (not approximate smoke tests)
--------------------------------------------------------------
1. ``sharpe`` / ``compute_stat`` are checked against a hand-computed value
   (xs = 1..5 -> mean 3, sample-std sqrt(2.5), Sharpe 3/sqrt(2.5)).

2. STATIONARY edge: a constant positive mean across all time. By construction
   in-sample and out-of-sample Sharpe must agree closely, so:
       mean_oos_sharpe > 0
       abs(aggregate_degradation_pct) < ~25  (small; OOS may even beat IS a bit)
       oos_positive_fold_frac == 1.0
   This is robust across seeds (verified seeds 0..5).

3. IN-SAMPLE-ONLY edge: positive edge only in the first 60% of the series; the
   edge then DECAYS to a dead, no-edge regime (zero-mean noise net of a small
   adverse cost drift -- the realistic overfit failure mode). The expanding IS
   set, anchored on the strong early data, keeps a high IS Sharpe while the late
   OOS folds land in the dead regime and go non-positive, so:
       aggregate_degradation_pct  large (robustly ~55-70%)
       oos_positive_fold_frac     low  (robustly 0.5; half the OOS folds dead)
       mean_oos_sharpe << mean_is_sharpe; late folds' OOS Sharpe < 0
   Robust across seeds (verified seeds 100..105).

The module is pure-stdlib, so this test is too: it runs under pytest if present
AND as a plain script via ``/opt/homebrew/bin/python3 <thisfile>`` (no pytest
dependency). The optional final section runs the analyzer on the REAL combined
book series and prints the four headline metrics.
"""

from __future__ import annotations

import datetime
import math
import os
import random
import sys

# Allow running as a bare script (add repo root to path) as well as via pytest.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src.research_infra.validation_integrity.walk_forward_oos import (  # noqa: E402
    compute_stat,
    purged_embargoed_walkforward,
    rolling_walk_forward,
    sharpe,
)

REQUIRED_TOP_KEYS = {
    "folds",
    "mean_is_sharpe",
    "mean_oos_sharpe",
    "aggregate_degradation_pct",
    "oos_positive_fold_frac",
}
REQUIRED_FOLD_KEYS = {
    "fold",
    "is_start",
    "is_end",
    "oos_start",
    "oos_end",
    "is_sharpe",
    "oos_sharpe",
    "degradation",
}


# ---------------------------------------------------------------------------
# Synthetic data generators (deterministic, pure stdlib)
# ---------------------------------------------------------------------------
def _mkdates(T: int):
    d0 = datetime.date(2015, 1, 1)
    return [d0 + datetime.timedelta(days=i) for i in range(T)]


def _stationary_series(T: int = 2000, mu: float = 0.6, sd: float = 1.0, seed: int = 0):
    rng = random.Random(seed)
    dates = _mkdates(T)
    return [(dates[i], mu + rng.gauss(0.0, sd)) for i in range(T)]


def _in_sample_only_series(
    T: int = 2000,
    mu_pre: float = 0.6,
    mu_post: float = -0.2,
    sd: float = 1.0,
    pre_frac: float = 0.6,
    seed: int = 100,
):
    """Positive edge in the first ``pre_frac`` of the series; the edge then dies
    to a no-edge regime (small adverse drift ``mu_post`` dominated by noise)."""
    rng = random.Random(seed)
    dates = _mkdates(T)
    cut = int(pre_frac * T)
    out = []
    for i in range(T):
        mu = mu_pre if i < cut else mu_post
        out.append((dates[i], mu + rng.gauss(0.0, sd)))
    return out


# ---------------------------------------------------------------------------
# Unit: statistic primitives (hand-verified)
# ---------------------------------------------------------------------------
def test_sharpe_known_answer():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    # mean = 3; sample variance = sum((x-3)^2)/4 = (4+1+0+1+4)/4 = 2.5
    # sample std = sqrt(2.5) = 1.5811388...; sharpe = 3 / 1.5811388 = 1.8973665961
    expected = 3.0 / math.sqrt(2.5)
    got = sharpe(xs)
    assert abs(got - expected) < 1e-12, (got, expected)
    # annualization is a pure multiplier
    assert abs(sharpe(xs, ann_factor=math.sqrt(252)) - expected * math.sqrt(252)) < 1e-9
    # ddof=0 (population) std = sqrt(2.0)
    assert abs(sharpe(xs, ddof=0) - 3.0 / math.sqrt(2.0)) < 1e-12


def test_compute_stat_dispatch():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(compute_stat(xs, stat="mean") - 3.0) < 1e-12
    assert abs(compute_stat(xs, stat="sharpe") - 3.0 / math.sqrt(2.5)) < 1e-12
    # constant series -> undefined Sharpe (std 0) -> NaN, no crash
    assert math.isnan(sharpe([2.0, 2.0, 2.0, 2.0]))
    # fewer than 2 points -> NaN
    assert math.isnan(sharpe([1.0]))
    # sortino of an all-positive window has no downside -> NaN
    assert math.isnan(compute_stat([0.1, 0.2, 0.3], stat="sortino"))
    try:
        compute_stat(xs, stat="bogus")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unknown stat must raise ValueError")


# ---------------------------------------------------------------------------
# Structure / contract
# ---------------------------------------------------------------------------
def _assert_shape(res):
    assert REQUIRED_TOP_KEYS.issubset(res.keys()), res.keys()
    assert isinstance(res["folds"], list)
    for f in res["folds"]:
        assert REQUIRED_FOLD_KEYS.issubset(f.keys()), f.keys()
        # chronology within a fold: is window ends before oos window starts
        assert f["is_end"] < f["oos_start"], (f["is_end"], f["oos_start"])
        assert f["is_start"] <= f["is_end"]
        assert f["oos_start"] <= f["oos_end"]


def test_shape_and_keys():
    ds = _stationary_series(T=1500, seed=1)
    _assert_shape(purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.01))
    _assert_shape(rolling_walk_forward(ds, train_frac=0.5, step_frac=0.1))


def test_embargo_actually_purges_rows():
    """The embargo must remove exactly ``round(embargo_frac*T)`` IS rows that sit
    adjacent to each OOS fold (leakage defense)."""
    T = 1000
    ds = _stationary_series(T=T, seed=2)
    no_emb = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.0)
    emb = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.05)
    embargo_rows = round(0.05 * T)  # 50
    assert emb["embargo_rows"] == embargo_rows
    # same number of evaluated folds, but each IS window is shorter by exactly embargo
    assert no_emb["n_folds_evaluated"] == emb["n_folds_evaluated"]
    for f0, f1 in zip(no_emb["folds"], emb["folds"]):
        assert f1["n_is"] == f0["n_is"] - embargo_rows, (f0["n_is"], f1["n_is"])
        # the purged gap really sits between IS end and OOS start
        gap_days = (f1["oos_start"] - f1["is_end"]).days
        assert gap_days == embargo_rows + 1, gap_days  # +1: end->start is one extra step


def test_first_fold_skipped_under_expanding():
    ds = _stationary_series(T=1500, seed=3)
    res = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.01)
    # 5 OOS folds requested, first has no past -> 4 evaluated
    assert res["n_folds_evaluated"] == 4
    assert all(f["fold"] >= 1 for f in res["folds"])


# ---------------------------------------------------------------------------
# KNOWN ANSWER (1): stationary edge -> survives OOS
# ---------------------------------------------------------------------------
def test_stationary_edge_known_answer():
    ds = _stationary_series(T=2000, mu=0.6, sd=1.0, seed=0)
    res = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.01, stat="sharpe")

    assert res["mean_is_sharpe"] > 0.4, res["mean_is_sharpe"]
    assert res["mean_oos_sharpe"] > 0.4, res["mean_oos_sharpe"]
    # small degradation (may be slightly negative -> OOS beat IS); magnitude small
    assert abs(res["aggregate_degradation_pct"]) < 25.0, res["aggregate_degradation_pct"]
    assert res["oos_positive_fold_frac"] == 1.0, res["oos_positive_fold_frac"]
    return res


# ---------------------------------------------------------------------------
# KNOWN ANSWER (2): in-sample-only edge -> large degradation, low OOS frac
# ---------------------------------------------------------------------------
def test_in_sample_only_edge_known_answer():
    ds = _in_sample_only_series(T=2000, mu_pre=0.6, mu_post=-0.2, sd=1.0, seed=100)
    res = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.01, stat="sharpe")

    assert res["mean_is_sharpe"] > 0.3, res["mean_is_sharpe"]
    assert res["mean_oos_sharpe"] < res["mean_is_sharpe"], (
        res["mean_oos_sharpe"], res["mean_is_sharpe"])
    assert res["aggregate_degradation_pct"] > 30.0, res["aggregate_degradation_pct"]
    # low OOS-positive fraction: the late (decayed-regime) folds go non-positive
    assert res["oos_positive_fold_frac"] <= 0.5, res["oos_positive_fold_frac"]
    # strictly worse than the stationary case (which is 1.0)
    stationary = test_stationary_edge_known_answer()
    assert res["oos_positive_fold_frac"] < stationary["oos_positive_fold_frac"]
    # at least one OOS fold is outright negative (edge died)
    assert min(f["oos_sharpe"] for f in res["folds"]) < 0.0
    # and per-fold degradation in the dead region is near-total (>0.5)
    big_deg = [f for f in res["folds"] if f["degradation"] > 0.5]
    assert len(big_deg) >= 2, [round(f["degradation"], 3) for f in res["folds"]]


# ---------------------------------------------------------------------------
# Rolling variant: same shape; stationary survives, in-sample-only degrades
# ---------------------------------------------------------------------------
def test_rolling_variant_known_answer():
    ds_stat = _stationary_series(T=2000, mu=0.6, sd=1.0, seed=0)
    r = rolling_walk_forward(ds_stat, train_frac=0.5, step_frac=0.1, stat="sharpe")
    _assert_shape(r)
    assert r["n_folds_evaluated"] >= 3
    assert r["mean_oos_sharpe"] > 0.4
    assert r["oos_positive_fold_frac"] == 1.0
    assert abs(r["aggregate_degradation_pct"]) < 25.0

    ds_iso = _in_sample_only_series(T=2000, mu_pre=0.6, mu_post=-0.2, sd=1.0, seed=100)
    r2 = rolling_walk_forward(ds_iso, train_frac=0.5, step_frac=0.1, stat="sharpe")
    _assert_shape(r2)
    # rolling windows that step into the dead regime degrade vs the IS window
    assert r2["aggregate_degradation_pct"] > r["aggregate_degradation_pct"]
    assert r2["oos_positive_fold_frac"] < 1.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_edge_cases():
    # empty
    e = purged_embargoed_walkforward([], n_folds=5)
    assert e["folds"] == [] and e["n_folds_evaluated"] == 0
    assert math.isnan(e["mean_oos_sharpe"]) and math.isnan(e["oos_positive_fold_frac"])

    # series shorter than n_folds
    short = [(datetime.date(2020, 1, 1) + datetime.timedelta(days=i), 0.1) for i in range(3)]
    s = purged_embargoed_walkforward(short, n_folds=5)
    assert s["folds"] == []

    # constant series -> Sharpe undefined (std 0) -> NaN stats, no crash
    const = [(datetime.date(2020, 1, 1) + datetime.timedelta(days=i), 0.5) for i in range(500)]
    c = purged_embargoed_walkforward(const, n_folds=5, embargo_frac=0.01)
    assert all(math.isnan(f["is_sharpe"]) for f in c["folds"])
    assert math.isnan(c["oos_positive_fold_frac"])

    # unsorted input is sorted internally (chronology holds in output)
    unsorted = list(reversed(_stationary_series(T=600, seed=4)))
    u = purged_embargoed_walkforward(unsorted, n_folds=4, embargo_frac=0.0)
    for f in u["folds"]:
        assert f["is_end"] < f["oos_start"]

    # invalid params raise
    for bad in (0, 1):
        try:
            purged_embargoed_walkforward(_stationary_series(T=100), n_folds=bad)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError("n_folds < 2 must raise")
    for kw in ({"train_frac": 0.0}, {"train_frac": 1.0}, {"step_frac": 0.0}):
        try:
            rolling_walk_forward(_stationary_series(T=100), **kw)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError("invalid frac must raise")


# ---------------------------------------------------------------------------
# Optional: REAL combined-book run (best-effort; prints headline metrics)
# ---------------------------------------------------------------------------
def run_real_book(verbose: bool = True):
    book_dir = os.path.join(
        _REPO_ROOT,
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10",
    )
    if not os.path.isdir(book_dir):
        if verbose:
            print("[real-book] dir not found; skipped")
        return None
    saved = sys.path[:]
    try:
        sys.path.insert(0, book_dir)
        import INTEG_W7_final_book as W7  # type: ignore
        import KB7_growth_kelly_sizing as K  # type: ignore

        all_days, sleeves, M_base, M_tick, sd_book, ero = W7.build_final_matrix()
        nact = [K.conviction_count(r) for r in M_tick]
        M_final = W7.apply_kelly_matrix(M_tick, nact)
        comb = [sum(r) for r in M_final]
        ds = list(zip(all_days, comb))

        res = purged_embargoed_walkforward(ds, n_folds=5, embargo_frac=0.01, stat="sharpe")
        roll = rolling_walk_forward(ds, train_frac=0.6, step_frac=0.1, stat="sharpe")
        if verbose:
            print(f"[real-book] n={len(comb)} days {all_days[0]}..{all_days[-1]}")
            print(f"[real-book] EXPANDING  mean_is_sharpe={res['mean_is_sharpe']:.5f} "
                  f"mean_oos_sharpe={res['mean_oos_sharpe']:.5f} "
                  f"aggregate_degradation_pct={res['aggregate_degradation_pct']:.4f} "
                  f"oos_positive_fold_frac={res['oos_positive_fold_frac']}")
            for f in res["folds"]:
                print(f"           fold {f['fold']} oos {f['oos_start']}..{f['oos_end']} "
                      f"is_sharpe={f['is_sharpe']:.4f} oos_sharpe={f['oos_sharpe']:.4f} "
                      f"deg={f['degradation']:.4f}")
            print(f"[real-book] ROLLING    mean_is_sharpe={roll['mean_is_sharpe']:.5f} "
                  f"mean_oos_sharpe={roll['mean_oos_sharpe']:.5f} "
                  f"aggregate_degradation_pct={roll['aggregate_degradation_pct']:.4f} "
                  f"oos_positive_fold_frac={roll['oos_positive_fold_frac']}")
        return res, roll
    except Exception as exc:  # pragma: no cover - integration best-effort
        if verbose:
            print(f"[real-book] skipped ({type(exc).__name__}: {exc})")
        return None
    finally:
        sys.path[:] = saved


# ---------------------------------------------------------------------------
# Script runner (works without pytest)
# ---------------------------------------------------------------------------
def _main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {t.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"ERROR {t.__name__}: {type(exc).__name__}: {exc}")
    print("-" * 60)
    print(f"{len(tests) - failures}/{len(tests)} passed")
    print("-" * 60)
    run_real_book(verbose=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_main())
