"""The firing-rate decomposition: opportunity x per-gate pass rates.

THE IDENTITY THIS RESTS ON
---------------------------
A sequential funnel is exact, not a model. For a sleeve, a period, and an ordered gate
chain,

    fires  =  eval_slots  x  PROD_g (passed_g / reached_g)

because `reached_(g+1) == passed_g` by construction of the walk. So the log ramp between
two eras splits with no residual:

    log(fires_B / fires_A) = log(slots_B / slots_A) + SUM_g log(rate_g,B / rate_g,A)
                             \_____ cause (a) _____/   \___ causes (b) and (c) ____/

`eval_slots` counts (symbol, bar) pairs the live engine would have evaluated — a symbol
with no archive series contributes zero, which is exactly what "the setup never appeared"
means when it means "the instrument did not exist here".

SEPARATING (b) FROM (c), BY MEASUREMENT RATHER THAN BY ASSERTION
------------------------------------------------------------------
A threshold gate's pass rate can move for two different reasons and the repairs are
opposite:

  (b) the cut is fixed and the statistic's DISTRIBUTION moved underneath it. Then the
      sleeve was firing all along at the right scale and the repair is to re-express the
      cut scale-free (`normalize.py`). Signature: the threshold's percentile rank inside
      the era's own distribution of that statistic moves.
  (c) the distribution is stable and the pass rate still moved — the market's joint
      structure changed. Then a regime gate is the honest answer and the deliverable is
      the named variable.

So every threshold gate is reported with `thr_pct_rank` per era. This is a diagnostic,
not a proof: a pass rate can also move because two statistics' JOINT distribution moved
while both marginals held. `joint_residual` reports exactly that gap — the part of a
gate's rate change its own statistic's drift does not explain.

THE RAMP CUTS BOTH WAYS AND THAT IS PUBLISHED
----------------------------------------------
If a scale-free threshold makes a sleeve fire far more in 2015 and its out-of-window
economics get *worse*, that is a result. `restate.py` prices every variant this module
proposes; nothing here selects on the answer.
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
from collections import defaultdict
from typing import Any, Iterable, Optional, Sequence

from src.research_infra.regime_spine.conditions import (
    THRESHOLD,
    BarVerdict,
    SleeveConditions,
    walk,
)
from src.research_infra.regime_spine.state import BarFrame

__all__ = [
    "FunnelCounts",
    "funnel_by_period",
    "decompose",
    "stat_series",
    "threshold_percentile_ranks",
    "weekday_sessions",
]


def weekday_sessions(a: dt.date, b: dt.date) -> int:
    """Mon-Fri days in [a, b] inclusive — the denominator `SESSION_V` used for density."""
    if b < a:
        return 0
    n = 0
    d = a
    while d <= b:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


class FunnelCounts:
    """Per-period funnel for one sleeve: slots, per-gate reached/passed, fires."""

    __slots__ = ("slots", "reached", "passed", "marginal", "fires", "symbols")

    def __init__(self, gate_names: Sequence[str]):
        self.slots = 0
        self.reached = {g: 0 for g in gate_names}
        self.passed = {g: 0 for g in gate_names}
        self.marginal = {g: 0 for g in gate_names}
        self.fires = 0
        self.symbols: set[str] = set()

    def add(self, v: BarVerdict, gate_names: Sequence[str], symbol: str) -> None:
        self.slots += 1
        self.symbols.add(symbol)
        for g in gate_names:
            if v.marginal.get(g):
                self.marginal[g] += 1
        stop = v.stopped_by
        for g in gate_names:
            self.reached[g] += 1
            if stop == g:
                break
            self.passed[g] += 1
        if v.fired:
            self.fires += 1

    def rates(self, gate_names: Sequence[str]) -> dict[str, Optional[float]]:
        return {g: (self.passed[g] / self.reached[g] if self.reached[g] else None)
                for g in gate_names}

    def to_json(self, gate_names: Sequence[str]) -> dict[str, Any]:
        return {
            "eval_slots": self.slots,
            "symbols_with_bars": sorted(self.symbols),
            "n_symbols": len(self.symbols),
            "fires": self.fires,
            "fire_rate_per_slot": (self.fires / self.slots) if self.slots else None,
            "gates": {
                g: {
                    "reached": self.reached[g],
                    "passed": self.passed[g],
                    "conditional_rate": (self.passed[g] / self.reached[g]
                                         if self.reached[g] else None),
                    "marginal_rate": (self.marginal[g] / self.slots) if self.slots else None,
                }
                for g in gate_names
            },
        }


def _period_of(t: dt.datetime, grain: str) -> str:
    if grain == "year":
        return f"{t.year:04d}"
    if grain == "month":
        return f"{t.year:04d}-{t.month:02d}"
    raise ValueError(f"unknown grain {grain!r}")


def funnel_by_period(frames: dict[str, BarFrame], cond: SleeveConditions, *,
                     params: Optional[dict] = None, grain: str = "year",
                     symbols: Optional[Iterable[str]] = None,
                     ) -> dict[str, FunnelCounts]:
    """Walk every symbol's frame and bucket the funnel by calendar period.

    `symbols` restricts to a **fixed panel** of canonical names. That control matters more
    than it looks: the armed four's surface grows from 1-3 symbols to 13 in 2021, so an
    unrestricted per-era comparison confounds "the gate's pass rate moved" with "the gate
    is now being asked about indices instead of gold". Every headline rate change in this
    package is reported both ways.
    """
    names = cond.gate_names()
    keep = None if symbols is None else set(symbols)
    out: dict[str, FunnelCounts] = defaultdict(lambda: FunnelCounts(names))
    for canon in cond.surface:
        if keep is not None and canon not in keep:
            continue
        f = frames.get(canon)
        if f is None:
            continue
        for v in walk(f, cond, params, marginal=True):
            out[_period_of(f.times_utc[v.i], grain)].add(v, names, f.symbol)
    return dict(out)


def common_panel(frames: dict[str, BarFrame], cond: SleeveConditions,
                 era_a: Sequence[str], era_b: Sequence[str]) -> list[str]:
    """Canonical symbols with evaluable bars in **both** eras — the like-for-like panel."""
    return _panel(frames, cond, era_a, era_b, strict=False)


def strict_panel(frames: dict[str, BarFrame], cond: SleeveConditions,
                 era_a: Sequence[str], era_b: Sequence[str]) -> list[str]:
    """Symbols with evaluable bars in **every** year of both eras.

    `common_panel` admits a symbol present in one year of an era, which still lets the
    composition shift inside the era — `US30_cash` starts 2019-02 and would be counted as
    "present in 2015-2019". Anything headline-bearing uses this stricter version.
    """
    return _panel(frames, cond, era_a, era_b, strict=True)


def _panel(frames: dict[str, BarFrame], cond: SleeveConditions,
           era_a: Sequence[str], era_b: Sequence[str], *, strict: bool) -> list[str]:
    out = []
    for canon in cond.surface:
        f = frames.get(canon)
        if f is None:
            continue
        yrs = {f.times_utc[i].strftime("%Y")
               for i in range(cond.warmup_bars - 1, len(f))}
        a, b = set(era_a), set(era_b)
        # only years the archive could carry at all — an era key past the archive's end
        # must not disqualify a symbol that covers everything available
        horizon = {str(y) for y in range(2000, 2027)}
        a &= horizon
        b &= horizon
        if strict:
            ok = a.issubset(yrs) and b.issubset(yrs)
        else:
            ok = bool(yrs & a) and bool(yrs & b)
        if ok:
            out.append(canon)
    return out


def _log_ratio(b: Optional[float], a: Optional[float]) -> Optional[float]:
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return math.log(b / a)


def decompose(funnels: dict[str, FunnelCounts], cond: SleeveConditions,
              era_a: Sequence[str], era_b: Sequence[str]) -> dict[str, Any]:
    """Attribute log(fires_B / fires_A) to the opportunity term and each gate.

    Eras are lists of period keys. A term whose ratio is undefined (a zero count) is
    reported as `None` with `closed_in_a` / `closed_in_b` set, rather than silently
    dropped or clamped — a gate that shut completely is the strongest possible finding
    and must not be averaged away.
    """
    names = cond.gate_names()

    def agg(era: Sequence[str]) -> FunnelCounts:
        acc = FunnelCounts(names)
        for k in era:
            f = funnels.get(k)
            if f is None:
                continue
            acc.slots += f.slots
            acc.fires += f.fires
            acc.symbols |= f.symbols
            for g in names:
                acc.reached[g] += f.reached[g]
                acc.passed[g] += f.passed[g]
                acc.marginal[g] += f.marginal[g]
        return acc

    A, B = agg(era_a), agg(era_b)
    ra, rb = A.rates(names), B.rates(names)

    def joint(acc: FunnelCounts) -> dict[str, Any]:
        """Observed fires vs the fires the gates' MARGINALS alone would predict.

        If every gate were independent, `fires = slots * PROD_g marginal_g`. The ratio of
        observed to that is the **joint lift** — how much more (or less) often the gates
        co-occur than chance. It is the cleanest (b)/(c) discriminator available from the
        funnel alone: a threshold whose own distribution moved shows up in the marginals
        and leaves the lift alone; a market whose joint structure changed moves the lift
        while the marginals hold.
        """
        if not acc.slots:
            return {"independent_fires": None, "joint_lift": None}
        prod = 1.0
        for g in names:
            prod *= acc.marginal[g] / acc.slots
        exp = acc.slots * prod
        return {"independent_fires": exp,
                "joint_lift": (acc.fires / exp) if exp > 0 else None,
                "marginal_rates": {g: acc.marginal[g] / acc.slots for g in names}}

    jA, jB = joint(A), joint(B)
    terms: dict[str, Any] = {}
    total_known = 0.0
    for g in names:
        lr = _log_ratio(rb[g], ra[g])
        terms[g] = {
            "rate_a": ra[g], "rate_b": rb[g], "log_ratio": lr,
            "closed_in_a": bool(A.reached[g] and not A.passed[g]),
            "closed_in_b": bool(B.reached[g] and not B.passed[g]),
            "unreached_in_a": A.reached[g] == 0,
        }
        if lr is not None:
            total_known += lr
    slot_lr = _log_ratio(float(B.slots), float(A.slots))
    if slot_lr is not None:
        total_known += slot_lr
    fires_lr = _log_ratio(float(B.fires), float(A.fires))

    def share(x: Optional[float]) -> Optional[float]:
        if x is None or fires_lr in (None, 0):
            return None
        return x / fires_lr

    return {
        "era_a": {"periods": list(era_a), **A.to_json(names)},
        "era_b": {"periods": list(era_b), **B.to_json(names)},
        "log_fire_ratio": fires_lr,
        "opportunity": {
            "slots_a": A.slots, "slots_b": B.slots, "log_ratio": slot_lr,
            "share_of_ramp": share(slot_lr),
            "n_symbols_a": len(A.symbols), "n_symbols_b": len(B.symbols),
            "symbols_only_in_b": sorted(B.symbols - A.symbols),
        },
        "gates": {g: {**terms[g], "share_of_ramp": share(terms[g]["log_ratio"]),
                      "cause_class": _cause_class(cond, g)} for g in names},
        "independence": {
            "era_a": jA, "era_b": jB,
            "log_joint_lift_ratio": _log_ratio(jB.get("joint_lift"),
                                               jA.get("joint_lift")),
            "share_of_ramp": share(_log_ratio(jB.get("joint_lift"),
                                              jA.get("joint_lift"))),
            "note": ("Marginal drift is cause (b) and is repairable by a percentile cut; "
                     "joint-lift drift is cause (c) and its repair is a named regime "
                     "variable. Reported per era so the split is visible, not inferred."),
        },
        "sum_of_terms": total_known,
        "unexplained": (None if fires_lr is None else fires_lr - total_known),
        "note": ("The identity is exact when every term is defined; `unexplained` is a "
                 "float-rounding residual, not a model error. A None term means a count "
                 "was zero — read `closed_in_a` / `closed_in_b`."),
    }


def _cause_class(cond: SleeveConditions, gate: str) -> str:
    for g in cond.gates:
        if g.name == gate:
            return g.cause
    return "unknown"


# --------------------------------------------------------------------------------------
# the (b) test: did the statistic's distribution move under the fixed cut?
# --------------------------------------------------------------------------------------
def mtf_decomposition(frames: dict[str, BarFrame], cond: SleeveConditions, *,
                      params: Optional[dict] = None, grain: str = "year",
                      symbols: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """Split `P(mtf == conflict)` into the two things it can mean.

        P(conflict) = P(both horizons non-neutral) x P(opposite sign | both non-neutral)

    The first factor is the **0.5 cut** on ATR-normalised displacement: it moves when the
    slope distribution's width moves, and it is repairable by re-expressing the cut as a
    percentile. That is cause (b). The second factor is the market genuinely disagreeing
    across horizons more often — cause (c), and the thing a named regime dial would watch.

    Without this split, `sub_xvol_pullback`'s 17x conflict-rate change reads as one number
    and is unattributable.
    """
    p = dict(cond.defaults)
    if params:
        p.update(params)
    thr = p.get("mtf_sgn_thr", 0.5)
    keep = None if symbols is None else set(symbols)
    acc: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "both_active": 0, "conflict": 0, "aligned": 0})
    for canon in cond.surface:
        if keep is not None and canon not in keep:
            continue
        f = frames.get(canon)
        if f is None:
            continue
        for i in range(cond.warmup_bars - 1, len(f)):
            s20, s100 = f.slope20[i], f.slope100[i]
            if s20 is None or s100 is None:
                continue
            k = _period_of(f.times_utc[i], grain)
            a = acc[k]
            a["n"] += 1
            if abs(s20) > thr and abs(s100) > thr:
                a["both_active"] += 1
                if (s20 > 0) != (s100 > 0):
                    a["conflict"] += 1
                else:
                    a["aligned"] += 1
    return {
        "sgn_threshold": thr,
        "by_period": {
            k: {
                "n": v["n"],
                "p_both_active": v["both_active"] / v["n"] if v["n"] else None,
                "p_conflict_given_active": (v["conflict"] / v["both_active"]
                                            if v["both_active"] else None),
                "p_conflict": v["conflict"] / v["n"] if v["n"] else None,
            }
            for k, v in sorted(acc.items())
        },
        "note": ("p_both_active is the (b) factor — it is what a percentile cut would "
                 "hold constant. p_conflict_given_active is the (c) factor."),
    }


def stat_series(frames: dict[str, BarFrame], cond: SleeveConditions, stat: str, *,
                grain: str = "year", symbols: Optional[Iterable[str]] = None,
                ) -> dict[str, list[float]]:
    """Values of one frame statistic, per period, over the sleeve's evaluable bars.

    Restricted to evaluable bars (past warmup) so the distribution is the one the gate
    actually saw, not the one the raw series carries.
    """
    getter = _STAT_GETTERS.get(stat)
    if getter is None:
        return {}
    keep = None if symbols is None else set(symbols)
    out: dict[str, list[float]] = defaultdict(list)
    for canon in cond.surface:
        if keep is not None and canon not in keep:
            continue
        f = frames.get(canon)
        if f is None:
            continue
        for i in range(cond.warmup_bars - 1, len(f)):
            v = getter(f, i)
            if v is None:
                continue
            out[_period_of(f.times_utc[i], grain)].append(float(v))
    return {k: sorted(v) for k, v in out.items()}


def _g_vr(f: BarFrame, i: int) -> Optional[float]:
    return f.vr_raw[i]


def _g_ac_prim(f: BarFrame, i: int) -> Optional[float]:
    return f.ac60_prim[i]


def _g_ac_sub(f: BarFrame, i: int) -> Optional[float]:
    return f.ac60_sub[i]


def _g_slope50(f: BarFrame, i: int) -> Optional[float]:
    return f.slope50[i]


def _g_d30_over_atr(f: BarFrame, i: int) -> Optional[float]:
    a, d = f.atr[i], f.d30[i]
    return None if (a <= 0 or d is None) else d / a


def _g_break_margin(f: BarFrame, i: int) -> Optional[float]:
    """Signed distance of the close past the nearer Donchian edge, in ATR."""
    hh, ll, a = f.don_hh[i], f.don_ll[i], f.atr[i]
    if hh is None or ll is None or a <= 0:
        return None
    c = f.bars[i].c
    return max(c - hh, ll - c) / a


def _g_mtf(f: BarFrame, i: int) -> Optional[float]:
    s20, s100 = f.slope20[i], f.slope100[i]
    if s20 is None or s100 is None:
        return None
    # A single scalar whose sign carries "conflict": negative when the two horizons
    # disagree, magnitude = the weaker |slope|, which is what the 0.5 cut bites.
    return math.copysign(min(abs(s20), abs(s100)), s20 * s100)


_STAT_GETTERS = {
    "vr": _g_vr,
    "ac60_prim": _g_ac_prim,
    "ac60_sub": _g_ac_sub,
    "slope50": _g_slope50,
    "d30_over_atr": _g_d30_over_atr,
    "break_margin_atr": _g_break_margin,
    "mtf_align": _g_mtf,
    "atr": lambda f, i: (f.atr[i] if f.atr[i] > 0 else None),
}


def _pct_rank(sorted_vals: Sequence[float], x: float) -> Optional[float]:
    if not sorted_vals:
        return None
    return bisect.bisect_left(sorted_vals, x) / len(sorted_vals)


def threshold_percentile_ranks(frames: dict[str, BarFrame], cond: SleeveConditions, *,
                               params: Optional[dict] = None, grain: str = "year",
                               symbols: Optional[Iterable[str]] = None,
                               ) -> dict[str, Any]:
    """For every threshold gate: where its fixed cut sits in each era's own distribution.

    A cut whose percentile rank is stable across 26 years is scale-free **in practice**,
    whatever its units. A cut whose rank slides is the (b) case, and the size of the slide
    is the size of the repair.
    """
    p = dict(cond.defaults)
    if params:
        p.update(params)
    out: dict[str, Any] = {}
    for g in cond.gates:
        if g.cause != THRESHOLD or not g.stat:
            continue
        series = stat_series(frames, cond, g.stat, grain=grain, symbols=symbols)
        if not series:
            continue
        thr = _representative_threshold(g.name, p)
        out[g.name] = {
            "stat": g.stat,
            "threshold": thr,
            "by_period": {
                k: {
                    "n": len(v),
                    "median": v[len(v) // 2] if v else None,
                    "p90": v[int(0.90 * (len(v) - 1))] if v else None,
                    "thr_pct_rank": (None if thr is None else _pct_rank(v, thr)),
                }
                for k, v in sorted(series.items())
            },
        }
    return out


def _representative_threshold(gate: str, p: dict) -> Optional[float]:
    """The single scalar a gate's percentile rank is meaningful against."""
    return {
        "vol_expansion": p.get("gate_k"),
        "persistence": p.get("ac_thr"),
        "persistence_band": p.get("ac_thr"),
        "size_multiplier": p.get("ac_floor_sb"),
        "vol_xhi": p.get("vr_xhi"),
        "trend_up": p.get("slope_up"),
        "mtf_conflict": None,      # a sign test, not a level cut
        "htf_trend": 1.0,          # `|c - c[-30]| > 1.0 * ATR`
        "energy_state": p.get("vr_shock"),
    }.get(gate)
