"""Permutation-null + stationary-bootstrap significance for return series.

Part of the Standing Validation-Integrity Gauntlet. This is a gate that decides
what real money trades, so the statistics must be CORRECT, not "good enough".

Two methods are provided:

1. ``block_permutation_test`` -- a Monte-Carlo permutation (randomization) test
   for whether a return series has a real directional edge (positive
   mean / Sharpe) that survives its own short-horizon autocorrelation.

   IMPORTANT method note. A naive "block-shuffle" that merely *reorders* blocks
   of the series leaves the mean and the Sharpe ratio completely unchanged
   (they are permutation-invariant statistics), so it would yield a degenerate
   null where ``p_value == 1`` for every series -- statistically meaningless.
   The correct construction that (a) preserves short-horizon autocorrelation and
   (b) actually generates a non-degenerate null for a *location / direction*
   statistic is **block sign-flip randomization**: partition the series into
   contiguous blocks of length ``block`` and independently multiply each block
   by a random +/-1. Flipping the sign of a whole contiguous block preserves the
   within-block autocorrelation (correlation is invariant to a global sign flip
   of the block) while randomizing the *direction* of each block's contribution.
   Under the null hypothesis "no directional edge" (sign-symmetric increments)
   this is an exact randomization scheme; the all-(+1) assignment reproduces the
   observed series, which is why the p-value uses the standard
   ``(1 + #{null >= observed}) / (n_perm + 1)`` add-one estimator
   (Phipson & Smyth 2010; Davison & Hinkley 1997).

2. ``stationary_bootstrap_ci`` -- the Politis & Romano (1994) stationary
   bootstrap. Blocks have a *geometric* random length with mean ``block``
   (restart probability ``p = 1/block``), wrapping circularly, which produces a
   strictly stationary resample and a percentile confidence interval that is
   robust to serial dependence.

The normal CDF / inverse-CDF used for the auxiliary Gaussian cross-checks are
implemented with ``math.erf`` / ``math.erfc`` and a numerically-stable inverse
(Acklam + one Halley refinement) so the module has **no hard scipy dependency**.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

__all__ = [
    "block_permutation_test",
    "stationary_bootstrap_ci",
    "normal_cdf",
    "normal_ppf",
]


# --------------------------------------------------------------------------- #
# Numerically-stable normal CDF / inverse-CDF (no scipy).                      #
# --------------------------------------------------------------------------- #
_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def normal_cdf(x: float) -> float:
    """Standard-normal CDF Phi(x) via ``math.erfc`` (stable in both tails)."""
    return 0.5 * math.erfc(-x / _SQRT2)


def _normal_sf(x: float) -> float:
    """Standard-normal survival function 1 - Phi(x) = 0.5 * erfc(x/sqrt2)."""
    return 0.5 * math.erfc(x / _SQRT2)


# Acklam's rational approximation coefficients for the inverse normal CDF.
_A = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
      1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
_B = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
      6.680131188771972e+01, -1.328068155288572e+01]
_C = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
      -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
_D = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
      3.754408661907416e+00]


def normal_ppf(p: float) -> float:
    """Inverse standard-normal CDF (quantile). Acklam approx + Halley refine.

    Accurate to ~1e-12 across (0, 1); no scipy dependency.
    """
    if not (0.0 < p < 1.0):
        if p == 0.0:
            return -math.inf
        if p == 1.0:
            return math.inf
        raise ValueError(f"normal_ppf requires 0 < p < 1, got {p}")
    plow = 0.02425
    phigh = 1.0 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
            ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        x = (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q / \
            (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
            ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    # One Halley step against the erf-based CDF for full double precision.
    e = normal_cdf(x) - p
    u = e * _SQRT2PI * math.exp(x * x / 2.0)
    x = x - u / (1.0 + x * u / 2.0)
    return x


# --------------------------------------------------------------------------- #
# Helpers.                                                                     #
# --------------------------------------------------------------------------- #
def _as_clean_array(series: Sequence[float]) -> np.ndarray:
    arr = np.asarray(series, dtype=np.float64).ravel()
    if arr.size == 0:
        raise ValueError("series is empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("series contains non-finite values (NaN/Inf)")
    return arr


def _stat_1d(arr: np.ndarray, stat: str) -> float:
    if stat == "mean":
        return float(arr.mean())
    if stat == "sharpe":
        sd = float(arr.std(ddof=0))
        if sd == 0.0:
            return 0.0
        return float(arr.mean()) / sd
    raise ValueError(f"unknown stat {stat!r}; use 'mean' or 'sharpe'")


def _stat_rows(mat: np.ndarray, stat: str) -> np.ndarray:
    """Vectorized statistic across axis=1 (one value per row)."""
    if stat == "mean":
        return mat.mean(axis=1)
    if stat == "sharpe":
        mean = mat.mean(axis=1)
        sd = mat.std(axis=1, ddof=0)
        out = np.zeros_like(mean)
        nz = sd > 0.0
        out[nz] = mean[nz] / sd[nz]
        return out
    raise ValueError(f"unknown stat {stat!r}; use 'mean' or 'sharpe'")


# --------------------------------------------------------------------------- #
# 1. Block sign-flip permutation test.                                        #
# --------------------------------------------------------------------------- #
def block_permutation_test(series, block: int = 5, n_perm: int = 5000,
                           stat: str = "sharpe", seed: int = 12345) -> dict:
    """Block sign-flip permutation test for a directional edge.

    Parameters
    ----------
    series : sequence of float
        Per-period returns (e.g. daily R).
    block : int
        Contiguous block length whose sign is flipped together (preserves
        short-horizon autocorrelation). Must be >= 1.
    n_perm : int
        Number of random sign-flip permutations.
    stat : {'sharpe', 'mean'}
        'sharpe' = mean / std(ddof=0); 'mean' = arithmetic mean.
    seed : int
        Seed for the numpy ``Generator`` (deterministic output).

    Returns
    -------
    dict with keys ``observed``, ``p_value``, ``null_mean``, ``null_p95``.
    Also includes ``p_value_normal`` (Gaussian-fit right-tail cross-check),
    ``null_std``, ``n_perm``, ``block``, ``stat`` for diagnostics.

    The p-value is one-sided (right tail): probability that sign-randomization
    produces a statistic >= the observed one.
    """
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    if n_perm < 1:
        raise ValueError(f"n_perm must be >= 1, got {n_perm}")
    arr = _as_clean_array(series)
    n = arr.size

    observed = _stat_1d(arr, stat)

    rng = np.random.default_rng(seed)
    n_blocks = int(math.ceil(n / block))
    # Random +/-1 per block per permutation -> expand to length n.
    block_signs = rng.choice(
        np.array([-1.0, 1.0]), size=(n_perm, n_blocks))
    signs = np.repeat(block_signs, block, axis=1)[:, :n]  # (n_perm, n)
    permuted = signs * arr[np.newaxis, :]                 # broadcast multiply
    null_stats = _stat_rows(permuted, stat)

    ge = int(np.count_nonzero(null_stats >= observed))
    p_value = (1.0 + ge) / (n_perm + 1.0)

    null_mean = float(null_stats.mean())
    null_std = float(null_stats.std(ddof=0))
    null_p95 = float(np.quantile(null_stats, 0.95))

    # Gaussian-fit right-tail p as an independent cross-check (erf-based).
    if null_std > 0.0:
        p_value_normal = float(_normal_sf((observed - null_mean) / null_std))
    else:
        p_value_normal = 0.0 if observed > null_mean else 1.0

    return {
        "observed": float(observed),
        "p_value": float(p_value),
        "null_mean": null_mean,
        "null_p95": null_p95,
        "p_value_normal": p_value_normal,
        "null_std": null_std,
        "n_perm": int(n_perm),
        "block": int(block),
        "stat": stat,
    }


# --------------------------------------------------------------------------- #
# 2. Politis-Romano stationary bootstrap CI.                                  #
# --------------------------------------------------------------------------- #
def _stationary_indices(n: int, n_boot: int, block: int,
                        rng: np.random.Generator) -> np.ndarray:
    """Generate (n_boot, n) circular indices for the stationary bootstrap.

    Geometric block length with mean ``block`` => restart probability p = 1/block.
    """
    p = 1.0 / float(block)
    idx = np.empty((n_boot, n), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n, size=n_boot)
    if n == 1:
        return idx
    restart = rng.random((n_boot, n)) < p     # restart[:, 0] unused
    fresh = rng.integers(0, n, size=(n_boot, n))
    for t in range(1, n):
        cont = idx[:, t - 1] + 1
        cont[cont >= n] = 0                    # circular wrap
        idx[:, t] = np.where(restart[:, t], fresh[:, t], cont)
    return idx


def stationary_bootstrap_ci(series, stat_fn_name: str = "mean", block: int = 5,
                            n_boot: int = 5000, alpha: float = 0.05,
                            seed: int = 12345) -> dict:
    """Politis & Romano (1994) stationary-bootstrap percentile CI.

    Parameters
    ----------
    series : sequence of float
    stat_fn_name : {'mean', 'sharpe'}
        'sharpe' = mean / std(ddof=0).
    block : int
        Mean (geometric) block length; restart prob = 1/block. Must be >= 1.
    n_boot : int
        Number of bootstrap resamples.
    alpha : float
        Two-sided miscoverage; CI is the [alpha/2, 1-alpha/2] percentile band.
    seed : int
        Generator seed (deterministic).

    Returns
    -------
    dict with keys ``point``, ``ci_low``, ``ci_high``, ``alpha``.
    Also ``ci_low_normal`` / ``ci_high_normal`` (point +/- z * bootstrap SE,
    a Gaussian cross-check), ``boot_se``, ``n_boot``, ``block``, ``stat``.
    """
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    if n_boot < 1:
        raise ValueError(f"n_boot must be >= 1, got {n_boot}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    arr = _as_clean_array(series)
    n = arr.size

    point = _stat_1d(arr, stat_fn_name)

    rng = np.random.default_rng(seed)
    idx = _stationary_indices(n, n_boot, block, rng)
    samples = arr[idx]                          # (n_boot, n)
    boot_stats = _stat_rows(samples, stat_fn_name)

    ci_low = float(np.quantile(boot_stats, alpha / 2.0))
    ci_high = float(np.quantile(boot_stats, 1.0 - alpha / 2.0))

    # Gaussian cross-check interval from the bootstrap standard error.
    boot_se = float(boot_stats.std(ddof=1)) if n_boot > 1 else 0.0
    z = normal_ppf(1.0 - alpha / 2.0)
    ci_low_normal = float(point - z * boot_se)
    ci_high_normal = float(point + z * boot_se)

    return {
        "point": float(point),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "alpha": float(alpha),
        "ci_low_normal": ci_low_normal,
        "ci_high_normal": ci_high_normal,
        "boot_se": boot_se,
        "n_boot": int(n_boot),
        "block": int(block),
        "stat": stat_fn_name,
    }
