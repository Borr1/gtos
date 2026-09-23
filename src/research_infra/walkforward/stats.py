"""The null, the dependence, and the multiplicity — the three ways a gate flatters a sleeve.

DEPENDENCE
----------
Day-aggregation in `panel.py` removes the *within-day* cluster. What remains is dependence
*across* days, and it is real: B279 measured that treating trades as iid understated the
delivered error budget by **2.1x to 7.7x** (crypto's 0.020 gate budget actually delivered
0.0956). Two independent treatments are available here and the gate runs both:

  * **Block sign-flip permutation** — `validation_integrity.perm_null.block_permutation_test`,
    reused rather than reimplemented. Flipping the sign of a contiguous block preserves
    within-block autocorrelation while randomising the block's direction.
  * **Circular block bootstrap** — implemented here. `validation_integrity` has no
    one-sided mean-null bootstrap (`perm_null.stationary_bootstrap_ci` returns a CI, not a
    p-value against H0: mu <= 0), but one directory up
    `methodology_alternatives.stationary_bootstrap_mean_test:180` DOES do exactly this
    construction. The honest reason for a second implementation is narrower than "it does
    not exist": that one loops in Python over `reps` and is unusable at `n_boot=10000`
    across 21 sleeves, and it lacks the add-one estimator that keeps p strictly positive.
    Same construction, different performance envelope — not a novel method.

WHY BOTH, AND WHY THE LARGER p
-------------------------------
The sign-flip null assumes the series is symmetric about zero. Realised R is not: it is
bounded below near -1 by the stop and open above at the target, so the distribution is
right-skewed with a hard left wall. Under skew, a sign-flip null can be anti-conservative.
The bootstrap needs no symmetry assumption but is more sensitive to short samples. They
fail in different directions, so `null_test="both_conservative"` takes **max(p)**. A gate
guarding a funded account should fail toward rejection.

MULTIPLICITY
------------
This is not a theoretical concern here; it is the actual provenance of the thing being
judged. The live market-expansion policy is named `positive_weighted12_after_swap` and it
is literally "the 12 of the 14 that came out positive"
(`candidate_registry.py:425-438`), selected on the same data that scored them, and then
chosen over `robust6_every_split_positive` on `monthly_pct`/`sharpe`
(`MARKET_EXPANSION_CONDITIONED_POLICY_METADATA`: 5.090 vs 5.052, 0.28419 vs 0.282076). A
gate that reports per-sleeve p-values without a family correction reproduces exactly that.

Benjamini-Hochberg (FDR) is the default rather than Bonferroni (FWER) because the question
here is "what fraction of what I admit is junk", not "what is the chance I admit any junk
at all" — a book can carry one bad sleeve out of ten; it cannot carry ten. Bonferroni is
offered and Borhen may prefer it; `ADMISSION_STANDARD_OPTIONS.md` prices both.

A worked example of why it matters, from this programme: the JPY-cluster live signal-level
p is quoted as 0.0059 in `THIRD_REVIEW.md:495` and in the brief for this session. The same
sentence in the source that produced it (`third_review_receipts/read_g1b.md:115`) continues:
"Bonferroni x12 -> **0.0706, which does NOT survive at 0.05**." The raw p travelled; the
correction did not.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from src.research_infra.validation_integrity import perm_null as _perm

__all__ = [
    "lag1_autocorr",
    "effective_n",
    "block_length_auto",
    "block_length_auto_segmented",
    "perm_p_floor",
    "weighted_effective_n",
    "apply_pooling_weights",
    "day_block_bootstrap_p",
    "block_permutation_p",
    "combined_null_p",
    "benjamini_hochberg",
    "bonferroni",
]


def lag1_autocorr(x: Sequence[float]) -> float:
    """Lag-1 autocorrelation. NaN when undefined (n<3 or zero variance)."""
    n = len(x)
    if n < 3:
        return float("nan")
    a = np.asarray(x, dtype=float)
    m = a.mean()
    d = a - m
    denom = float(np.dot(d, d))
    if denom <= 0.0:
        return float("nan")
    return float(np.dot(d[:-1], d[1:]) / denom)


def effective_n(x: Sequence[float]) -> float:
    """n * (1-rho)/(1+rho), the classic AR(1) variance-inflation adjustment.

    Reported as a diagnostic only — the gate's p-values come from the resampling, which
    needs no parametric dependence model. It is here so a reader can see how much of the
    nominal sample the dependence costs.
    """
    n = len(x)
    if n < 3:
        return float(n)
    rho = lag1_autocorr(x)
    if not math.isfinite(rho) or rho <= -0.999:
        return float(n)
    rho = min(max(rho, 0.0), 0.99)  # negative rho would *inflate* n; refuse that credit
    return float(n) * (1.0 - rho) / (1.0 + rho)


def _segment_arrays(
    x: Sequence[float] | np.ndarray,
    segment_lengths: Sequence[int] | None,
) -> tuple[np.ndarray, ...]:
    """Split a series without ever manufacturing adjacency across captures."""

    a = np.asarray(list(x) if not isinstance(x, np.ndarray) else x, dtype=float)
    if segment_lengths is None:
        return (a,)
    lengths = tuple(int(length) for length in segment_lengths)
    if not lengths or any(length <= 0 for length in lengths):
        raise ValueError("segment_lengths must contain positive integers")
    if sum(lengths) != len(a):
        raise ValueError(
            f"segment_lengths sum to {sum(lengths)}, series has {len(a)} observations"
        )
    out: list[np.ndarray] = []
    start = 0
    for length in lengths:
        out.append(a[start : start + length])
        start += length
    return tuple(out)


def block_length_auto(x: Sequence[float], min_blocks: int = 8) -> int:
    """Block length in days: max(cube-root rule, AR(1) decorrelation length), capped so at
    least ``min_blocks`` blocks exist.

    THE PREVIOUS RULE WAS WRONG IN TWO WAYS AND AN ADVERSARIAL REFUTER MEASURED BOTH.

    It took the first lag whose |ACF| fell below ``2/sqrt(n)``. That is a SIGNIFICANCE
    threshold — "is this autocorrelation distinguishable from zero at this n" — not a
    DECORRELATION criterion. At n=250 it evaluates to 0.1265, so for an AR(1) with rho=0.7
    it stopped at lag 7, where adjacent block sums were still correlated **0.258**. Measured
    type-I error at rho=0.7 was **2.1x nominal** (0.104 at alpha=0.05), against 0.044 when
    the block was forced to 30.

    Worse, when no lag qualified it fell through to ``l_acf = k + 1`` and pinned L at the
    cap. With the cap at ``n//4`` that forces exactly 4 blocks — and a block sign-flip null
    over B blocks has only ``2**B`` distinct outcomes, so its smallest attainable p-value is
    ``(1 + n_perm * 2**-B) / (n_perm + 1)`` REGARDLESS of n_perm. At B=4 that is 0.0626.
    Measured end to end: a series with mean +0.2793 R/day and a naive one-sided t-statistic
    of 13.49 got L=62, B=5, and a gate p of **0.1254** — a REJECT whose printed reason was
    indistinguishable from a real failure. Sweeping the block on the same series moved the
    decision statistic **1250x**.

    So: the decay criterion is now the AR(1)-implied lag at which the autocorrelation falls
    to 1%, ``ceil(ln(0.01)/ln(|rho1|))``, and the cap is ``n // min_blocks`` with
    min_blocks defaulting to 8 — enough blocks that a p-value below 1% is attainable at all.
    Whether the resulting floor is actually reachable at the caller's alpha is not silently
    assumed: `perm_p_floor` reports it and the gate refuses rather than rejecting when it
    binds.
    """
    n = len(x)
    if n < 8:
        return 1
    a = np.asarray(x, dtype=float)
    d = a - a.mean()
    denom = float(np.dot(d, d))
    cap = max(1, n // max(2, int(min_blocks)))
    l_cube = max(1, int(round(n ** (1.0 / 3.0))))
    if denom <= 0.0:
        return min(l_cube, cap)
    rho = abs(float(np.dot(d[:-1], d[1:]) / denom))
    if 1e-6 < rho < 0.999:
        l_ar = max(1, int(math.ceil(math.log(0.01) / math.log(rho))))
    elif rho >= 0.999:
        l_ar = cap
    else:
        l_ar = 1
    return int(min(max(l_cube, l_ar), cap))


def block_length_auto_segmented(
    x: Sequence[float],
    segment_lengths: Sequence[int],
    min_blocks: int = 8,
) -> int:
    """Auto block over the pooled sample without cross-capture lag pairs.

    Cube-root scale and the ``min_blocks`` cap are properties of the pooled null
    sample, so they retain the total observation count. Only the AR(1) numerator
    changes: its lag products restart inside each capture. Applying the cap to
    each short capture separately would silently shrink a declared three-day
    block to one day, which changes the test rather than merely fixing adjacency.
    """
    if min_blocks < 2:
        raise ValueError("min_blocks must be >= 2")

    segments = _segment_arrays(x, segment_lengths)
    n = sum(len(segment) for segment in segments)
    if n < 8:
        return 1
    a = np.concatenate(segments)
    d = a - a.mean()
    denom = float(np.dot(d, d))
    cap = max(1, n // max(2, int(min_blocks)))
    l_cube = max(1, int(round(n ** (1.0 / 3.0))))
    if denom <= 0.0:
        return min(l_cube, cap)
    start = 0
    numerator = 0.0
    for segment in segments:
        length = len(segment)
        local = d[start : start + length]
        if length > 1:
            numerator += float(np.dot(local[:-1], local[1:]))
        start += length
    rho = abs(numerator / denom)
    if 1e-6 < rho < 0.999:
        l_ar = max(1, int(math.ceil(math.log(0.01) / math.log(rho))))
    elif rho >= 0.999:
        l_ar = cap
    else:
        l_ar = 1
    return int(min(max(l_cube, l_ar), cap))


def perm_p_floor(
    n_obs: int,
    block: int,
    n_perm: int,
    *,
    segment_lengths: Sequence[int] | None = None,
) -> dict:
    """Smallest p the configured block sign-flip can attain.

    The sign-flip null has ``2**B`` distinct outcomes for ``B = ceil(n/L)`` blocks, so
    segmented exact enumeration floors p at ``1/2**B``; a sampled null uses the add-one
    floor ``1/(n_perm+1)``. The legacy continuous path retains its historical expected-MC
    floor. ``max(p_boot, p_perm)`` promotes this to the GATE's floor. Reported so a
    structurally unreachable threshold is never mistaken for a sleeve that failed.
    """
    if n_obs < 1:
        raise ValueError("n_obs must be >= 1")
    if block < 1:
        raise ValueError("block must be >= 1")
    if n_perm < 1:
        raise ValueError("n_perm must be >= 1")
    if segment_lengths is None:
        block_counts = [max(1, int(math.ceil(n_obs / max(1, block))))]
        block_lengths = [max(1, int(block))]
        exact = False
        floor = (1.0 + n_perm * (2.0 ** -sum(block_counts))) / (
            n_perm + 1.0
        )
        floor_basis = "legacy_expected_monte_carlo_add_one"
    else:
        lengths = tuple(int(length) for length in segment_lengths)
        if not lengths or any(length <= 0 for length in lengths):
            raise ValueError("segment_lengths must contain positive integers")
        if sum(lengths) != int(n_obs):
            raise ValueError(
                f"segment_lengths sum to {sum(lengths)}, n_obs is {n_obs}"
            )
        block_lengths = [min(max(1, int(block)), length) for length in lengths]
        block_counts = [
            int(math.ceil(length / segment_block))
            for length, segment_block in zip(lengths, block_lengths)
        ]
        distinct = 2 ** sum(block_counts)
        exact = distinct <= int(n_perm)
        floor = 1.0 / distinct if exact else 1.0 / (n_perm + 1.0)
        floor_basis = (
            "exact_sign_enumeration"
            if exact
            else "monte_carlo_add_one"
        )
    b = sum(block_counts)
    out = {"n_blocks": b, "two_pow_minus_b": 2.0 ** -b, "p_floor": floor,
           "n_obs": int(n_obs), "block": int(block), "n_perm": int(n_perm),
           "enumeration": "exact" if exact else "monte_carlo_add_one",
           "floor_basis": floor_basis}
    if segment_lengths is not None:
        out.update(
            {
                "segment_lengths": list(segment_lengths),
                "block_lengths_by_segment": block_lengths,
                "n_blocks_by_segment": block_counts,
                "boundary_policy": "blocks_restart_at_each_capture",
                "alignment_policy": "first_oos_day_of_each_sealed_capture",
            }
        )
    return out


def weighted_effective_n(w: Sequence[float]) -> dict:
    """Kish effective sample size of a weighted mean, and the largest single weight share.

    Reported because `pooling_weights="equal_by_fold"` can hand one small fold most of the
    estimator's leverage and nothing else would show it. Measured by an adversarial refuter:
    folds of [120,120,120,120,3] days give the 3-day fold **59%** of the leverage and cut
    the effective sample from 483 to 68 (14%); power at the BH threshold fell from 0.805 to
    0.133. That is a real sleeve rejected on significance while the printed reason blames
    its edge, so the diagnostic has to be visible.
    """
    n = len(w)
    if n == 0:
        return {"n": 0, "n_eff": 0.0, "n_eff_frac": float("nan"), "max_weight_share": float("nan")}
    tot = math.fsum(w)
    sq = math.fsum(wi * wi for wi in w)
    n_eff = (tot * tot / sq) if sq > 0 else 0.0
    return {
        "n": n,
        "n_eff": n_eff,
        "n_eff_frac": (n_eff / n) if n else float("nan"),
        "max_weight_share": (max(w) / tot) if tot > 0 else float("nan"),
    }


def apply_pooling_weights(x: Sequence[float], w: Sequence[float]) -> list[float]:
    """Fold pooling weights into the series so a plain mean IS the weighted mean.

    ``scaled_i = x_i * w_i * n / sum(w)``  =>  ``mean(scaled) == sum(w_i x_i) / sum(w)``.

    This keeps the point estimate and the null test on the same statistic under every
    pooling rule, without needing a weighted bootstrap or a weighted sign-flip. The
    rescaling is a fixed deterministic transform applied before any resampling, so the
    sign-flip null remains valid on it and the bootstrap's centring still imposes
    H0: weighted-mean <= 0. Without this, `pooling_weights="equal_by_fold"` would report a
    fold-weighted expectancy and test a day-weighted null — two different quantities, which
    is precisely the kind of gap the sealed spec exists to close.
    """
    n = len(x)
    if n == 0:
        return []
    if len(w) != n:
        raise ValueError(f"weights length {len(w)} != series length {n}")
    tot = math.fsum(w)
    if tot <= 0:
        raise ValueError("pooling weights sum to zero")
    k = n / tot
    return [float(xi) * float(wi) * k for xi, wi in zip(x, w)]


def day_block_bootstrap_p(
    x: Sequence[float],
    *,
    block: int,
    n_boot: int = 10000,
    seed: int = 20260729,
    segment_lengths: Sequence[int] | None = None,
) -> dict:
    """One-sided p for H0: mean <= 0, via a circular block bootstrap of the daily series.

    H0 is imposed by centring the series before resampling, which is the standard
    construction: the bootstrap distribution is then the sampling distribution of the mean
    *under the null*, and p is the mass at or above the observed mean. The add-one
    estimator floors p at 1/(n_boot+1), matching `perm_null`'s convention.

    Circular wrap keeps every block the same length so no observation is systematically
    under-weighted at the ends.
    """
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    if n_boot < 1:
        raise ValueError(f"n_boot must be >= 1, got {n_boot}")
    a = np.asarray(list(x), dtype=float)
    n = a.size
    if n < 2:
        return {"p_value": float("nan"), "observed": float("nan"), "n": int(n),
                "block": int(block), "n_boot": int(n_boot), "reason": "n<2"}
    if not np.all(np.isfinite(a)):
        raise ValueError("series contains non-finite values (NaN/Inf)")
    observed = float(a.mean())
    L = max(1, min(int(block), n))
    centred = a - observed  # impose H0 while retaining between-capture mean differences

    rng = np.random.default_rng(seed)
    if segment_lengths is None:
        wrapped = np.concatenate([centred, centred[: L - 1]]) if L > 1 else centred
        n_blocks = int(math.ceil(n / L))
        starts = rng.integers(0, n, size=(n_boot, n_blocks))
        # offsets[j] = 0..L-1 -> index into the wrapped array
        offs = np.arange(L)
        idx = (starts[:, :, None] + offs[None, None, :]).reshape(
            n_boot, n_blocks * L
        )[:, :n]
        boot_means = wrapped[idx].mean(axis=1)
        blocks_by_segment = [n_blocks]
        block_lengths_by_segment = [L]
    else:
        centred_segments = _segment_arrays(centred, segment_lengths)
        boot_sums = np.zeros(n_boot, dtype=float)
        blocks_by_segment = []
        block_lengths_by_segment = []
        for segment in centred_segments:
            segment_n = len(segment)
            segment_block = max(1, min(int(block), segment_n))
            block_lengths_by_segment.append(segment_block)
            wrapped = (
                np.concatenate([segment, segment[: segment_block - 1]])
                if segment_block > 1
                else segment
            )
            n_blocks = int(math.ceil(segment_n / segment_block))
            blocks_by_segment.append(n_blocks)
            starts = rng.integers(0, segment_n, size=(n_boot, n_blocks))
            offs = np.arange(segment_block)
            idx = (starts[:, :, None] + offs[None, None, :]).reshape(
                n_boot, n_blocks * segment_block
            )[:, :segment_n]
            boot_sums += wrapped[idx].sum(axis=1)
        boot_means = boot_sums / n

    ge = int(np.count_nonzero(boot_means >= observed))
    out = {
        "p_value": (1.0 + ge) / (n_boot + 1.0),
        "observed": observed,
        "null_mean": float(boot_means.mean()),
        "null_sd": float(boot_means.std(ddof=1)) if n_boot > 1 else 0.0,
        "null_p95": float(np.quantile(boot_means, 0.95)),
        "n": int(n),
        "block": int(L),
        "n_boot": int(n_boot),
    }
    if segment_lengths is not None:
        out.update(
            {
                "segment_lengths": list(segment_lengths),
                "block_lengths_by_segment": block_lengths_by_segment,
                "n_blocks_by_segment": blocks_by_segment,
                "boundary_policy": "circular_blocks_wrap_within_capture_only",
            }
        )
    return out


def block_permutation_p(
    x: Sequence[float],
    *,
    block: int,
    n_perm: int = 10000,
    seed: int = 20260729,
    segment_lengths: Sequence[int] | None = None,
) -> dict:
    """One-sided p from the package's block sign-flip test, on the MEAN.

    Continuous series compose `validation_integrity/perm_null.py:156`. Capture-segmented
    series apply that same prospective rule independently inside each sealed capture: the
    first block starts at the capture's first OOS day. Capture start is authority, not a
    nuisance selected after outcomes, so no circular phase is introduced. Fixed block-sign
    transformations form the declared randomization set; every sign assignment is enumerated
    when it fits inside ``n_perm``, otherwise the frozen seed drives an add-one Monte Carlo
    sample. `stat="mean"` rather than `"sharpe"` because the admission standard is stated in
    expectancy (R per day net of cost).
    """
    if len(x) < 2:
        return {"p_value": float("nan"), "observed": float("nan"), "reason": "n<2",
                "block": int(block), "n_perm": int(n_perm)}
    if segment_lengths is None:
        res = _perm.block_permutation_test(
            list(x), block=max(1, int(block)), n_perm=int(n_perm), stat="mean", seed=int(seed)
        )
        return dict(res)
    if block < 1:
        raise ValueError(f"block must be >= 1, got {block}")
    if n_perm < 1:
        raise ValueError(f"n_perm must be >= 1, got {n_perm}")
    segments = _segment_arrays(x, segment_lengths)
    if not all(np.all(np.isfinite(segment)) for segment in segments):
        raise ValueError("series contains non-finite values (NaN/Inf)")
    n = sum(len(segment) for segment in segments)
    observed = float(sum(float(segment.sum()) for segment in segments) / n)
    block_lengths = [max(1, min(int(block), len(segment))) for segment in segments]
    blocks_by_segment = [
        int(math.ceil(len(segment) / segment_block))
        for segment, segment_block in zip(segments, block_lengths)
    ]
    total_blocks = sum(blocks_by_segment)
    distinct_sign_assignments = 2 ** total_blocks
    exact = distinct_sign_assignments <= n_perm
    rng = np.random.default_rng(seed)
    if exact:
        states = np.arange(distinct_sign_assignments, dtype=np.uint64)[:, None]
        bits = np.arange(total_blocks, dtype=np.uint64)[None, :]
        all_block_signs = np.where(((states >> bits) & 1) == 1, 1.0, -1.0)
    else:
        all_block_signs = rng.choice(
            np.array([-1.0, 1.0]), size=(n_perm, total_blocks)
        )
    draws = len(all_block_signs)
    null_sums = np.zeros(draws, dtype=float)
    block_offset = 0
    for segment, n_blocks, segment_block in zip(
        segments, blocks_by_segment, block_lengths
    ):
        block_signs = all_block_signs[
            :, block_offset : block_offset + n_blocks
        ]
        block_offset += n_blocks
        signs = np.repeat(block_signs, segment_block, axis=1)[:, : len(segment)]
        null_sums += (signs * segment[np.newaxis, :]).sum(axis=1)
    null_stats = null_sums / n
    n_evaluated = len(null_stats)
    # A randomization tail includes transformations whose statistic is exactly
    # tied with the observation.  Different valid summation orders can put that
    # same algebraic value a few ulps below ``observed`` (for example, signed
    # decimal block sums with cancellation).  Bound only floating accumulation
    # error; do not apply a statistical or data-scale epsilon.
    mean_abs_scale = math.fsum(
        abs(float(value)) for segment in segments for value in segment
    ) / n
    tail_comparison_tolerance = (
        np.finfo(np.float64).eps
        * max(8, 4 * n)
        * max(1.0, mean_abs_scale)
    )
    total_ge = int(
        np.count_nonzero(null_stats >= observed - tail_comparison_tolerance)
    )
    p_value = (
        total_ge / n_evaluated
        if exact
        else (1.0 + total_ge) / (n_evaluated + 1.0)
    )
    null_mean = float(null_stats.mean())
    null_std = float(null_stats.std(ddof=0))
    if null_std > 0.0:
        p_value_normal = 0.5 * math.erfc(
            ((observed - null_mean) / null_std) / math.sqrt(2.0)
        )
    else:
        p_value_normal = 0.0 if observed > null_mean else 1.0
    return {
        "observed": observed,
        "p_value": float(p_value),
        "null_mean": null_mean,
        "null_p95": float(np.quantile(null_stats, 0.95)),
        "p_value_normal": float(p_value_normal),
        "null_std": null_std,
        "n_perm": int(n_perm),
        "n_permutations_evaluated": int(n_evaluated),
        "enumeration": "exact" if exact else "monte_carlo_add_one",
        "distinct_sign_assignments": int(distinct_sign_assignments),
        "block": int(block),
        "stat": "mean",
        "segment_lengths": list(segment_lengths),
        "block_lengths_by_segment": block_lengths,
        "n_blocks_by_segment": blocks_by_segment,
        "boundary_policy": "sign_blocks_restart_at_each_capture",
        "phase_policy": "none_capture_start_anchored",
        "alignment_policy": "first_oos_day_of_each_sealed_capture",
        "seed_effective": not exact,
        "tail_comparison_tolerance": float(tail_comparison_tolerance),
    }


def combined_null_p(
    x: Sequence[float],
    *,
    block: int,
    mode: str = "both_conservative",
    n_boot: int = 10000,
    n_perm: int = 10000,
    seed: int = 20260729,
    segment_lengths: Sequence[int] | None = None,
) -> dict:
    """Run the configured null(s) and return the p the gate will act on."""
    out: dict = {"mode": mode, "block": int(block)}
    if segment_lengths is not None:
        out.update(
            {
                "segment_lengths": list(segment_lengths),
                "boundary_policy": "null_blocks_restart_at_each_capture",
            }
        )
    boot = perm = None
    if mode in ("both_conservative", "bootstrap"):
        boot = day_block_bootstrap_p(
            x,
            block=block,
            n_boot=n_boot,
            seed=seed,
            segment_lengths=segment_lengths,
        )
        out["bootstrap"] = boot
    if mode in ("both_conservative", "permutation"):
        perm = block_permutation_p(
            x,
            block=block,
            n_perm=n_perm,
            seed=seed,
            segment_lengths=segment_lengths,
        )
        out["permutation"] = perm

    ps = [r["p_value"] for r in (boot, perm) if r is not None]
    ps = [p for p in ps if isinstance(p, float) and math.isfinite(p)]
    if not ps:
        out["p_value"] = float("nan")
        out["p_basis"] = "undefined"
        return out
    out["p_value"] = max(ps) if mode == "both_conservative" else ps[0]
    out["p_basis"] = "max(bootstrap, permutation)" if mode == "both_conservative" else mode
    return out


def benjamini_hochberg(pvalues: Sequence[float], alpha: float) -> dict:
    """Benjamini-Hochberg step-up FDR control.

    Genuinely absent from this repo before now: `validation_anti_overfit_v4.py:463` emits a
    `benjamini_hochberg_rank_alpha` COLUMN with no p-values and no rejection logic,
    self-labelled `"multiple_testing_control_design_not_validation_result"`.

    Returns `{"rejected": [bool...], "qvalues": [float...], "threshold": float, "k": int}`
    in the caller's original order. Non-finite p-values are treated as 1.0 (never rejected)
    rather than dropped, so a sleeve whose null could not be computed cannot quietly shrink
    the family and make its neighbours easier to admit.
    """
    m = len(pvalues)
    if m == 0:
        return {"rejected": [], "qvalues": [], "threshold": 0.0, "k": 0, "m": 0, "alpha": alpha}
    clean = [p if isinstance(p, float) and math.isfinite(p) else 1.0 for p in pvalues]
    order = sorted(range(m), key=lambda i: clean[i])
    k = 0
    thresh = 0.0
    for rank, i in enumerate(order, start=1):
        if clean[i] <= alpha * rank / m:
            k = rank
            thresh = alpha * rank / m
    rejected = [False] * m
    for rank, i in enumerate(order, start=1):
        if rank <= k:
            rejected[i] = True
    # Monotone step-up adjusted p-values (BH q-values).
    q = [1.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, clean[i] * m / rank)
        q[i] = min(1.0, running)
    return {"rejected": rejected, "qvalues": q, "threshold": thresh, "k": k, "m": m,
            "alpha": alpha}


def bonferroni(pvalues: Sequence[float], alpha: float) -> dict:
    """Bonferroni FWER control. Same return shape as `benjamini_hochberg`.

    NOT the first Bonferroni in this tree — `bonferroni_survival.bonferroni_correct:315` is
    the canonical one, and there are four further copies. It is not reused here only because
    it returns a bare adjusted-p list with no rejection mask, family size or threshold, and
    this gate needs the same shape as `benjamini_hochberg` so the two are interchangeable
    behind `spec.multiplicity`. The two differ on one edge case, deliberately: the existing
    one propagates NaN, this one coerces a non-finite p to 1.0 so an uncomputable null can
    never be rejected. If they are ever unified, that is the semantic to preserve.

    A THIRD OPTION THIS GATE DOES NOT TAKE, and should be revisited by Session X:
    `methodology_alternatives.romano_wolf_stepm:290` is a max-t bootstrap that preserves
    dependence ACROSS hypotheses and can therefore be far less conservative than Bonferroni
    on a correlated family. (An earlier revision of this docstring said dependence is
    something "both BH and Bonferroni assume away". That is wrong about Bonferroni, which
    is valid under ARBITRARY dependence by the union bound — it is merely conservative. BH
    is the one needing a positive-dependence condition, and measured on this family it is
    fine: FDR came out 0.068/0.068/0.062/0.055 at equicorrelation 0/0.3/0.6/0.9 against a
    0.067 target.) The reason it is not used is a real trade-off rather than an
    oversight: as implemented it row-resamples iid and is two-sided, so adopting it would
    buy cross-sleeve dependence at the cost of the across-day dependence that B279 measured
    as the larger error here (2.1x-7.7x). The right fix is a day-blocked StepM, which does
    not exist yet.
    """
    m = len(pvalues)
    if m == 0:
        return {"rejected": [], "qvalues": [], "threshold": 0.0, "k": 0, "m": 0, "alpha": alpha}
    clean = [p if isinstance(p, float) and math.isfinite(p) else 1.0 for p in pvalues]
    thresh = alpha / m
    rejected = [p <= thresh for p in clean]
    return {
        "rejected": rejected,
        "qvalues": [min(1.0, p * m) for p in clean],
        "threshold": thresh,
        "k": sum(rejected),
        "m": m,
        "alpha": alpha,
    }
