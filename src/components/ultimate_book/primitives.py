"""Vendored pure backtest/decision primitives for the live W7 book engine.

Byte-faithful copies of the LOCKED research primitives so the live sleeve generators
compute IDENTICALLY to the validated book:
  - Bar / atr14 / simulate / simulate_detail  <- geometry_lib.py (the unit-tested geometry library)
  - wins / autocorr / vol_ratio / exit_state_d <- compounding_sleeve.py (STATE_D scale-out exit)

A numeric-parity test (tests/ultimate_book/test_vendor_parity.py) asserts these stay identical to
the route originals. Pure: stdlib only, no MT5/network/file IO. Do NOT "improve" these — any change
silently breaks parity with the locked book.
"""
from __future__ import annotations
from dataclasses import dataclass
import statistics


# --------------------------------------------------------------------------- geometry_lib.py ----
@dataclass
class Bar:
    o: float; h: float; l: float; c: float; v: float = 0.0


def atr14(bars, i):
    if i < 14:
        return 0.0
    s = 0.0
    for j in range(i - 13, i + 1):
        tr = max(bars[j].h - bars[j].l, abs(bars[j].h - bars[j - 1].c), abs(bars[j].l - bars[j - 1].c))
        s += tr
    return s / 14


def simulate(bars, i, direction, *, stop_dist, target_dist=None, trail_arm=None, trail_gap=None,
             maxbars=80, cost=0.0):
    """Explicit two-sided fill. direction +1 long / -1 short. Distances in PRICE.
    R-unit = stop_dist. Returns realized R (net of cost). Pessimistic same-bar: stop wins ties."""
    entry = bars[i].c
    if direction > 0:
        stop = entry - stop_dist
        tgt = entry + target_dist if target_dist else None
        arm = entry + trail_arm if trail_arm else None
        mx = entry; armed = False
        end = min(i + maxbars, len(bars) - 1)
        for j in range(i + 1, end + 1):
            if bars[j].l <= stop:
                return (stop - entry) / stop_dist - cost
            if tgt is not None and bars[j].h >= tgt:
                return (tgt - entry) / stop_dist - cost
            if arm is not None:
                if bars[j].h > mx: mx = bars[j].h
                if not armed and bars[j].h >= arm: armed = True
                if armed and bars[j].l <= mx - trail_gap:
                    return ((mx - trail_gap) - entry) / stop_dist - cost
        return (bars[end].c - entry) / stop_dist - cost
    else:
        stop = entry + stop_dist
        tgt = entry - target_dist if target_dist else None
        arm = entry - trail_arm if trail_arm else None
        mn = entry; armed = False
        end = min(i + maxbars, len(bars) - 1)
        for j in range(i + 1, end + 1):
            if bars[j].h >= stop:
                return (entry - stop) / stop_dist - cost
            if tgt is not None and bars[j].l <= tgt:
                return (entry - tgt) / stop_dist - cost
            if arm is not None:
                if bars[j].l < mn: mn = bars[j].l
                if not armed and bars[j].l <= arm: armed = True
                if armed and bars[j].h >= mn + trail_gap:
                    return (entry - (mn + trail_gap)) / stop_dist - cost
        return (entry - bars[end].c) / stop_dist - cost


def simulate_detail(bars, i, direction, *, stop_dist, target_dist=None, trail_arm=None, trail_gap=None,
                    maxbars=80, cost=0.0):
    """Same logic as simulate() but returns (R, exit_index)."""
    entry = bars[i].c
    if direction > 0:
        stop = entry - stop_dist; tgt = entry + target_dist if target_dist else None
        arm = entry + trail_arm if trail_arm else None; mx = entry; armed = False
        end = min(i + maxbars, len(bars) - 1)
        for j in range(i + 1, end + 1):
            if bars[j].l <= stop: return (stop - entry) / stop_dist - cost, j
            if tgt is not None and bars[j].h >= tgt: return (tgt - entry) / stop_dist - cost, j
            if arm is not None:
                if bars[j].h > mx: mx = bars[j].h
                if not armed and bars[j].h >= arm: armed = True
                if armed and bars[j].l <= mx - trail_gap: return ((mx - trail_gap) - entry) / stop_dist - cost, j
        return (bars[end].c - entry) / stop_dist - cost, end
    else:
        stop = entry + stop_dist; tgt = entry - target_dist if target_dist else None
        arm = entry - trail_arm if trail_arm else None; mn = entry; armed = False
        end = min(i + maxbars, len(bars) - 1)
        for j in range(i + 1, end + 1):
            if bars[j].h >= stop: return (entry - stop) / stop_dist - cost, j
            if tgt is not None and bars[j].l <= tgt: return (entry - tgt) / stop_dist - cost, j
            if arm is not None:
                if bars[j].l < mn: mn = bars[j].l
                if not armed and bars[j].l <= arm: armed = True
                if armed and bars[j].h >= mn + trail_gap: return (entry - (mn + trail_gap)) / stop_dist - cost, j
        return (entry - bars[end].c) / stop_dist - cost, end


# ------------------------------------------------------------------------ compounding_sleeve.py --
def wins(r):
    return max(-1.3, min(5.0, r))


def autocorr(B, i, n=60):
    if i < n + 1:
        return None
    rets = [B[k].c - B[k - 1].c for k in range(i - n + 1, i + 1)]
    m = statistics.mean(rets)
    num = sum((rets[k] - m) * (rets[k - 1] - m) for k in range(1, len(rets)))
    den = sum((x - m) ** 2 for x in rets)
    return num / den if den > 0 else 0.0


def vol_ratio(atrs, i):
    if i < 100:
        return 1.0
    s = sum(atrs[i - 99:i + 1]) / 100
    return atrs[i] / s if s > 0 else 1.0


def exit_state_d(B, i, d, sd, vr, cost, maxbars=80):
    entry = B[i].c
    if vr < 1.35: scaleR, runR = 1.5, 4.0
    elif vr < 1.6: scaleR, runR = 1.5, 3.0
    else: scaleR, runR = 1.0, 2.5
    scaled = False; mfe = 0.0; mae = 0.0; bars1R = None; leg2 = None; reason = None; end = min(i + maxbars, len(B) - 1)
    for j in range(i + 1, end + 1):
        hi = B[j].h; lo = B[j].l
        favp = hi if d > 0 else lo; advp = lo if d > 0 else hi
        fav = d * (favp - entry) / sd; adv = d * (advp - entry) / sd
        mfe = max(mfe, fav); mae = min(mae, adv)
        if bars1R is None and fav >= 1.0: bars1R = j - i
        if not scaled:
            if adv <= -1.0: return dict(R=-1.0 - cost, mfe=mfe, mae=mae, bars1R=bars1R, reason='full_stop', vr=vr)
            if fav >= scaleR: scaled = True
        else:
            if adv <= 0.0: leg2 = 0.0; reason = 'scratch_be'; break
            if fav >= runR: leg2 = runR; reason = 'win_runner'; break
    if reason is None:
        if scaled:
            leg2 = d * (B[end].c - entry) / sd; reason = 'win_partial' if leg2 > 0 else 'partial_flat'
        else:
            R = d * (B[end].c - entry) / sd
            return dict(R=wins(R - cost), mfe=mfe, mae=mae, bars1R=bars1R, reason='market_close', vr=vr)
    R = 0.5 * scaleR + 0.5 * leg2
    return dict(R=wins(R - cost), mfe=mfe, mae=mae, bars1R=bars1R, reason=reason, vr=vr)
