"""Purged / embargoed walk-forward in-sample -> out-of-sample degradation.

North-Star Phase A2 validation-integrity gate. This is the leakage-aware
walk-forward analyzer: does an edge that looks good *in-sample* survive on
*strictly-future* data once you (a) only train on the past, and (b) purge an
embargo gap of rows between the train window and the test window so the
in-sample stat cannot peek at information adjacent to the test fold?

Two public entry points, both returning the SAME dict shape:

* ``purged_embargoed_walkforward`` -- expanding (anchored) walk-forward. The
  in-sample set is every row strictly before the OOS fold, minus an embargo
  gap of ``round(embargo_frac * T)`` rows immediately preceding the fold.

* ``rolling_walk_forward`` -- rolling (fixed-width) walk-forward. The
  in-sample set is a fixed-size trailing window that slides forward by
  ``step_frac`` of the series each step.

Method references
-----------------
* Combinatorial-purged / embargoed cross-validation: Lopez de Prado,
  *Advances in Financial Machine Learning* (2018), ch. 7 (purging & embargo
  to defeat leakage from overlapping / serially-correlated samples).
* Walk-forward analysis: Pardo, *The Evaluation and Optimization of Trading
  Strategies* (2008).
* Sharpe ratio: Sharpe (1994), per-period ``mean / std``; annualize by a
  ``sqrt(periods_per_year)`` factor via ``ann_factor`` if desired.

Design rules (honesty-by-construction)
--------------------------------------
* Pure standard library. No numpy / scipy / pandas hard dependency. (A normal
  CDF helper is provided via ``math.erf`` only, used for an OPTIONAL diagnostic
  p-value; the core degradation math needs no special functions.)
* The first chronological fold can never be evaluated under an expanding
  scheme (there is no past before it); such folds, and any fold whose
  in-sample or out-of-sample window is too small to form the statistic, are
  skipped. ``oos_positive_fold_frac`` and the means are computed over the
  EVALUATED folds only.
* ``std`` uses the sample estimator (``ddof=1``) by default, the standard
  choice for a Sharpe estimate. Pass ``ddof=0`` for the population estimator.
* Degradation per fold ``= (is_stat - oos_stat) / abs(is_stat)``. Positive
  means OOS is worse than IS (the usual case); negative means OOS improved
  (e.g. an inflated future holdout). NaN when ``is_stat`` is ~0 or undefined.
* ``aggregate_degradation_pct = (mean_is - mean_oos) / abs(mean_is) * 100``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

__all__ = [
    "purged_embargoed_walkforward",
    "rolling_walk_forward",
    "sharpe",
    "compute_stat",
]

_EPS = 1e-12

DatedSeries = Sequence[Tuple[Any, float]]


# ---------------------------------------------------------------------------
# Numerically careful primitives (pure stdlib)
# ---------------------------------------------------------------------------
def _mean(xs: Sequence[float]) -> float:
    n = len(xs)
    if n == 0:
        return float("nan")
    return math.fsum(xs) / n


def _std(xs: Sequence[float], ddof: int = 1) -> float:
    n = len(xs)
    if n - ddof <= 0:
        return float("nan")
    m = _mean(xs)
    # fsum of squared deviations -> reduced floating error vs naive sum
    ss = math.fsum((float(x) - m) * (float(x) - m) for x in xs)
    var = ss / (n - ddof)
    if var < 0.0:  # only possible from rounding at ~0 variance
        var = 0.0
    return math.sqrt(var)


def sharpe(xs: Sequence[float], ann_factor: float = 1.0, ddof: int = 1) -> float:
    """Per-period Sharpe = mean/std, scaled by ``ann_factor``.

    Returns NaN when fewer than 2 points or std is ~0 (a degenerate/constant
    window has no defined Sharpe).
    """
    if len(xs) < 2:
        return float("nan")
    s = _std(xs, ddof=ddof)
    if not math.isfinite(s) or s <= _EPS:
        return float("nan")
    return (_mean(xs) / s) * ann_factor


def _sortino(xs: Sequence[float], ann_factor: float = 1.0, ddof: int = 1) -> float:
    if len(xs) < 2:
        return float("nan")
    m = _mean(xs)
    downside = [float(x) for x in xs if float(x) < 0.0]
    if len(downside) - ddof <= 0:
        return float("nan")
    dd = math.sqrt(math.fsum(x * x for x in downside) / (len(downside) - ddof))
    if not math.isfinite(dd) or dd <= _EPS:
        return float("nan")
    return (m / dd) * ann_factor


def compute_stat(xs: Sequence[float], stat: str = "sharpe",
                 ann_factor: float = 1.0, ddof: int = 1) -> float:
    """Dispatch a window statistic. Supported: 'sharpe', 'mean', 'sortino'."""
    if stat == "sharpe":
        return sharpe(xs, ann_factor=ann_factor, ddof=ddof)
    if stat == "mean":
        return _mean(xs) * ann_factor if len(xs) else float("nan")
    if stat == "sortino":
        return _sortino(xs, ann_factor=ann_factor, ddof=ddof)
    raise ValueError(f"unknown stat {stat!r}; supported: 'sharpe','mean','sortino'")


def _norm_cdf(z: float) -> float:
    """Standard-normal CDF via math.erf (no scipy). Provided for the optional
    diagnostic p-value only; not used by the core degradation math."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _prepare(dated_series: DatedSeries) -> Tuple[List[Any], List[float]]:
    if dated_series is None:
        raise ValueError("dated_series is None")
    items = list(dated_series)
    if not items:
        return [], []
    # Stable chronological sort by date key (index 0). Stable so ties keep order.
    items = sorted(items, key=lambda t: t[0])
    dates = [t[0] for t in items]
    rets = [float(t[1]) for t in items]
    return dates, rets


def _degradation(is_v: float, oos_v: float) -> float:
    if not (math.isfinite(is_v) and math.isfinite(oos_v)):
        return float("nan")
    if abs(is_v) <= _EPS:
        return float("nan")
    return (is_v - oos_v) / abs(is_v)


def _fold_record(fold_id: int, dates: List[Any],
                 is_lo: int, is_hi: int, oos_lo: int, oos_hi: int,
                 rets: List[float], stat: str, ann_factor: float, ddof: int,
                 embargo: int) -> Dict[str, Any]:
    is_rets = rets[is_lo:is_hi]
    oos_rets = rets[oos_lo:oos_hi]
    is_stat = compute_stat(is_rets, stat=stat, ann_factor=ann_factor, ddof=ddof)
    oos_stat = compute_stat(oos_rets, stat=stat, ann_factor=ann_factor, ddof=ddof)
    return {
        "fold": fold_id,
        "is_start": dates[is_lo],
        "is_end": dates[is_hi - 1],
        "oos_start": dates[oos_lo],
        "oos_end": dates[oos_hi - 1],
        "is_sharpe": is_stat,
        "oos_sharpe": oos_stat,
        "degradation": _degradation(is_stat, oos_stat),
        "n_is": len(is_rets),
        "n_oos": len(oos_rets),
        "embargo_rows": embargo,
    }


def _summarize(folds_out: List[Dict[str, Any]], stat: str,
               embargo: int, expanding: bool) -> Dict[str, Any]:
    base = {
        "folds": folds_out,
        "stat": stat,
        "expanding": expanding,
        "embargo_rows": embargo,
        "n_folds_evaluated": len(folds_out),
        "mean_is_sharpe": float("nan"),
        "mean_oos_sharpe": float("nan"),
        "aggregate_degradation_pct": float("nan"),
        "oos_positive_fold_frac": float("nan"),
    }
    if not folds_out:
        return base

    is_vals = [f["is_sharpe"] for f in folds_out if math.isfinite(f["is_sharpe"])]
    oos_vals = [f["oos_sharpe"] for f in folds_out if math.isfinite(f["oos_sharpe"])]

    mean_is = _mean(is_vals) if is_vals else float("nan")
    mean_oos = _mean(oos_vals) if oos_vals else float("nan")
    base["mean_is_sharpe"] = mean_is
    base["mean_oos_sharpe"] = mean_oos

    if math.isfinite(mean_is) and math.isfinite(mean_oos) and abs(mean_is) > _EPS:
        base["aggregate_degradation_pct"] = (mean_is - mean_oos) / abs(mean_is) * 100.0

    evaluable = [f for f in folds_out if math.isfinite(f["oos_sharpe"])]
    if evaluable:
        pos = sum(1 for f in evaluable if f["oos_sharpe"] > 0.0)
        base["oos_positive_fold_frac"] = pos / len(evaluable)
    return base


# ---------------------------------------------------------------------------
# Public: expanding (anchored) purged + embargoed walk-forward
# ---------------------------------------------------------------------------
def purged_embargoed_walkforward(
    dated_series: DatedSeries,
    n_folds: int = 5,
    embargo_frac: float = 0.01,
    expanding: bool = True,
    stat: str = "sharpe",
    *,
    ann_factor: float = 1.0,
    ddof: int = 1,
    min_is: int = 2,
    min_oos: int = 2,
) -> Dict[str, Any]:
    """Expanding-window purged/embargoed walk-forward IS->OOS degradation.

    Parameters
    ----------
    dated_series : list of (date, r)
        Returns keyed by a sortable date. Sorted chronologically internally.
    n_folds : int
        Number of contiguous chronological OOS folds the series is cut into.
        The first fold has no past and is skipped (used as initial training).
    embargo_frac : float
        Fraction of the FULL series length T purged between IS and OOS:
        ``embargo = round(embargo_frac * T)`` rows immediately before each OOS
        fold are dropped from the in-sample set.
    expanding : bool
        True  -> IS = all rows from index 0 up to (fold_start - embargo).
        False -> IS = the single fold-width window immediately before the
                 embargo gap (a one-block rolling train inside this function;
                 see ``rolling_walk_forward`` for the train_frac/step_frac API).
    stat : str
        'sharpe' (default), 'mean', or 'sortino'.

    Returns
    -------
    dict with keys: folds (list of per-fold dicts with fold, is_start, is_end,
    oos_start, oos_end, is_sharpe, oos_sharpe, degradation, ...), mean_is_sharpe,
    mean_oos_sharpe, aggregate_degradation_pct, oos_positive_fold_frac, plus
    diagnostics (stat, expanding, embargo_rows, n_folds_evaluated).
    """
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    dates, rets = _prepare(dated_series)
    T = len(rets)
    if T < n_folds:
        return _summarize([], stat, 0, expanding)

    embargo = int(round(embargo_frac * T))
    if embargo < 0:
        embargo = 0

    # n_folds contiguous OOS blocks covering the whole series.
    bounds = [int(round(i * T / n_folds)) for i in range(n_folds + 1)]

    folds_out: List[Dict[str, Any]] = []
    for k in range(n_folds):
        oos_lo, oos_hi = bounds[k], bounds[k + 1]
        if oos_hi - oos_lo < min_oos:
            continue
        is_hi = oos_lo - embargo  # purge the embargo rows just before the fold
        if expanding:
            is_lo = 0
        else:
            # non-expanding inside this function: one prior fold-width block
            is_lo = max(0, bounds[k - 1] if k >= 1 else 0)
        if is_hi - is_lo < min_is:
            continue
        folds_out.append(
            _fold_record(k, dates, is_lo, is_hi, oos_lo, oos_hi,
                         rets, stat, ann_factor, ddof, embargo)
        )

    return _summarize(folds_out, stat, embargo, expanding)


# ---------------------------------------------------------------------------
# Public: rolling (fixed-width) walk-forward
# ---------------------------------------------------------------------------
def rolling_walk_forward(
    dated_series: DatedSeries,
    train_frac: float = 0.6,
    step_frac: float = 0.1,
    stat: str = "sharpe",
    *,
    embargo_frac: float = 0.0,
    ann_factor: float = 1.0,
    ddof: int = 1,
    min_oos: int = 2,
) -> Dict[str, Any]:
    """Rolling fixed-width walk-forward IS->OOS degradation.

    A trailing in-sample window of ``round(train_frac * T)`` rows is followed by
    an embargo gap of ``round(embargo_frac * T)`` rows, then an out-of-sample
    window of ``round(step_frac * T)`` rows. The whole train+oos block slides
    forward by the OOS step each fold. Same return shape as
    ``purged_embargoed_walkforward``.
    """
    if not (0.0 < train_frac < 1.0):
        raise ValueError("train_frac must be in (0, 1)")
    if not (0.0 < step_frac < 1.0):
        raise ValueError("step_frac must be in (0, 1)")
    dates, rets = _prepare(dated_series)
    T = len(rets)
    if T < 4:
        return _summarize([], stat, 0, False)

    train_n = max(2, int(round(train_frac * T)))
    step_n = max(1, int(round(step_frac * T)))
    embargo = max(0, int(round(embargo_frac * T)))

    folds_out: List[Dict[str, Any]] = []
    fold_id = 0
    oos_lo = train_n + embargo
    while oos_lo < T:
        oos_hi = min(oos_lo + step_n, T)
        if oos_hi - oos_lo < min_oos:
            break
        is_hi = oos_lo - embargo
        is_lo = max(0, is_hi - train_n)
        if is_hi - is_lo >= 2:
            folds_out.append(
                _fold_record(fold_id, dates, is_lo, is_hi, oos_lo, oos_hi,
                             rets, stat, ann_factor, ddof, embargo)
            )
            fold_id += 1
        oos_lo += step_n

    return _summarize(folds_out, stat, embargo, False)
