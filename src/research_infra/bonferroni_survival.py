"""K52 — Bonferroni-Survival Re-Test of GTOS Validated Numbers.

Re-run the statistical tests behind the five Bonferroni-surviving findings in
``CLAUDE.md`` against the current 2-year dataset. Confirms which findings still
survive after the H2-2026 decay.

Strategic question
------------------
Five baseline findings each carry a per-test raw p-value and a Bonferroni-
corrected p-value computed at the time the headline numbers were minted.
Do they still survive Bonferroni correction at the current dataset?

If they don't, the Validated Numbers in CLAUDE.md are stale. If they do, the
decay is concentrated in instruments / conditions outside those five.

Methodology
-----------
For each baseline finding we instantiate a ``TestSpec`` declaring:

- ``test_kind`` — one of ``binomial_one_sample`` (WR vs breakeven) or
  ``two_sample_wr`` (OB-zone vs baseline pullback; FVG-in-impulse vs non-FVG).
- A ``populate(data) -> dict`` callable that returns the test's raw inputs
  (wins / n / p_null, or wins_a/n_a/wins_b/n_b) drawn from the current
  dataset.
- ``baseline_*`` numbers literally from CLAUDE.md so the report can show
  side-by-side H1 vs current.

The family size for Bonferroni is **always 5** — five independent baseline
findings — regardless of how many of those tests can actually be run on the
current data. This is the canonical pre-registered family size from the
original validation work.

This module is pure-Python (uses only ``math``/``statistics``/``json``).
No third-party dependencies — same constraints as the rest of
``src/research_infra``.

Inputs
------
The ``data`` dict consumed by ``evaluate_survival`` is shaped:

    {
        "xau_ob_retest": {
            # Only filled trades (real broker fills with realized R).
            "filled_trades": [{"r": float}, ...],
            "wins": int,    # wins / total breakdown if pre-aggregated
            "n":    int,
        },
        "us30_ob_retest": {...},
        "usdjpy_ob_retest": {...},
        "ob_zone_vs_baseline_80pct": {
            "ob_wins":   int,  "ob_n":   int,
            "base_wins": int,  "base_n": int,
        },
        "fvg_in_impulse_per_instrument": {
            # Per-instrument FVG-in-impulse vs non-FVG OB outcomes.
            "<INSTRUMENT>": {"fvg_wins": int, "fvg_n": int,
                             "non_wins": int, "non_n": int},
        },
    }

The ``run_k52_bonferroni_survival.py`` CLI builds this dict from the canonical
realized-R sources (``trades_unified.csv`` + ``_trade_index.json`` +
``knowledge_base_backtest/sessions/``) and the structural-WR scorecard.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

# ────────────────────────────────────────────────────────────────────────────
# Public dataclasses
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TestSpec:
    """Specification for a single baseline finding in the survival family.

    Attributes
    ----------
    key : str
        Stable identifier (used as dict key and in the report).
    label : str
        Human-readable name (e.g. "XAUUSD WR vs breakeven").
    test_kind : str
        One of ``binomial_one_sample`` or ``two_sample_wr``.
    p_null : float
        Null-hypothesis probability for one-sample binomial. Always 0.5
        for "WR vs breakeven" tests. Ignored for two-sample.
    baseline_n : int
        n at original validation time.
    baseline_wins : int
        wins at original validation time (one-sample) — None for
        two-sample.
    baseline_raw_p : float
        Raw p reported in CLAUDE.md / validated-numbers caveats. Used
        purely for side-by-side reporting (no recomputation).
    baseline_corrected_p : float
        Corrected p reported in CLAUDE.md (raw_p × family_size, capped 1).
    populate : Callable
        ``(data: dict) -> dict | None`` — returns the per-test inputs
        from the current dataset. Returns ``None`` when the test cannot
        be run (e.g. no realized-R data for a given instrument).
    description : str
        One-sentence description of the test (printed in the report).
    """

    key: str
    label: str
    test_kind: str
    p_null: float
    baseline_n: int
    baseline_raw_p: float
    baseline_corrected_p: float
    populate: Callable[[dict], dict | None]
    description: str
    baseline_wins: int | None = None
    baseline_extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TestResult:
    """Per-test result row in a SurvivalReport.

    Attributes
    ----------
    spec_key : str
    spec_label : str
    baseline_raw_p : float
    baseline_corrected_p : float
    current_n : int
        Total sample size (one-sample: n; two-sample: n_a + n_b). 0 if
        the test could not be run.
    current_raw_p : float
        Raw p computed on current data. NaN when test not runnable or
        n below floor.
    current_corrected_p : float
        ``min(1, current_raw_p × family_size)``.
    current_summary : dict
        Per-test summary fields (e.g. ``{"wins": k, "n": n, "wr": ...}``
        for one-sample, ``{"wr_a":..., "wr_b":..., "delta_pp":...}`` for
        two-sample).
    status : str
        One of ``SURVIVES``, ``FAILS``, ``INSUFFICIENT_N``, ``NO_DATA``.
    notes : str
        Brief reasoning for the verdict.
    """

    spec_key: str
    spec_label: str
    baseline_raw_p: float
    baseline_corrected_p: float
    current_n: int
    current_raw_p: float
    current_corrected_p: float
    current_summary: dict
    status: str
    notes: str = ""


@dataclass(frozen=True)
class SurvivalReport:
    """Top-level evaluation result.

    Attributes
    ----------
    family_size : int
        Number of baseline findings (always 5 for the canonical K52 family).
    alpha : float
        Significance threshold applied to the *corrected* p-value.
    n_min : int
        Minimum total trades for a non-INSUFFICIENT_N verdict.
    results : list[TestResult]
        Per-finding outcomes, in spec order.
    surviving : list[str]
        Spec keys with status SURVIVES.
    failed : list[str]
        Spec keys with status FAILS.
    insufficient : list[str]
        Spec keys with status INSUFFICIENT_N or NO_DATA.
    """

    family_size: int
    alpha: float
    n_min: int
    results: tuple[TestResult, ...]
    surviving: tuple[str, ...]
    failed: tuple[str, ...]
    insufficient: tuple[str, ...]


# ────────────────────────────────────────────────────────────────────────────
# Pure statistical primitives
# ────────────────────────────────────────────────────────────────────────────

def _log_binomial_coeff(n: int, k: int) -> float:
    """log(C(n, k)) via lgamma — stable for large n."""
    if k < 0 or k > n:
        return float("-inf")
    return (
        math.lgamma(n + 1.0)
        - math.lgamma(k + 1.0)
        - math.lgamma(n - k + 1.0)
    )


def _binomial_pmf(n: int, k: int, p: float) -> float:
    """Probability mass at k under Binomial(n, p)."""
    if not (0 <= k <= n):
        return 0.0
    if p <= 0:
        return 1.0 if k == 0 else 0.0
    if p >= 1:
        return 1.0 if k == n else 0.0
    log_pmf = (
        _log_binomial_coeff(n, k)
        + k * math.log(p)
        + (n - k) * math.log(1.0 - p)
    )
    return math.exp(log_pmf)


def binomial_test(wins: int, n: int, p_null: float) -> float:
    """Two-sided exact binomial test.

    Returns the probability under H0 of an outcome at least as extreme
    (in the small-tail / total-probability sense) as ``wins`` out of ``n``,
    given true success probability ``p_null``.

    Method: sum over all k in [0, n] where Binomial(n, p_null) PMF at k is
    ≤ PMF at the observed wins. This is the "minimum likelihood" two-sided
    convention used by ``scipy.stats.binom_test`` when the null is asymmetric
    (or symmetric — at p_null=0.5 it reduces to the symmetric two-sided).

    Edge cases:
      - ``n == 0`` → returns NaN.
      - ``p_null in {0, 1}`` → returns 0.0 if observed wins matches p_null
        exactly, else 1.0.

    Hand-verified for k=8, n=10, p_null=0.5 → 0.10937500 (see tests).
    """
    if n <= 0:
        return float("nan")
    if not (0 <= wins <= n):
        raise ValueError(f"wins must be in [0, n]; got wins={wins}, n={n}")
    if not (0.0 <= p_null <= 1.0):
        raise ValueError(f"p_null must be in [0, 1]; got {p_null}")

    # Trivial-null branches
    if p_null == 0.0:
        return 1.0 if wins > 0 else 1.0
    if p_null == 1.0:
        return 1.0 if wins < n else 1.0

    observed_pmf = _binomial_pmf(n, wins, p_null)
    # Numerical guard: include all k whose PMF is "approximately" ≤ observed.
    # 1e-12 relative slack avoids dropping the symmetric counterpart at
    # p_null = 0.5 due to float roundoff.
    tol = observed_pmf * 1e-12 + 1e-300
    total = 0.0
    for k in range(n + 1):
        pmf = _binomial_pmf(n, k, p_null)
        if pmf <= observed_pmf + tol:
            total += pmf
    return min(1.0, max(0.0, total))


def _norm_cdf(x: float) -> float:
    """Standard-normal CDF via erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_sample_wr_test(
    wins_a: int,
    n_a: int,
    wins_b: int,
    n_b: int,
) -> float:
    """Two-proportion z-test (two-sided).

    Tests H0: p_a == p_b, against H1: p_a != p_b. Pooled-variance
    statistic:

        z = (p_a - p_b) / sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
        p-value = 2 * (1 - Phi(|z|))

    where p_pool = (wins_a + wins_b) / (n_a + n_b).

    Edge cases:
      - Either n is 0 → NaN.
      - p_pool is 0 or 1 (no variance) → returns 1.0 (cannot reject).
      - Identical observed proportions → p == 1.0.
    """
    if n_a <= 0 or n_b <= 0:
        return float("nan")
    if not (0 <= wins_a <= n_a) or not (0 <= wins_b <= n_b):
        raise ValueError(
            f"wins must be in [0, n] per side; got "
            f"wins_a={wins_a}/n_a={n_a}, wins_b={wins_b}/n_b={n_b}"
        )
    p_a = wins_a / n_a
    p_b = wins_b / n_b
    p_pool = (wins_a + wins_b) / (n_a + n_b)
    var = p_pool * (1.0 - p_pool) * (1.0 / n_a + 1.0 / n_b)
    if var <= 0.0 or not math.isfinite(var):
        return 1.0
    z = (p_a - p_b) / math.sqrt(var)
    if not math.isfinite(z):
        return 1.0
    # Two-sided
    return min(1.0, max(0.0, 2.0 * (1.0 - _norm_cdf(abs(z)))))


def bonferroni_correct(p_values: list[float]) -> list[float]:
    """Apply Bonferroni correction across a family of raw p-values.

    Returns ``[min(1.0, p * len(p_values))]`` with ``NaN`` propagated
    unchanged. Always uses ``len(p_values)`` as the family size — caller
    is responsible for picking the right family. This module's
    canonical family size for K52 is always 5 (see ``TEST_REGISTRY``).

    Examples
    --------
    >>> bonferroni_correct([0.01, 0.5, 0.001, 0.1, 0.3])
    [0.05, 1.0, 0.005, 0.5, 1.0]

    >>> bonferroni_correct([0.0])
    [0.0]

    >>> import math
    >>> [math.isnan(p) for p in bonferroni_correct([float('nan'), 0.1])]
    [True, False]
    """
    n = len(p_values)
    if n <= 0:
        return []
    out: list[float] = []
    for p in p_values:
        if p is None or (isinstance(p, float) and math.isnan(p)):
            out.append(float("nan"))
        else:
            out.append(min(1.0, max(0.0, float(p) * n)))
    return out


# ────────────────────────────────────────────────────────────────────────────
# Test populators (consume the data dict assembled by the CLI)
# ────────────────────────────────────────────────────────────────────────────

def _wins_from_filled(filled: list[dict]) -> tuple[int, int]:
    """Count (wins, n) where a win is r > 0.

    Treats BE / exact-zero R as a loss, matching the WR convention used
    throughout GTOS validated numbers (XAUUSD 62% etc).
    """
    wins = 0
    n = 0
    for t in filled or []:
        r = t.get("r")
        if r is None or not isinstance(r, (int, float)) or not math.isfinite(r):
            continue
        n += 1
        if r > 0:
            wins += 1
    return wins, n


def _populate_one_sample_wr(data_key: str) -> Callable[[dict], dict | None]:
    """Build a one-sample binomial WR-vs-breakeven populator."""
    def _populate(data: dict) -> dict | None:
        block = data.get(data_key)
        if not isinstance(block, dict):
            return None
        # Prefer pre-aggregated wins/n
        if "wins" in block and "n" in block:
            wins = int(block["wins"])
            n = int(block["n"])
        else:
            filled = block.get("filled_trades")
            if not isinstance(filled, list):
                return None
            wins, n = _wins_from_filled(filled)
        if n <= 0:
            return None
        return {"wins": wins, "n": n}
    return _populate


def _populate_two_sample_ob_zone(data: dict) -> dict | None:
    block = data.get("ob_zone_vs_baseline_80pct")
    if not isinstance(block, dict):
        return None
    keys = ("ob_wins", "ob_n", "base_wins", "base_n")
    if not all(k in block for k in keys):
        return None
    n_a = int(block["ob_n"])
    n_b = int(block["base_n"])
    if n_a <= 0 or n_b <= 0:
        return None
    return {
        "wins_a": int(block["ob_wins"]),
        "n_a": n_a,
        "wins_b": int(block["base_wins"]),
        "n_b": n_b,
    }


def _populate_fvg_in_impulse(data: dict) -> dict | None:
    """Aggregate FVG-in-impulse vs non-FVG-OB across instruments.

    The original CLAUDE.md finding is "+7-20pp across 6 instruments,
    6/6 positive, p=0.0156 from sign-test". Re-tested as a pooled
    two-sample z-test on the union: pool wins_a / n_a (FVG-in-impulse)
    and wins_b / n_b (non-FVG OB) across all available instruments.

    The stricter sign-style test (number of instruments with positive
    delta out of n_tested) is reported in the summary alongside the
    pooled z-test result. The headline raw p from CLAUDE.md (<0.016)
    is the sign-test result; we recompute both to keep the comparison
    honest and report the pooled-z p as the primary current_raw_p so
    the family stays type-consistent (all numeric two-proportion tests).
    """
    block = data.get("fvg_in_impulse_per_instrument")
    if not isinstance(block, dict) or not block:
        return None
    pooled_wins_a = 0
    pooled_n_a = 0
    pooled_wins_b = 0
    pooled_n_b = 0
    per_instrument: list[dict] = []
    for sym, sub in block.items():
        if not isinstance(sub, dict):
            continue
        try:
            fvg_wins = int(sub.get("fvg_wins", 0))
            fvg_n = int(sub.get("fvg_n", 0))
            non_wins = int(sub.get("non_wins", 0))
            non_n = int(sub.get("non_n", 0))
        except (TypeError, ValueError):
            continue
        if fvg_n <= 0 or non_n <= 0:
            continue
        pooled_wins_a += fvg_wins
        pooled_n_a += fvg_n
        pooled_wins_b += non_wins
        pooled_n_b += non_n
        per_instrument.append({
            "symbol": sym,
            "fvg_wr": fvg_wins / fvg_n,
            "non_wr": non_wins / non_n,
            "delta_pp": (fvg_wins / fvg_n - non_wins / non_n) * 100.0,
            "fvg_n": fvg_n,
            "non_n": non_n,
        })
    if pooled_n_a <= 0 or pooled_n_b <= 0:
        return None
    return {
        "wins_a": pooled_wins_a,
        "n_a": pooled_n_a,
        "wins_b": pooled_wins_b,
        "n_b": pooled_n_b,
        "per_instrument": per_instrument,
    }


# ────────────────────────────────────────────────────────────────────────────
# TEST_REGISTRY — five canonical baseline findings
# ────────────────────────────────────────────────────────────────────────────

# Family size for the K52 re-test is fixed at 5 (the five Bonferroni-surviving
# baseline findings). Every TEST_REGISTRY entry is ALWAYS counted in the
# Bonferroni divisor regardless of whether its current-data populate() returns
# inputs — so a test that drops to NO_DATA still consumes its α/5 share. This
# is the conservative pre-registered choice: the family is the family of
# *baseline claims* not the family of *currently-runnable claims*.
FAMILY_SIZE = 5

TEST_REGISTRY: tuple[TestSpec, ...] = (
    TestSpec(
        key="xau_wr_vs_be",
        label="XAUUSD WR vs breakeven",
        test_kind="binomial_one_sample",
        p_null=0.5,
        baseline_n=129,
        baseline_wins=80,  # 62.0% × 129 ≈ 80
        baseline_raw_p=6.84e-09,  # 3.42e-08 / 5 → headline corrected ÷ family
        baseline_corrected_p=3.42e-08,
        populate=_populate_one_sample_wr("xau_ob_retest"),
        description=(
            "One-sample exact binomial test of XAUUSD realised-R win rate "
            "against the 50% breakeven null. Baseline n=129 from "
            "Oct 2025–Mar 2026 batch."
        ),
    ),
    TestSpec(
        key="ob_zone_advantage",
        label="OB zone advantage +17pp vs 80% pullback",
        test_kind="two_sample_wr",
        p_null=float("nan"),
        baseline_n=219 + 219,  # OB n + 80%-baseline n on the same population
        baseline_raw_p=6.0e-04,  # 0.003 / 5
        baseline_corrected_p=0.003,
        populate=_populate_two_sample_ob_zone,
        description=(
            "Two-proportion z-test of OB-zone simulated WR vs 80%-retrace "
            "baseline simulated WR on the 219 BOS-event population from the "
            "Test A rerun (`.context/03_analysis/test_a_rerun_real_bos_results.md`)."
        ),
    ),
    TestSpec(
        key="us30_wr_vs_be",
        label="US30 WR vs breakeven",
        test_kind="binomial_one_sample",
        p_null=0.5,
        baseline_n=41,
        baseline_wins=24,  # 58.5% × 41 ≈ 24
        baseline_raw_p=1.668e-03,  # 8.34e-03 / 5
        baseline_corrected_p=8.34e-03,
        populate=_populate_one_sample_wr("us30_ob_retest"),
        description=(
            "One-sample exact binomial test of US30 realised-R win rate "
            "against the 50% breakeven null. Baseline n=41 from batch."
        ),
    ),
    TestSpec(
        key="usdjpy_wr_vs_be",
        label="USDJPY WR vs breakeven",
        test_kind="binomial_one_sample",
        p_null=0.5,
        baseline_n=33,
        baseline_wins=25,  # 75.8% × 33 ≈ 25
        baseline_raw_p=3.92e-05,  # 1.96e-04 / 5
        baseline_corrected_p=1.96e-04,
        populate=_populate_one_sample_wr("usdjpy_ob_retest"),
        description=(
            "One-sample exact binomial test of USDJPY realised-R win rate "
            "against the 50% breakeven null. Baseline n=33 from batch."
        ),
    ),
    TestSpec(
        key="fvg_in_impulse",
        label="FVG-in-impulse signal across 6 instruments",
        test_kind="two_sample_wr",
        p_null=float("nan"),
        baseline_n=0,  # not pre-aggregated in CLAUDE.md
        baseline_raw_p=0.0156,  # one-sided 6/6 sign-test (CLAUDE.md cite: <0.016)
        baseline_corrected_p=0.0780,  # 0.0156 × 5 ≈ 0.078 (K52 family-size-5)
        populate=_populate_fvg_in_impulse,
        description=(
            "Pooled two-proportion z-test of FVG-in-impulse OB WR vs non-FVG OB WR "
            "across all instruments with structural-WR data. The original "
            "CLAUDE.md citation is a 6/6 sign-test (p≈1.56%) over per-instrument "
            "deltas; the per-instrument deltas + sign-test count are reported "
            "in the summary alongside the pooled-z p."
        ),
    ),
)


# ────────────────────────────────────────────────────────────────────────────
# evaluate_survival — main entry point
# ────────────────────────────────────────────────────────────────────────────

def _classify_status(
    inputs: dict | None,
    raw_p: float,
    corrected_p: float,
    *,
    n_total: int,
    n_min: int,
    alpha: float,
) -> tuple[str, str]:
    """Decide SURVIVES / FAILS / INSUFFICIENT_N / NO_DATA + reasoning string."""
    if inputs is None:
        return (
            "NO_DATA",
            f"No current-data inputs available for this test "
            "(populate() returned None — typically means the realized-R "
            "data is missing for this instrument).",
        )
    if n_total < n_min:
        return (
            "INSUFFICIENT_N",
            f"n={n_total} below floor n_min={n_min}; refuses to claim "
            "significance at small samples (Agent Reliability Rule 6).",
        )
    if not math.isfinite(raw_p) or not math.isfinite(corrected_p):
        return (
            "INSUFFICIENT_N",
            f"Test returned non-finite p (raw={raw_p}, corrected={corrected_p}). "
            "Treat as INSUFFICIENT_N.",
        )
    if corrected_p < alpha:
        return (
            "SURVIVES",
            f"Corrected p = {corrected_p:.4g} < α = {alpha} → survives.",
        )
    return (
        "FAILS",
        f"Corrected p = {corrected_p:.4g} ≥ α = {alpha} → fails Bonferroni.",
    )


def _run_one_sample(spec: TestSpec, inputs: dict) -> tuple[float, dict]:
    wins = int(inputs["wins"])
    n = int(inputs["n"])
    raw_p = binomial_test(wins, n, spec.p_null)
    summary = {
        "wins": wins,
        "n": n,
        "wr": (wins / n) if n > 0 else float("nan"),
        "p_null": spec.p_null,
    }
    return raw_p, summary


def _run_two_sample(spec: TestSpec, inputs: dict) -> tuple[float, dict]:
    wins_a = int(inputs["wins_a"])
    n_a = int(inputs["n_a"])
    wins_b = int(inputs["wins_b"])
    n_b = int(inputs["n_b"])
    raw_p = two_sample_wr_test(wins_a, n_a, wins_b, n_b)
    wr_a = (wins_a / n_a) if n_a > 0 else float("nan")
    wr_b = (wins_b / n_b) if n_b > 0 else float("nan")
    summary: dict = {
        "wins_a": wins_a,
        "n_a": n_a,
        "wr_a": wr_a,
        "wins_b": wins_b,
        "n_b": n_b,
        "wr_b": wr_b,
        "delta_pp": (wr_a - wr_b) * 100.0 if math.isfinite(wr_a) and math.isfinite(wr_b) else float("nan"),
    }
    # Pass through optional FVG sign-test detail
    if "per_instrument" in inputs:
        per_inst = inputs["per_instrument"]
        n_pos = sum(1 for r in per_inst if r.get("delta_pp", 0) > 0)
        summary["per_instrument"] = per_inst
        summary["sign_test_n_positive"] = n_pos
        summary["sign_test_n_total"] = len(per_inst)
        # Two-sided sign-test under p=0.5
        if per_inst:
            summary["sign_test_raw_p"] = binomial_test(n_pos, len(per_inst), 0.5)
        else:
            summary["sign_test_raw_p"] = float("nan")
    return raw_p, summary


def evaluate_survival(
    test_specs: list[TestSpec] | tuple[TestSpec, ...],
    data: dict,
    *,
    family_size: int | None = None,
    alpha: float = 0.05,
    n_min: int = 20,
) -> SurvivalReport:
    """Re-evaluate each TestSpec on ``data`` and apply Bonferroni.

    Parameters
    ----------
    test_specs : iterable of TestSpec
        The family of baseline findings (typically ``TEST_REGISTRY``).
    data : dict
        Per-test current-data inputs. Layout is documented in the module
        docstring.
    family_size : int, optional
        Bonferroni divisor. Default = ``len(test_specs)`` so the K52
        canonical 5-test family auto-corrects at 5×. Pass an explicit
        value to test a different convention.
    alpha : float, default 0.05
        Significance threshold applied to the corrected p-value.
    n_min : int, default 20
        Minimum n for a non-INSUFFICIENT_N verdict.

    Returns
    -------
    SurvivalReport
    """
    specs = tuple(test_specs)
    if family_size is None:
        family_size = max(1, len(specs))

    raw_results: list[tuple[TestSpec, dict | None, float, dict, int]] = []
    raw_p_values: list[float] = []
    for spec in specs:
        try:
            inputs = spec.populate(data)
        except Exception as exc:
            inputs = None
            raw_p = float("nan")
            summary = {"populate_error": repr(exc)}
            n_total = 0
            raw_results.append((spec, inputs, raw_p, summary, n_total))
            raw_p_values.append(raw_p)
            continue

        if inputs is None:
            raw_p = float("nan")
            summary = {}
            n_total = 0
        elif spec.test_kind == "binomial_one_sample":
            raw_p, summary = _run_one_sample(spec, inputs)
            n_total = int(inputs.get("n", 0))
        elif spec.test_kind == "two_sample_wr":
            raw_p, summary = _run_two_sample(spec, inputs)
            n_total = int(inputs.get("n_a", 0)) + int(inputs.get("n_b", 0))
        else:
            raise ValueError(f"unknown test_kind: {spec.test_kind!r}")
        raw_results.append((spec, inputs, raw_p, summary, n_total))
        raw_p_values.append(raw_p)

    # Bonferroni-correct using the explicit family_size (independent of
    # how many were runnable). bonferroni_correct uses len(p_values) as
    # divisor — call it directly with a list of length family_size by
    # padding NaN slots if the caller chose a smaller list, but our spec
    # is to use family_size literally.
    corrected: list[float] = []
    for p in raw_p_values:
        if isinstance(p, float) and math.isnan(p):
            corrected.append(float("nan"))
        else:
            corrected.append(min(1.0, max(0.0, float(p) * family_size)))

    results: list[TestResult] = []
    surviving: list[str] = []
    failed: list[str] = []
    insufficient: list[str] = []
    for (spec, inputs, raw_p, summary, n_total), corr_p in zip(raw_results, corrected):
        status, notes = _classify_status(
            inputs, raw_p, corr_p,
            n_total=n_total, n_min=n_min, alpha=alpha,
        )
        results.append(TestResult(
            spec_key=spec.key,
            spec_label=spec.label,
            baseline_raw_p=spec.baseline_raw_p,
            baseline_corrected_p=spec.baseline_corrected_p,
            current_n=n_total,
            current_raw_p=raw_p,
            current_corrected_p=corr_p,
            current_summary=summary,
            status=status,
            notes=notes,
        ))
        if status == "SURVIVES":
            surviving.append(spec.key)
        elif status == "FAILS":
            failed.append(spec.key)
        else:
            insufficient.append(spec.key)

    return SurvivalReport(
        family_size=family_size,
        alpha=alpha,
        n_min=n_min,
        results=tuple(results),
        surviving=tuple(surviving),
        failed=tuple(failed),
        insufficient=tuple(insufficient),
    )
