"""Probability of Backtest Overfitting (PBO) via CSCV.

Combinatorially-Symmetric Cross-Validation, exactly as defined in:

    D. H. Bailey, J. Borwein, M. López de Prado, Q. J. Zhu (2017),
    "The Probability of Backtest Overfitting", Journal of Computational
    Finance, 20(4), 39-69.

Intuition
---------
Given a performance matrix ``M`` of shape ``(T, N)`` — ``T`` time-rows, ``N``
candidate strategy/configuration columns — CSCV asks: *if I select the column
that looks best in-sample, how often does it land below the median out-of-sample?*
That fraction is the PBO. A genuine edge keeps its rank out-of-sample (low PBO);
a lucky in-sample winner reverts to the OOS median (PBO -> 0.5).

Algorithm (one pass)
--------------------
1. Split the ``T`` rows into ``S`` contiguous, (near-)equal blocks.
2. For each of the ``C(S, S/2)`` ways to choose ``S/2`` blocks as the in-sample
   (IS) set, the remaining ``S/2`` blocks are the out-of-sample (OOS) set. Both
   directions of every split are enumerated — that is the *symmetric* part.
3. Rank the ``N`` columns by the IS metric; take the IS-best column ``n*``.
4. Find the OOS metric of ``n*`` and its *relative rank* ``w`` in ``(0,1)`` among
   the ``N`` OOS metrics, with ``w = rank/(N+1)`` (average-rank for ties), so the
   logit ``lambda = ln(w/(1-w))`` is always finite and ``lambda = 0`` is the OOS
   median.
5. ``PBO = #{lambda <= 0} / #combinations`` — the fraction of splits where the
   IS-best column is at-or-below the OOS median.

The module depends only on ``numpy`` + the standard library (no scipy).
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any, Dict, Sequence

import numpy as np

__all__ = ["pbo_cscv"]

# When the full combination count C(S, S/2) exceeds this, the enumeration is
# subsampled (uniformly, without replacement) down to this many combinations.
DEFAULT_MAX_COMBINATIONS = 20000


def _column_metric(
    s1: np.ndarray,
    s2: np.ndarray,
    cnt: int,
    metric: str,
) -> np.ndarray:
    """Per-column metric from pre-aggregated block sums.

    ``s1`` is the per-column sum of returns over the selected rows, ``s2`` the
    per-column sum of squared returns, ``cnt`` the number of selected rows.

    - ``metric='mean'``  -> mean return per column.
    - ``metric='sharpe'`` -> mean/std (population std). The ddof choice does not
      affect ranking because every column shares the same ``cnt``; a degenerate
      zero-variance column is mapped to ``0.0`` rather than +/-inf/NaN so ties
      and constant columns are handled gracefully.
    """
    mean = s1 / cnt
    if metric == "mean":
        return mean
    if metric == "sharpe":
        # population variance = E[x^2] - E[x]^2; clamp tiny negatives from
        # floating-point cancellation on (near-)constant columns.
        var = s2 / cnt - mean * mean
        var = np.where(var < 0.0, 0.0, var)
        std = np.sqrt(var)
        out = np.zeros_like(mean)
        nz = std > 0.0
        out[nz] = mean[nz] / std[nz]
        return out
    raise ValueError(f"metric must be 'sharpe' or 'mean', got {metric!r}")


def _relative_rank(values: np.ndarray, idx: int) -> float:
    """Average-rank relative position of ``values[idx]`` within ``values``.

    Returns ``w = rank/(N+1)`` in the open interval ``(0, 1)`` where ``rank`` is
    the 1..N average rank (ties share the mean of their ordinal positions).
    Average ranks keep the mapping symmetric and put the median at ``w = 0.5``.
    """
    v = values[idx]
    n = values.shape[0]
    n_less = int(np.count_nonzero(values < v))
    n_equal = int(np.count_nonzero(values == v))  # >= 1 (includes idx itself)
    rank = n_less + (n_equal + 1) / 2.0  # average rank in [1, N]
    return rank / (n + 1.0)


def pbo_cscv(
    returns_matrix: Sequence[Sequence[float]] | np.ndarray,
    n_partitions: int = 16,
    metric: str = "sharpe",
    max_combinations: int = DEFAULT_MAX_COMBINATIONS,
    random_state: int = 0,
) -> Dict[str, Any]:
    """Probability of Backtest Overfitting via CSCV.

    Parameters
    ----------
    returns_matrix : array-like, shape (T, N)
        ``T`` time-rows by ``N`` strategy/configuration columns. Each cell is the
        per-period performance of that column.
    n_partitions : int, default 16
        Number of contiguous time-blocks ``S``. Must be even and ``2 <= S <= T``.
        ``C(S, S/2)`` combinations are evaluated (e.g. ``S=16`` -> 12870).
    metric : {'sharpe', 'mean'}, default 'sharpe'
        Per-block column score. ``'sharpe'`` is mean/std of the block returns.
    max_combinations : int, default 20000
        If ``C(S, S/2)`` exceeds this, combinations are uniformly subsampled
        without replacement to this cap and ``subsampled=True`` is returned.
    random_state : int, default 0
        Seed used only when subsampling.

    Returns
    -------
    dict with keys:
        pbo : float
            Fraction of combinations whose logit ``lambda <= 0`` (IS-best column
            at or below the OOS median).
        n_combinations : int
            Number of combinations actually evaluated.
        logits : list[float]
            The ``lambda`` value for every evaluated combination.
        mean_logit : float
            Mean of ``logits`` (nan if empty).
        n_partitions, n_strategies, metric, total_combinations, subsampled :
            Diagnostic context.
    """
    M = np.asarray(returns_matrix, dtype=float)
    if M.ndim != 2:
        raise ValueError(f"returns_matrix must be 2D (T, N); got shape {M.shape}")
    T, N = M.shape
    if N < 2:
        raise ValueError(f"need at least 2 strategy columns to rank; got N={N}")
    if not np.all(np.isfinite(M)):
        raise ValueError("returns_matrix contains non-finite values (nan/inf)")

    S = int(n_partitions)
    if S < 2 or S % 2 != 0:
        raise ValueError(f"n_partitions must be an even integer >= 2; got {n_partitions}")
    if S > T:
        raise ValueError(f"n_partitions={S} exceeds number of time-rows T={T}")

    # --- Pre-aggregate each contiguous block once (O(T*N) total). -----------
    # array_split yields contiguous index groups whose sizes differ by <= 1.
    block_rows = np.array_split(np.arange(T), S)
    cnt_blocks = np.array([len(b) for b in block_rows], dtype=float)        # (S,)
    s1_blocks = np.vstack([M[b].sum(axis=0) for b in block_rows])           # (S, N)
    s2_blocks = np.vstack([(M[b] ** 2).sum(axis=0) for b in block_rows])    # (S, N)

    tot_cnt = float(cnt_blocks.sum())
    tot_s1 = s1_blocks.sum(axis=0)
    tot_s2 = s2_blocks.sum(axis=0)

    half = S // 2
    total_combinations = math.comb(S, half)

    # --- Decide enumeration vs subsampling. ---------------------------------
    subsampled = total_combinations > max_combinations
    if subsampled:
        rng = np.random.default_rng(random_state)
        seen: set = set()
        combos = []
        target = int(max_combinations)
        # Rejection-sample distinct S/2-subsets. The space is >> target here,
        # so collisions are rare and this terminates quickly.
        while len(combos) < target:
            pick = tuple(sorted(rng.choice(S, size=half, replace=False).tolist()))
            if pick not in seen:
                seen.add(pick)
                combos.append(pick)
        combo_iter: Any = combos
    else:
        combo_iter = combinations(range(S), half)

    # --- Main CSCV loop. ----------------------------------------------------
    logits = []
    n_combos = 0
    for is_blocks in combo_iter:
        idx = list(is_blocks)
        s1_is = s1_blocks[idx].sum(axis=0)
        s2_is = s2_blocks[idx].sum(axis=0)
        cnt_is = float(cnt_blocks[idx].sum())

        # OOS = everything minus IS (complement of the chosen blocks).
        s1_oos = tot_s1 - s1_is
        s2_oos = tot_s2 - s2_is
        cnt_oos = tot_cnt - cnt_is

        R_is = _column_metric(s1_is, s2_is, cnt_is, metric)
        R_oos = _column_metric(s1_oos, s2_oos, cnt_oos, metric)

        n_star = int(np.argmax(R_is))          # IS-best column (first on ties)
        w = _relative_rank(R_oos, n_star)      # relative OOS rank in (0,1)
        lam = math.log(w / (1.0 - w))          # logit; finite by construction
        logits.append(lam)
        n_combos += 1

    logits_arr = np.asarray(logits, dtype=float)
    pbo = float(np.count_nonzero(logits_arr <= 0.0) / n_combos) if n_combos else float("nan")
    mean_logit = float(logits_arr.mean()) if n_combos else float("nan")

    return {
        "pbo": pbo,
        "n_combinations": n_combos,
        "logits": logits,
        "mean_logit": mean_logit,
        "n_partitions": S,
        "n_strategies": N,
        "metric": metric,
        "total_combinations": total_combinations,
        "subsampled": subsampled,
    }
