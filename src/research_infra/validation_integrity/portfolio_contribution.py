"""Portfolio-contribution certification — the diversifier gate (North-Star N2/√breadth).

The standalone Validation-Integrity Gauntlet (dsr.py) deflates a strategy's Sharpe against the
expected MAX of N trials — the correct test for "is this the best of a big search" (cherry-picking
ONE strategy). But the north star is Sharpe × BREADTH: a genuine, regime-clean, ~uncorrelated edge
RAISES the pooled book's Sharpe even when its standalone Sharpe is below the max-of-N bar. That is
the Fundamental Law of Active Management (IR ≈ IC × √breadth) — many small uncorrelated edges pool
into a high book Sharpe.

This module certifies a candidate as a book-IMPROVING diversifier WITHOUT lowering the honesty bar:
  1. genuine edge        — caller supplies the standalone gauntlet result; require PSR-vs-zero
                           significant, permutation-significant, PBO<0.5, regime contamination_flag FALSE.
  2. positive contribution — at a FIXED, non-optimized satellite weight (default 0.5× book risk),
                           the vol-matched book+candidate daily Sharpe exceeds the book alone.
  3. significance        — block-permutation null: shuffle the candidate's day-blocks (break any real
                           book-timing relationship) and recompute the Sharpe improvement; the real
                           improvement must beat that null (this is the multiple-testing-honest test of
                           the DIVERSIFICATION, not of the candidate alone).
  4. OOS-robust          — the improvement holds on a held-out (e.g. sealed) split, not just in-sample.
  5. low correlation     — |corr to book| below a ceiling (diversification, not duplication).
  6. no risk regression  — caller may supply an MC breach/drawdown delta; require it not to worsen.

Pure stdlib + the package's own perm_null/regime helpers. No scipy.
"""
from __future__ import annotations

import math
import statistics as st
from typing import Dict, List, Optional, Sequence, Tuple


def _pop_std(xs: Sequence[float]) -> float:
    return st.pstdev(xs) if len(xs) > 1 else 0.0


def _sharpe(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    s = _pop_std(xs)
    return (sum(xs) / len(xs)) / s if s > 0 else 0.0


def _align_union(book_by_day: Dict[str, float], cand_by_day: Dict[str, float]) -> Tuple[List[str], List[float], List[float]]:
    """Union of trading days; a day absent from one series contributes 0 there (flat = no position)."""
    days = sorted(set(book_by_day) | set(cand_by_day))
    b = [book_by_day.get(d, 0.0) for d in days]
    c = [cand_by_day.get(d, 0.0) for d in days]
    return days, b, c


def _corr_on_overlap(book_by_day: Dict[str, float], cand_by_day: Dict[str, float]) -> Tuple[float, int]:
    common = sorted(set(book_by_day) & set(cand_by_day))
    if len(common) < 6:
        return float("nan"), len(common)
    b = [book_by_day[d] for d in common]
    c = [cand_by_day[d] for d in common]
    mb, mc = sum(b) / len(b), sum(c) / len(c)
    sb, sc = _pop_std(b), _pop_std(c)
    if sb == 0 or sc == 0:
        return 0.0, len(common)
    cov = sum((bi - mb) * (ci - mc) for bi, ci in zip(b, c)) / len(b)
    return cov / (sb * sc), len(common)


def combine_vol_matched(book: Sequence[float], cand: Sequence[float], weight: float) -> List[float]:
    """book + (weight * book_sd / cand_sd) * cand  — candidate scaled to `weight` fraction of book daily risk."""
    sd_b, sd_c = _pop_std(book), _pop_std(cand)
    scale = (weight * sd_b / sd_c) if sd_c > 0 else 0.0
    return [book[i] + scale * cand[i] for i in range(len(book))]


def incremental_sharpe(book_by_day: Dict[str, float], cand_by_day: Dict[str, float], weight: float = 0.5) -> Dict[str, float]:
    days, b, c = _align_union(book_by_day, cand_by_day)
    base = _sharpe(b)
    comb = _sharpe(combine_vol_matched(b, c, weight))
    return {"book_sharpe": base, "combined_sharpe": comb, "delta": comb - base,
            "delta_pct": (comb - base) / base * 100.0 if base else 0.0, "weight": weight, "n_days_union": len(days)}


def contribution_bootstrap_ci(book_by_day: Dict[str, float], cand_by_day: Dict[str, float],
                              weight: float = 0.5, block: int = 5, n_boot: int = 3000,
                              alpha: float = 0.05, seed: int = 12345) -> Dict[str, float]:
    """PAIRED stationary block-bootstrap CI on the delta-Sharpe (combined - book).

    The right significance question for a DIVERSIFIER is not "does its timing matter" (a block
    permutation preserves the candidate mean, so it cannot answer this) but "is the Sharpe
    improvement real given finite-sample noise". We resample contiguous day-blocks of the PAIRED
    (book, cand) union series, recompute delta-Sharpe on each resample, and report the percentile CI.
    delta is significant if the lower CI bound is > 0.
    """
    days, b, c = _align_union(book_by_day, cand_by_day)
    n = len(b)
    base = _sharpe(b)
    observed = _sharpe(combine_vol_matched(b, c, weight)) - base
    a, cc, m = 1664525, 1013904223, 2 ** 32
    state = seed & 0xFFFFFFFF
    p_restart = 1.0 / block
    deltas: List[float] = []
    for _ in range(n_boot):
        bb: List[float] = []
        cb: List[float] = []
        idx = 0
        # stationary bootstrap: geometric block lengths, circular wrap
        while len(bb) < n:
            state = (a * state + cc) % m
            idx = state % n
            while True:
                bb.append(b[idx]); cb.append(c[idx])
                if len(bb) >= n:
                    break
                state = (a * state + cc) % m
                if (state / m) < p_restart:
                    break
                idx = (idx + 1) % n
        bb = bb[:n]; cb = cb[:n]
        d = _sharpe(combine_vol_matched(bb, cb, weight)) - _sharpe(bb)
        deltas.append(d)
    deltas.sort()
    lo = deltas[int((alpha / 2) * n_boot)]
    hi = deltas[int((1 - alpha / 2) * n_boot)]
    return {"observed_delta": observed, "ci_low": lo, "ci_high": hi,
            "significant": lo > 0, "alpha": alpha, "n_boot": n_boot, "weight": weight}


def split_robust_contribution(book_by_day: Dict[str, float], cand_by_day: Dict[str, float],
                              sealed_start: str, weight: float = 0.5) -> Dict[str, Dict]:
    """Incremental Sharpe computed on the pre-sealed and on the sealed slice separately."""
    pre_book = {d: v for d, v in book_by_day.items() if d < sealed_start}
    pre_cand = {d: v for d, v in cand_by_day.items() if d < sealed_start}
    se_book = {d: v for d, v in book_by_day.items() if d >= sealed_start}
    se_cand = {d: v for d, v in cand_by_day.items() if d >= sealed_start}
    return {"pre_sealed": incremental_sharpe(pre_book, pre_cand, weight),
            "sealed": incremental_sharpe(se_book, se_cand, weight)}


def certify_diversifier(book_by_day: Dict[str, float], cand_by_day: Dict[str, float], *,
                        standalone_edge_ok: bool, regime_clean: bool, sealed_start: str,
                        weight: float = 0.5, corr_ceiling: float = 0.35,
                        mc_breach_delta: Optional[float] = None, n_boot: int = 3000) -> Dict:
    """Full diversifier certification.

    standalone_edge_ok : caller-supplied bool — the candidate is a genuine edge vs ZERO (PSR-vs-zero
                         significant AND block-permutation directional p<0.05). Computed by the caller
                         from dsr.probabilistic_sharpe_ratio + perm_null.block_permutation_test (PBO is
                         a multi-strategy concept and is not required for a single diversifier sleeve).
    regime_clean       : caller-supplied bool — regime_inflation contamination_flag is False (the edge
                         is NOT selection/regime-inflated; its sealed magnitude is not a hot-window artifact).
    """
    inc = incremental_sharpe(book_by_day, cand_by_day, weight)
    boot = contribution_bootstrap_ci(book_by_day, cand_by_day, weight, n_boot=n_boot)
    splits = split_robust_contribution(book_by_day, cand_by_day, sealed_start, weight)
    corr, n_overlap = _corr_on_overlap(book_by_day, cand_by_day)

    checks = {
        "genuine_edge": {"pass": bool(standalone_edge_ok)},
        "regime_clean": {"pass": bool(regime_clean)},
        "positive_contribution": {"pass": inc["delta"] > 0, "delta": inc["delta"], "delta_pct": inc["delta_pct"]},
        "contribution_significant": {"pass": boot["significant"], "ci_low": boot["ci_low"], "ci_high": boot["ci_high"]},
        "oos_robust": {"pass": splits["sealed"]["delta"] > 0, "sealed_delta": splits["sealed"]["delta"],
                       "pre_sealed_delta": splits["pre_sealed"]["delta"]},
        "low_correlation": {"pass": (not math.isnan(corr)) and abs(corr) <= corr_ceiling, "corr": corr, "n_overlap": n_overlap},
        "no_risk_regression": {"pass": (mc_breach_delta is None) or (mc_breach_delta <= 1e-9), "mc_breach_delta": mc_breach_delta},
    }
    all_pass = all(v["pass"] for v in checks.values())
    verdict = "CERTIFIED_DIVERSIFIER" if all_pass else "NOT_CERTIFIED"
    reasons = [k for k, v in checks.items() if not v["pass"]]
    return {"verdict": verdict, "weight": weight, "incremental": inc, "bootstrap": boot,
            "splits": splits, "corr_to_book": corr, "checks": checks, "failed_checks": reasons}
