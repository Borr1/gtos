"""idxdeep — Harden the index failed-breakout reversion sleeve (track key: idxdeep).

GOAL (KB2_deepen_index): turn the highest-frequency index reversion pocket (~1050 trades/yr,
least-validated, 2024+ only) into a robust larger-size sleeve by adding a CROSS-SECTIONAL /
RISK-OFF filter for the sign-flip symbols (GER40/US30/JP225).

THESIS: a failed breakout is a TRUE reversion (fade pays) when the move is IDIOSYNCRATIC —
the index basket is NOT in a synchronized trend. A failed breakout DURING a synchronized
basket trend is more likely a genuine breakout pause that resumes, which is why GER40/US30/JP225
sign-flip (they are high-beta to the US/global risk regime). Gate the fade to fire only when
the basket is NOT synchronously trending.

LEAK-FREE: the cross-sectional basket-trend feature at H4 timestamp ts uses, for every basket
member, ONLY that member's bars with open-time <= ts (strictly closed bars; binary search to the
last bar at-or-before ts). Entry = close of the signal bar i. geometry_lib.simulate scores the
outcome (leak-free pessimistic). FORWARD HOLDOUT: the locked rule (chosen on NAS100 TRAIN<=2024 +
the prior KB pocket logic) is reported FORWARD 2025 and 2026 SEPARATELY, per-year & per-symbol.
"""
import sys, json, statistics, collections, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import idxrev_sleeve as ir
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

POCKET = ["SPX500", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225", "GER40", "US30_cash"]
SIGN_FLIP = ["GER40", "US30_cash", "JP225"]
CONSISTENT = ["SPX500", "UK100", "US2000_cash", "EU50_cash"]
# Basket used to define the synchronized-trend regime. Use the broad members that exist as
# early as possible so the feature is well-populated; these are the "market" proxies.
BASKET = ["NAS100", "SPX500", "GER40", "US30_cash", "JP225", "UK100", "FRA40_cash", "EU50_cash", "US2000_cash"]

def wins(r): return max(-1.3, min(5.0, r))

# ---- leak-free per-symbol series cache (times + bars + ATR + ema) ----
_SER = {}
def series(sym):
    if sym in _SER: return _SER[sym]
    T, B = w1.load(sym)
    atrs = [atr14(B, k) for k in range(len(B))]
    _SER[sym] = (T, B, atrs)
    return _SER[sym]

def last_idx_at_or_before(T, ts):
    """index of last bar with open-time <= ts (strictly closed at the decision instant)."""
    lo, hi = 0, len(T)
    while lo < hi:
        mid = (lo + hi) // 2
        if T[mid] <= ts: lo = mid + 1
        else: hi = mid
    return lo - 1  # -1 if none

def trend_strength(B, atrs, j, lb=10):
    """Leak-free per-symbol normalized trend over the last lb closed bars ending at j.
    (close[j]-close[j-lb]) / (ATR[j]*sqrt(lb)) -> signed, ~unit-variance for a random walk.
    Returns None if insufficient history."""
    if j is None or j < lb or j >= len(B): return None
    a = atrs[j]
    if a is None or a <= 0: return None
    import math
    return (B[j].c - B[j-lb].c) / (a * math.sqrt(lb))

def basket_state(ts, lb=10, members=None):
    """Cross-sectional basket trend at timestamp ts (leak-free).
    Returns (n_members, mean_abs_trend, frac_same_sign, signed_breadth).
    - mean_abs_trend: average |trend_strength| across members = how strongly trending the basket is
    - frac_same_sign: fraction of members trending the SAME (dominant) direction = synchronization
    - signed_breadth: (n_up - n_dn)/n in [-1,1]
    """
    mem = members or BASKET
    ts_list = []
    for s in mem:
        try: T, B, atrs = series(s)
        except Exception: continue
        j = last_idx_at_or_before(T, ts)
        tsr = trend_strength(B, atrs, j, lb)
        if tsr is not None: ts_list.append(tsr)
    n = len(ts_list)
    if n == 0: return (0, 0.0, 0.0, 0.0)
    mean_abs = sum(abs(x) for x in ts_list) / n
    n_up = sum(1 for x in ts_list if x > 0); n_dn = n - n_up
    dom = max(n_up, n_dn)
    frac_same = dom / n
    signed = (n_up - n_dn) / n
    return (n, mean_abs, frac_same, signed)

def run(symbols, lb_range=16, stop_atr=1.5, tgt_R=0.75, maxbars=60,
        sync_lb=10, sync_abs_max=None, sync_frac_max=None, align_filter=None):
    """Failed-breakout fade with optional cross-sectional risk-off gate.
    sync_abs_max: only take fade if basket mean_abs_trend <= this (NOT strongly trending).
    sync_frac_max: only take fade if basket frac_same_sign <= this (NOT synchronized).
    align_filter: if 'against' only fade AGAINST the basket's dominant direction is BLOCKED
                  when basket synchronized (i.e. require fade not be fighting a sync trend).
    All gates leak-free (basket state from bars<=signal time)."""
    rows = []
    for s in symbols:
        cost = w1.cost_for(s)
        for (t, d, i, B, ac, vr, a, dist_opp, c, rhi, rlo, pdh, pdl) in ir.signals(s, lb_range):
            ts = t  # signal bar open time; bar i is closed at decision -> basket uses <= ts (incl bar i of others)
            n_b, mabs, frac, signed = basket_state(ts, sync_lb)
            if sync_abs_max is not None and mabs > sync_abs_max: continue
            if sync_frac_max is not None and frac > sync_frac_max: continue
            if align_filter == 'against':
                # block fade that fights a synchronized basket trend:
                # short-fade (d=-1) during sync UP basket, or long-fade (d=+1) during sync DOWN.
                if frac >= 0.70 and abs(signed) >= 0.40:
                    if (d < 0 and signed > 0) or (d > 0 and signed < 0):
                        continue
            sd = stop_atr * a
            rcost = cost / stop_atr
            R = simulate(B, i, d, stop_dist=sd, target_dist=tgt_R*sd, maxbars=maxbars, cost=rcost)
            rows.append(dict(sym=s, year=t.year, date=str(t)[:10], dir=d,
                             mabs=round(mabs, 3), frac=round(frac, 3), signed=round(signed, 3),
                             R=wins(R)))
    return rows

def stat(rows):
    if not rows: return (0, 0.0, 0.0)
    n = len(rows); m = sum(r['R'] for r in rows)/n
    w = sum(1 for r in rows if r['R'] > 0)/n*100
    return n, m, w

def per_year(rows):
    out = {}
    for y in sorted(set(r['year'] for r in rows)):
        out[y] = stat([r for r in rows if r['year'] == y])
    return out

def buckets(rows):
    """trades/yr scaled by # forward years present (2025 full, 2026 partial ~5.4mo)."""
    fwd = [r for r in rows if r['year'] >= 2025]
    # 2026 partial through ~mid-June => ~0.46 yr; 2025 full
    yr2025 = sum(1 for r in fwd if r['year'] == 2025)
    yr2026 = sum(1 for r in fwd if r['year'] == 2026)
    yrs = 1.0 + (5.4/12.0)
    return (len(fwd)/yrs) if yrs > 0 else 0.0
