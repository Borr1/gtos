"""Sub-selection stability control (North-Star N6 — the 3rd selection-leak guard).

THE LESSON (cycles 30→32). After walk-forward CELL selection (cycle-23) exposed that selecting cells
on the data the series spans inflates the edge, the program tried a fresh lens: discover market
REGIMES (k-means on leak-free past-only features) and concentrate an edge into its in-sample-best
regime. Cycle-30 reported a metals "IC upgrade" (R2 train-best AND OOS-best, +0.772). But cycle-32
stress-tested it across 96 reasonable specifications (feature-subset × K × seed) and the in-sample-best
regime beat the FULL sleeve OOS in only 54% — a coin flip, mean improvement ≈ 0. The cycle-30 result
was a favorable DRAW, not a stable edge.

THE PRINCIPLE this codifies: a REGIME label is just another selection dimension. ANY data-driven
sub-selection (regime/cluster/threshold/top-N) of an edge must, to be deployable, beat the FULL
population OOS in the LARGE MAJORITY of reasonable clustering specifications — not in one favorable
choice of (features, K, seed). A genuine sub-edge is STABLE to researcher degrees of freedom; an
artifact is a coin flip. This is the regime-level analogue of the walk-forward-cell-selection control.

`subselection_stability` sweeps (feature-subset × K × seed), and for each spec fits k-means on the
IN-SAMPLE rows ONLY (leak-free), picks the in-sample-best group (a train decision), and checks whether
concentrating to it BEATS trading the full population OOS. STABLE iff the beat-rate >= threshold AND
mean OOS improvement > 0. Use it before deploying any regime/sub-selection-conditioned sleeve.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence
import statistics as _st

import numpy as np


def _kmeans(X: np.ndarray, k: int, seed: int, iters: int = 80) -> np.ndarray:
    """Tiny deterministic k-means++ (no sklearn dep). X assumed standardized."""
    rng = np.random.default_rng(seed)
    idx = [int(rng.integers(len(X)))]
    for _ in range(1, k):
        d2 = np.min(((X[:, None, :] - X[idx][None, :, :]) ** 2).sum(-1), axis=1)
        tot = d2.sum()
        p = d2 / tot if tot > 0 else np.full(len(X), 1.0 / len(X))
        idx.append(int(rng.choice(len(X), p=p)))
    C = X[idx].copy()
    for _ in range(iters):
        lab = np.argmin(((X[:, None, :] - C[None, :, :]) ** 2).sum(-1), axis=1)
        newC = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
        if np.allclose(newC, C):
            break
        C = newC
    return C


def _mean(xs) -> float:
    return float(sum(xs) / len(xs)) if len(xs) else 0.0


def subselection_stability(returns: Sequence[float],
                           features: Sequence[Sequence[float]],
                           in_sample_mask: Sequence[bool],
                           *,
                           ks: Sequence[int] = (2, 3, 4),
                           n_seeds: int = 8,
                           feature_subsets: Optional[Sequence[Sequence[int]]] = None,
                           min_group: int = 8,
                           beat_threshold: float = 0.75,
                           min_mean_delta: float = 0.0) -> Dict:
    """Is concentrating an edge to its in-sample-best discovered sub-group a STABLE deployable
    improvement over trading the full population, or a favorable-draw artifact?

    returns         : per-trade outcome (R) aligned with `features` and `in_sample_mask`.
    features        : per-trade feature vectors used to discover sub-groups (e.g. regime features).
    in_sample_mask  : True where the trade is in the SELECTION (train/past-only) window; the
                      sub-group choice may ONLY use these. OOS = the rest (never-seen).
    Sweeps feature_subsets × ks × seeds. For each spec: standardize on in-sample rows, k-means,
    pick the in-sample-best group (mean R, >=min_group support), and compare that group's OOS mean
    R to the FULL-population OOS mean R. Returns the fraction of specs where the sub-selection BEATS
    the full population OOS and the mean OOS improvement.

    Verdict STABLE_SUBSELECTION iff beat_rate >= beat_threshold AND mean_delta > min_mean_delta;
    else UNSTABLE_SELECTION (the apparent sub-edge is researcher degrees of freedom — deploy the
    FULL population, do not add the sub-selection gate).
    """
    R = np.asarray(returns, float)
    X = np.asarray(features, float)
    if X.ndim != 2:
        raise ValueError("features must be 2-D (n_trades × n_features)")
    if not (len(R) == len(X) == len(in_sample_mask)):
        raise ValueError("returns, features, in_sample_mask must align in length")
    mask = np.asarray(in_sample_mask, bool)
    oos = ~mask
    n_feat = X.shape[1]
    if feature_subsets is None:
        feature_subsets = [list(range(n_feat))]
        if n_feat >= 2:                                  # add leave-one-out subsets for the sweep
            feature_subsets += [[j for j in range(n_feat) if j != drop] for drop in range(n_feat)]

    full_oos = _mean(R[oos])
    Xis_all = X[mask]
    if len(Xis_all) < min_group or oos.sum() < min_group:
        return {"verdict": "INSUFFICIENT", "n_in_sample": int(mask.sum()), "n_oos": int(oos.sum()),
                "full_oos_ev": round(full_oos, 4)}

    beats = 0
    total = 0
    deltas = []
    for cols in feature_subsets:
        cols = list(cols)
        if not cols:
            continue
        mu = Xis_all[:, cols].mean(0)
        sd = Xis_all[:, cols].std(0)
        sd = np.where(sd == 0, 1.0, sd)
        Xz_all = (X[:, cols] - mu) / sd
        Xz_is = Xz_all[mask]
        for k in ks:
            if len(Xz_is) < k * max(2, min_group // 2):
                continue
            for seed in range(n_seeds):
                C = _kmeans(Xz_is, k, seed)
                lab = np.argmin(((Xz_all[:, None, :] - C[None, :, :]) ** 2).sum(-1), axis=1)
                lab_is, lab_oos = lab[mask], lab[oos]
                R_is, R_oos = R[mask], R[oos]
                # in-sample-best group (>= min_group support) — the train decision
                cand = [g for g in range(k) if (lab_is == g).sum() >= min_group]
                if not cand:
                    continue
                best = max(cand, key=lambda g: _mean(R_is[lab_is == g]))
                sub_oos = _mean(R_oos[lab_oos == best])
                total += 1
                deltas.append(sub_oos - full_oos)
                if sub_oos > full_oos:
                    beats += 1

    if total == 0:
        return {"verdict": "INSUFFICIENT", "n_in_sample": int(mask.sum()), "n_oos": int(oos.sum()),
                "full_oos_ev": round(full_oos, 4)}

    beat_rate = beats / total
    mean_delta = _mean(deltas)
    stable = (beat_rate >= beat_threshold) and (mean_delta > min_mean_delta)
    return {
        "verdict": "STABLE_SUBSELECTION" if stable else "UNSTABLE_SELECTION",
        "beat_rate": round(beat_rate, 4),
        "n_specs": total,
        "mean_oos_delta": round(mean_delta, 4),
        "median_oos_delta": round(float(_st.median(deltas)), 4),
        "min_oos_delta": round(min(deltas), 4),
        "max_oos_delta": round(max(deltas), 4),
        "full_oos_ev": round(full_oos, 4),
        "beat_threshold": beat_threshold,
        "note": ("STABLE => the sub-selection robustly beats the full population OOS across "
                 "specifications (a real sub-edge). UNSTABLE => coin-flip/zero-mean improvement "
                 "= favorable-draw artifact; deploy the FULL population, reject the sub-gate."),
    }


def assert_subselection_robust(returns, features, in_sample_mask, **kw) -> Dict:
    """Convenience guard: returns the stability report and raises AssertionError if UNSTABLE.
    Use to fail-closed before wiring a regime/sub-selection-conditioned sleeve into the book."""
    rep = subselection_stability(returns, features, in_sample_mask, **kw)
    if rep["verdict"] == "UNSTABLE_SELECTION":
        raise AssertionError(
            f"sub-selection UNSTABLE (beat_rate {rep['beat_rate']} < {rep['beat_threshold']}, "
            f"mean OOS delta {rep['mean_oos_delta']}): favorable-draw artifact, deploy the full "
            f"population — do NOT add the sub-selection/regime gate.")
    return rep


def universe_robustness(eval_on_universe, full_universe, *,
                        n_draws: int = 24, subset_fracs=(0.5, 0.7, 0.9), seed: int = 0,
                        min_universe: int = 6, beat_threshold: float = 0.6) -> Dict:
    """4th selection-leak guard (cycles 47-49 lesson): is a CROSS-SECTIONAL / multi-instrument edge a
    real mechanism, or an INSTRUMENT-SUBSET selection artifact?

    A cross-sectional edge claimed on a hand-picked instrument subset can be a subset artifact: it
    looks real on those names but INVERTS when the comparable universe is broadened (cycle-49: the FX
    volume-climax reversal was +0.25 OOS Sharpe on 14 crosses, −0.18 on the full 28 G10 crosses). The
    existing guards (placebo / walk-forward-cell-selection / sub-selection-stability) test the return
    series / cells / regime sub-selection — NONE tests the INSTRUMENT-SET selection. This does.

    eval_on_universe(universe: list) -> float : the edge's OOS metric (higher = better, e.g. OOS Sharpe
      or EV) recomputed on the given instrument list. full_universe : the FULL comparable instrument set.
    Evaluates the FULL universe, plus n_draws random subsets across subset_fracs. ROBUST iff the FULL
    universe metric > 0 AND the fraction of random subsets with metric > 0 >= beat_threshold; else
    SUBSET_SELECTION_ARTIFACT (the edge depends on the specific instrument subset, not the mechanism).
    """
    full_universe = list(full_universe)
    if len(full_universe) < min_universe:
        return {"verdict": "INSUFFICIENT", "n_universe": len(full_universe)}
    rng = np.random.default_rng(seed)
    full_metric = float(eval_on_universe(full_universe))
    draws = []
    for _ in range(n_draws):
        frac = float(subset_fracs[int(rng.integers(len(subset_fracs)))])
        k = max(min_universe, int(round(len(full_universe) * frac)))
        k = min(k, len(full_universe))
        idx = rng.choice(len(full_universe), size=k, replace=False)
        sub = [full_universe[i] for i in idx]
        draws.append(float(eval_on_universe(sub)))
    pos = sum(1 for m in draws if m > 0)
    beat_rate = pos / len(draws) if draws else 0.0
    robust = (full_metric > 0) and (beat_rate >= beat_threshold)
    return {
        "verdict": "ROBUST_UNIVERSE" if robust else "SUBSET_SELECTION_ARTIFACT",
        "full_universe_metric": round(full_metric, 5),
        "subset_positive_rate": round(beat_rate, 4), "n_draws": len(draws),
        "subset_metric_mean": round(float(_mean(draws)), 5),
        "subset_metric_min": round(min(draws), 5), "subset_metric_max": round(max(draws), 5),
        "beat_threshold": beat_threshold,
        "note": ("ROBUST => the edge holds on the full comparable universe and most random subsets (a "
                 "mechanism). SUBSET_SELECTION_ARTIFACT => it depends on the hand-picked instrument set "
                 "(inverts/collapses when broadened) — do NOT deploy; it is instrument-set overfitting."),
    }


def assert_universe_robust(eval_on_universe, full_universe, **kw) -> Dict:
    """Fail-closed guard for a cross-sectional/multi-instrument edge before deploy."""
    rep = universe_robustness(eval_on_universe, full_universe, **kw)
    if rep["verdict"] == "SUBSET_SELECTION_ARTIFACT":
        raise AssertionError(
            f"universe NOT robust (full-universe metric {rep['full_universe_metric']}, subset "
            f"positive-rate {rep['subset_positive_rate']}): instrument-subset artifact — do NOT deploy.")
    return rep
