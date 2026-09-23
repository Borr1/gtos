"""structural_retest.py — NEW SLEEVE (GENERAL): M15 break-and-retest, multi-class/regime, by a VERIFIED CELL whitelist.

Generalizes the M15 structural break-retest detector (OB/BRK/DISP/SWP/FVG) across asset classes, sessions, HTF
regimes and vol-states. Direction = the HTF regime (LONG in an up-trend, SHORT in a down-trend). It fires ONLY in
(class, session, regime, vol-state) cells that PRINCIPAL-VERIFIED every-split + beat the CORRECT null — the ultimate
system "knows what/when/which", so the surface is a whitelist, extensible as more cells verify.

VERIFIED CELLS (one-per-bar deduped, real cost, my own re-derivation; the system's structural-retest breadth incl.
its only dedicated SHORT exposure):
  (crypto, NY,     dn, high) -> SHORT  n=5957 every-split +0.057/+0.055/+0.073, regime-SHORT null p=0.043
  (metal,  London, dn, high) -> SHORT  n=2017 every-split +0.143/+0.075/+0.283, 9 metals+, null p=0.043
  (index,  Asian,  up, high) -> LONG   n=1291 every-split +0.057/+0.091/+0.188, US30/SPX/NAS+, null p=0.010
Exit = fixed 2R + 32-bar time-stop. DEFAULT-OFF candidate; live wiring owner-gated. Supersedes structural_retest_short
(the crypto-short cell is preserved as one whitelist entry). Leak-free (HTF trend uses completed HTF bars<=i; pivots
use closed bars<i; entry at close[i]).
"""
from __future__ import annotations
from typing import Optional
from ..primitives import Bar, atr14
from ..admission import TradeIntent
from ._stop_floor import DEFAULT_ATR_STOP_FLOOR, floor_stop
from ._server_clock import server_hour
from .spot_choice import all_false, ask, bar_id

HTF_BARS = 16
HTF_LB = 30
GATE_K = 1.2
HIGH_VOL = 1.4
STOP_BUF = 0.10
#: Shared legacy constant; retained as this module's public name.
ATR_STOP_FLOOR = DEFAULT_ATR_STOP_FLOOR
TARGET_R = 2.0
MAXBARS = 32
MIN_BARS = 512

# class -> symbols (the verified surfaces per cell)
_CRYPTO = ("BTCUSD", "ETHUSD", "XRPUSD", "XTZUSD", "DASHUSD", "DOTUSD", "ADAUSD", "LTCUSD")
_METAL = ("XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "XCUUSD")
_INDEX = ("SPX500", "GER40", "UK100", "NAS100", "JP225", "US500_cash", "US100_cash", "AUS200_cash")
_CLASS_OF = {**{s: "crypto" for s in _CRYPTO}, **{s: "metal" for s in _METAL}, **{s: "index" for s in _INDEX}}
ON_SURFACE = tuple(_CLASS_OF.keys())

# verified (class, session, regime, vol) cells -> the regime fixes the trade direction (up=+1 long / dn=-1 short)
WHITELIST = {
    ("crypto", "NY", "dn", "high"),
    ("metal", "London", "dn", "high"),
    ("index", "Asian", "up", "high"),
}


def _hour(t):
    """SERVER-LOCAL hour of the decision bar. Repaired 2026-07-30 (Session AK, B950).

    This sleeve's `_session` boundaries (8 / 16) are a verbatim port of
    `wave1_structure_setups_ict.session_id` (`:93-97`), which read `t.hour` off the
    broker-clock research CSV archive — so they are FTMO **server** hours, exactly as
    `_server_clock`'s docstring says of every sleeve in this package. The live feed is true
    UTC (`bar_provider.py:5-7`), so the original `return t.hour` put every bar 2 h (winter)
    or 3 h (summer) into the WRONG session bucket. That is not cosmetic here: the whole
    surface is a `(class, session, regime, vol)` whitelist, so the bucket decides whether the
    bar can trade at all and in which direction.

    Why the F7/B29/B54 repair pass missed it: those nine sleeves are all in a production
    registry and this one is not (no `SleeveSpec` in `sleeves/registry.py`), so it was never
    in the deployed set the repair enumerated. `tests/ultimate_book/test_sleeve_server_clock.py`
    covers the nine and omitted this one; it now covers this one too.

    Carries NO live-behaviour change: `structural_retest` is reachable from no registry and
    is not in the deployed candidate allowlist. Fails closed on an unusable stamp, as every
    other caller of this module does.
    """
    return server_hour(t)


def _session(h):
    if h is None:
        return None
    if h < 8:
        return "Asian"
    if h < 16:
        return "London"
    return "NY"


def _htf_trend_at(bars, i):
    HB = []
    blk_o = blk_h = blk_l = blk_c = None
    cnt = 0
    completed_at_i = -1
    for k in range(i + 1):
        b = bars[k]
        if cnt == 0:
            blk_o, blk_h, blk_l = b.o, b.h, b.l
        blk_h = max(blk_h, b.h); blk_l = min(blk_l, b.l); blk_c = b.c; cnt += 1
        if k == i:
            completed_at_i = len(HB) - 1
        if cnt == HTF_BARS:
            HB.append(Bar(blk_o, blk_h, blk_l, blk_c)); cnt = 0
    hk = completed_at_i
    if hk is None or hk < HTF_LB:
        return 0
    a = atr14(HB, hk)
    if a <= 0:
        return 0
    diff = HB[hk].c - HB[hk - HTF_LB].c
    return 1 if diff > a else (-1 if diff < -a else 0)


def _pivot_high(bars, i, left=2, right=2, lookback=40):
    for p in range(i - 1 - right, max(i - 1 - right - lookback, left), -1):
        seg = bars[p - left:p + right + 1]
        if seg and bars[p].h == max(b.h for b in seg) and all(bars[p].h >= b.h for b in seg):
            return bars[p].h, p
    return None, None


def _pivot_low(bars, i, left=2, right=2, lookback=40):
    for p in range(i - 1 - right, max(i - 1 - right - lookback, left), -1):
        seg = bars[p - left:p + right + 1]
        if seg and bars[p].l == min(b.l for b in seg) and all(bars[p].l <= b.l for b in seg):
            return bars[p].l, p
    return None, None


def _detect(bars, A, i, d):
    """Run the 5 detectors in direction d (+1 long / -1 short) at bar i. Return stop_dist or None (OB->BRK->DISP->SWP->FVG)."""
    a = A[i]
    b = bars[i]
    if d > 0:
        for k in range(i - 2, max(i - 9, 110), -1):                                  # OB long
            if bars[k].c < bars[k].o and bars[k + 1].c > bars[k].h:
                ob_top, ob_bot = bars[k].h, bars[k].l
                if b.l <= ob_top and b.c > ob_bot and b.c > b.o:
                    return floor_stop((b.c - min(b.l, ob_bot)) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        ph, pp = _pivot_high(bars, i)                                                 # BRK long
        if ph is not None and any(bars[j].c > ph + 0.10 * a for j in range(pp + 1, i)) and b.l <= ph and b.c > ph and b.c > b.o:
            return floor_stop((b.c - b.l) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        for k in range(i - 1, max(i - 5, 110), -1):                                   # DISP long
            if (bars[k].h - bars[k].l) >= 1.5 * a and bars[k].c > bars[k].o and bars[k].c > bars[k - 1].c and b.l < bars[k].c and b.c > b.o and b.c >= bars[k].o:
                return floor_stop((b.c - b.l) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        pl, pp = _pivot_low(bars, i)                                                  # SWP long
        if pl is not None and (pl - b.l) >= 0.05 * a and b.c > pl and (b.c - pl) >= 0.10 * a and b.c > b.o:
            return floor_stop((b.c - b.l) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        for k in range(i - 2, max(i - 9, 110), -1):                                   # FVG long
            gap_top = bars[k].l; gap_bot = bars[k - 2].h
            if gap_top - gap_bot >= 0.10 * a and b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                return floor_stop((b.c - min(b.l, gap_bot)) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        return None
    else:
        for k in range(i - 2, max(i - 9, 110), -1):                                   # OB short
            if bars[k].c > bars[k].o and bars[k + 1].c < bars[k].l:
                ob_top, ob_bot = bars[k].h, bars[k].l
                if b.h >= ob_bot and b.c < ob_top and b.c < b.o:
                    return floor_stop((max(b.h, ob_top) - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        pl, pp = _pivot_low(bars, i)                                                  # BRK short
        if pl is not None and any(bars[j].c < pl - 0.10 * a for j in range(pp + 1, i)) and b.h >= pl and b.c < pl and b.c < b.o:
            return floor_stop((b.h - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        for k in range(i - 1, max(i - 5, 110), -1):                                   # DISP short
            if (bars[k].h - bars[k].l) >= 1.5 * a and bars[k].c < bars[k].o and bars[k].c < bars[k - 1].c and b.h > bars[k].c and b.c < b.o and b.c <= bars[k].o:
                return floor_stop((b.h - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        ph, pp = _pivot_high(bars, i)                                                 # SWP short
        if ph is not None and (b.h - ph) >= 0.05 * a and b.c < ph and (ph - b.c) >= 0.10 * a and b.c < b.o:
            return floor_stop((b.h - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        for k in range(i - 2, max(i - 9, 110), -1):                                   # FVG short
            gap_bot = bars[k].h; gap_top = bars[k - 2].l
            if gap_top - gap_bot >= 0.10 * a and b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                return floor_stop((max(b.h, gap_top) - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
        return None


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit a structural-retest TradeIntent (direction = HTF regime) when (class,session,regime,high-vol) is a
    verified whitelist cell and a detector triggers. Fixed 2R + MAXBARS time-stop. Leak-free."""
    if not bars:
        return None
    cls = _CLASS_OF.get(symbol)
    i = len(bars) - 1
    t = bar_time if bar_time is not None else (bar_times[i] if bar_times and len(bar_times) == len(bars) else None)
    hour = _hour(t)
    sess = _session(hour)
    if sess is None:
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None
    vol_fail = True
    if i >= 99:
        sma = sum(atr14(bars, k) for k in range(i - 99, i + 1)) / 100
        if sma <= 0:
            return None
        vol_fail = a / sma < HIGH_VOL or a < GATE_K * sma
    tr = _htf_trend_at(bars, i) if i >= MIN_BARS else 0
    regime = "up" if tr == 1 else ("dn" if tr == -1 else "range")
    whitelist_miss = cls is None or (cls, sess, regime, "high") not in WHITELIST
    sd = None
    if cls is not None and i >= 100:
        Afull = [atr14(bars, k) for k in range(len(bars))]
        sd = _detect(bars, Afull, i, tr)
    if sd is not None and sd <= 0:
        return None
    sides = ask(
        sleeve="structural_retest",
        symbol=symbol,
        bar_id=bar_id(decision_day, i, bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"symbol {symbol} has no structural class",
                "measured": cls is None,
            },
            "warmup_short": {
                "condition": f"latest bar index {i} is below {MIN_BARS} or below 100",
                "measured": i < MIN_BARS or i < 100,
            },
            "vol_fail": {
                "condition": f"atr over its 100-bar mean is below {HIGH_VOL} or atr is below {GATE_K} times that mean",
                "measured": vol_fail,
            },
            "whitelist_miss": {
                "condition": "the tuple (class, session, regime, high) is not in the verified whitelist",
                "measured": whitelist_miss,
            },
            "detector_absent": {
                "condition": "no structural detector printed a stop at the latest closed bar",
                "measured": sd is None,
            },
        },
    )
    if not all_false(sides):
        return None
    if sd is None:
        return None
    return TradeIntent(sleeve="structural_retest", symbol=symbol, direction=tr,
                       decision_day=decision_day, stop_dist=sd, target_dist=TARGET_R * sd)
