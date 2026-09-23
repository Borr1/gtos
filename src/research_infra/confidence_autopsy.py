"""B12 — Confidence Scorer Deep Autopsy.

Find ANY conditional under which the AI's ``confidence_score`` is predictive
of realized R.

Why this exists
===============
The headline number in CLAUDE.md (``confidence_filter_mode: shadow``) says
the confidence scorer is useless because **98% of CANDIDATEs receive
confidence=80**. That is the global / live-population read.

B12 zooms one level in. Maybe confidence IS predictive *within specific
strata* — ``(instrument, regime, session, framework, setup_grade,
hour_of_day)``. If we find any stratum where ``Spearman(confidence,
realized_R)`` is meaningfully non-zero AND survives Bonferroni
correction, that stratum becomes a conditional re-deployment candidate.

If we find nothing, B12 supplies the rigorous "scorer is dead" evidence
that the live shadow note relied on intuition for.

Hard rules
==========
* **No AI / Anthropic API calls.** $0 budget. Pure-Python statistics.
* **Read-only inputs.** ``research/**/all_results.json``,
  ``knowledge_base/index/_trade_index.json``,
  ``knowledge_base_backtest/sessions/*.json`` are read-only.
* **No production-code writes.** This module only writes when the
  caller passes an output path; it does NOT touch ``shadow_logs/`` or
  any file under production trading paths.
* **Walk-level vs realized-R discipline** (memory
  ``feedback_walk_level_evidence_not_predictive``) — we test
  Spearman of the AI confidence score against the **realized R** of
  the trade, NOT against any walk-level decision flip.
* **Bonferroni correction** across the strata family. We surface only
  strata with ``|rho| >= rho_threshold AND p_corrected < alpha AND n
  >= min_n``.

Key types
=========
``Trade``
    A single CANDIDATE with realized R + AI confidence + stratification
    axes. Schema::

        {
            "symbol":        str,
            "candle_time":   ISO-8601 UTC str,
            "kill_zone":     "london"|"ny"|"tokyo"|"off"|None,
            "regime":        "trending_bull"|"trending_bear"|"range"
                              |"reversal"|"unclear"|"UNTAGGED"|None,
            "framework":     "ob_retest"|"fvg_fill"|"breaker_re_entry"|None,
            "setup_grade":   "A+"|"A"|"B+"|"C"|None,
            "direction":     "LONG"|"SHORT"|None,
            "hour_of_day":   int (0..23),
            "confidence":    float (the AI's emitted score),
            "r_multiple":    float (realized R),
            "source":        provenance str (debug),
        }

``StratumResult``
    Per-stratum statistical row.

``AutopsyReport``
    Full report: distribution headline + per-stratum results + family
    size + Bonferroni decisions.

Functions
=========
``spearman(x, y)``
    Returns the Spearman rank-order correlation. Pure-Python (uses
    scipy if installed, but does not require it).

``permutation_p_value(x, y, n_perms=1000, seed=1)``
    Two-sided permutation test on Spearman rho. Shuffles ``x`` within
    the supplied series ``n_perms`` times and counts how often the
    shuffled |rho| is >= the observed |rho|. Returns the empirical p.

``bonferroni_correct(p_values, family_size=None)``
    Multiplies each raw p by ``family_size`` (defaults to ``len(p_values)``),
    capping at 1.0.

``stratify_and_test(trades, strata_axes, *, min_n=20, alpha=0.05,
                    rho_threshold=0.2, n_perms=1000, seed=1)``
    Run the full pipeline. Returns an ``AutopsyReport``.

``compute_confidence_distribution(trades)``
    Histogram + mode + mean + fraction at 80 — feeds the report
    headline.

The CLI ``scripts/research/run_b12_confidence_autopsy.py`` consumes this
module and writes ``autopsy.json`` + ``report.md``.
"""

from __future__ import annotations

import logging
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional, Sequence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


# Default strata axes used by ``stratify_and_test`` when the caller passes
# None. We deliberately exclude ``hour_of_day`` from the default cross since
# combining 24 hours × 7 instruments × 5 regimes × 4 sessions × 3 frameworks
# × 4 setup grades blows up the family size to thousands and over-corrects
# every stratum to nothing. The CLI exposes the choice; tests verify both
# the small-family default and a larger one.
DEFAULT_STRATA_AXES: tuple[str, ...] = (
    "symbol",
    "regime",
    "kill_zone",
    "framework",
    "setup_grade",
)


VALID_STRATA_AXES: frozenset[str] = frozenset({
    "symbol",
    "regime",
    "kill_zone",
    "framework",
    "setup_grade",
    "direction",
    "hour_of_day",
})


@dataclass(frozen=True)
class StratumResult:
    """Per-stratum statistical row.

    ``stratum`` is a tuple of (axis_name, axis_value) pairs ordered by
    ``axis_name`` for stable serialization.
    """

    stratum: tuple[tuple[str, Any], ...]
    n: int
    rho: Optional[float]
    raw_p: Optional[float]
    corrected_p: Optional[float]
    flag: str  # "PREDICTIVE" | "NOT_PREDICTIVE" | "INSUFFICIENT_N" | "DEGENERATE"
    note: str = ""

    def to_row(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "stratum": dict(self.stratum),
            "n": self.n,
            "rho": self.rho,
            "raw_p": self.raw_p,
            "corrected_p": self.corrected_p,
            "flag": self.flag,
        }
        if self.note:
            out["note"] = self.note
        return out


@dataclass
class AutopsyReport:
    """Full B12 report.

    ``predictive`` is the filtered list of strata that satisfied the
    threshold gates. ``all_results`` carries every stratum the
    stratifier scanned (including INSUFFICIENT_N and DEGENERATE) so a
    reader can verify nothing was silently dropped.
    """

    distribution: dict[str, Any]
    strata_axes: list[str]
    family_size: int
    min_n: int
    alpha: float
    rho_threshold: float
    n_perms: int
    seed: int
    all_results: list[StratumResult]
    predictive: list[StratumResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "distribution": self.distribution,
            "strata_axes": list(self.strata_axes),
            "family_size": self.family_size,
            "min_n": self.min_n,
            "alpha": self.alpha,
            "rho_threshold": self.rho_threshold,
            "n_perms": self.n_perms,
            "seed": self.seed,
            "all_results": [r.to_row() for r in self.all_results],
            "predictive": [r.to_row() for r in self.predictive],
        }


# ---------------------------------------------------------------------------
# Statistics primitives
# ---------------------------------------------------------------------------


def _ranks(values: Sequence[float]) -> list[float]:
    """Average-rank array (1-based). Ties get the mean of their ranks.

    Pure Python; matches scipy.stats.rankdata default ('average').
    """
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        # Advance j while values are tied with values[indexed[i]].
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        # Average rank in this tied block (1-based positions i+1..j+1).
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank-order correlation coefficient.

    Uses scipy if available (``scipy.stats.spearmanr``) so test results
    match the canonical reference; otherwise falls back to a pure-Python
    Pearson-on-ranks computation.

    Returns ``float('nan')`` when the input is degenerate (n < 2 or zero
    variance on either side after ranking — happens when every value on
    one side is identical, e.g. all confidence == 80).
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must be same length; got {len(x)} vs {len(y)}")
    n = len(x)
    if n < 2:
        return float("nan")
    # Pure-Python path. We use Pearson on the average ranks — this is the
    # textbook tie-handling Spearman.
    rx = _ranks(x)
    ry = _ranks(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    var_x = sum((r - mean_rx) ** 2 for r in rx)
    var_y = sum((r - mean_ry) ** 2 for r in ry)
    if var_x <= 0.0 or var_y <= 0.0:
        return float("nan")
    return cov / math.sqrt(var_x * var_y)


def permutation_p_value(
    x: Sequence[float],
    y: Sequence[float],
    n_perms: int = 1000,
    seed: int = 1,
) -> float:
    """Two-sided permutation p-value for Spearman rho.

    The null hypothesis: rho = 0 (x and y independent). Under the null
    we can shuffle ``x`` (or equivalently ``y``) freely and recompute
    rho. The empirical p is the fraction of shuffles that produced a
    |rho_shuffled| >= |rho_observed|.

    The ``+1`` in numerator and denominator is the standard
    permutation-test correction so the smallest possible p is
    ``1 / (n_perms + 1)`` rather than 0 (which would imply impossible
    certainty). See e.g. Phipson & Smyth 2010.

    Degenerate inputs return p=1.0 (cannot reject the null).
    """
    if len(x) != len(y):
        raise ValueError(f"x and y must be same length; got {len(x)} vs {len(y)}")
    n = len(x)
    if n < 2 or n_perms <= 0:
        return 1.0
    rho_obs = spearman(x, y)
    if math.isnan(rho_obs):
        return 1.0
    abs_obs = abs(rho_obs)

    rng = random.Random(seed)
    x_list = list(x)
    y_list = list(y)
    count = 0
    for _ in range(n_perms):
        rng.shuffle(x_list)
        rho_perm = spearman(x_list, y_list)
        if math.isnan(rho_perm):
            # Degenerate permutation (e.g. all-tie shuffle of constants);
            # treat as |rho_perm| = 0 — does not exceed observed.
            continue
        if abs(rho_perm) >= abs_obs:
            count += 1
    # Phipson-Smyth correction.
    return (count + 1) / (n_perms + 1)


def bonferroni_correct(
    raw_p_values: Sequence[float],
    family_size: Optional[int] = None,
) -> list[float]:
    """Bonferroni-correct a list of raw p-values.

    ``family_size`` defaults to ``len(raw_p_values)``. Pass an explicit
    family size when correcting a SUBSET of a larger family (e.g. only
    the strata that passed n>=min_n; the family includes the ones we
    skipped). NaN p-values pass through unchanged.
    """
    if family_size is None:
        family_size = len(raw_p_values)
    if family_size < 0:
        raise ValueError(f"family_size must be >= 0; got {family_size}")
    out: list[float] = []
    for p in raw_p_values:
        if p is None or (isinstance(p, float) and math.isnan(p)):
            out.append(float("nan"))
            continue
        if family_size == 0:
            # No family — pass through.
            out.append(float(p))
            continue
        out.append(min(1.0, float(p) * family_size))
    return out


# ---------------------------------------------------------------------------
# Distribution headline
# ---------------------------------------------------------------------------


def compute_confidence_distribution(trades: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Histogram + mean + mode + fraction at 80.

    The ``fraction_at_80`` field is the headline-validating number:
    CLAUDE.md asserts ~98% live, but research backtests under Opus
    (``model_used: claude-opus-4-5``) show a different distribution.
    This function does NOT split by model — the CLI emits per-model
    breakdowns when it has the data.
    """
    confidences = [t["confidence"] for t in trades if t.get("confidence") is not None]
    n = len(confidences)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "mode": None,
            "mode_fraction": None,
            "fraction_at_80": None,
            "histogram": {},
        }
    # Round to nearest int for histogram so 79.99/80.0 collapse.
    hist = Counter(int(round(c)) for c in confidences)
    mode_val, mode_count = hist.most_common(1)[0]
    mean_val = sum(confidences) / n
    at_80 = sum(1 for c in confidences if int(round(c)) == 80)
    # Sorted histogram (ints) for deterministic JSON output.
    return {
        "n": n,
        "mean": mean_val,
        "mode": mode_val,
        "mode_fraction": mode_count / n,
        "fraction_at_80": at_80 / n,
        "histogram": dict(sorted(hist.items())),
    }


# ---------------------------------------------------------------------------
# Stratification + testing
# ---------------------------------------------------------------------------


def _normalize_stratum_value(axis: str, value: Any) -> Any:
    """Normalize an axis value for stratification.

    ``hour_of_day`` is taken as-is (assumed already int 0..23).
    Everything else lower-cases strings, leaves None as None.
    """
    if value is None:
        return None
    if axis == "hour_of_day":
        try:
            h = int(value)
        except (TypeError, ValueError):
            return None
        if 0 <= h <= 23:
            return h
        return None
    if isinstance(value, str):
        return value.strip().lower() or None
    return value


def _stratum_key(trade: dict[str, Any], axes: Sequence[str]) -> tuple[tuple[str, Any], ...]:
    """Build the canonical (sorted) stratum key for a trade."""
    parts: list[tuple[str, Any]] = []
    for axis in sorted(axes):
        if axis not in VALID_STRATA_AXES:
            raise ValueError(
                f"unknown axis {axis!r}; valid: {sorted(VALID_STRATA_AXES)}"
            )
        parts.append((axis, _normalize_stratum_value(axis, trade.get(axis))))
    return tuple(parts)


def _filter_valid_trades(trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only trades that have BOTH a non-None confidence AND r_multiple."""
    out: list[dict[str, Any]] = []
    for t in trades:
        c = t.get("confidence")
        r = t.get("r_multiple")
        if c is None or r is None:
            continue
        try:
            float(c)
            float(r)
        except (TypeError, ValueError):
            continue
        out.append(t)
    return out


def stratify_and_test(
    trades: Sequence[dict[str, Any]],
    strata_axes: Optional[Sequence[str]] = None,
    *,
    min_n: int = 20,
    alpha: float = 0.05,
    rho_threshold: float = 0.2,
    n_perms: int = 1000,
    seed: int = 1,
) -> AutopsyReport:
    """Run B12 end-to-end.

    Parameters
    ----------
    trades:
        Sequence of trade dicts (see module docstring schema).
    strata_axes:
        Iterable of axes to stratify by. Defaults to ``DEFAULT_STRATA_AXES``.
    min_n:
        Minimum sample size for a stratum to be tested. Below this we
        emit ``INSUFFICIENT_N`` rather than reporting an unstable rho.
    alpha:
        Significance threshold AFTER Bonferroni correction.
    rho_threshold:
        Minimum |Spearman rho| to consider a stratum predictive.
    n_perms:
        Permutation count for the empirical p-value.
    seed:
        Seed for the permutation RNG.

    Returns
    -------
    ``AutopsyReport`` carrying the headline distribution + every
    stratum (with flags) + the filtered predictive subset.

    Notes
    -----
    * Bonferroni family = strata with n>=min_n that we actually
      tested. Strata flagged INSUFFICIENT_N or DEGENERATE are NOT
      counted in the family — they didn't burn a test.
    """
    if strata_axes is None:
        strata_axes = DEFAULT_STRATA_AXES
    axes = list(strata_axes)
    if not axes:
        raise ValueError("strata_axes must be non-empty")
    for a in axes:
        if a not in VALID_STRATA_AXES:
            raise ValueError(
                f"unknown axis {a!r}; valid: {sorted(VALID_STRATA_AXES)}"
            )

    valid = _filter_valid_trades(trades)
    distribution = compute_confidence_distribution(valid)

    # Group by stratum key.
    groups: dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]] = {}
    for t in valid:
        key = _stratum_key(t, axes)
        groups.setdefault(key, []).append(t)

    # First pass: compute raw rho + (placeholder) raw p for testable strata
    # so we know the family size for Bonferroni correction. INSUFFICIENT_N
    # and DEGENERATE strata are recorded but excluded from the family.
    pre_results: list[tuple[StratumResult, Optional[float]]] = []
    family_indices: list[int] = []  # indices into pre_results that are in the family

    # Sort with a None-safe key so axis values that came in as None (e.g.
    # regime=None for sources that don't tag regime, kill_zone=None for
    # backtest-session rows) don't crash the sort. We coerce Nones to
    # ("", None) so they sort first (empty string < any string).
    def _sort_key(item: tuple[tuple[tuple[str, Any], ...], list[dict[str, Any]]]) -> tuple:
        return tuple(
            ("" if v is None else str(v), v) for _axis, v in item[0]
        )

    for key, members in sorted(groups.items(), key=_sort_key):
        n = len(members)
        if n < min_n:
            pre_results.append(
                (
                    StratumResult(
                        stratum=key,
                        n=n,
                        rho=None,
                        raw_p=None,
                        corrected_p=None,
                        flag="INSUFFICIENT_N",
                        note=f"n={n} < min_n={min_n}",
                    ),
                    None,
                )
            )
            continue
        x = [float(m["confidence"]) for m in members]
        y = [float(m["r_multiple"]) for m in members]
        rho = spearman(x, y)
        if math.isnan(rho):
            pre_results.append(
                (
                    StratumResult(
                        stratum=key,
                        n=n,
                        rho=None,
                        raw_p=None,
                        corrected_p=None,
                        flag="DEGENERATE",
                        note="zero variance in confidence or r_multiple",
                    ),
                    None,
                )
            )
            continue
        raw_p = permutation_p_value(x, y, n_perms=n_perms, seed=seed)
        # Mark in family.
        family_indices.append(len(pre_results))
        pre_results.append(
            (
                StratumResult(
                    stratum=key,
                    n=n,
                    rho=rho,
                    raw_p=raw_p,
                    corrected_p=None,  # filled in below
                    flag="PENDING",
                ),
                raw_p,
            )
        )

    family_size = len(family_indices)

    # Second pass: Bonferroni correction across the family of TESTED strata.
    raw_ps_in_family = [pre_results[i][1] for i in family_indices]
    corrected = bonferroni_correct(raw_ps_in_family, family_size=family_size)
    family_iter = iter(zip(family_indices, corrected))
    final: list[StratumResult] = []
    for idx, (result, _raw_p) in enumerate(pre_results):
        if result.flag != "PENDING":
            final.append(result)
            continue
        family_idx, corrected_p = next(family_iter)
        assert family_idx == idx
        rho = result.rho if result.rho is not None else float("nan")
        is_predictive = (
            abs(rho) >= rho_threshold
            and corrected_p is not None
            and not math.isnan(corrected_p)
            and corrected_p < alpha
        )
        final.append(
            StratumResult(
                stratum=result.stratum,
                n=result.n,
                rho=result.rho,
                raw_p=result.raw_p,
                corrected_p=corrected_p,
                flag="PREDICTIVE" if is_predictive else "NOT_PREDICTIVE",
                note=result.note,
            )
        )

    # Sanity: we should have exhausted the family iterator.
    assert next(family_iter, None) is None

    predictive = [r for r in final if r.flag == "PREDICTIVE"]
    # Sort predictive by |rho| desc, then by corrected_p asc.
    predictive.sort(
        key=lambda r: (-abs(r.rho or 0.0), r.corrected_p or 1.0)
    )

    return AutopsyReport(
        distribution=distribution,
        strata_axes=axes,
        family_size=family_size,
        min_n=min_n,
        alpha=alpha,
        rho_threshold=rho_threshold,
        n_perms=n_perms,
        seed=seed,
        all_results=final,
        predictive=predictive,
    )
