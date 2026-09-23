"""Vendored VOLUME / AUCTION PROFILE engine for the live vp_euidx_pocgrav sleeve.

BYTE-FAITHFUL port of the LOCKED route engine
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/volume_profile.py
The ONLY adaptation is the M1 SOURCE: the route reads M1 CSVs from data/mt5_research_exports
(volume_profile.load_m1, route lines 54-81); the live port has no CSV — it consumes the live M1
feed as (aux_bars, aux_times) the book engine fetches (bar_provider TF_M1, tick_volume in Bar.v).
Every other function is a verbatim copy with the cited source lines, so the live profile/POC/value-
area/node computation is IDENTICAL to the validated book:

  DayProfile            <- route volume_profile.py:87-105   (container, verbatim)
  _distribute_bar_volume<- route volume_profile.py:108-127  (verbatim)
  _value_area           <- route volume_profile.py:130-144  (verbatim)
  _find_nodes           <- route volume_profile.py:147-172  (verbatim)
  build_day_profile     <- route volume_profile.py:175-200  (verbatim)
  daily_profiles        <- route volume_profile.py:203-232  (verbatim body; SOURCE line adapted:
                            `T, B = load_m1(sym)` -> `T, B = load_m1(aux_bars, aux_times)`)
  prior_profile_at      <- route volume_profile.py:239-250  (verbatim — the leak-free prior-day pick)
  nearest_node_state    <- route volume_profile.py:253-286  (verbatim)
  load_m1               <- route volume_profile.py:54-81    (ADAPTED: CSV -> (aux_bars, aux_times))
  BIN_FRAC              <- route VP_confluence.py:29 (=0.03, the bin_atr_frac the VP sleeve passes
                            via `vp.daily_profiles(sym, bin_atr_frac=vc.BIN_FRAC)`).

LEAK DISCIPLINE (route docstring lines 15-22, preserved): a day-D profile is built ONLY from day-D
M1 bars; an entry at H4 bar time t uses prior_profile_at -> the most recent COMPLETED day strictly
before t.date(). Reproduced verbatim here. Pure compute: stdlib only, no IO/MT5/network.
"""
from __future__ import annotations
import math, statistics
from dataclasses import dataclass, field
from datetime import date, timezone
from collections import OrderedDict

# Route VP_confluence.py:29 — the bin_atr_frac the VP sleeve actually uses (NOT the volume_profile.py
# default of 0.10). The generator passes this explicitly, exactly as the route does (vc.BIN_FRAC).
BIN_FRAC = 0.03


# -------------------------------------------------------------------------
# M1 loading — ADAPTED from route volume_profile.load_m1 (lines 54-81).
# Route: reads {sym}_M1.csv across monthly bridge dirs, builds Bar(o,h,l,c,v) with v=TICK VOLUME,
#        dedups by timestamp (merged[t]=Bar(...), last wins), returns (times, bars) ascending.
# Live: the M1 feed already arrives as (aux_bars, aux_times) from the engine (bar_provider TF_M1;
#       Bar.v carries tick_volume). This function reproduces the route's POST-LOAD INVARIANTS
#       byte-for-byte — dedup by timestamp (last wins) + ascending sort — over the live feed instead
#       of CSV rows. tz-aware times are normalized to UTC so the per-day grouping in daily_profiles
#       (`t.date()`) is the UTC calendar date (the route's M1 timestamps are already day-local/naive;
#       naive inputs are left untouched so synthetic-parity fixtures match the route exactly).
# -------------------------------------------------------------------------
def _to_utc(t):
    """Normalize a tz-aware datetime to UTC (so `.date()` is the UTC day); leave naive datetimes
    untouched (the route's M1 timestamps are naive — keeps synthetic parity exact)."""
    tz = getattr(t, "tzinfo", None)
    return t.astimezone(timezone.utc) if tz is not None else t


def load_m1(aux_bars, aux_times):
    """Return (times[list[datetime]], bars[list[Bar(o,h,l,c,v)]]) of M1, ascending, deduped — the
    same shape route volume_profile.load_m1 returns, but sourced from the live (aux_bars, aux_times)
    feed instead of CSV. v is TICK VOLUME (Bar.v). Returns ([], []) when the feed is empty/misaligned.

    Route invariants reproduced: dedup by timestamp (merged[t]=bar, last wins — route line 69 overwrite
    semantics) and ascending sort by timestamp (route lines 78-79)."""
    if not aux_bars or not aux_times or len(aux_bars) != len(aux_times):
        return [], []
    merged = {}
    for t, b in zip(aux_times, aux_bars):
        merged[_to_utc(t)] = b            # dedup: last wins (route merged[t]=Bar(...) overwrite)
    if not merged:
        return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    T = [k for k, _ in items]; B = [v for _, v in items]
    return T, B


# -------------------------------------------------------------------------
# DayProfile container + builders  (route volume_profile.py:87-200, verbatim)
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


def daily_profiles(aux_bars, aux_times, bin_atr_frac=0.10):
    """Build a leak-free per-day profile dict {date: DayProfile} from the live M1 feed.
    bin_w is set PER DAY from a TRAILING M1 ATR proxy (prior ~ rolling), so it never uses
    that day's full range to set its own resolution beyond the natural day range it bins.
    Returns (profiles_by_date, sorted_dates).

    VERBATIM route volume_profile.daily_profiles (lines 203-232) EXCEPT the SOURCE line:
    route `T, B = load_m1(sym)` -> live `T, B = load_m1(aux_bars, aux_times)`. The bin-width logic
    (statistics.median(recent[-20:]); first day seeds with its own range) is unchanged, so SHORT
    HISTORY (<20 prior M1 days, e.g. the ~16 live now) naturally uses the median of whatever prior
    days exist — no special case, exactly the route's behavior."""
    T, B = load_m1(aux_bars, aux_times)
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
# Query helpers (leak-free)  (route volume_profile.py:239-286, verbatim)
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
