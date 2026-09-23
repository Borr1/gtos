"""Decay monitor (North-Star A3 / N4 decay-resistance / N7 compounding).

The edge factory must know which sleeves are DECAYING so it can demote them and prove that the
replacement-rate (new certified sleeves) exceeds the decay-rate (sleeves losing edge). This module
computes, per sleeve, a rolling-Sharpe trajectory and an honest decay verdict, and rolls them into a
book-level replacement-vs-decay summary.

Pure stdlib. Decay is judged on the SHAPE of the rolling Sharpe over time + the recent-vs-historical
ratio — NOT on a single blended average (the cardinal sin). A sleeve whose edge is intact shows a
flat/rising rolling Sharpe; a decaying one shows a falling trajectory and a recent window below its
own history.
"""
from __future__ import annotations

import statistics as st
from typing import Dict, List, Optional, Sequence, Tuple


def _sharpe(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    s = st.pstdev(xs)
    return (sum(xs) / len(xs)) / s if s > 0 else 0.0


def rolling_sharpe(series: Sequence[float], window: int) -> List[float]:
    """Rolling per-period Sharpe over a trailing `window`. Returns one value per position >= window-1."""
    out: List[float] = []
    n = len(series)
    if n < window:
        return out
    for end in range(window, n + 1):
        out.append(_sharpe(series[end - window:end]))
    return out


def _ols_slope(ys: Sequence[float]) -> float:
    """Slope of ys vs index (per-step) — the trajectory direction of the rolling Sharpe."""
    n = len(ys)
    if n < 2:
        return 0.0
    xbar = (n - 1) / 2.0
    ybar = sum(ys) / n
    num = sum((i - xbar) * (ys[i] - ybar) for i in range(n))
    den = sum((i - xbar) ** 2 for i in range(n))
    return num / den if den else 0.0


def decay_assessment(series: Sequence[float], *, recent_frac: float = 0.25, window: int = 60,
                     decay_ratio_thresh: float = 0.5) -> Dict:
    """Per-sleeve decay verdict.

    - full_sharpe          : Sharpe over the whole active series.
    - recent_sharpe        : Sharpe over the last recent_frac of the series.
    - historical_sharpe    : Sharpe over the FIRST (1-recent_frac).
    - recent_vs_hist_ratio : recent / historical (guard signs).
    - rolling_slope        : OLS slope of the rolling-`window` Sharpe trajectory (per step) — sign = direction.
    - verdict              : INTACT | DECAYING | DEAD | THIN (insufficient n).
    """
    n = len(series)
    if n < max(window, 40):
        return {"verdict": "THIN", "n": n, "full_sharpe": _sharpe(series) if n >= 2 else 0.0,
                "recent_sharpe": None, "historical_sharpe": None, "recent_vs_hist_ratio": None,
                "rolling_slope": None}
    k = max(20, int(n * recent_frac))
    recent = series[-k:]
    hist = series[:n - k]
    full_sh = _sharpe(series)
    rec_sh = _sharpe(recent)
    hist_sh = _sharpe(hist) if len(hist) >= 2 else 0.0
    ratio = (rec_sh / hist_sh) if hist_sh > 1e-9 else (float("inf") if rec_sh > 0 else 0.0)
    roll = rolling_sharpe(series, window)
    slope = _ols_slope(roll) if len(roll) >= 5 else 0.0
    # Verdict logic (shape + level, never a single blended number alone):
    if rec_sh <= 0 and full_sh > 0:
        verdict = "DEAD"            # the recent window has lost the edge outright
    elif hist_sh > 0 and ratio < decay_ratio_thresh and slope < 0:
        verdict = "DECAYING"       # recent materially below history AND trajectory falling
    elif rec_sh > 0 and (ratio >= decay_ratio_thresh or slope >= 0):
        verdict = "INTACT"
    else:
        verdict = "DECAYING"
    return {"verdict": verdict, "n": n, "full_sharpe": full_sh, "recent_sharpe": rec_sh,
            "historical_sharpe": hist_sh, "recent_vs_hist_ratio": ratio, "rolling_slope": slope,
            "recent_window_len": k, "rolling_window": window}


def book_decay_report(sleeve_series: Dict[str, Sequence[float]], *, recent_frac: float = 0.25,
                      window: int = 60) -> Dict:
    """Run decay_assessment per sleeve + a book-level replacement-vs-decay summary.

    sleeve_series: name -> daily-R series (already aligned per sleeve; zeros on inactive days are fine).
    """
    per_sleeve = {name: decay_assessment(s, recent_frac=recent_frac, window=window)
                  for name, s in sleeve_series.items()}
    counts: Dict[str, int] = {}
    for a in per_sleeve.values():
        counts[a["verdict"]] = counts.get(a["verdict"], 0) + 1
    n_alive = counts.get("INTACT", 0)
    n_decaying = counts.get("DECAYING", 0) + counts.get("DEAD", 0)
    return {"per_sleeve": per_sleeve, "verdict_counts": counts,
            "n_intact": n_alive, "n_decaying_or_dead": n_decaying,
            "decay_rate": n_decaying / len(per_sleeve) if per_sleeve else 0.0,
            "summary": f"{n_alive} intact / {n_decaying} decaying-or-dead / "
                       f"{counts.get('THIN',0)} thin of {len(per_sleeve)} sleeves"}
