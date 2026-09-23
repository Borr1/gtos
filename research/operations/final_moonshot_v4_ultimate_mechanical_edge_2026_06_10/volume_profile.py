"""
volume_profile.py — VOLUME / AUCTION PROFILE (Market Profile / TPO) LAYER
========================================================================
Track key: VP. Built for the ultimate mechanical-edge substrate (Grand Vision sec II:
"Volume/auction profile from M1/tick: value area, POC, HVN/LVN ... NOT BUILT YET").

WHAT THIS LAYER PRODUCES (a reusable, leak-free volume-by-price substrate):
  Per rolling DAY (UTC), from CLOSED M1 bars only:
    - a volume-by-price histogram (price binned in ATR-relative ticks)
    - POC          : point-of-control = max-volume price bin
    - VAH / VAL    : 70% value-area high / low (expand from POC by heavier neighbour)
    - HVN list     : high-volume nodes (local volume peaks -> price ACCEPTANCE / magnets)
    - LVN list     : low-volume nodes / VOIDS (local volume troughs -> price REJECTION / fast-through)

LEAK DISCIPLINE (mandatory, enforced):
  - A profile for day D is built ONLY from M1 bars whose timestamp.date() == D and which are
    CLOSED. When evaluating an entry at H4/M15 bar index i (time t_i), we use the PRIOR completed
    day's profile (built entirely from bars strictly before t_i's day) — never the current day's
    full profile (that would peek at the future of day D).
  - The "developing" intraday profile uses only M1 bars with timestamp < t_i (closed bars), so
    an intraday POC/VA is also leak-free if needed.
  - geometry_lib.simulate is the only labeler (pessimistic same-bar, stop wins ties).

ENGINE IS IMPORTABLE:
  from volume_profile import (load_m1, daily_profiles, profile_for_day, DayProfile,
                              prior_profile_at, nearest_node_state)
"""
from __future__ import annotations
import sys, os, csv, math, json, statistics
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from geometry_lib import Bar, atr14, simulate  # noqa
import wave1_structure_setups_ict as w1        # H4 loader, cost_for, levels
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa

MROOT = ROOT + "/data/mt5_research_exports"

# -------------------------------------------------------------------------
# M1 loading (tick-volume) across all monthly bridge dirs, deduped by timestamp
# -------------------------------------------------------------------------
def _m1_month_dirs():
    ds = []
    for d in sorted(os.listdir(MROOT)):
        if d.startswith("bridge_ftmo_m1_") or d.startswith("bridge_ftmo_ext_m1_"):
            ds.append(os.path.join(MROOT, d))
    return ds

_M1_CACHE = {}
def load_m1(sym):
    """Return (times[list[datetime]], bars[list[Bar(o,h,l,c,v)]]) of M1, ascending, deduped.
    v is TICK VOLUME (the standard FX/CFD volume proxy). Cached per symbol."""
    if sym in _M1_CACHE:
        return _M1_CACHE[sym]
    merged = {}
    for d in _m1_month_dirs():
        p = os.path.join(d, f"{sym}_M1.csv")
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                for row in csv.DictReader(f):
                    try:
                        t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                        merged[t] = Bar(float(row["open"]), float(row["high"]),
                                        float(row["low"]), float(row["close"]),
                                        float(row.get("volume", 0) or 0))
                    except Exception:
                        continue
        except Exception:
            continue
    if not merged:
        _M1_CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    T = [k for k, _ in items]; B = [v for _, v in items]
    _M1_CACHE[sym] = (T, B)
    return T, B


# -------------------------------------------------------------------------
# DayProfile container + builders
# -------------------------------------------------------------------------
@dataclass
class DayProfile:
    day: date
    bin_w: float                      # price width of one bin
    lo: float                         # bottom price of bin 0
    hist: list = field(default_factory=list)   # volume per bin (index 0 = lowest price)
    total_v: float = 0.0
    poc: float = 0.0                  # price (bin center) of point-of-control
    poc_bin: int = 0
    vah: float = 0.0                  # value-area high (price)
    val: float = 0.0                  # value-area low (price)
    day_h: float = 0.0
    day_l: float = 0.0
    hvn: list = field(default_factory=list)   # list of HVN prices (bin centers), strongest first
    lvn: list = field(default_factory=list)   # list of LVN/void prices (bin centers)
    n_m1: int = 0

    def bin_center(self, b):
        return self.lo + (b + 0.5) * self.bin_w


def _distribute_bar_volume(hist, lo, bin_w, nbins, bar):
    """Distribute one M1 bar's volume across the price bins its range spans.
    Uses uniform spread across [low,high] (the standard volume-profile approximation when
    only OHLCV per bar is available). Leak-free: uses only this closed bar's own OHLC."""
    if bar.h <= bar.l:
        b = int((bar.c - lo) / bin_w)
        if 0 <= b < nbins:
            hist[b] += bar.v
        return
    b_lo = int((bar.l - lo) / bin_w)
    b_hi = int((bar.h - lo) / bin_w)
    b_lo = max(0, min(nbins - 1, b_lo))
    b_hi = max(0, min(nbins - 1, b_hi))
    span = b_hi - b_lo + 1
    if span <= 1:
        hist[b_lo] += bar.v
    else:
        share = bar.v / span
        for b in range(b_lo, b_hi + 1):
            hist[b] += share


def _value_area(hist, poc_bin, total_v, frac=0.70):
    """Expand from POC bin outward, each step taking the heavier of the two neighbouring bins,
    until cumulative volume >= frac*total. Returns (low_bin, high_bin)."""
    n = len(hist)
    lo_b = hi_b = poc_bin
    acc = hist[poc_bin]
    target = frac * total_v
    while acc < target and (lo_b > 0 or hi_b < n - 1):
        down = hist[lo_b - 1] if lo_b > 0 else -1.0
        up = hist[hi_b + 1] if hi_b < n - 1 else -1.0
        if up >= down:
            hi_b += 1; acc += hist[hi_b]
        else:
            lo_b -= 1; acc += hist[lo_b]
    return lo_b, hi_b


def _find_nodes(hist, bin_w, lo, total_v):
    """HVN = local maxima with volume >= 1.3x neighbourhood mean; LVN = local minima with
    volume <= 0.5x neighbourhood mean (and > 0 occupancy somewhere around them, i.e. inside the
    traded range). Returns (hvn_prices_sorted_by_strength, lvn_prices)."""
    n = len(hist)
    if n < 5 or total_v <= 0:
        return [], []
    # occupied range
    occ = [i for i in range(n) if hist[i] > 0]
    if not occ:
        return [], []
    a, z = occ[0], occ[-1]
    mean_v = total_v / max(1, (z - a + 1))
    hvn = []; lvn = []
    for i in range(a + 1, z):
        v = hist[i]
        left = hist[i - 1]; right = hist[i + 1]
        # local peak
        if v >= left and v >= right and v >= 1.3 * mean_v:
            hvn.append((v, lo + (i + 0.5) * bin_w))
        # local trough / void (must be a real interior trough between traded prices)
        if v <= left and v <= right and v <= 0.5 * mean_v:
            lvn.append((v, lo + (i + 0.5) * bin_w))
    hvn.sort(key=lambda x: -x[0])
    lvn.sort(key=lambda x: x[0])
    return [p for _, p in hvn], [p for _, p in lvn]


def build_day_profile(day, m1_bars, bin_w):
    """Build a DayProfile from a list of CLOSED M1 bars belonging to `day`. bin_w in price units.
    All inputs are that day's own bars -> for forward use, callers must take the PRIOR day."""
    if not m1_bars or bin_w <= 0:
        return None
    day_l = min(b.l for b in m1_bars)
    day_h = max(b.h for b in m1_bars)
    rng = day_h - day_l
    if rng <= 0:
        return None
    nbins = max(5, int(math.ceil(rng / bin_w)) + 1)
    lo = day_l
    hist = [0.0] * nbins
    for b in m1_bars:
        _distribute_bar_volume(hist, lo, bin_w, nbins, b)
    total_v = sum(hist)
    if total_v <= 0:
        return None
    poc_bin = max(range(nbins), key=lambda i: hist[i])
    lo_b, hi_b = _value_area(hist, poc_bin, total_v, 0.70)
    hvn, lvn = _find_nodes(hist, bin_w, lo, total_v)
    dp = DayProfile(day=day, bin_w=bin_w, lo=lo, hist=hist, total_v=total_v,
                    poc_bin=poc_bin, poc=lo + (poc_bin + 0.5) * bin_w,
                    vah=lo + (hi_b + 0.5) * bin_w, val=lo + (lo_b + 0.5) * bin_w,
                    day_h=day_h, day_l=day_l, hvn=hvn, lvn=lvn, n_m1=len(m1_bars))
    return dp


def daily_profiles(sym, bin_atr_frac=0.10):
    """Build a leak-free per-day profile dict {date: DayProfile} for a symbol.
    bin_w is set PER DAY from a TRAILING M1 ATR proxy (prior ~ rolling), so it never uses
    that day's full range to set its own resolution beyond the natural day range it bins.
    Returns (profiles_by_date, sorted_dates)."""
    T, B = load_m1(sym)
    if not B:
        return {}, []
    # group M1 by day
    by_day = OrderedDict()
    for t, b in zip(T, B):
        by_day.setdefault(t.date(), []).append(b)
    days = list(by_day.keys())
    # per-day bin width = bin_atr_frac * (rolling median of recent daily ranges) — a stable,
    # non-lookahead resolution (uses ONLY prior days' ranges).
    day_rng = {d: (max(x.h for x in bs) - min(x.l for x in bs)) for d, bs in by_day.items()}
    profiles = {}
    recent = []
    for d in days:
        # bin width from PRIOR days' median range (leak-free); seed with own range if first
        if recent:
            med_rng = statistics.median(recent[-20:])
        else:
            med_rng = day_rng[d]
        bw = max(1e-9, bin_atr_frac * med_rng)
        dp = build_day_profile(d, by_day[d], bw)
        if dp is not None:
            profiles[d] = dp
        recent.append(day_rng[d])
    return profiles, [d for d in days if d in profiles]


# -------------------------------------------------------------------------
# Query helpers (leak-free): given an entry time, fetch the PRIOR-day profile,
# and classify where the entry price sits relative to the profile's nodes.
# -------------------------------------------------------------------------
def prior_profile_at(profiles, sorted_days, t):
    """Return the DayProfile of the most recent COMPLETED day strictly before t.date().
    This is the leak-free profile available at decision time t."""
    td = t.date()
    # binary-ish search: sorted_days ascending
    prev = None
    for d in sorted_days:
        if d < td:
            prev = d
        else:
            break
    return profiles.get(prev) if prev is not None else None


def nearest_node_state(dp, price, atr):
    """Classify `price` against a DayProfile. Returns a dict of leak-free state features:
      d_poc_atr   : signed (price-poc)/atr
      in_va       : price within [VAL,VAH]
      above_vah   : price > VAH ; below_val : price < VAL
      near_lvn_atr: distance to nearest LVN/void in ATR (None if no LVN)
      near_hvn_atr: distance to nearest HVN in ATR (None if no HVN)
      at_lvn      : within 0.25 ATR of an LVN/void
      at_hvn      : within 0.25 ATR of an HVN
      at_poc      : within 0.25 ATR of POC
      at_vah/at_val: within 0.25 ATR of the value-area edge
    """
    if dp is None or atr <= 0:
        return None
    s = {}
    s["d_poc_atr"] = (price - dp.poc) / atr
    s["in_va"] = dp.val <= price <= dp.vah
    s["above_vah"] = price > dp.vah
    s["below_val"] = price < dp.val
    def nearest(lst):
        if not lst:
            return None, None
        best = min(lst, key=lambda p: abs(p - price))
        return best, abs(best - price) / atr
    hvn_p, hvn_d = nearest(dp.hvn)
    lvn_p, lvn_d = nearest(dp.lvn)
    s["near_hvn_atr"] = hvn_d
    s["near_lvn_atr"] = lvn_d
    s["at_hvn"] = hvn_d is not None and hvn_d <= 0.25
    s["at_lvn"] = lvn_d is not None and lvn_d <= 0.25
    s["at_poc"] = abs(price - dp.poc) / atr <= 0.25
    s["at_vah"] = abs(price - dp.vah) / atr <= 0.25
    s["at_val"] = abs(price - dp.val) / atr <= 0.25
    return s


# small self-test when run directly
if __name__ == "__main__":
    for sym in ["XAUUSD", "NAS100", "USOIL_cash"]:
        profs, days = daily_profiles(sym)
        if not days:
            print(sym, "no M1"); continue
        d = days[len(days)//2]
        dp = profs[d]
        print(f"{sym} {d}: POC={dp.poc:.4f} VAH={dp.vah:.4f} VAL={dp.val:.4f} "
              f"nHVN={len(dp.hvn)} nLVN={len(dp.lvn)} totV={dp.total_v:.0f} ndays={len(days)} "
              f"binw={dp.bin_w:.5f}")
