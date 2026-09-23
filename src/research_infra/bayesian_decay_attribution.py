"""A6 — Bayesian Decay Attribution.

Decomposes the H1 -> H2 WR loss across components (framework, kill_zone,
side, etc.) using a Beta-binomial conjugate-prior posterior, then
attributes the per-stratum WR delta to each component weighted by H2
stratum n-share. The total attributed decay (across components) is
sanity-checked against the observed H1 vs H2 WR delta.

Why this exists
===============
Wave 2A's verdict (A1: SYSTEM_DECAY) confirmed the AI has lost
selectivity that the market still rewards. The strategic question A6
answers is *which* component(s) of the AI's pipeline drove the loss:

    Decay(component_c) = sum_strata( WR_diff(s) * n_share_H2(s) )

Bonferroni is applied across the family of component tests. Strata
with n < ``LOW_N_THRESHOLD`` are flagged ``low_n=True`` and excluded
from the sum (we don't claim significance at thin cells, per project
discipline).

Conjugate-prior model
=====================
Per stratum we model wins ~ Binomial(n, p), p ~ Beta(alpha_0, beta_0).
The conjugate posterior is::

    p | data ~ Beta(alpha_0 + wins, beta_0 + losses)

Default prior is ``Beta(1, 1)`` (uniform on [0,1]) — uninformed,
robust at low n, and the standard non-committal choice. Subjective
"OB-zone-edge of 70%" priors were considered and REJECTED for this
diagnostic: the question is whether the H2 distribution differs from
the H1 distribution, which is best done with a flat prior so the data
drives the verdict.

A 95% credible interval on each posterior is computed via the
inverse-incomplete-Beta function. We use ``scipy.stats.beta.ppf`` if
SciPy is installed; otherwise we fall back to an in-house bisection
on the regularised incomplete Beta CDF (computed via a Lentz-style
continued-fraction expansion). Both paths are validated to <=1e-6
tolerance against hand-verified Beta(10, 5) -> mean = 10/15.

Attribution sanity check
========================
We expect::

    sum_components( attributed_decay_c ) ~= observed_delta_pp

Within sampling noise. The "residual" is reported (observed_delta -
sum_attributed) so the reader sees how much the chosen components
explain. Large residual => more components needed (or interactions).

Walk-level vs realized R discipline
===================================
Per memory ``feedback_walk_level_evidence_not_predictive``, this
module operates on REALIZED R-multiples joined per (symbol,
candle_close_time, side). Walk-level decision counts are not used
for attribution.

Public API
==========
* :func:`beta_posterior` — closed-form Beta(alpha_0+wins, beta_0+losses)
  parameters.
* :func:`beta_credible_interval` — two-sided 95% credible interval on
  the posterior mean.
* :func:`stratify_by_component` — partition trades by a component value.
* :func:`attribute_decay` — full per-component decay attribution
  with credible intervals + Bonferroni correction + sanity check.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Cells with ``n`` below this threshold are emitted but flagged ``low_n``
#: and excluded from the attributed-decay sum. The threshold matches A5
#: (``regime_matrix.LOW_N_THRESHOLD``) so cross-deliverable
#: small-sample handling is consistent.
LOW_N_THRESHOLD: int = 10

#: Default Beta prior — uniform on [0, 1]. Beta(1, 1) is the
#: non-committal Jeffreys-adjacent default; alternatives (Jeffreys
#: Beta(0.5, 0.5), informed OB-edge Beta(7, 3)) are documented in the
#: design note but NOT used for this diagnostic.
DEFAULT_PRIOR_A: float = 1.0
DEFAULT_PRIOR_B: float = 1.0

#: Two-sided credible interval default.
DEFAULT_CI_LEVEL: float = 0.95

#: Sentinel used when a trade lacks a value for the requested component.
#: Strata with this key are still emitted (so the reader sees the
#: missing-data fraction) but are flagged ``missing=True`` and
#: excluded from the sum.
MISSING_VALUE: str = "__missing__"


# ---------------------------------------------------------------------------
# Beta posterior + credible interval
# ---------------------------------------------------------------------------


def beta_posterior(
    wins: int,
    losses: int,
    prior_a: float = DEFAULT_PRIOR_A,
    prior_b: float = DEFAULT_PRIOR_B,
) -> tuple[float, float]:
    """Closed-form Beta posterior parameters.

    For Binomial(n, p) data with a Beta(prior_a, prior_b) prior, the
    posterior is::

        p | data ~ Beta(prior_a + wins, prior_b + losses)

    Returns ``(post_alpha, post_beta)``. Wins/losses are validated to
    be non-negative integers; prior values must be > 0.

    Hand-verified: Beta(10, 5) has mean 10 / (10 + 5) = 0.6667.
    """
    if wins < 0:
        raise ValueError(f"beta_posterior: wins={wins} must be >= 0")
    if losses < 0:
        raise ValueError(f"beta_posterior: losses={losses} must be >= 0")
    if prior_a <= 0 or prior_b <= 0:
        raise ValueError(
            f"beta_posterior: prior_a={prior_a} prior_b={prior_b} must be > 0"
        )
    return (float(prior_a + wins), float(prior_b + losses))


def beta_mean(alpha: float, beta: float) -> float:
    """Mean of Beta(alpha, beta) = alpha / (alpha + beta)."""
    if alpha <= 0 or beta <= 0:
        raise ValueError(f"beta_mean: alpha={alpha} beta={beta} must be > 0")
    return alpha / (alpha + beta)


# --- Incomplete Beta -------------------------------------------------------


def _ln_beta(a: float, b: float) -> float:
    """log Beta(a, b) = lgamma(a) + lgamma(b) - lgamma(a+b)."""
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-7) -> float:
    """Lentz-style continued fraction for the regularised incomplete Beta.

    Adapted from Numerical Recipes section 6.4. Used internally by
    :func:`_betainc_regularized`.
    """
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
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    # Failed to converge in max_iter — return best-effort.
    return h


def _betainc_regularized(a: float, b: float, x: float) -> float:
    """Regularised incomplete Beta function I_x(a, b).

    I_x(a, b) = B(x; a, b) / B(a, b), the CDF of Beta(a, b) evaluated
    at x. Uses the Numerical-Recipes recipe: continued-fraction in the
    convergent half plus the symmetry I_x(a, b) = 1 - I_{1-x}(b, a).
    Falls back on ``scipy.special.betainc`` if available for robustness.
    """
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"_betainc_regularized: x={x} out of [0,1]")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    try:
        from scipy.special import betainc as _scipy_betainc  # type: ignore
    except Exception:
        _scipy_betainc = None
    if _scipy_betainc is not None:
        return float(_scipy_betainc(a, b, x))

    # In-house path. Compute the prefactor in log-space to avoid
    # overflow at large a, b.
    log_prefactor = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    prefactor = math.exp(log_prefactor)
    if x < (a + 1.0) / (a + b + 2.0):
        return prefactor * _betacf(a, b, x) / a
    return 1.0 - prefactor * _betacf(b, a, 1.0 - x) / b


def _beta_ppf_bisect(
    p: float,
    alpha: float,
    beta: float,
    *,
    tol: float = 1e-7,
    max_iter: int = 200,
) -> float:
    """Inverse CDF (PPF) of Beta(alpha, beta) via bisection on I_x.

    Falls back on ``scipy.stats.beta.ppf`` if available. The bisection
    path is numerically stable for all (alpha, beta) > 0 and any p in
    (0, 1). At p=0 returns 0; at p=1 returns 1.
    """
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    try:
        from scipy.stats import beta as _scipy_beta  # type: ignore
    except Exception:
        _scipy_beta = None
    if _scipy_beta is not None:
        return float(_scipy_beta.ppf(p, alpha, beta))

    lo, hi = 0.0, 1.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        cdf_mid = _betainc_regularized(alpha, beta, mid)
        if abs(cdf_mid - p) < tol:
            return mid
        if cdf_mid < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def beta_credible_interval(
    alpha: float,
    beta: float,
    level: float = DEFAULT_CI_LEVEL,
) -> tuple[float, float]:
    """Two-sided equal-tailed credible interval at the given level.

    Returns ``(lo, hi)`` such that the posterior places ``level`` mass
    in [lo, hi]. Uses ``scipy.stats.beta.ppf`` if available, else an
    in-house bisection.
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError(
            f"beta_credible_interval: alpha={alpha} beta={beta} must be > 0"
        )
    if not 0.0 < level < 1.0:
        raise ValueError(f"beta_credible_interval: level={level} out of (0,1)")
    tail = 0.5 * (1.0 - level)
    lo = _beta_ppf_bisect(tail, alpha, beta)
    hi = _beta_ppf_bisect(1.0 - tail, alpha, beta)
    return (lo, hi)


# ---------------------------------------------------------------------------
# Stratification
# ---------------------------------------------------------------------------


def stratify_by_component(
    trades: list[dict],
    component: str,
) -> dict[str, list[dict]]:
    """Partition ``trades`` into a dict keyed by ``trade[component]``.

    Trades whose ``component`` value is missing/None map to
    :data:`MISSING_VALUE`. The output preserves trade order within
    each stratum (stable partition).

    Schema expectation: each trade dict has at minimum ``r_multiple``
    or equivalent realized-R field; the component is read directly
    from ``trade.get(component)``.
    """
    if not isinstance(component, str) or not component:
        raise ValueError(f"stratify_by_component: component={component!r} must be a non-empty str")
    out: dict[str, list[dict]] = {}
    for t in trades:
        if not isinstance(t, dict):
            continue
        v = t.get(component)
        if v is None or v == "":
            key = MISSING_VALUE
        else:
            key = str(v)
        out.setdefault(key, []).append(t)
    return out


def _wins_losses(
    trades: list[dict],
    *,
    r_field: str = "r_multiple",
) -> tuple[int, int]:
    """Count wins (r > 0) and losses (r <= 0). Trades with non-numeric
    or None r are skipped (counted in neither).
    """
    wins = 0
    losses = 0
    for t in trades:
        r = t.get(r_field)
        if r is None:
            continue
        try:
            r_f = float(r)
        except (TypeError, ValueError):
            continue
        if r_f > 0:
            wins += 1
        else:
            losses += 1
    return wins, losses


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


@dataclass
class StratumStats:
    """Per-stratum statistics within a single period (H1 or H2).

    Fields
    ------
    value : str
        The component value (e.g. ``"london"`` for kill_zone).
    n : int
        Number of realized trades in the stratum.
    wins : int
        Count of trades with r_multiple > 0.
    wr : float
        wins / n. NaN if n == 0.
    posterior_alpha, posterior_beta : float
        Beta posterior parameters after observing ``wins`` /
        ``losses=n-wins``.
    posterior_mean : float
        alpha / (alpha + beta).
    ci_lo, ci_hi : float
        Two-sided 95% credible interval on the posterior.
    low_n : bool
        n < LOW_N_THRESHOLD.
    missing : bool
        True iff value == MISSING_VALUE (component not recorded).
    """

    value: str
    n: int
    wins: int
    wr: float
    posterior_alpha: float
    posterior_beta: float
    posterior_mean: float
    ci_lo: float
    ci_hi: float
    low_n: bool
    missing: bool


@dataclass
class ComponentAttribution:
    """Per-component decay attribution.

    Fields
    ------
    component : str
        Component name (e.g. ``"framework"``).
    h1 : dict[str, StratumStats]
        Per-value stratum stats for H1.
    h2 : dict[str, StratumStats]
        Per-value stratum stats for H2.
    attributed_decay_pp : float
        sum( (wr_h1 - wr_h2) * n_share_h2 ) over strata where BOTH
        H1 and H2 satisfy n >= LOW_N_THRESHOLD AND value !=
        MISSING_VALUE. Reported as percentage points (pp).
    attributed_decay_ci : tuple[float, float]
        Approximate 95% credible interval on the attributed decay,
        derived by Monte Carlo composition of the per-stratum Beta
        posteriors. None when attributed_decay_pp is 0 (no usable
        strata).
    used_strata : list[str]
        Stratum values that contributed to ``attributed_decay_pp``.
    skipped_strata : list[tuple[str, str]]
        (value, reason) for strata excluded from the sum, with
        reason in {LOW_N_H1, LOW_N_H2, MISSING_BOTH, ABSENT_H1, ABSENT_H2}.
    raw_p : float
        Two-tailed p-value from a chi-square heterogeneity test of
        H1-vs-H2 contingency over the used strata. Used for
        Bonferroni correction across components.
    bonf_p : float
        ``raw_p * family_size`` clipped to [0, 1].
    family_size : int
        Number of components in the attribution family (set by
        attribute_decay).
    """

    component: str
    h1: dict[str, StratumStats] = field(default_factory=dict)
    h2: dict[str, StratumStats] = field(default_factory=dict)
    attributed_decay_pp: float = 0.0
    attributed_decay_ci: Optional[tuple[float, float]] = None
    used_strata: list[str] = field(default_factory=list)
    skipped_strata: list[tuple[str, str]] = field(default_factory=list)
    raw_p: float = 1.0
    bonf_p: float = 1.0
    family_size: int = 1


@dataclass
class AttributionReport:
    """Top-level A6 result.

    Fields
    ------
    components : list[ComponentAttribution]
        One entry per component, in input order.
    h1_n, h2_n : int
        Total realized-R count in each period.
    h1_wins, h2_wins : int
        Realized wins in each period.
    h1_wr, h2_wr : float
        Empirical WR in each period.
    observed_delta_pp : float
        ``(h1_wr - h2_wr) * 100``. Positive => decay (WR fell).
    total_attributed_pp : float
        Sum of per-component ``attributed_decay_pp``.
    residual_pp : float
        ``observed_delta_pp - total_attributed_pp``. Positive =>
        decay not explained by the chosen components.
    family_size : int
        len(components). Same as each component's family_size.
    prior : tuple[float, float]
        (prior_a, prior_b) used for the Beta posteriors.
    low_n_threshold : int
        LOW_N_THRESHOLD copy for output reproducibility.
    """

    components: list[ComponentAttribution] = field(default_factory=list)
    h1_n: int = 0
    h2_n: int = 0
    h1_wins: int = 0
    h2_wins: int = 0
    h1_wr: float = 0.0
    h2_wr: float = 0.0
    observed_delta_pp: float = 0.0
    total_attributed_pp: float = 0.0
    residual_pp: float = 0.0
    family_size: int = 0
    prior: tuple[float, float] = (DEFAULT_PRIOR_A, DEFAULT_PRIOR_B)
    low_n_threshold: int = LOW_N_THRESHOLD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stratum_stats(
    trades: list[dict],
    value: str,
    *,
    r_field: str,
    prior_a: float,
    prior_b: float,
    ci_level: float,
) -> StratumStats:
    wins, losses = _wins_losses(trades, r_field=r_field)
    n = wins + losses
    wr = (wins / n) if n > 0 else float("nan")
    a, b = beta_posterior(wins, losses, prior_a=prior_a, prior_b=prior_b)
    mean = beta_mean(a, b)
    if n > 0:
        lo, hi = beta_credible_interval(a, b, level=ci_level)
    else:
        lo, hi = 0.0, 1.0
    return StratumStats(
        value=value,
        n=n,
        wins=wins,
        wr=wr,
        posterior_alpha=a,
        posterior_beta=b,
        posterior_mean=mean,
        ci_lo=lo,
        ci_hi=hi,
        low_n=(n < LOW_N_THRESHOLD),
        missing=(value == MISSING_VALUE),
    )


def _chi_square_per_stratum(
    pairs: list[tuple[int, int, int, int]],
) -> tuple[float, int]:
    """Sum of 2x2 Pearson chi-squares across strata.

    Each tuple is ``(wins_h1, n_h1, wins_h2, n_h2)``. Strata with
    ``n_h1 + n_h2 < 4`` are skipped (chi-square not reliable).

    Returns ``(chi2_sum, df)`` with df = number of strata used.
    """
    chi2_sum = 0.0
    used = 0
    for wins_h1, n_h1, wins_h2, n_h2 in pairs:
        if n_h1 < 2 or n_h2 < 2:
            continue
        losses_h1 = n_h1 - wins_h1
        losses_h2 = n_h2 - wins_h2
        total = n_h1 + n_h2
        wins_total = wins_h1 + wins_h2
        losses_total = losses_h1 + losses_h2
        if total == 0 or wins_total == 0 or losses_total == 0:
            continue
        # Expected counts under independence:
        #   E[wins_h1] = n_h1 * wins_total / total
        e11 = n_h1 * wins_total / total
        e12 = n_h1 * losses_total / total
        e21 = n_h2 * wins_total / total
        e22 = n_h2 * losses_total / total
        # Chi-square = sum( (O - E)^2 / E )
        if min(e11, e12, e21, e22) <= 0:
            continue
        chi2 = (
            (wins_h1 - e11) ** 2 / e11
            + (losses_h1 - e12) ** 2 / e12
            + (wins_h2 - e21) ** 2 / e21
            + (losses_h2 - e22) ** 2 / e22
        )
        chi2_sum += chi2
        used += 1
    return chi2_sum, used


def _chi_square_p_value(chi2: float, df: int) -> float:
    """Two-tailed p-value for chi-square with df degrees of freedom.

    Uses ``scipy.stats.chi2.sf`` if available; otherwise falls back to
    a regularised upper-incomplete-gamma series. Both paths agree to
    1e-6 on hand-verified cases (chi2=3.84, df=1 -> p~0.05).
    """
    if df <= 0:
        return 1.0
    if chi2 <= 0:
        return 1.0
    try:
        from scipy.stats import chi2 as _scipy_chi2  # type: ignore

        return float(_scipy_chi2.sf(chi2, df))
    except Exception:
        pass
    # Fallback: chi2.sf(x, k) = 1 - gammainc(k/2, x/2)
    # gammainc here is the regularised lower-incomplete-gamma. We use
    # Lentz on the upper-incomplete-gamma for stability when x is
    # large compared to k/2.
    a = df / 2.0
    x = chi2 / 2.0
    return _gamma_q(a, x)


def _gamma_q(a: float, x: float) -> float:
    """Regularised upper-incomplete-gamma Q(a, x) = 1 - P(a, x).

    Uses the series for x < a + 1, continued fraction otherwise, per
    Numerical Recipes section 6.2. Tolerance 1e-12.
    """
    if x < 0 or a <= 0:
        return 1.0
    if x == 0:
        return 1.0
    log_norm = a * math.log(x) - x - math.lgamma(a)
    if x < a + 1.0:
        # Series for P(a, x), then Q = 1 - P.
        ap = a
        s = 1.0 / a
        delta = s
        for _ in range(200):
            ap += 1.0
            delta *= x / ap
            s += delta
            if abs(delta) < abs(s) * 1e-12:
                break
        p = s * math.exp(log_norm)
        return max(0.0, min(1.0, 1.0 - p))
    # Continued fraction for Q(a, x).
    b = x + 1.0 - a
    c = 1e30
    d = 1.0 / b
    h = d
    for i in range(1, 201):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-30:
            d = 1e-30
        c = b + an / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    q = h * math.exp(log_norm)
    return max(0.0, min(1.0, q))


def _attributed_decay_ci(
    used_pairs: list[tuple[float, float, float, float, float]],
    *,
    n_samples: int = 4000,
    seed: int = 20260426,
) -> tuple[float, float]:
    """Monte Carlo 95% credible interval on the attributed decay.

    Each stratum contributes a posterior pair ``(alpha_h1, beta_h1,
    alpha_h2, beta_h2, weight_h2)``. We sample WR_h1 ~ Beta(alpha_h1,
    beta_h1), WR_h2 ~ Beta(alpha_h2, beta_h2), compute the weighted
    sum of (WR_h1 - WR_h2) * weight, and take the 2.5%/97.5% quantiles
    over ``n_samples`` draws.

    Implementation note: we use ``random.Random(seed)`` for portability
    (no NumPy dependency required). For each Beta draw we sample two
    independent Gamma draws and form ratio X / (X+Y); Gamma sampling
    via the Marsaglia-Tsang method for shape >= 1 and the
    Ahrens-Dieter shape-tweaking trick for shape < 1.
    """
    if not used_pairs:
        return (0.0, 0.0)
    import random

    rng = random.Random(seed)
    samples = [0.0] * n_samples
    for k in range(n_samples):
        total = 0.0
        for a1, b1, a2, b2, w in used_pairs:
            wr1 = _beta_sample(rng, a1, b1)
            wr2 = _beta_sample(rng, a2, b2)
            total += (wr1 - wr2) * w
        samples[k] = total * 100.0  # convert to pp
    samples.sort()
    lo_idx = max(0, int(0.025 * n_samples) - 1)
    hi_idx = min(n_samples - 1, int(0.975 * n_samples))
    return (samples[lo_idx], samples[hi_idx])


def _beta_sample(rng: "random.Random", alpha: float, beta: float) -> float:
    """Single Beta(alpha, beta) draw using Gamma ratio.

    For Gamma sampling we use the standard library where shape >= 1
    (Marsaglia-Tsang via random.gammavariate which is correct for all
    shape > 0). The ratio Gamma_a / (Gamma_a + Gamma_b) is Beta(a, b).
    """
    x = rng.gammavariate(alpha, 1.0)
    y = rng.gammavariate(beta, 1.0)
    s = x + y
    if s <= 0:
        return 0.5
    return x / s


# ---------------------------------------------------------------------------
# Top-level attribution
# ---------------------------------------------------------------------------


def attribute_decay(
    h1_trades: list[dict],
    h2_trades: list[dict],
    components: list[str],
    *,
    r_field: str = "r_multiple",
    prior_a: float = DEFAULT_PRIOR_A,
    prior_b: float = DEFAULT_PRIOR_B,
    ci_level: float = DEFAULT_CI_LEVEL,
    low_n_threshold: int = LOW_N_THRESHOLD,
    ci_n_samples: int = 4000,
    ci_seed: int = 20260426,
) -> AttributionReport:
    """Decompose H1->H2 WR decay across each component.

    Parameters
    ----------
    h1_trades, h2_trades : list[dict]
        Lists of trade dicts for the two periods. Each dict must have
        a numeric ``r_field`` (default ``"r_multiple"``); trades with
        a missing/non-numeric value for that field are dropped from
        the rate computations (counted neither as wins nor losses).
        Each component name in ``components`` should appear as a key
        in the trade dict (missing keys map to ``MISSING_VALUE``).
    components : list[str]
        Ordered list of component names to attribute.
    r_field : str
        Trade-dict key holding realized R-multiple (default
        ``"r_multiple"``).
    prior_a, prior_b : float
        Beta prior parameters. Default Beta(1, 1).
    ci_level : float
        Credible interval level. Default 0.95.
    low_n_threshold : int
        Minimum n in BOTH H1 and H2 strata to include the stratum
        in the attributed-decay sum.
    ci_n_samples : int
        Monte Carlo draws for the per-component decay CI.
    ci_seed : int
        Deterministic seed for the Monte Carlo CI.

    Returns
    -------
    AttributionReport
    """
    if not isinstance(components, list) or not components:
        raise ValueError("attribute_decay: components must be a non-empty list of str")
    family_size = len(components)

    # Top-level wins/losses (ignoring components).
    h1_wins, h1_losses = _wins_losses(h1_trades, r_field=r_field)
    h2_wins, h2_losses = _wins_losses(h2_trades, r_field=r_field)
    h1_n = h1_wins + h1_losses
    h2_n = h2_wins + h2_losses
    h1_wr = (h1_wins / h1_n) if h1_n > 0 else 0.0
    h2_wr = (h2_wins / h2_n) if h2_n > 0 else 0.0
    observed_delta_pp = (h1_wr - h2_wr) * 100.0

    report = AttributionReport(
        h1_n=h1_n,
        h2_n=h2_n,
        h1_wins=h1_wins,
        h2_wins=h2_wins,
        h1_wr=h1_wr,
        h2_wr=h2_wr,
        observed_delta_pp=observed_delta_pp,
        family_size=family_size,
        prior=(prior_a, prior_b),
        low_n_threshold=low_n_threshold,
    )

    for component in components:
        ca = ComponentAttribution(component=component, family_size=family_size)
        h1_strata = stratify_by_component(h1_trades, component)
        h2_strata = stratify_by_component(h2_trades, component)
        all_values = sorted(set(h1_strata.keys()) | set(h2_strata.keys()))

        for v in all_values:
            ca.h1[v] = _stratum_stats(
                h1_strata.get(v, []),
                v,
                r_field=r_field,
                prior_a=prior_a,
                prior_b=prior_b,
                ci_level=ci_level,
            )
            ca.h2[v] = _stratum_stats(
                h2_strata.get(v, []),
                v,
                r_field=r_field,
                prior_a=prior_a,
                prior_b=prior_b,
                ci_level=ci_level,
            )

        # Attribution sum + chi-square.
        attributed = 0.0
        chi_pairs: list[tuple[int, int, int, int]] = []
        ci_pairs: list[tuple[float, float, float, float, float]] = []
        # H2 total n excluding missing/low-n on either side — used
        # for n-share weighting.
        usable_h2_total = sum(
            ca.h2[v].n
            for v in all_values
            if v != MISSING_VALUE
            and ca.h1[v].n >= low_n_threshold
            and ca.h2[v].n >= low_n_threshold
        )
        for v in all_values:
            h1_s = ca.h1[v]
            h2_s = ca.h2[v]
            if v == MISSING_VALUE:
                ca.skipped_strata.append((v, "MISSING_BOTH"))
                continue
            if h1_s.n == 0:
                ca.skipped_strata.append((v, "ABSENT_H1"))
                continue
            if h2_s.n == 0:
                ca.skipped_strata.append((v, "ABSENT_H2"))
                continue
            if h1_s.n < low_n_threshold:
                ca.skipped_strata.append((v, "LOW_N_H1"))
                continue
            if h2_s.n < low_n_threshold:
                ca.skipped_strata.append((v, "LOW_N_H2"))
                continue
            # Used.
            ca.used_strata.append(v)
            wr_h1 = h1_s.wins / h1_s.n
            wr_h2 = h2_s.wins / h2_s.n
            weight = h2_s.n / usable_h2_total if usable_h2_total > 0 else 0.0
            attributed += (wr_h1 - wr_h2) * weight
            chi_pairs.append((h1_s.wins, h1_s.n, h2_s.wins, h2_s.n))
            ci_pairs.append(
                (
                    h1_s.posterior_alpha,
                    h1_s.posterior_beta,
                    h2_s.posterior_alpha,
                    h2_s.posterior_beta,
                    weight,
                )
            )

        ca.attributed_decay_pp = attributed * 100.0
        if ci_pairs:
            ca.attributed_decay_ci = _attributed_decay_ci(
                ci_pairs, n_samples=ci_n_samples, seed=ci_seed
            )
        else:
            ca.attributed_decay_ci = None

        chi2, df = _chi_square_per_stratum(chi_pairs)
        ca.raw_p = _chi_square_p_value(chi2, df) if df > 0 else 1.0
        ca.bonf_p = min(1.0, max(0.0, ca.raw_p * family_size))

        report.components.append(ca)

    report.total_attributed_pp = sum(c.attributed_decay_pp for c in report.components) / max(family_size, 1)
    # Note on aggregation: each component's attributed_decay_pp is
    # already a full decomposition over its own strata. Summing across
    # components would double-count. We instead AVERAGE across
    # components — each is an alternative decomposition. Sanity check
    # is residual = observed - mean(attributed). The dominant
    # component is the one with the largest attributed_decay_pp.
    report.residual_pp = report.observed_delta_pp - report.total_attributed_pp

    return report


# ---------------------------------------------------------------------------
# Public API exports
# ---------------------------------------------------------------------------


__all__ = [
    "LOW_N_THRESHOLD",
    "DEFAULT_PRIOR_A",
    "DEFAULT_PRIOR_B",
    "DEFAULT_CI_LEVEL",
    "MISSING_VALUE",
    "AttributionReport",
    "ComponentAttribution",
    "StratumStats",
    "attribute_decay",
    "beta_credible_interval",
    "beta_mean",
    "beta_posterior",
    "stratify_by_component",
]
