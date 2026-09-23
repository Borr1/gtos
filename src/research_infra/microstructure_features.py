"""E26 — Microstructure-WR correlation study.

Strategic question
==================
The agent currently consumes M15 OHLCV + a handful of swing/POI tags but
no microstructure signals (no order-flow imbalance, no cumulative
delta, no per-bar buy/sell pressure). The research-program backlog
records E26 as the "correlation-with-realized-R" gating step that decides
whether *any* synthetic-from-OHLC microstructure feature deserves an
upgrade into the production MSO payload.

This module operates strictly on the **synthetic-tick reconstructor**
(E24) outputs. We compute three microstructure summary statistics over
the N M15 bars leading up to each historical CANDIDATE candle and then
correlate each statistic with the realized R-multiple for that fill::

    cumulative_delta              = signed sum of bar Lee-Ready directions,
                                    weighted by volume_proxy
    footprint_imbalance           = (buy_vol - sell_vol) / (buy_vol + sell_vol)
    micro_reversal_count          = number of consecutive M1/M5 bars whose
                                    Lee-Ready direction differs from the
                                    immediately previous bar's

We then join ``(symbol, candle_close_ts) -> {feature -> value}`` against
the realized-R outcomes harvested from
``knowledge_base_backtest/sessions/`` and compute Spearman rank
correlation per (symbol, feature) cell. p-values use the asymptotic
``t = r * sqrt((n-2)/(1-r^2))`` approximation against a Student-t
distribution with ``n - 2`` degrees of freedom; we Bonferroni-correct
across the family of (symbol × feature) tests.

Hard rules preserved
====================
* **REALIZED R is the verdict, not walk-level counts.** Per
  ``feedback_walk_level_evidence_not_predictive`` we never surface a
  feature as "predictive" on the basis of its own distribution — only
  on the basis of correlation with realized R.
* **Bonferroni across (instrument × feature).** Family size = 6
  symbols × 3 features = 18 tests. Survivors must pass
  ``p_bonferroni < 0.05``.
* **Pure-Python statistics.** Spearman = rank-rank Pearson, Pearson
  computed by hand. Student-t CDF is approximated using a
  Wilson-Hilferty cube-root transform of the F(1, n-2) → chi-square
  intermediate, sufficient at n ≥ 10 to within ~1e-3.
* **n ≥ 10 minimum per cell.** Below that the noise floor on a single
  Spearman is dominated by sample size and the test is uninformative.
  Such cells are flagged ``INSUFFICIENT_N`` and excluded from the
  Bonferroni denominator.
* **Synthetic-tick caveat carried forward.** The synthetic ticks come
  from OHLC alone (no broker aggressor flags), so the upper bound on
  this analysis is whatever signal survives Lee-Ready 1991's
  candle-direction proxy. A null result here does NOT mean
  microstructure is unimportant — it means *OHLC-derivable*
  microstructure has no edge over current MSO inputs.

Schema
======
Fill dict (input)::

    {
        "symbol": "XAUUSD",
        "candle_close_ts": datetime("2026-04-15T13:30:00+00:00"),
        # candle_close_ts = bar OPEN of the M15 that triggered the
        # CANDIDATE + 15 minutes (= bar close = entry-decision time).
        "r_multiple": 0.75,
    }

Per-fill feature dict::

    {
        "fill_id": "bt_2026-04-15_ny_001",
        "symbol": "XAUUSD",
        "cumulative_delta": -120.5,
        "footprint_imbalance": -0.382,
        "micro_reversal_count": 7,
        "lookback_bars_used": 60,
        "lookback_minutes": 60,
        "input_timeframe": "M1",
    }

Per-cell correlation row (output)::

    {
        "symbol": "XAUUSD",
        "feature": "cumulative_delta",
        "n": 42,
        "spearman_rho": -0.18,
        "p_value": 0.255,
        "p_bonferroni": 1.0,
        "verdict": "NO_SIGNAL",
    }
"""

from __future__ import annotations

import logging
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Sequence

from .synthetic_tick_reconstructor import (
    SUB_M15_TIMEFRAMES,
    bar_lee_ready_direction,
    load_sub_m15_bars,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default lookback window for microstructure aggregates, in minutes.
#: 60 minutes = the last 4 M15 bars worth of microstructure leading
#: into the entry candle. This window mirrors the M15 H4-context window
#: most ICT-style frameworks consider relevant for "which side is in
#: control right now". Caller may override.
DEFAULT_LOOKBACK_MIN: int = 60

#: Minimum sample size per (symbol, feature) cell. Below this the
#: Spearman test is flagged INSUFFICIENT_N rather than tested.
MIN_N_PER_CELL: int = 10

#: Feature names tracked in this module. Locked: changing this list
#: changes the Bonferroni denominator and would invalidate any
#: previously-saved verdicts.
FEATURE_NAMES: tuple[str, ...] = (
    "cumulative_delta",
    "footprint_imbalance",
    "micro_reversal_count",
)


# ---------------------------------------------------------------------------
# Per-fill feature extraction
# ---------------------------------------------------------------------------


def compute_features_for_window(bars: Sequence[dict]) -> dict:
    """Compute the three microstructure aggregates over a bar window.

    The bars list is expected to be sorted by time. All three features
    are pure functions of the OHLC sequence; they delegate the
    direction-classification step to ``bar_lee_ready_direction``.
    """
    if not bars:
        return {
            "cumulative_delta": 0.0,
            "footprint_imbalance": 0.0,
            "micro_reversal_count": 0,
        }

    cum_delta = 0.0
    buy_vol = 0.0
    sell_vol = 0.0
    reversals = 0
    last_dir: Optional[str] = None

    for b in bars:
        d = bar_lee_ready_direction(b)
        v = float(b.get("volume") or 1.0)
        if d == "buy":
            cum_delta += v
            buy_vol += v
        elif d == "sell":
            cum_delta -= v
            sell_vol += v
        # neutral: don't move delta, don't add volume to either side

        if last_dir is not None and d != last_dir and d != "neutral" and last_dir != "neutral":
            reversals += 1
        if d != "neutral":
            last_dir = d

    total_vol = buy_vol + sell_vol
    imbalance = (buy_vol - sell_vol) / total_vol if total_vol > 0 else 0.0

    return {
        "cumulative_delta": cum_delta,
        "footprint_imbalance": imbalance,
        "micro_reversal_count": reversals,
    }


def compute_features_for_fill(
    fill: dict,
    bars: Sequence[dict],
    *,
    lookback_min: int = DEFAULT_LOOKBACK_MIN,
) -> Optional[dict]:
    """Compute features over ``[candle_close_ts - lookback, candle_close_ts)``.

    Returns ``None`` if the lookback window contains zero bars (e.g.
    weekend or pre-history). The caller decides whether to skip or
    record the gap.
    """
    end = fill["candle_close_ts"]
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    start = end - timedelta(minutes=lookback_min)

    window = [b for b in bars if start <= b["time"] < end]
    if not window:
        return None

    feats = compute_features_for_window(window)
    feats.update({
        "fill_id": fill.get("fill_id") or fill.get("trade_id"),
        "symbol": fill["symbol"],
        "candle_close_ts": end.isoformat(),
        "lookback_bars_used": len(window),
        "lookback_minutes": lookback_min,
        "r_multiple": fill["r_multiple"],
    })
    return feats


def compute_features_per_symbol(
    fills: Sequence[dict],
    data_dir: str | Path,
    *,
    lookback_min: int = DEFAULT_LOOKBACK_MIN,
) -> tuple[list[dict], dict]:
    """Compute features for every fill, grouped by symbol for IO efficiency.

    Returns ``(per_fill_features, telemetry)`` where ``telemetry`` is a
    dict with ``loaded_symbols``, ``input_timeframes``, ``skipped_fills``
    counts.
    """
    by_sym: dict[str, list[dict]] = {}
    for f in fills:
        by_sym.setdefault(f["symbol"], []).append(f)

    out: list[dict] = []
    timeframes: dict[str, str] = {}
    skipped = 0
    for sym, sym_fills in by_sym.items():
        try:
            bars, tf = load_sub_m15_bars(sym, data_dir)
        except FileNotFoundError as e:
            logger.warning("No sub-M15 data for %s: %s — skipping %d fills", sym, e, len(sym_fills))
            skipped += len(sym_fills)
            continue
        timeframes[sym] = tf
        for fill in sym_fills:
            feats = compute_features_for_fill(fill, bars, lookback_min=lookback_min)
            if feats is None:
                skipped += 1
                continue
            feats["input_timeframe"] = tf
            out.append(feats)
    return out, {
        "loaded_symbols": list(timeframes.keys()),
        "input_timeframes": timeframes,
        "skipped_fills": skipped,
        "total_fills_in": len(fills),
        "total_features_out": len(out),
    }


# ---------------------------------------------------------------------------
# Statistics — Spearman + Student-t p-value
# ---------------------------------------------------------------------------


def _ranks(xs: Sequence[float]) -> list[float]:
    """Return midrank-tied ranks for ``xs`` (1-indexed)."""
    n = len(xs)
    indexed = sorted(enumerate(xs), key=lambda p: p[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-indexed midrank
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Pearson correlation coefficient. Returns 0 if either var is 0."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation. Pure Python."""
    if len(xs) != len(ys):
        raise ValueError("xs and ys must be the same length")
    if len(xs) < 2:
        return 0.0
    return _pearson(_ranks(xs), _ranks(ys))


def _student_t_two_sided_p(t: float, df: int) -> float:
    """Two-sided p-value for Student-t with ``df`` degrees of freedom.

    Uses the standard relation ``F_{1,df}(t^2) = F_t(|t|, df)`` for the
    one-sided side; returns ``2 * (1 - cdf)``. The CDF here uses the
    incomplete-beta form via a Wilson-Hilferty cube-root chi-square
    transform on F(1, df). Accuracy is within ~1e-3 for df >= 8 — more
    than sufficient for the tests in this module (n >= 10 ⇒ df >= 8).

    For df < 5 we fall back to a conservative ``min(1.0, 1/(t^2 + 1))``
    bound that always *over-estimates* the p-value (so a SURVIVOR
    verdict is never reported on insufficient df).
    """
    if df < 1:
        return 1.0
    if df < 5:
        return min(1.0, 1.0 / (t * t + 1.0))
    x = (t * t) / (t * t + df)  # F-statistic-like CDF input
    # Symmetric Beta(1/2, df/2) CDF via regularised-incomplete-beta
    # approximation. We use the continued-fraction form from Numerical
    # Recipes §6.4 (truncated). Accuracy is sufficient for the
    # research-grade verdicts here.
    a, b = 0.5, df / 2.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(max(x, 1e-300)) + b * math.log(max(1.0 - x, 1e-300))
    )
    if x < (a + 1.0) / (a + b + 2.0):
        cf = _betacf(x, a, b)
        ix = bt * cf / a
    else:
        cf = _betacf(1.0 - x, b, a)
        ix = 1.0 - bt * cf / b
    # ix = P(F < x); two-sided p = 1 - ix
    p = 1.0 - ix
    return max(0.0, min(1.0, p))


def _betacf(x: float, a: float, b: float, max_iter: int = 200, eps: float = 3e-7) -> float:
    """Continued-fraction expansion for the regularised incomplete beta."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        del_ = d * c
        h *= del_
        if abs(del_ - 1.0) < eps:
            break
    return h


def spearman_p(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Return ``(rho, two_sided_p)`` for Spearman rank correlation.

    Uses the asymptotic ``t = rho * sqrt((n-2)/(1-rho^2))`` Student-t
    approximation. For tiny n (< 10) the p-value will be a conservative
    upper bound from ``_student_t_two_sided_p``.
    """
    n = len(xs)
    if n < 3:
        return 0.0, 1.0
    rho = spearman(xs, ys)
    if abs(rho) >= 0.999999:
        return rho, 0.0
    t = rho * math.sqrt(max((n - 2) / max(1.0 - rho * rho, 1e-9), 0.0))
    p = _student_t_two_sided_p(t, n - 2)
    return rho, p


# ---------------------------------------------------------------------------
# Per-cell correlation table
# ---------------------------------------------------------------------------


def correlate_features_with_r(
    feature_rows: Sequence[dict],
    *,
    feature_names: Sequence[str] = FEATURE_NAMES,
    min_n: int = MIN_N_PER_CELL,
) -> list[dict]:
    """Build the per-cell ``{symbol × feature -> spearman + p}`` table.

    Counts only cells with ``n >= min_n`` toward the Bonferroni
    denominator. Cells below the threshold are returned with
    ``verdict="INSUFFICIENT_N"`` and ``p_bonferroni=None``.
    """
    by_sym: dict[str, list[dict]] = {}
    for r in feature_rows:
        by_sym.setdefault(r["symbol"], []).append(r)

    results: list[dict] = []
    # First pass: compute raw rho + p, decide which cells contribute to family
    family_rows: list[dict] = []
    for sym, rows in by_sym.items():
        for feat in feature_names:
            xs = [r[feat] for r in rows]
            ys = [r["r_multiple"] for r in rows]
            n = len(xs)
            if n < min_n:
                results.append({
                    "symbol": sym,
                    "feature": feat,
                    "n": n,
                    "spearman_rho": None,
                    "p_value": None,
                    "p_bonferroni": None,
                    "verdict": "INSUFFICIENT_N",
                })
                continue
            rho, p = spearman_p(xs, ys)
            row = {
                "symbol": sym,
                "feature": feat,
                "n": n,
                "spearman_rho": round(rho, 4),
                "p_value": round(p, 6),
                "p_bonferroni": None,
                "verdict": None,
            }
            results.append(row)
            family_rows.append(row)

    family_size = len(family_rows)
    for r in family_rows:
        bp = min(1.0, r["p_value"] * family_size) if family_size > 0 else r["p_value"]
        r["p_bonferroni"] = round(bp, 6)
        if bp < 0.05:
            r["verdict"] = "SURVIVES_BONFERRONI"
        elif r["p_value"] < 0.05:
            r["verdict"] = "RAW_SIG_NOT_SURVIVING"
        else:
            r["verdict"] = "NO_SIGNAL"
    return results


def aggregate_by_feature(per_cell_rows: Sequence[dict]) -> list[dict]:
    """Roll up per-cell results into per-feature pooled summaries.

    The pooled view answers "across instruments, does this feature
    correlate with R" by computing the median Spearman across cells
    that passed the n-floor and counting how many per-cell tests
    reached either RAW_SIG_NOT_SURVIVING or SURVIVES_BONFERRONI.
    """
    by_feat: dict[str, list[dict]] = {}
    for r in per_cell_rows:
        by_feat.setdefault(r["feature"], []).append(r)

    out: list[dict] = []
    for feat, rows in by_feat.items():
        valid = [r for r in rows if r["spearman_rho"] is not None]
        if not valid:
            out.append({
                "feature": feat,
                "cells_tested": 0,
                "median_spearman": None,
                "raw_sig_count": 0,
                "bonferroni_survivors": 0,
                "verdict": "INSUFFICIENT_N_ALL_CELLS",
            })
            continue
        rhos = [r["spearman_rho"] for r in valid]
        raw_sig = sum(1 for r in valid if r["verdict"] in ("RAW_SIG_NOT_SURVIVING", "SURVIVES_BONFERRONI"))
        bf = sum(1 for r in valid if r["verdict"] == "SURVIVES_BONFERRONI")
        if bf > 0:
            verdict = "FEATURE_HAS_SURVIVOR_CELL"
        elif raw_sig >= 2:
            verdict = "WEAK_RAW_SIGNAL_NO_SURVIVOR"
        else:
            verdict = "NO_SIGNAL"
        out.append({
            "feature": feat,
            "cells_tested": len(valid),
            "median_spearman": round(statistics.median(rhos), 4),
            "mean_spearman": round(statistics.mean(rhos), 4),
            "raw_sig_count": raw_sig,
            "bonferroni_survivors": bf,
            "verdict": verdict,
        })
    return out
