#!/usr/bin/env python3
"""Measured-R geometry. Both directions. Never up>=0.5.

Cohort A contract (default):
  stop ∈ {0.75, 1, 1.5, 2, 3}
  target ∈ {1, 2, 3, 4, 6}
  direction ∈ {+1, −1}
  maxbars = 32
  first-touch, stop wins same-bar ties, entry = close
  split 2022-01-01
  best_both_halves = max holdout R among (side, stop, target) with
  R_disc > 0 and R_hold > 0 and n_disc, n_hold ≥ 80
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

import numpy as np

STOPS = (0.75, 1.0, 1.5, 2.0, 3.0)
TGTS = (1.0, 2.0, 3.0, 4.0, 6.0)
H = 32
MIN_N_HALF = 80
MDE80_MULT = 2.1231727991175147


def day_blocked_se(day_sum: np.ndarray, day_n: np.ndarray) -> tuple[float, int]:
    """Cluster-robust SE of the pooled mean, one block per weekday-date.

    Never iid √n. Each UTC calendar date is one block. The point estimate
    this SE belongs to is sum(R)/n (the same R_disc / R_hold we publish).
    """
    mask = np.asarray(day_n) > 0
    B = int(mask.sum())
    if B < 2:
        return float("nan"), B
    s = np.asarray(day_sum, dtype=np.float64)[mask]
    c = np.asarray(day_n, dtype=np.float64)[mask]
    N = float(c.sum())
    if N <= 0:
        return float("nan"), B
    mu = float(s.sum() / N)
    resid = s - mu * c
    var = (B / (B - 1.0)) * float(np.dot(resid, resid)) / (N * N)
    return float(np.sqrt(max(var, 0.0))), B


def firsthit(arr: np.ndarray, lvl: float, ge: bool = True) -> np.ndarray:
    """arr (H, n) running excursion; first k (1-indexed) where it crosses lvl, else 999."""
    H_, n = arr.shape
    k = np.full(n, 999, dtype=np.int16)
    for i in range(H_ - 1, -1, -1):
        hit = (arr[i] >= lvl) if ge else (arr[i] <= lvl)
        k = np.where(hit & np.isfinite(arr[i]), np.int16(i + 1), k)
    return k


def first_touch_R(
    mfe: np.ndarray,
    mae: np.ndarray,
    to: np.ndarray,
    stop: float,
    target: float,
    side: float,
) -> np.ndarray:
    """First-touch R. side +1 long / −1 short. Stop wins ties (ks <= kt → −1)."""
    if side > 0:
        MFE, MAE, TO = mfe, mae, to
    else:
        MFE, MAE, TO = -mae, -mfe, -to
    ks = firsthit(MAE, -stop, ge=False)
    kt = firsthit(MFE, target, ge=True)
    return np.where(
        (ks <= kt) & (ks < 999),
        -1.0,
        np.where((kt < ks) & (kt < 999), target / stop, np.clip(TO, -stop, target) / stop),
    ).astype(np.float32)


def add_cell(agg: dict, key: str, n: int, sR: float, nwin: int) -> None:
    cur = agg.get(key, [0, 0.0, 0])
    agg[key] = [cur[0] + n, cur[1] + sR, cur[2] + nwin]


def cell_record(a: list, b: list, side: str, stop: float, target: float) -> dict[str, Any]:
    md, mh = a[1] / a[0], b[1] / b[0]
    return {
        "side": side,
        "stop_atr": stop,
        "target_atr": target,
        "n_disc": int(a[0]),
        "n_hold": int(b[0]),
        "R_disc": float(md),
        "R_hold": float(mh),
        "win_disc": float(a[2] / a[0]),
        "win_hold": float(b[2] / b[0]),
        "both_positive": bool(md > 0 and mh > 0),
    }


def best_both_halves(
    rec: Mapping[str, list],
    *,
    stops: Iterable[float] = STOPS,
    tgts: Iterable[float] = TGTS,
    min_n: int = MIN_N_HALF,
    sides: Iterable[str] = ("L", "S"),
    side_names: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Pick the best (side, stop, target) that is positive in both eras.

    rec keys: '{tag}|{S}|{T}|{era}' -> [n, sum_R, n_win]
    V2 up-rate is not consulted. Side is an output of this search.
    """
    names = side_names or {"L": "LONG", "S": "SHORT", "R": "RESOLVER", "F": "FADE_RESOLVER"}
    cands = []
    for tag in sides:
        for S in stops:
            for T in tgts:
                a = rec.get(f"{tag}|{S}|{T}|0")
                b = rec.get(f"{tag}|{S}|{T}|1")
                if not a or not b or a[0] < min_n or b[0] < min_n:
                    continue
                cands.append(cell_record(a, b, names.get(tag, tag), float(S), float(T)))
    both = [c for c in cands if c["both_positive"]]
    both.sort(key=lambda c: c["R_hold"], reverse=True)
    return {
        "best_both_halves": both[0] if both else None,
        "n_both_positive": len(both),
        "n_candidates": len(cands),
        "top5": both[:5],
    }
