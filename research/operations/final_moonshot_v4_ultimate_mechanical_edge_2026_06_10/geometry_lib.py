"""TESTED shared backtest primitives — correct explicit long/short, no sign tricks.
The whole geometry campaign was wrecked by a short-side sign bug; this library
is unit-tested (test_geometry_lib.py) with synthetic known-answer cases so that
class of error cannot recur. All analysis must import from here, not reinvent.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Bar:
    o: float; h: float; l: float; c: float; v: float = 0.0

def atr14(bars, i):
    if i < 14: return 0.0
    s = 0.0
    for j in range(i-13, i+1):
        tr = max(bars[j].h-bars[j].l, abs(bars[j].h-bars[j-1].c), abs(bars[j].l-bars[j-1].c))
        s += tr
    return s/14

def simulate(bars, i, direction, *, stop_dist, target_dist=None, trail_arm=None, trail_gap=None,
             maxbars=80, cost=0.0):
    """Explicit two-sided fill. direction +1 long / -1 short. Distances in PRICE.
    R-unit = stop_dist. Returns realized R (net of cost). Pessimistic same-bar: stop wins ties.
    Modes: fixed target (target_dist set) OR trail (trail_arm & trail_gap set, in PRICE).
    """
    entry = bars[i].c
    if direction > 0:
        stop = entry - stop_dist
        tgt = entry + target_dist if target_dist else None
        arm = entry + trail_arm if trail_arm else None
        mx = entry; armed = False
        end = min(i+maxbars, len(bars)-1)
        for j in range(i+1, end+1):
            if bars[j].l <= stop:                       # stop first (pessimistic)
                return (stop-entry)/stop_dist - cost
            if tgt is not None and bars[j].h >= tgt:
                return (tgt-entry)/stop_dist - cost
            if arm is not None:
                if bars[j].h > mx: mx = bars[j].h
                if not armed and bars[j].h >= arm: armed = True
                if armed and bars[j].l <= mx - trail_gap:
                    return ((mx-trail_gap)-entry)/stop_dist - cost
        return (bars[end].c-entry)/stop_dist - cost
    else:
        stop = entry + stop_dist
        tgt = entry - target_dist if target_dist else None
        arm = entry - trail_arm if trail_arm else None
        mn = entry; armed = False
        end = min(i+maxbars, len(bars)-1)
        for j in range(i+1, end+1):
            if bars[j].h >= stop:
                return (entry-stop)/stop_dist - cost
            if tgt is not None and bars[j].l <= tgt:
                return (entry-tgt)/stop_dist - cost
            if arm is not None:
                if bars[j].l < mn: mn = bars[j].l
                if not armed and bars[j].l <= arm: armed = True
                if armed and bars[j].h >= mn + trail_gap:
                    return (entry-(mn+trail_gap))/stop_dist - cost
        return (entry-bars[end].c)/stop_dist - cost


def simulate_detail(bars, i, direction, *, stop_dist, target_dist=None, trail_arm=None, trail_gap=None,
                    maxbars=80, cost=0.0):
    """Same logic as simulate() but returns (R, exit_index). Used for lookahead-correct
    gating (knowing WHEN a trade closes). Unit-tested to match simulate()'s R."""
    entry = bars[i].c
    if direction > 0:
        stop = entry - stop_dist; tgt = entry + target_dist if target_dist else None
        arm = entry + trail_arm if trail_arm else None; mx = entry; armed = False
        end = min(i+maxbars, len(bars)-1)
        for j in range(i+1, end+1):
            if bars[j].l <= stop: return (stop-entry)/stop_dist - cost, j
            if tgt is not None and bars[j].h >= tgt: return (tgt-entry)/stop_dist - cost, j
            if arm is not None:
                if bars[j].h > mx: mx = bars[j].h
                if not armed and bars[j].h >= arm: armed = True
                if armed and bars[j].l <= mx - trail_gap: return ((mx-trail_gap)-entry)/stop_dist - cost, j
        return (bars[end].c-entry)/stop_dist - cost, end
    else:
        stop = entry + stop_dist; tgt = entry - target_dist if target_dist else None
        arm = entry - trail_arm if trail_arm else None; mn = entry; armed = False
        end = min(i+maxbars, len(bars)-1)
        for j in range(i+1, end+1):
            if bars[j].h >= stop: return (entry-stop)/stop_dist - cost, j
            if tgt is not None and bars[j].l <= tgt: return (entry-tgt)/stop_dist - cost, j
            if arm is not None:
                if bars[j].l < mn: mn = bars[j].l
                if not armed and bars[j].l <= arm: armed = True
                if armed and bars[j].h >= mn + trail_gap: return (entry-(mn+trail_gap))/stop_dist - cost, j
        return (entry-bars[end].c)/stop_dist - cost, end
