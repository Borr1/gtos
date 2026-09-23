"""Deflated Sharpe Ratio (DSR) and Probabilistic Sharpe Ratio (PSR).

Reference
---------
Bailey, D. H. and López de Prado, M. (2014). "The Deflated Sharpe Ratio:
Correcting for Selection Bias, Backtest Overfitting and Non-Normality."
Journal of Portfolio Management, 40(5), pp. 94-107.

Also draws on Bailey & López de Prado (2012), "The Sharpe Ratio Efficient
Frontier" (Journal of Risk, 15(2)), for the closed-form standard error of the
Sharpe-ratio estimator under non-normal returns.

What this module does
---------------------
The Sharpe ratio is an *estimator*. Two distinct distortions inflate it:

1. **Non-normality.**  A skewed / fat-tailed return series makes the naive
   Sharpe estimator more uncertain than the Gaussian textbook formula assumes.
   The **Probabilistic Sharpe Ratio (PSR)** replaces the point estimate with the
   probability that the *true* per-period Sharpe exceeds a benchmark, using the
   observed skew and (non-excess) kurtosis to widen the estimator's standard
   error.

2. **Selection under multiple testing.**  When a strategy is the best of ``N``
   trials, its Sharpe is biased upward by the expected maximum of ``N`` draws.
   The **Deflated Sharpe Ratio (DSR)** is the PSR evaluated against that
   selection-aware benchmark ``E[max_N SR]`` instead of against zero.

Conventions (documented, deliberate, internally consistent)
-----------------------------------------------------------
* ``SR_hat`` is the **per-period** Sharpe (NOT annualised): ``mean / std``.
* All moments (std, skew, kurtosis) use the **population / MLE estimators**
  (``ddof = 0``).  This keeps the Sharpe estimator and its higher moments
  mutually consistent, and it matches the population standard deviation used by
  the orchestrator's verified ground truth.  For ``n`` in the hundreds-to-
  thousands the difference versus the sample (``ddof = 1``) estimator is
  < 0.05% and does not affect any decision.  The ``(n - 1)`` term that appears
  in the PSR is the *analytic standard-error* factor from Bailey & López de
  Prado and is independent of the moment convention.
* ``kurtosis`` is the **non-excess** fourth standardised moment (a Gaussian has
  kurtosis 3, so the ``(kurt - 1) / 4`` term equals 0.5 — the textbook Gaussian
  PSR denominator ``sqrt(1 + SR^2 / 2)``).
* The standard normal CDF ``Phi`` is implemented with ``math.erf``; the inverse
  CDF ``Z`` uses Acklam's rational approximation refined with one Halley step
  (full double precision).  **No SciPy dependency.**

Public API
----------
* ``probabilistic_sharpe_ratio(returns, sr_benchmark=0.0) -> dict``
* ``expected_max_sharpe(n_trials, sr_variance) -> float``
* ``deflated_sharpe_ratio(returns, n_trials, sr_variance=None,
      sr_benchmark=None, periods_per_year=252) -> dict``
* ``phi(x) -> float`` / ``inv_phi(p) -> float``  (exposed for testing/reuse)
"""

from __future__ import annotations

import math
from typing import Iterable, Optional

__all__ = [
    "phi",
    "inv_phi",
    "probabilistic_sharpe_ratio",
    "expected_max_sharpe",
    "deflated_sharpe_ratio",
    "EULER_MASCHERONI",
]

# Euler-Mascheroni constant (Bailey & López de Prado use this exact value).
EULER_MASCHERONI: float = 0.5772156649015329

_SQRT2 = math.sqrt(2.0)
_SQRT_2PI = math.sqrt(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Standard normal CDF (Phi) and inverse CDF (Z) — pure stdlib, no SciPy.
# ---------------------------------------------------------------------------
def phi(x: float) -> float:
    """Standard normal CDF via ``math.erf`` (numerically stable, no SciPy)."""
    return 0.5 * math.erfc(-x / _SQRT2)


# Acklam's coefficients for the inverse standard-normal CDF.
# (P. J. Acklam, "An algorithm for computing the inverse normal cumulative
#  distribution function".)  Relative error < 1.15e-9 before refinement.
_A = (
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
)
_B = (
    -5.447609879822406e01,
    1.615858368580409e02,
    -1.556989798598866e02,
    6.680131188771972e01,
    -1.328068155288572e01,
)
_C = (
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
)
_D = (
    7.784695709041462e-03,
    3.224671290700398e-01,
    2.445134137142996e00,
    3.754408661907416e00,
)
_P_LOW = 0.02425
_P_HIGH = 1.0 - _P_LOW


def inv_phi(p: float) -> float:
    """Inverse standard normal CDF ``Z`` (quantile function).

    Acklam's rational approximation followed by a single Halley refinement step
    that drives the error to full double precision (~1e-15).  ``Z(0.975)`` is
    reproduced as 1.9599639845...  Returns ``-inf`` at ``p<=0`` and ``+inf`` at
    ``p>=1`` (the degenerate tails).
    """
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")

    # --- Acklam rational approximation (initial guess) ---
    if p < _P_LOW:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / (
            (((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0
        )
    elif p <= _P_HIGH:
        q = p - 0.5
        r = q * q
        x = (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q / (
            ((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0
        )
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / (
            (((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0
        )

    # --- One Halley step: refine x so Phi(x) == p to machine precision ---
    # e = Phi(x) - p ; u = e / Phi'(x) ; Halley: x -= u / (1 + x*u/2)
    e = phi(x) - p
    u = e * _SQRT_2PI * math.exp(0.5 * x * x)
    x = x - u / (1.0 + 0.5 * x * u)
    return x


# ---------------------------------------------------------------------------
# Moments
# ---------------------------------------------------------------------------
def _moments(returns: Iterable[float]) -> tuple[int, float, float, float, float]:
    """Return ``(n, mean, std_pop, skew, kurt_nonexcess)`` (all ddof=0).

    ``std_pop`` is the population standard deviation; ``skew`` and ``kurt`` are
    the standardised 3rd and 4th central moments (kurtosis is *non-excess*: a
    Gaussian gives 3.0).
    """
    xs = [float(v) for v in returns]
    n = len(xs)
    if n < 2:
        raise ValueError(f"need at least 2 return observations, got {n}")
    mean = math.fsum(xs) / n
    d = [v - mean for v in xs]
    m2 = math.fsum(dd * dd for dd in d) / n
    if m2 <= 0.0:
        raise ValueError("return series has zero variance; Sharpe ratio undefined")
    m3 = math.fsum(dd ** 3 for dd in d) / n
    m4 = math.fsum(dd ** 4 for dd in d) / n
    std = math.sqrt(m2)
    skew = m3 / (m2 ** 1.5)
    kurt = m4 / (m2 * m2)  # non-excess
    return n, mean, std, skew, kurt


def _psr_from_stats(
    sr_hat: float,
    sr_benchmark: float,
    n: int,
    skew: float,
    kurt: float,
) -> float:
    """Core PSR computation given pre-computed statistics.

    PSR = Phi( (SR_hat - SR*) * sqrt(n-1)
               / sqrt(1 - skew*SR_hat + ((kurt-1)/4)*SR_hat^2) )

    where SR_hat, SR* are *per-period* Sharpe ratios and ``kurt`` is the
    non-excess kurtosis.
    """
    var_term = 1.0 - skew * sr_hat + ((kurt - 1.0) / 4.0) * sr_hat * sr_hat
    if var_term <= 0.0:
        # Pathological combination of extreme skew/kurtosis with a large SR.
        # The estimator standard error is not real-valued; fail loud rather
        # than silently return a wrong probability.
        raise ValueError(
            "PSR variance term <= 0 (extreme skew/kurtosis vs SR_hat); "
            f"var_term={var_term!r}, sr_hat={sr_hat!r}, skew={skew!r}, kurt={kurt!r}"
        )
    z = (sr_hat - sr_benchmark) * math.sqrt(n - 1) / math.sqrt(var_term)
    return phi(z)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def probabilistic_sharpe_ratio(
    returns: Iterable[float],
    sr_benchmark: float = 0.0,
) -> dict:
    """Probabilistic Sharpe Ratio with the non-normality correction.

    Parameters
    ----------
    returns : iterable of float
        Per-period return series (e.g. daily R multiples).
    sr_benchmark : float, default 0.0
        Benchmark **per-period** Sharpe ratio to test against.  The default of
        zero asks "what is the probability the true Sharpe is positive?".

    Returns
    -------
    dict with keys:
        ``psr``           -- P[ true SR > sr_benchmark ]  (in [0, 1])
        ``sr_per_period`` -- observed per-period Sharpe (mean / std_pop)
        ``skew``          -- observed skewness (ddof=0)
        ``kurtosis``      -- observed non-excess kurtosis (Gaussian -> 3)
        ``n``             -- number of observations
        ``sr_benchmark``  -- the benchmark used
        ``p_value``       -- 1 - psr
    """
    n, mean, std, skew, kurt = _moments(returns)
    sr_hat = mean / std
    psr = _psr_from_stats(sr_hat, sr_benchmark, n, skew, kurt)
    return {
        "psr": psr,
        "sr_per_period": sr_hat,
        "skew": skew,
        "kurtosis": kurt,
        "n": n,
        "sr_benchmark": sr_benchmark,
        "p_value": 1.0 - psr,
    }


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Expected maximum of ``N`` independent trial Sharpe ratios.

    E[max_N SR] = sqrt(V) * ( (1 - gamma) * Z(1 - 1/N)
                              + gamma     * Z(1 - 1/(N*e)) )

    where ``V = sr_variance`` is the *variance of the (per-period) Sharpe
    ratios across the N trials*, ``gamma`` is the Euler-Mascheroni constant,
    ``Z`` is the inverse standard normal CDF, and ``e`` is Euler's number.
    This is the standard extreme-value (Gumbel) approximation used in the
    Deflated Sharpe Ratio.

    Edge case: for ``N <= 1`` there is no selection, and the expected maximum
    of a single trial equals the mean of the trial distribution, which is 0.
    (The asymptotic formula is only valid for ``N >= 2``: ``Z(1 - 1/1) =
    Z(0) = -inf``.)  We therefore return ``0.0`` for ``N <= 1``.

    Parameters
    ----------
    n_trials : int
        Number of independent trials / configurations searched over.
    sr_variance : float
        Variance of the per-period Sharpe ratios across those trials (V >= 0).
    """
    if n_trials < 1:
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")
    if sr_variance < 0.0:
        raise ValueError(f"sr_variance must be >= 0, got {sr_variance}")
    if n_trials == 1:
        return 0.0
    if sr_variance == 0.0:
        return 0.0
    nf = float(n_trials)
    gamma = EULER_MASCHERONI
    z1 = inv_phi(1.0 - 1.0 / nf)
    z2 = inv_phi(1.0 - 1.0 / (nf * math.e))
    return math.sqrt(sr_variance) * ((1.0 - gamma) * z1 + gamma * z2)


def deflated_sharpe_ratio(
    returns: Iterable[float],
    n_trials: int,
    sr_variance: Optional[float] = None,
    sr_benchmark: Optional[float] = None,
    periods_per_year: int = 252,
) -> dict:
    """Deflated Sharpe Ratio.

    The DSR is the PSR of the strategy evaluated against a *selection-aware*
    benchmark: the expected maximum Sharpe across ``n_trials`` independent
    trials.  A strategy that merely looks good because it was the best of many
    backtests deflates toward insignificance.

    Benchmark resolution (documented choice)
    ----------------------------------------
    * If ``sr_benchmark`` is given explicitly, it is used as-is (per-period).
    * Else if ``sr_variance`` is given, the benchmark is
      ``expected_max_sharpe(n_trials, sr_variance)``.
    * Else (**both** ``sr_variance`` and ``sr_benchmark`` are ``None``) a
      ``ValueError`` is raised.  We deliberately do **not** silently invent a
      variance: the cross-trial Sharpe variance ``V`` cannot be recovered from
      a single combined return series — it is a property of the *search* (the
      dispersion of Sharpe across the N configurations actually tried) and must
      be supplied by the caller (e.g. the variance of the per-trial / per-sleeve
      Sharpe ratios).  Fabricating it would corrupt the very gate this module
      exists to enforce.

    Parameters
    ----------
    returns : iterable of float
        Per-period return series for the (selected) strategy.
    n_trials : int
        Number of trials the strategy was selected from (>= 1).
    sr_variance : float, optional
        Variance of per-period Sharpe across the trials (see above).
    sr_benchmark : float, optional
        Explicit per-period benchmark Sharpe; overrides ``sr_variance``.
    periods_per_year : int, default 252
        Annualisation factor for the *reported* annualised Sharpe only; it does
        not enter the PSR/DSR probability (those are scale-free in time).

    Returns
    -------
    dict with keys:
        ``sr_per_period``, ``sr_annualized``, ``psr``, ``dsr``, ``n_trials``,
        ``sr_benchmark``, ``significant`` (dsr > 0.95), ``p_value`` (1 - dsr).
        Also includes ``skew``, ``kurtosis``, ``n_obs`` for transparency.
    """
    if n_trials < 1:
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")

    n, mean, std, skew, kurt = _moments(returns)
    sr_hat = mean / std
    sr_annualized = sr_hat * math.sqrt(periods_per_year)

    # PSR against zero (significance ignoring selection).
    psr = _psr_from_stats(sr_hat, 0.0, n, skew, kurt)

    # Resolve the deflation benchmark.
    if sr_benchmark is None:
        if sr_variance is None:
            raise ValueError(
                "deflated_sharpe_ratio requires either sr_benchmark or "
                "sr_variance. The cross-trial Sharpe variance cannot be "
                "estimated from a single return series; pass sr_variance "
                "(e.g. variance of per-trial Sharpe ratios) or an explicit "
                "sr_benchmark."
            )
        benchmark = expected_max_sharpe(n_trials, sr_variance)
    else:
        benchmark = float(sr_benchmark)

    # DSR = PSR evaluated at the deflated benchmark.
    dsr = _psr_from_stats(sr_hat, benchmark, n, skew, kurt)

    return {
        "sr_per_period": sr_hat,
        "sr_annualized": sr_annualized,
        "psr": psr,
        "dsr": dsr,
        "n_trials": n_trials,
        "sr_benchmark": benchmark,
        "significant": dsr > 0.95,
        "p_value": 1.0 - dsr,
        "skew": skew,
        "kurtosis": kurt,
        "n_obs": n,
    }
