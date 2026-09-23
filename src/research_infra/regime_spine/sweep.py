"""Evaluate a sleeve variant end to end: fires -> fill -> broker-true cost -> statistics.

One function, `evaluate`, so every sweep in this session prices its variants the same way
and a cell is comparable to the production cell beside it.

THE TWO GEOMETRY OVERRIDES, AND WHY THEY ARE SEPARATE FROM THE THRESHOLDS
--------------------------------------------------------------------------
A threshold change moves WHICH bars fire. A geometry change moves what happens after one
does, and therefore re-simulates the path. `evaluate` takes both, because the cost-geometry
repair `FOURTH_REVIEW.md` section 2.2 prescribes for an "expectancy fails with gross > 0"
sleeve is precisely a geometry sweep:

    cost in R = price drag / stop distance

so widening the stop divides every cost term by the widening factor — while the R-geometry
of the trade moves with the *path*, because a wider stop is hit less often and a target set
at the same R multiple is further away in price. Those two effects run in opposite
directions and only a re-simulation says which wins. That is the whole content of the
sweep, and it is why the answer cannot be reasoned out.

`stop_scale` multiplies the sleeve's own stop; `atr_floor` raises the ATR-relative floor
under it (`metals.ATR_STOP_FLOOR` is 0.25, and the floor is where the R-cost is worst
because it produces the tightest stops). `target_r_scale` moves the target in R.

FOLD DISCIPLINE
---------------
`fit_last_year` splits the record into a fit era and a validation era at a calendar
boundary. Everything in this session fits pre-2024 and validates 2024+ — the reverse of
the contamination being repaired, in which the sleeves were selected on 2025+ and then
scored on 2025+.
"""

from __future__ import annotations

import collections
import datetime as dt
import statistics
from typing import Any, Iterable, Optional

from src.components.ultimate_book.admission import winsorize_R
from src.components.ultimate_book.primitives import simulate_detail
from src.research_infra.regime_spine.conditions import SleeveConditions, fires
from src.research_infra.regime_spine.state import BarFrame

__all__ = ["evaluate", "Variant", "grid"]

MAXBARS = 80
IVL = dt.timedelta(hours=4)


def grid(**axes: Iterable) -> list[dict]:
    """Cartesian product of named axes, in a stable order."""
    keys = list(axes)
    out: list[dict] = [{}]
    for k in keys:
        out = [dict(d, **{k: v}) for d in out for v in axes[k]]
    return out


class Variant(dict):
    """A parameter dict that knows how to name itself, so a ledger row is greppable."""

    def vid(self, prefix: str = "") -> str:
        body = ",".join(f"{k}={self[k]:g}" if isinstance(self[k], (int, float))
                        else f"{k}={self[k]}" for k in sorted(self))
        return f"{prefix}{body}" if prefix else body


def evaluate(frames: dict[str, BarFrame], cond: SleeveConditions, *,
             params: Optional[dict] = None,
             stop_scale: float = 1.0,
             atr_floor: Optional[float] = None,
             target_r_scale: float = 1.0,
             account: str = "FTMO",
             costs: Any = None,
             fit_last_year: int = 2023,
             symbols: Optional[Iterable[str]] = None,
             ) -> dict[str, Any]:
    """Fire, fill, price, and summarise one variant over the archive.

    Returns per-era statistics in **both** R-per-trade and R-per-trading-day. The day
    figure is the one an admission decision uses (day aggregation is the first clustering
    control, `panel.py`); the trade figure is the one a cost-geometry repair moves.

    An unpriceable trade is dropped and counted, never back-filled — the F38 rule.
    """
    from src.costs import (
        CostTruthError,
        cost_r,
        elapsed_holding_hours,
        load_broker_true_costs,
    )

    truth = costs if costs is not None else load_broker_true_costs()
    keep = None if symbols is None else set(symbols)
    rows: list[dict] = []
    n_fire = 0
    unpriced: collections.Counter = collections.Counter()

    for canon in cond.surface:
        if keep is not None and canon not in keep:
            continue
        f = frames.get(canon)
        if f is None:
            continue
        for i, intent in fires(f, cond, params):
            n_fire += 1
            if i + 2 >= len(f):
                unpriced["no_room"] += 1
                continue
            sd = float(intent["stop_dist"]) * stop_scale
            if atr_floor is not None:
                sd = max(sd, atr_floor * f.atr[i])
            if sd <= 0:
                unpriced["nonpositive_stop"] += 1
                continue
            td = intent.get("target_dist")
            # Target held at its R multiple of the (possibly rescaled) stop, so the sweep
            # moves stop WIDTH and not the reward:risk ratio — otherwise two things move
            # at once and neither is attributable.
            tr = (float(td) / float(intent["stop_dist"])) if td else None
            td2 = (tr * target_r_scale * sd) if tr else None
            r, xi = simulate_detail(f.bars, i, intent["direction"], stop_dist=sd,
                                    target_dist=td2, maxbars=MAXBARS, cost=0.0)
            r = winsorize_R(r)
            entry_utc = f.times_utc[i] + IVL
            exit_utc = f.times_utc[xi] + IVL
            # `xi-i` counts tradable H4 bars and silently deletes weekends/closures.
            # Swap is charged on broker-wall rollover crossings, so its input must be
            # actual elapsed time between the simulated fill and exit instants.
            hold = elapsed_holding_hours(entry_utc, exit_utc)
            try:
                b = cost_r(f.symbol, account, hold, sl_distance_price=sd,
                           entry_price=f.bars[i].c,
                           side="LONG" if intent["direction"] > 0 else "SHORT",
                           entry_utc=entry_utc, costs=truth)
            except CostTruthError as e:
                unpriced[str(e).split(".")[0][:60]] += 1
                continue
            tot = float(getattr(b.total_r, "value", b.total_r))
            rows.append({
                "sleeve": cond.sleeve, "symbol": f.symbol, "canonical": canon,
                "year": f.times_utc[i].year,
                "date": (f.times_utc[i] + IVL).strftime("%Y-%m-%d"),
                "r_gross": float(r), "cost_r": tot, "r_net": float(r) - tot,
                "hold_hours": hold, "stop_over_atr": (sd / f.atr[i]) if f.atr[i] > 0 else None,
            })

    def stats(sub: list[dict]) -> dict[str, Any]:
        if not sub:
            return {"n": 0, "n_days": 0, "mean_r_net": None, "mean_r_gross": None,
                    "mean_cost_r": None, "total_r_net": 0.0, "mean_r_net_per_day": None,
                    "pos_frac": None}
        by_day: dict[str, list[float]] = collections.defaultdict(list)
        for r in sub:
            by_day[r["date"]].append(r["r_net"])
        dayvals = [statistics.fmean(v) for v in by_day.values()]
        return {
            "n": len(sub),
            "n_days": len(by_day),
            "mean_r_gross": round(statistics.fmean([r["r_gross"] for r in sub]), 5),
            "mean_cost_r": round(statistics.fmean([r["cost_r"] for r in sub]), 5),
            "mean_r_net": round(statistics.fmean([r["r_net"] for r in sub]), 5),
            "total_r_net": round(sum(r["r_net"] for r in sub), 3),
            "mean_r_net_per_day": round(statistics.fmean(dayvals), 5),
            "total_r_net_per_day_sum": round(sum(dayvals), 3),
            "pos_frac": round(sum(1 for r in sub if r["r_net"] > 0) / len(sub), 4),
            "median_hold_hours": round(statistics.median(
                [r["hold_hours"] for r in sub]), 2),
            "median_stop_over_atr": round(statistics.median(
                [r["stop_over_atr"] for r in sub if r["stop_over_atr"] is not None]), 4)
            if any(r["stop_over_atr"] is not None for r in sub) else None,
        }

    fit = [r for r in rows if r["year"] <= fit_last_year]
    val = [r for r in rows if r["year"] > fit_last_year]
    return {
        "n_fires": n_fire,
        "n_priced": len(rows),
        "unpriced": dict(unpriced),
        "coverage_frac": (len(rows) / n_fire) if n_fire else None,
        "all": stats(rows),
        "fit": {"era": f"<= {fit_last_year}", **stats(fit)},
        "validate": {"era": f"> {fit_last_year}", **stats(val)},
        "by_year": {str(y): len([r for r in rows if r["year"] == y])
                    for y in sorted({r["year"] for r in rows})},
    }
