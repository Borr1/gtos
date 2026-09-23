"""B14 — Walk-Level vs Realized-R Systematic Study.

Strategic question
==================
Memory ``feedback_walk_level_evidence_not_predictive`` records the observation
that walk-level statistical evidence (touch-count walk-level p=5e-16 reported
in session 39) does NOT translate into realized-R differences across strata —
in that case the touch=2 stratum actually beat touch=1 in realized R despite
losing the walk-level test in the opposite direction.

B14 stress-tests this default policy. It asks the inverse question across the
ENTIRE family of walk-level signals available in MSO ``raw_data``: is there
ANY signal where a walk-level partition (e.g. ``touch_count: 1, 2, 3+``)
ALSO partitions realized-R distributions in a statistically distinguishable
way that matches the walk-level direction? Such a signal would be a candidate
to feed K54 (ML classifier training pipeline) as a high-priority feature.

Hard rules preserved
====================
* **Pure-Python statistics.** No scipy dependency. Kruskal-Wallis is
  implemented from first principles using the asymptotic chi-square
  approximation; tested against hand-verified expected values.
* **No AI calls, no prompt edits, no production-config edits.** This is
  ``src/research_infra`` (additive-only research helpers).
* **Heavy-tailed-aware.** Memory ``project_distributional_findings``: gold
  realized-R has fat tails (ξ=0.35). We use Kruskal-Wallis (rank-based,
  non-parametric) rather than ANOVA so a single 1.5R outlier doesn't
  carry a stratum's mean.
* **Bonferroni across the family.** When testing N walk-level signals, raw
  p-values are multiplied by N (clipped to 1.0). Survivors must pass
  ``p_bonferroni < 0.05``.
* **Direction consistency.** A signal cannot SURVIVE if its walk-level
  ranking is opposite to the realized-R ranking — that's the failure mode
  documented in memory ``feedback_walk_level_evidence_not_predictive``
  (touch-count walk evidence ranked touch=1 > touch=2 but realized R
  flipped). The validator records both orderings and flags the
  consistency check.
* **Min stratum n=10.** Below that, the noise floor on a per-stratum mean
  makes any rank-based test uninformative. Such signals are flagged
  ``INSUFFICIENT_N`` rather than tested — preserves the family-wise
  Bonferroni correction.

Schema (canonical)
==================
Trade dict (input)::

    {
        "candle_close_time": "2026-04-15T13:15:00Z",   # ISO-8601 UTC
        "symbol": "XAUUSD",
        "direction": "LONG"|"SHORT"|None,
        "r_multiple": 1.5,                              # realized R (REQUIRED)
        # walk-level signals — any subset present:
        "touch_count": 1,
        "ob_retest_distance_atr": 0.42,
        "fvg_overlap_pct": 0.31,
        "liquidity_proximity_atr": 0.85,
        "displacement_quality_score": 7,
        "framework": "ob_retest",
        "session": "London",
        "regime": "trending_bull",
        "bias_alignment": "aligned",
        ...
    }

Stratum row (output) — one per (signal, stratum_label)::

    {
        "signal": "touch_count",
        "stratum": "1",
        "n": 14,
        "mean_r": 0.43,
        "median_r": 0.0,
        "wr": 0.643,
        "wr_lo": 0.40,                # Wilson 95% lower
        "wr_hi": 0.83,                # Wilson 95% upper
        "total_r": 6.0,
        "rank_order_walk": 1,         # walk-level ranking position (1 = best)
        "rank_order_realized": 2,     # realized-R mean ranking (1 = best)
    }

SignalReport row (output) — one per signal::

    {
        "signal": "touch_count",
        "n_strata_tested": 3,
        "min_stratum_n": 14,
        "kw_h": 12.34,                # Kruskal-Wallis H statistic
        "kw_df": 2,                   # k - 1 strata
        "kw_p_raw": 0.0021,
        "kw_p_bonferroni": 0.014,     # raw_p * family_size, clipped to 1.0
        "direction_consistent": false,
        "walk_ranking": ["1", "2", ">=3"],
        "realized_ranking": [">=3", "1", "2"],
        "status": "NON_PREDICTIVE",   # SURVIVOR | NON_PREDICTIVE | INSUFFICIENT_N
        "notes": "rank flip at stratum '1'",
    }

ValidatorReport (output) — top-level::

    {
        "family_size": 11,
        "n_survivors": 0,
        "survivors": [],
        "signals": [SignalReport, ...],
        "strata_by_signal": {signal: [stratum_row, ...]},
        "n_trades_total": 75,
        "generated_at": "2026-04-26T18:00:00Z",
    }
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional, Sequence


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StratumRow:
    """Realized-R outcomes for a single (signal, stratum_label)."""

    signal: str
    stratum: str
    n: int
    mean_r: float
    median_r: float
    wr: float
    wr_lo: float
    wr_hi: float
    total_r: float
    rank_walk: Optional[int] = None
    rank_realized: Optional[int] = None

    def to_row(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "stratum": self.stratum,
            "n": self.n,
            "mean_r": round(self.mean_r, 6),
            "median_r": round(self.median_r, 6),
            "wr": round(self.wr, 6),
            "wr_lo": round(self.wr_lo, 6),
            "wr_hi": round(self.wr_hi, 6),
            "total_r": round(self.total_r, 6),
            "rank_walk": self.rank_walk,
            "rank_realized": self.rank_realized,
        }


@dataclass(frozen=True)
class SignalReport:
    """Outcome of testing one walk-level signal."""

    signal: str
    n_strata_tested: int
    min_stratum_n: int
    kw_h: Optional[float]
    kw_df: Optional[int]
    kw_p_raw: Optional[float]
    kw_p_bonferroni: Optional[float]
    direction_consistent: Optional[bool]
    walk_ranking: list[str]
    realized_ranking: list[str]
    status: str  # SURVIVOR | NON_PREDICTIVE | INSUFFICIENT_N
    notes: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "n_strata_tested": self.n_strata_tested,
            "min_stratum_n": self.min_stratum_n,
            "kw_h": (round(self.kw_h, 6) if self.kw_h is not None else None),
            "kw_df": self.kw_df,
            "kw_p_raw": (
                round(self.kw_p_raw, 8) if self.kw_p_raw is not None else None
            ),
            "kw_p_bonferroni": (
                round(self.kw_p_bonferroni, 8)
                if self.kw_p_bonferroni is not None
                else None
            ),
            "direction_consistent": self.direction_consistent,
            "walk_ranking": list(self.walk_ranking),
            "realized_ranking": list(self.realized_ranking),
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class ValidatorReport:
    """Top-level report — one B14 evaluation."""

    family_size: int
    n_trades_total: int
    signals: list[SignalReport] = field(default_factory=list)
    strata_by_signal: dict[str, list[StratumRow]] = field(default_factory=dict)
    generated_at: str = ""

    @property
    def survivors(self) -> list[SignalReport]:
        return [s for s in self.signals if s.status == "SURVIVOR"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_size": self.family_size,
            "n_trades_total": self.n_trades_total,
            "n_survivors": len(self.survivors),
            "survivors": [s.signal for s in self.survivors],
            "signals": [s.to_row() for s in self.signals],
            "strata_by_signal": {
                sig: [r.to_row() for r in rows]
                for sig, rows in self.strata_by_signal.items()
            },
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Signal registry — canonical list of walk-level signals + binning rules
# ---------------------------------------------------------------------------


def _bin_continuous(value: float, edges: Sequence[float], labels: Sequence[str]) -> str:
    """Place ``value`` in the first bucket whose right edge is > value.

    ``edges`` is the right-edge sequence (length k-1 for k labels). The last
    label catches everything above the final edge. Hand-verified semantics:

        edges=[0.3, 0.6], labels=["<0.3", "0.3-0.6", ">0.6"]:
          0.0  -> "<0.3"
          0.3  -> "0.3-0.6"   (right-open at edge: value < edge)
          0.5  -> "0.3-0.6"
          0.6  -> ">0.6"
          1.0  -> ">0.6"
    """
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def _label_touch_count(t: Any) -> Optional[str]:
    """Touch counts: 1 / 2 / >=3. None / negative / non-int → drop."""
    try:
        v = int(t)
    except (TypeError, ValueError):
        return None
    if v < 0:
        return None
    if v <= 0:
        return "0"
    if v == 1:
        return "1"
    if v == 2:
        return "2"
    return ">=3"


def _label_distance_atr(d: Any) -> Optional[str]:
    """OB-retest distance in ATR multiples."""
    try:
        v = float(d)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < 0:
        return None
    return _bin_continuous(v, [0.3, 0.6, 1.0], ["<0.3", "0.3-0.6", "0.6-1.0", ">=1.0"])


def _label_fvg_overlap_pct(p: Any) -> Optional[str]:
    """FVG overlap percent (0-1)."""
    try:
        v = float(p)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < 0 or v > 1.0:
        return None
    return _bin_continuous(v, [0.25, 0.5, 0.75], ["0-25%", "25-50%", "50-75%", ">=75%"])


def _label_liquidity_proximity_atr(d: Any) -> Optional[str]:
    """Liquidity proximity in ATR multiples (lower = closer to a sweep target)."""
    try:
        v = float(d)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < 0:
        return None
    return _bin_continuous(v, [0.5, 1.0], ["<0.5", "0.5-1.0", ">=1.0"])


def _label_displacement_quality(q: Any) -> Optional[str]:
    """Displacement quality score (integer 0-10 typically)."""
    try:
        v = int(q)
    except (TypeError, ValueError):
        return None
    if v < 0:
        return None
    return _bin_continuous(float(v), [4, 7], ["low(<4)", "med(4-6)", "high(>=7)"])


def _label_bias_alignment(b: Any) -> Optional[str]:
    """Bias alignment: 'aligned' / 'opposed' / boolean / None.

    Accepted inputs:
      - True / "aligned" / "yes" / "y" / "1" → "aligned"
      - False / "opposed" / "no" / "n" / "0" → "opposed"
      - None / unparseable → None (drop)
    """
    if b is None:
        return None
    if isinstance(b, bool):
        return "aligned" if b else "opposed"
    if isinstance(b, (int, float)):
        return "aligned" if b else "opposed"
    s = str(b).strip().lower()
    if s in ("aligned", "yes", "y", "1", "true", "same"):
        return "aligned"
    if s in ("opposed", "no", "n", "0", "false", "opposite"):
        return "opposed"
    return None


def _label_categorical(value: Any) -> Optional[str]:
    """Pass categorical values through verbatim. None / empty → drop."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s


def _label_kill_zone(value: Any) -> Optional[str]:
    """Normalize kill-zone labels. ``Off`` / empty → drop (not a kill-zone trade)."""
    s = _label_categorical(value)
    if s is None:
        return None
    sl = s.lower()
    if sl in ("off", "off-hours", "none"):
        return None
    return sl


def _label_setup_grade(value: Any) -> Optional[str]:
    """A+/A/B/C grades pass through; lowercase / synonym normalization."""
    s = _label_categorical(value)
    if s is None:
        return None
    s = s.upper()
    # Allow A+, A, B, C, B+, C+ etc. — strip trailing whitespace/quotes.
    return s


def _label_ob_touch_max(value: Any) -> Optional[str]:
    """Max H1 OB touch count from the MSO ``mso_h1_ob_touch_counts`` list."""
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        try:
            return _label_touch_count(value)
        except (TypeError, ValueError):
            return None
    if not value:
        return None
    try:
        m = max(int(v) for v in value)
    except (TypeError, ValueError):
        return None
    return _label_touch_count(m)


def _label_h1_fvg_unfilled_count(value: Any) -> Optional[str]:
    """Count of unfilled H1 FVGs (integer; bucket low/med/high)."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    if v < 0:
        return None
    return _bin_continuous(float(v), [3, 7], ["0-2", "3-6", ">=7"])


def _label_clv_current(value: Any) -> Optional[str]:
    """M15 CLV (close-location-value), [-1, 1]."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < -1.001 or v > 1.001:
        return None
    return _bin_continuous(v, [-0.33, 0.33], ["lower-third", "mid", "upper-third"])


def _label_buy_fraction(value: Any) -> Optional[str]:
    """M15 buy-volume fraction (0-1)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v < 0 or v > 1.001:
        return None
    return _bin_continuous(v, [0.4, 0.6], ["bear", "balanced", "bull"])


def _label_unmitigated_ob_count(value: Any) -> Optional[str]:
    """Count of unmitigated H1 OBs on the MSO."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    if v < 0:
        return None
    return _bin_continuous(float(v), [1, 3], ["0", "1-2", ">=3"])


# Each registry entry is a (signal_name, label_fn, walk_ranking) tuple.
# ``walk_ranking`` orders strata from "best walk-level prediction" (rank=1)
# to "worst" — used to test direction consistency. Set to None when the
# signal has no a-priori walk-level direction (regime tag, framework, etc.).
SIGNAL_REGISTRY: dict[str, dict[str, Any]] = {
    "touch_count": {
        # Direction-aware first (matches research/touch_count_audit/analyze.py),
        # then the general "h1_opp_ob_touch", then a flat "touch_count" key.
        "extract": lambda t: (
            _direction_aware_touch(t)
            if (_direction_aware_touch(t) is not None)
            else _first_present(t, ("touch_count", "h1_opp_ob_touch"))
        ),
        "label_fn": _label_touch_count,
        # Walk-level convention (ADR-005): fewer touches = stronger zone =
        # higher walk-level WR ranking.
        "walk_ranking": ["1", "2", ">=3"],
    },
    "touch_count_max_mso": {
        "extract": lambda t: t.get("mso_h1_ob_touch_counts"),
        "label_fn": _label_ob_touch_max,
        "walk_ranking": ["1", "2", ">=3"],
    },
    "ob_retest_distance_atr": {
        "extract": lambda t: _first_present(
            t,
            ("ob_retest_distance_atr", "mso_h1_nearest_ob_distance_atr", "nearest_ob_distance_atr"),
        ),
        "label_fn": _label_distance_atr,
        # Walk-level: closer to OB = stronger setup, BUT very close (already
        # touching) is a different cohort. Conventional walk-ranking puts
        # the 0.3-0.6 band as best; outside that we order by absolute
        # distance ascending. This is a pragmatic best-guess.
        "walk_ranking": ["0.3-0.6", "<0.3", "0.6-1.0", ">=1.0"],
    },
    "fvg_overlap_pct": {
        "extract": lambda t: t.get("fvg_overlap_pct"),
        "label_fn": _label_fvg_overlap_pct,
        # Walk-level: more overlap = stronger confluence.
        "walk_ranking": [">=75%", "50-75%", "25-50%", "0-25%"],
    },
    "liquidity_proximity_atr": {
        "extract": lambda t: t.get("liquidity_proximity_atr"),
        "label_fn": _label_liquidity_proximity_atr,
        # Walk-level: closer liquidity = better sweep target.
        "walk_ranking": ["<0.5", "0.5-1.0", ">=1.0"],
    },
    "displacement_quality_score": {
        "extract": lambda t: t.get("displacement_quality_score"),
        "label_fn": _label_displacement_quality,
        "walk_ranking": ["high(>=7)", "med(4-6)", "low(<4)"],
    },
    "bias_alignment": {
        "extract": lambda t: t.get("bias_alignment"),
        "label_fn": _label_bias_alignment,
        # Walk-level: aligned setups should beat opposed.
        "walk_ranking": ["aligned", "opposed"],
    },
    "session_id": {
        "extract": lambda t: _first_present(t, ("session", "kill_zone")),
        "label_fn": _label_kill_zone,
        # No a-priori walk-level direction across sessions — set to None.
        "walk_ranking": None,
    },
    "framework_id": {
        "extract": lambda t: _first_present(
            t, ("framework", "logger_framework", "framework_id")
        ),
        "label_fn": _label_categorical,
        "walk_ranking": None,
    },
    "regime_tag": {
        "extract": lambda t: _first_present(t, ("regime", "regime_tag")),
        "label_fn": _label_categorical,
        "walk_ranking": None,
    },
    "setup_grade": {
        "extract": lambda t: _first_present(
            t, ("setup_grade", "logger_setup_grade", "out_setup_grade")
        ),
        "label_fn": _label_setup_grade,
        # Walk-level: A+ > A > B > C by definition of the grading scheme.
        "walk_ranking": ["A+", "A", "B", "C"],
    },
    "h1_fvg_unfilled_count": {
        "extract": lambda t: t.get("h1_fvg_unfilled_count"),
        "label_fn": _label_h1_fvg_unfilled_count,
        # Walk-level: more unfilled FVGs = more nearby targets.
        "walk_ranking": [">=7", "3-6", "0-2"],
    },
    "m15_clv_current": {
        "extract": lambda t: _first_present(
            t, ("mso_m15_clv_current", "m15_clv_current")
        ),
        "label_fn": _label_clv_current,
        # Walk-level (LONG-biased proxy): close in upper-third = bullish
        # follow-through; for SHORT cohort we'd want the opposite. Direction
        # check flags this.
        "walk_ranking": None,  # mixed direction across LONG/SHORT cohort
    },
    "m15_buy_fraction": {
        "extract": lambda t: _first_present(
            t, ("mso_m15_bvc_buy_fraction", "m15_buy_fraction")
        ),
        "label_fn": _label_buy_fraction,
        "walk_ranking": None,
    },
    "unmitigated_ob_count": {
        "extract": lambda t: _first_present(
            t, ("mso_h1_unmitigated_ob_count", "unmitigated_ob_count")
        ),
        "label_fn": _label_unmitigated_ob_count,
        # Walk-level: more unmitigated OBs = more support — best>=3.
        "walk_ranking": [">=3", "1-2", "0"],
    },
}


def _first_present(t: dict, keys: Sequence[str]) -> Any:
    """Return the first value in ``t`` whose key is in ``keys`` and is not None.

    Unlike ``a or b``, this does NOT treat 0, 0.0, "", or False as missing —
    only ``None`` is treated as missing. The downstream ``label_fn`` for each
    signal is responsible for rejecting domain-invalid values (e.g. negative
    distances).
    """
    for k in keys:
        if k in t and t[k] is not None:
            return t[k]
    return None


def _direction_aware_touch(t: dict) -> Any:
    """Map the AI-evaluated direction onto the per-direction touch field.

    Mirrors ``research/touch_count_audit/analyze.py:get_dir_touch`` so the
    validator runs the same touch-count semantics as the production
    audit. Returns ``None`` when no direction or no per-direction touch
    is present.
    """
    direction = t.get("direction") or t.get("ai_direction_evaluated")
    if direction == "LONG":
        v = t.get("h1_opp_ob_touch_long")
    elif direction == "SHORT":
        v = t.get("h1_opp_ob_touch_short")
    else:
        v = None
    if v is None:
        v = t.get("h1_opp_ob_touch")
    return v


# ---------------------------------------------------------------------------
# Stratification
# ---------------------------------------------------------------------------


def stratify_by_signal(
    trades: Sequence[dict[str, Any]],
    signal_name: str,
) -> dict[str, list[dict[str, Any]]]:
    """Group trades by a signal's stratum label.

    Continuous signals are bucketed via the registered ``label_fn``; categorical
    signals pass through. Trades whose signal is missing or unparseable are
    silently dropped (they still count toward ``n_trades_total`` for the
    overall report header but do not appear in any stratum).

    Parameters
    ----------
    trades:
        Sequence of trade dicts. Each must carry ``r_multiple`` for downstream
        evaluation; this function does not require it (it just bins).
    signal_name:
        One of the keys in :data:`SIGNAL_REGISTRY`.

    Returns
    -------
    Dict mapping stratum label → list of trade dicts.
    """
    if signal_name not in SIGNAL_REGISTRY:
        raise KeyError(f"unknown signal {signal_name!r}; expected one of {sorted(SIGNAL_REGISTRY)}")
    spec = SIGNAL_REGISTRY[signal_name]
    extract = spec["extract"]
    label_fn = spec["label_fn"]
    out: dict[str, list[dict[str, Any]]] = {}
    for t in trades:
        try:
            raw = extract(t)
        except (KeyError, TypeError, AttributeError):
            continue
        label = label_fn(raw)
        if label is None:
            continue
        out.setdefault(label, []).append(t)
    return out


# ---------------------------------------------------------------------------
# Kruskal-Wallis H test (pure Python)
# ---------------------------------------------------------------------------


def _rank_with_ties(values: list[float]) -> list[float]:
    """Mid-rank tie correction. Returns ranks parallel to ``values``.

    Implementation: sort indices by value, walk groups of equal values,
    assign each member the mean of (rank_first + rank_last) within the
    tie group. This matches scipy's default ranking strategy.
    """
    n = len(values)
    if n == 0:
        return []
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks: list[float] = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        # Tied positions i..j get the mean of (i+1)..(j+1) (1-based ranks).
        mean_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = mean_rank
        i = j + 1
    return ranks


def _chi2_sf(x: float, df: int) -> float:
    """Survival function (1 - CDF) of a chi-squared distribution.

    Uses the regularized upper incomplete gamma function:
        SF(x; df) = Q(df/2, x/2) = Γ(df/2, x/2) / Γ(df/2)

    Implementation via the series for the regularized lower-incomplete
    gamma function (P) when x < df+1, otherwise via the continued
    fraction for Q. Adapted from Numerical Recipes §6.2 — this is a
    standard pure-Python implementation good for the precision we need
    (Bonferroni-corrected significance at the 0.05 level).

    Returns 1.0 for non-finite or negative ``x`` (as a conservative null).
    """
    if df <= 0:
        return 1.0
    if not math.isfinite(x) or x <= 0:
        return 1.0
    a = df / 2.0
    z = x / 2.0
    return _gamma_q(a, z)


def _gamma_q(a: float, z: float) -> float:
    """Regularized upper incomplete gamma Q(a, z) = Γ(a, z) / Γ(a)."""
    if z < 0 or a <= 0:
        return 1.0
    if z == 0.0:
        return 1.0
    if z < a + 1.0:
        # Series for P(a, z), then Q = 1 - P.
        return 1.0 - _gamma_p_series(a, z)
    return _gamma_q_continued_fraction(a, z)


def _gamma_p_series(a: float, z: float, max_iter: int = 200, tol: float = 1e-12) -> float:
    """Series expansion for the regularized lower incomplete gamma P(a, z)."""
    if z == 0.0:
        return 0.0
    ap = a
    summ = 1.0 / a
    delta = summ
    for _ in range(max_iter):
        ap += 1.0
        delta *= z / ap
        summ += delta
        if abs(delta) < abs(summ) * tol:
            break
    log_pref = -z + a * math.log(z) - math.lgamma(a)
    return summ * math.exp(log_pref)


def _gamma_q_continued_fraction(
    a: float, z: float, max_iter: int = 200, tol: float = 1e-12
) -> float:
    """Continued-fraction expansion for the regularized upper incomplete gamma Q(a, z)."""
    # Modified Lentz method.
    fpmin = 1e-300
    b = z + 1.0 - a
    c = 1.0 / fpmin
    d = 1.0 / b
    h = d
    for i in range(1, max_iter + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < fpmin:
            d = fpmin
        c = b + an / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < tol:
            break
    log_pref = -z + a * math.log(z) - math.lgamma(a)
    return h * math.exp(log_pref)


def kruskal_wallis(strata: list[list[float]]) -> tuple[float, float]:
    """Compute the Kruskal-Wallis H statistic + asymptotic chi-square p-value.

    Parameters
    ----------
    strata:
        List of k stratum-value lists. Each list is the realized-R values
        for one stratum. k >= 2 required; lists may have different sizes.

    Returns
    -------
    (H, p) where H is the Kruskal-Wallis test statistic and p is the
    asymptotic p-value from the chi-square distribution with k-1 degrees
    of freedom. With ties, H is divided by the standard tie-correction
    factor (1 - Σ(t_i^3 - t_i) / (N^3 - N)).

    Raises
    ------
    ValueError if k < 2 or any stratum is empty.

    Hand-verification example
    -------------------------
    Three strata: [1,2], [3,4], [5,6]. Stacked: [1..6], ranks 1..6.
    Stratum sums: 3, 7, 11. N=6, n_i=2 each.
    H = 12/(N(N+1)) * Σ(R_i^2/n_i) - 3(N+1)
      = 12/(6*7) * (9/2 + 49/2 + 121/2) - 21
      = (12/42) * 89.5 - 21
      = 25.5714... - 21
      = 4.5714...
    With df=2, p ≈ 0.10165 (no ties).
    """
    if len(strata) < 2:
        raise ValueError("kruskal_wallis requires k >= 2 strata")
    for s in strata:
        if not s:
            raise ValueError("kruskal_wallis: each stratum must be non-empty")
    sizes = [len(s) for s in strata]
    n_total = sum(sizes)
    if n_total <= 1:
        return (0.0, 1.0)
    # Concatenate then rank (with ties).
    flat: list[float] = []
    for s in strata:
        flat.extend(float(v) for v in s)
    ranks = _rank_with_ties(flat)
    # Sum-of-ranks per stratum.
    rank_sums: list[float] = []
    cur = 0
    for n in sizes:
        rank_sums.append(sum(ranks[cur : cur + n]))
        cur += n
    # H statistic.
    h = (12.0 / (n_total * (n_total + 1.0))) * sum(
        (rs * rs) / n for rs, n in zip(rank_sums, sizes)
    ) - 3.0 * (n_total + 1.0)
    # Tie correction: divide H by C = 1 - Σ(t_i^3 - t_i) / (N^3 - N).
    tie_groups = _count_tie_groups(flat)
    if n_total > 1:
        correction = 1.0 - sum(t * t * t - t for t in tie_groups) / (
            n_total * n_total * n_total - n_total
        )
        if correction > 0:
            h = h / correction
    df = len(strata) - 1
    p = _chi2_sf(h, df)
    return (h, p)


def _count_tie_groups(values: list[float]) -> list[int]:
    """Return the size of each tie group (singletons excluded -- tie size >=2).

    Used by the Kruskal-Wallis tie correction. A list of [1, 2, 2, 3, 3, 3]
    has tie groups [2, 3] (the value 2 ties twice, the value 3 ties three times).
    """
    if not values:
        return []
    sorted_vals = sorted(values)
    groups: list[int] = []
    i = 0
    n = len(sorted_vals)
    while i < n:
        j = i
        while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        size = j - i + 1
        if size >= 2:
            groups.append(size)
        i = j + 1
    return groups


# ---------------------------------------------------------------------------
# Wilson confidence interval (95%) — for stratum WR display
# ---------------------------------------------------------------------------


def _wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion. Returns (lo, hi) in [0, 1]."""
    if n <= 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


# ---------------------------------------------------------------------------
# evaluate_signals — main entrypoint
# ---------------------------------------------------------------------------


def _stratum_summary(signal: str, label: str, trades: list[dict[str, Any]]) -> StratumRow:
    rs = []
    for t in trades:
        try:
            rs.append(float(t["r_multiple"]))
        except (KeyError, TypeError, ValueError):
            continue
    n = len(rs)
    wins = sum(1 for r in rs if r > 0)
    mean_r = sum(rs) / n if n else 0.0
    median_r = _median(rs) if n else 0.0
    wr = wins / n if n else 0.0
    wr_lo, wr_hi = _wilson_ci(wins, n)
    return StratumRow(
        signal=signal,
        stratum=label,
        n=n,
        mean_r=mean_r,
        median_r=median_r,
        wr=wr,
        wr_lo=wr_lo,
        wr_hi=wr_hi,
        total_r=sum(rs),
    )


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _is_direction_consistent(
    walk_ranking: Optional[Sequence[str]],
    realized_ranking: Sequence[str],
) -> tuple[Optional[bool], str]:
    """Compare walk-level a-priori ranking against realized-R ranking.

    Returns ``(consistent, notes)``. ``consistent`` is True when the
    walk-level ranking matches the realized ranking position-for-position
    on all strata that appear in both. False when ANY rank-flip is detected.
    None when ``walk_ranking`` is None (no a-priori direction) — the test
    is not applicable.

    Strata in ``realized_ranking`` not listed in ``walk_ranking`` are
    ignored (the realized ranking may include strata the registry
    didn't pre-rank, e.g. an extra bucket added later).
    """
    if walk_ranking is None:
        return (None, "no a-priori walk-level direction")
    walk_present = [s for s in walk_ranking if s in realized_ranking]
    if len(walk_present) < 2:
        return (None, "fewer than 2 walk-ranked strata observed")
    realized_for_walk = [s for s in realized_ranking if s in walk_ranking]
    if walk_present == realized_for_walk:
        return (True, "")
    # Find first divergence for the notes.
    for w, r in zip(walk_present, realized_for_walk):
        if w != r:
            return (False, f"rank flip: walk[{w!r}] vs realized[{r!r}]")
    return (False, "rank-list length mismatch")


def evaluate_signals(
    trades: Sequence[dict[str, Any]],
    signals: Sequence[str],
    *,
    min_stratum_n: int = 10,
    p_threshold: float = 0.05,
) -> ValidatorReport:
    """Evaluate every walk-level signal in ``signals`` against realized R.

    For each signal:

    1. Stratify trades using :func:`stratify_by_signal`.
    2. Drop strata with ``n < min_stratum_n``. If fewer than 2 strata
       survive, mark the signal ``INSUFFICIENT_N``.
    3. Run :func:`kruskal_wallis` on the surviving strata.
    4. Bonferroni-correct the raw p across the family of tested signals
       (``p_corrected = min(1, p_raw * family_size)``). Family size is
       the number of signals that produced a tested KW result —
       ``INSUFFICIENT_N`` signals are excluded from the family count.
    5. Compute walk-vs-realized rank consistency.
    6. SURVIVOR iff p_corrected < p_threshold AND direction_consistent.

    Trades missing ``r_multiple`` are silently dropped.

    Returns the full :class:`ValidatorReport`.
    """
    # 1. Filter trades that have a finite realized R.
    valid_trades: list[dict[str, Any]] = []
    for t in trades:
        try:
            r = float(t.get("r_multiple"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(r):
            continue
        valid_trades.append(t)

    # 2. Per-signal stratification + Kruskal-Wallis.
    reports: list[SignalReport] = []
    strata_by_sig: dict[str, list[StratumRow]] = {}
    pending_kw_results: list[
        tuple[str, list[StratumRow], float, int, list[str], Optional[Sequence[str]]]
    ] = []

    for signal in signals:
        if signal not in SIGNAL_REGISTRY:
            reports.append(
                SignalReport(
                    signal=signal,
                    n_strata_tested=0,
                    min_stratum_n=0,
                    kw_h=None,
                    kw_df=None,
                    kw_p_raw=None,
                    kw_p_bonferroni=None,
                    direction_consistent=None,
                    walk_ranking=[],
                    realized_ranking=[],
                    status="INSUFFICIENT_N",
                    notes="unknown signal — not in registry",
                )
            )
            continue

        spec = SIGNAL_REGISTRY[signal]
        walk_ranking = spec.get("walk_ranking")
        # Stratify (keep all strata for stratum_rows, regardless of size).
        strata = stratify_by_signal(valid_trades, signal)
        all_rows = [
            _stratum_summary(signal, label, group)
            for label, group in strata.items()
        ]
        # Sort all_rows by descending mean_r (this is the realized ranking).
        all_rows.sort(key=lambda r: -r.mean_r)
        realized_ranking_full = [r.stratum for r in all_rows]
        # Tag rank positions.
        for idx, row in enumerate(all_rows):
            walk_idx = (
                walk_ranking.index(row.stratum) + 1
                if walk_ranking and row.stratum in walk_ranking
                else None
            )
            object.__setattr__(row, "rank_walk", walk_idx)
            object.__setattr__(row, "rank_realized", idx + 1)
        strata_by_sig[signal] = all_rows
        # Filter to testable strata.
        testable: dict[str, list[float]] = {}
        for label, group in strata.items():
            rs = [
                float(t["r_multiple"])
                for t in group
                if isinstance(t.get("r_multiple"), (int, float))
                and math.isfinite(float(t["r_multiple"]))
            ]
            if len(rs) >= min_stratum_n:
                testable[label] = rs

        if len(testable) < 2:
            min_n = min((len(g) for g in strata.values()), default=0)
            reports.append(
                SignalReport(
                    signal=signal,
                    n_strata_tested=len(testable),
                    min_stratum_n=min_n,
                    kw_h=None,
                    kw_df=None,
                    kw_p_raw=None,
                    kw_p_bonferroni=None,
                    direction_consistent=None,
                    walk_ranking=list(walk_ranking) if walk_ranking else [],
                    realized_ranking=realized_ranking_full,
                    status="INSUFFICIENT_N",
                    notes=(
                        f"only {len(testable)} stratum/strata with n>={min_stratum_n}; "
                        f"observed: { {k: len(v) for k, v in strata.items()} }"
                    ),
                )
            )
            continue

        # Run KW.
        labels_for_kw = list(testable.keys())
        groups_for_kw = [testable[k] for k in labels_for_kw]
        h, p_raw = kruskal_wallis(groups_for_kw)
        # Realized ranking restricted to the testable strata, ordered by mean R.
        means = [(label, sum(g) / len(g)) for label, g in zip(labels_for_kw, groups_for_kw)]
        means.sort(key=lambda x: -x[1])
        realized_ranking_testable = [label for label, _m in means]
        pending_kw_results.append(
            (signal, all_rows, h, len(testable), realized_ranking_testable, walk_ranking)
        )

    # 3. Apply Bonferroni across the tested family.
    family_size = len(pending_kw_results)
    for signal, _rows, h, n_strata, realized_ranking_testable, walk_ranking in pending_kw_results:
        # Re-derive p_raw (kruskal_wallis returns deterministic).
        # We could cache it but recomputing is cheap and keeps the dataflow clear.
        pass

    # Replay with cached p_raw (avoid recompute).
    for signal in signals:
        # Skip already-recorded INSUFFICIENT_N entries.
        if any(r.signal == signal for r in reports):
            continue
        # Find the matching pending entry.
        match = next((p for p in pending_kw_results if p[0] == signal), None)
        if match is None:
            continue  # defensive; shouldn't happen
        sig_name, all_rows, h, n_strata, realized_ranking_testable, walk_ranking = match
        # Compute KW p again from the strata (cheap).
        # We re-extract the testable groups from the strata_by_sig rows.
        spec = SIGNAL_REGISTRY[sig_name]
        strata_full = stratify_by_signal(valid_trades, sig_name)
        testable_groups: list[list[float]] = []
        for label, group in strata_full.items():
            rs = [
                float(t["r_multiple"])
                for t in group
                if isinstance(t.get("r_multiple"), (int, float))
                and math.isfinite(float(t["r_multiple"]))
            ]
            if len(rs) >= min_stratum_n:
                testable_groups.append(rs)
        h_val, p_raw = kruskal_wallis(testable_groups)
        p_bonf = min(1.0, p_raw * max(1, family_size))
        consistent, notes = _is_direction_consistent(walk_ranking, realized_ranking_testable)
        if p_bonf < p_threshold and consistent is True:
            status = "SURVIVOR"
        elif p_bonf < p_threshold and consistent is False:
            status = "NON_PREDICTIVE"
            if not notes:
                notes = "p_bonferroni significant but direction inconsistent"
        elif p_bonf < p_threshold and consistent is None:
            # No a-priori direction — significance alone qualifies as
            # SURVIVOR-style ("strata differ"), but we mark it as
            # NON_PREDICTIVE because the brief requires a direction match.
            status = "NON_PREDICTIVE"
            notes = (notes + "; " if notes else "") + (
                "p_bonferroni significant but no a-priori walk-level direction; "
                "needs domain interpretation"
            )
        else:
            status = "NON_PREDICTIVE"
        min_n_observed = min(
            (
                sum(
                    1
                    for t in group
                    if isinstance(t.get("r_multiple"), (int, float))
                    and math.isfinite(float(t["r_multiple"]))
                )
                for group in strata_full.values()
            ),
            default=0,
        )
        reports.append(
            SignalReport(
                signal=sig_name,
                n_strata_tested=n_strata,
                min_stratum_n=min_n_observed,
                kw_h=h_val,
                kw_df=n_strata - 1,
                kw_p_raw=p_raw,
                kw_p_bonferroni=p_bonf,
                direction_consistent=consistent,
                walk_ranking=list(walk_ranking) if walk_ranking else [],
                realized_ranking=realized_ranking_testable,
                status=status,
                notes=notes,
            )
        )

    return ValidatorReport(
        family_size=family_size,
        n_trades_total=len(valid_trades),
        signals=reports,
        strata_by_signal=strata_by_sig,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
