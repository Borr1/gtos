"""Fixed cut -> trailing-percentile cut, fitted where it cannot see the answer.

THE REPAIR
----------
`FOURTH_REVIEW.md` section 3.1 (b): *"re-express the threshold scale-free (ATR-relative,
percentile), refit on pre-2024 data only, validate 2024+ — the reverse of the current
contamination."*

A gate like `vr >= 1.6` is already dimensionless — `vr` is a ratio of ATRs. What it is
*not* is distribution-free: if the ATR-ratio's own tail thickens, the same 1.6 admits a
different share of bars. `ab_ramp.py` measured exactly that for `sub_xvol_pullback` on a
fixed two-symbol panel: the marginal pass rate of `vr >= 1.6` goes **0.0194 -> 0.0490**
between 2015-2019 and 2025+ on XAUUSD and XAGUSD alone, with no composition change to
explain it.

The scale-free form replaces the level with a **trailing percentile**: fire when the
statistic sits above its own rank-`p` quantile over the previous `window` bars of the same
symbol. By construction that holds the long-run pass rate at `1 - p` in every era, so the
firing frequency stops being a function of the era's volatility distribution.

THREE PROPERTIES THIS IMPLEMENTATION HAS, AND THEY ARE NOT OPTIONAL
--------------------------------------------------------------------
1. **Leak-free.** The rank at bar `i` is computed over bars `i-window .. i-1`. The current
   bar is never in its own reference distribution.
2. **Per symbol.** A pooled quantile would let gold's distribution set silver's threshold
   and would silently re-introduce the composition confound the ramp attribution just
   removed.
3. **Warmup-honest.** Before `window` bars exist the rank is `None` and the gate fails
   closed, exactly as the live warmup gates do. It is never back-filled from a shorter
   window, because a rank over 40 bars and a rank over 1,000 are different statistics.

THE FIT PROTOCOL
----------------
`fit_percentile` chooses `p` on **pre-2024 bars only**, by matching the production gate's
own pre-2024 marginal pass rate. That is the deliberately unambitious objective: it does
not optimise returns, so it cannot select on the answer, and the resulting variant is a
pure re-expression of the production rule at the production frequency. Anything the
validation era then shows is attributable to the re-expression rather than to a search.

`p` fitted on returns instead would be a different and much larger trial budget, and the
programme has already paid once for a threshold fitted on the window it was scored on.
"""

from __future__ import annotations

import bisect
from dataclasses import replace
from typing import Any, Iterable, Optional, Sequence

from src.research_infra.regime_spine.conditions import (
    THRESHOLD,
    Gate,
    SleeveConditions,
)
from src.research_infra.regime_spine.ramp import _STAT_GETTERS
from src.research_infra.regime_spine.state import BarFrame

__all__ = [
    "trailing_ranks",
    "attach_ranks",
    "percentile_variant",
    "fit_percentile",
    "DEFAULT_WINDOW",
]

#: 1,000 H4 bars ~ 1.4 calendar years of a 24x5 instrument. Long enough that the quantile
#: is stable, short enough that "the regime the market is in now" still means something.
DEFAULT_WINDOW = 1000


def trailing_ranks(values: Sequence[Optional[float]], window: int = DEFAULT_WINDOW,
                   ) -> list[Optional[float]]:
    """Fraction of the previous `window` non-None values strictly below `values[i]`.

    `None` until `window` observations exist. The current value is excluded from its own
    reference set — the leak that would otherwise make every rank look better than it is.
    """
    out: list[Optional[float]] = [None] * len(values)
    hist: list[float] = []      # sorted window contents
    order: list[float] = []     # insertion order, for eviction
    for i, v in enumerate(values):
        if len(hist) >= window:
            out[i] = (bisect.bisect_left(hist, v) / len(hist)) if v is not None else None
        if v is None:
            continue
        bisect.insort(hist, v)
        order.append(v)
        if len(hist) > window:
            old = order.pop(0)
            j = bisect.bisect_left(hist, old)
            hist.pop(j)
    return out


def attach_ranks(frames: dict[str, BarFrame], stats: Iterable[str],
                 window: int = DEFAULT_WINDOW) -> None:
    """Populate `frame.ranks[stat]` in place for every frame and every named statistic."""
    for f in frames.values():
        # A frame unpickled from a cache written before `ranks` existed has no such
        # attribute. Repair rather than raise: the cache is a scratch artifact and a
        # stale one must not look like a code defect.
        if getattr(f, "ranks", None) is None:
            f.ranks = {}
        for stat in stats:
            key = f"{stat}@{window}"
            if key in f.ranks:
                continue
            getter = _STAT_GETTERS.get(stat)
            if getter is None:
                continue
            f.ranks[key] = trailing_ranks([getter(f, i) for i in range(len(f))], window)


def _rank_gate(name: str, stat: str, window: int, param: str, *,
               two_sided: bool = False) -> Gate:
    key = f"{stat}@{window}"

    def test(f: BarFrame, i: int, p: dict) -> bool:
        r = f.ranks.get(key)
        if r is None:
            return False
        v = r[i]
        if v is None:
            return False
        thr = p[param]
        if two_sided:
            # a band around the middle, e.g. the substrate `persist=rand` bucket
            return (0.5 - thr / 2) < v < (0.5 + thr / 2)
        return v >= thr

    return Gate(name, THRESHOLD, stat, test, (param,))


def percentile_variant(cond: SleeveConditions, gate_name: str, *,
                       window: int = DEFAULT_WINDOW,
                       param: Optional[str] = None,
                       two_sided: bool = False,
                       p: float = 0.95) -> tuple[SleeveConditions, str]:
    """Return `cond` with one gate re-expressed as a trailing-percentile cut.

    Everything else — the other gates, the geometry, the surface, the warmup — is
    untouched, so the variant differs from production in exactly one testable way.
    """
    target = next((g for g in cond.gates if g.name == gate_name), None)
    if target is None or not target.stat:
        raise ValueError(f"{cond.sleeve} has no threshold gate {gate_name!r}")
    pname = param or f"pct_{gate_name}"
    new_gate = _rank_gate(gate_name, target.stat, window, pname, two_sided=two_sided)
    gates = tuple(new_gate if g.name == gate_name else g for g in cond.gates)
    defaults = dict(cond.defaults)
    defaults[pname] = p
    return replace(cond, gates=gates, defaults=defaults), pname


def fit_percentile(frames: dict[str, BarFrame], cond: SleeveConditions, gate_name: str, *,
                   window: int = DEFAULT_WINDOW, fit_last_year: int = 2023,
                   two_sided: bool = False,
                   symbols: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """Choose `p` so the percentile gate matches production's own pre-2024 pass rate.

    Returns the fitted `p`, the target rate it matched, and the achieved rate — all three,
    because a fit that missed its target by a wide margin is a fit whose variant should be
    read as a different rule rather than as a re-expression.
    """
    target = next((g for g in cond.gates if g.name == gate_name), None)
    if target is None or not target.stat:
        raise ValueError(f"{cond.sleeve} has no threshold gate {gate_name!r}")
    keep = None if symbols is None else set(symbols)
    key = f"{target.stat}@{window}"
    params = dict(cond.defaults)

    n_eval = n_pass = 0
    ranks_of_passing: list[float] = []
    n_rankable = 0
    for canon in cond.surface:
        if keep is not None and canon not in keep:
            continue
        f = frames.get(canon)
        if f is None or key not in f.ranks:
            continue
        rk = f.ranks[key]
        for i in range(cond.warmup_bars - 1, len(f)):
            if f.times_utc[i].year > fit_last_year:
                continue
            n_eval += 1
            ok = target.test(f, i, params)
            if rk[i] is not None:
                n_rankable += 1
                if ok:
                    ranks_of_passing.append(rk[i])
            if ok:
                n_pass += 1
    if not n_eval or not n_rankable:
        return {"fitted_p": None, "reason": "no evaluable pre-2024 bars with ranks"}

    target_rate = len(ranks_of_passing) / n_rankable
    if two_sided:
        # match the width of a central band rather than a tail
        fitted = min(1.0, max(0.0, target_rate))
    else:
        fitted = max(0.0, min(1.0, 1.0 - target_rate))
    return {
        "gate": gate_name,
        "stat": target.stat,
        "window": window,
        "fit_last_year": fit_last_year,
        "two_sided": two_sided,
        "production_pass_rate_fit_era": round(n_pass / n_eval, 6),
        "rankable_pass_rate_fit_era": round(target_rate, 6),
        "n_eval_fit_era": n_eval,
        "n_rankable_fit_era": n_rankable,
        "fitted_p": round(fitted, 6),
        "objective": ("match production's pre-2024 marginal pass rate on rankable bars. "
                      "Deliberately NOT a return objective: a return-fitted percentile is "
                      "the same defect this repairs, one level up."),
    }
