"""KB5_condition_families.py — NEW orthogonal condition families for the confluence engine
=========================================================================================
Track: new condition families. THE_GRAND_VISION lists four MM/behavioral condition
families the confluence engine (confluence.py, 7 families) lacks:
    1. round-number magnetism      (behavioral: price magnets at psychological levels)
    2. session / time-of-day       (institutional schedules: Asia / London / NY)
    3. DXY -> FX directional bias   (intermarket: dollar leads the FX laggard)
    4. oil -> CAD directional bias  (intermarket: crude leads USDCAD/CAD crosses)

DOCTRINE (enforced):
  - NO LOOKAHEAD: every condition is a pure function of CLOSED bars index<=i. For the
    intermarket families the LEADER series is sampled at the SAME timestamp as the
    laggard bar i (a closed bar), never a future bar.
  - Outcomes are labeled ONLY by geometry_lib.simulate (leak-free pessimistic same-bar).
  - NO AVERAGES AS VERDICTS: TRAIN(<=2024) vs FORWARD(2025-26), per-year, n-gate.
  - HIGH ODDS FROM CONFLUENCE: each family is a directional boolean
    (ctx,i,direction)->bool ("does this family AGREE with the trade direction at i?")
    so it slots straight into confluence.CONDITIONS, and we measure phi-independence vs
    the existing 7 + marginal odds-lift + whether adding it MULTIPLIES the stack.

DATA REALITY (load-bearing constraints, measured):
  - DXY_cash H4 only exists from 2025-01-06 (entirely FORWARD) -> real DXY cannot be
    forward-holdout validated. We therefore build a SYNTHETIC DXY proxy from the FX
    majors (full history), which tracks real DXY at return-corr +0.993 (4-major) /
    +0.987 (2-major) over the 2025+ overlap. The proxy is leak-free (closed bars<=i).
  - USOIL_cash from 2020-12-31, USDCAD from 2019-05-20 -> oil->CAD has train+forward.
  - H4 bars carry 6 hour-buckets (0,4,8,12,16,20 server time) -> session granularity is
    coarse (Asia / London / NY-overlap / NY), honestly reported as such.

This module imports cleanly and exposes EXTRA_CONDITIONS (same shape as
confluence.CONDITIONS) so the analyzer can append them to the registry.
"""
from __future__ import annotations
import sys, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import wave1_structure_setups_ict as w1
from geometry_lib import atr14

# ---------------------------------------------------------------------------
# SHARED LEADER SERIES (built once, cached) — all leak-free (close prices)
# ---------------------------------------------------------------------------
class _Leaders:
    """Builds and caches the intermarket leader series keyed by timestamp.
    DXY proxy + oil close. All values are CLOSED-bar closes; sampling at the
    laggard's timestamp i means we use leader data <= i (same bar close), never future."""
    def __init__(self):
        self._dxy = None      # dict t -> log-proxy level
        self._dxy_w = None    # which proxy was built
        self._oil = None      # dict t -> oil close
        self._cache = {}      # sym -> aligned arrays for fast condition eval

    # ---- DXY synthetic proxy (closed-bar) ----
    def dxy_log(self):
        if self._dxy is not None:
            return self._dxy
        def ser(sym):
            T, B = w1.load(sym)
            return {t: b.c for t, b in zip(T, B)}
        eur = ser("EURUSD"); jpy = ser("USDJPY")
        gbp = ser("GBPUSD"); chf = ser("USDCHF")
        # 4-major proxy where all available (corr +0.993), else 2-major (corr +0.987).
        # DXY official weights EUR .576 / JPY .136 / GBP .119 / CHF .036 (USD-numerator
        # pairs JPY/CHF add +ln, USD-denominator pairs EUR/GBP subtract ln).
        out = {}
        ts = set(eur) | set(jpy)
        for t in ts:
            if t in eur and t in jpy and t in gbp and t in chf:
                out[t] = (-0.576*math.log(eur[t]) - 0.119*math.log(gbp[t])
                          + 0.136*math.log(jpy[t]) + 0.036*math.log(chf[t]))
            elif t in eur and t in jpy:
                out[t] = (-0.576*math.log(eur[t]) + 0.136*math.log(jpy[t]))
        self._dxy = out
        return out

    def oil_close(self):
        if self._oil is not None:
            return self._oil
        # USOIL is the deeper/cleaner crude series; fall back to UKOIL if missing.
        try:
            T, B = w1.load("USOIL_cash")
            d = {t: b.c for t, b in zip(T, B)}
        except Exception:
            d = {}
        if len(d) < 200:
            T, B = w1.load("UKOIL_cash")
            d = {t: b.c for t, b in zip(T, B)}
        self._oil = d
        return d

LEAD = _Leaders()

# ---------------------------------------------------------------------------
# Helper: rolling slope-vs-its-own-vol classification of a leader log series at
# the laggard's bar timestamps. Pure function of values <= t.
# ---------------------------------------------------------------------------
def _leader_dir_at(series_by_t, T, i, lb=6, k=0.5):
    """Direction of the leader over the last `lb` laggard-bars ending at i, using only
    leader closes at timestamps <= T[i]. Returns +1/-1/0 (0 = no clear move / no data).
    Normalised by the leader's own recent abs-change so it is scale-free and adaptive."""
    if i < lb:
        return 0
    # collect leader values at the laggard timestamps it shares (closed bars only)
    vals = []
    for j in range(max(0, i-lb-20), i+1):
        v = series_by_t.get(T[j])
        vals.append(v)
    # need the endpoints present
    cur = series_by_t.get(T[i])
    prev = series_by_t.get(T[i-lb])
    if cur is None or prev is None:
        return 0
    diff = cur - prev
    # scale = mean abs step over the available window
    steps = [abs(vals[m]-vals[m-1]) for m in range(1, len(vals)) if vals[m] is not None and vals[m-1] is not None]
    if not steps:
        return 0
    scale = sum(steps)/len(steps)
    if scale <= 0:
        return 0
    z = diff/(scale*math.sqrt(lb))
    if z >= k:  return +1
    if z <= -k: return -1
    return 0

# Which symbols are "USD numerator" (USD is base): a STRONGER dollar pushes them UP.
# For "USD denominator" pairs (USD is quote, e.g. EURUSD), a stronger dollar pushes them DOWN.
_USD_NUMERATOR = {"USDJPY","USDCAD","USDCHF","USDCNH","USDSGD"}
_USD_DENOMINATOR = {"EURUSD","GBPUSD","AUDUSD","NZDUSD"}
# JPY crosses & EURGBP etc. have no clean single-dollar sign -> excluded from DXY family.
_FX_DOLLAR_SIGN = {}
for s in _USD_NUMERATOR: _FX_DOLLAR_SIGN[s] = +1   # dollar-up -> pair up
for s in _USD_DENOMINATOR: _FX_DOLLAR_SIGN[s] = -1 # dollar-up -> pair down

# CAD exposure: USDCAD (USD base) rises when oil FALLS (CAD is a petro-currency, so
# oil-up -> CAD-up -> USDCAD-down). So oil-up implies USDCAD SHORT bias.
_OIL_CAD_SIGN = {"USDCAD": -1}  # oil-up -> USDCAD-down ; CADJPY/CADCHF not in universe here


# ---------------------------------------------------------------------------
# NEW CONDITION FAMILIES — each (ctx, i, direction) -> bool (AGREES with d?)
# ctx is confluence.SymCtx (has .sym, .B, .atrs, .T? ) — we re-derive T via w1 if absent.
# ---------------------------------------------------------------------------
def _ctx_T(ctx):
    """confluence.SymCtx stores T as ctx.T; if a bare ctx is passed, load lazily."""
    T = getattr(ctx, "T", None)
    if T is not None:
        return T
    if not hasattr(ctx, "_T_cache"):
        T, _ = w1.load(ctx.sym)
        ctx._T_cache = T
    return ctx._T_cache


# --- 1. ROUND-NUMBER MAGNETISM ---------------------------------------------
# Behavioral: price clusters/reacts at psychological round levels. We measure the
# distance from the nearest round level (on a per-symbol price grid) and assert the
# trade direction is AWAY from a just-tested round level in the favour direction — i.e.
# for a LONG, the close is just ABOVE a round level it reclaimed (round = support/launch);
# for a SHORT, just BELOW a round level it rejected (round = resistance/cap).
def _round_grid(price):
    """Pick a round-number step appropriate to the price magnitude (1% of price ->
    snap to a 'clean' decade step). Returns the step size."""
    if price <= 0:
        return 0.0
    mag = 10 ** math.floor(math.log10(price))
    # step ~ one notch finer than the price magnitude: e.g. price 1.085 -> 0.01 ; 145 -> 1 ;
    # 1950 -> 10 ; 65000 -> 100. We use mag/100 as the psychological grid (00 levels).
    step = mag / 100.0
    return step

def c_round_magnet(ctx, i, d):
    """Round-number magnetism in the trade direction: the close is within 0.15*ATR of a
    round level AND on the favour side (long just above a reclaimed round; short just
    below a rejected round). Leak-free (bar i close only)."""
    a = ctx.atrs[i]
    if a <= 0:
        return False
    c = ctx.B[i].c
    step = _round_grid(c)
    if step <= 0:
        return False
    nearest = round(c/step)*step
    dist = abs(c - nearest)
    if dist > 0.15*a:
        return False
    # favour-side: long wants close >= round (reclaimed up off it); short wants close <= round
    if d > 0:
        return c >= nearest
    return c <= nearest

def c_round_reject(ctx, i, d):
    """Round-number REJECTION footprint on bar i in the trade direction: the bar's wick
    pierced a round level but the close came back on the favour side (a fade off the
    magnet). For a LONG: low pierced below a round level, close back above. Mirror short.
    A discrete behavioral MM-magnet event, independent of the static proximity above."""
    a = ctx.atrs[i]
    if a <= 0:
        return False
    b = ctx.B[i]
    step = _round_grid(b.c)
    if step <= 0:
        return False
    # nearest round in the wick span
    if d > 0:
        lvl = round(b.l/step)*step
        return b.l <= lvl and b.c > lvl and (b.c - lvl) >= 0.05*a and (b.c - b.l) >= 0.10*a
    lvl = round(b.h/step)*step
    return b.h >= lvl and b.c < lvl and (lvl - b.c) >= 0.05*a and (b.h - b.c) >= 0.10*a


# --- 2. SESSION / TIME-OF-DAY ----------------------------------------------
# Institutional schedules. H4 server hours -> coarse sessions:
#   0,4  = Asia ; 8 = London open ; 12 = London/NY overlap ; 16 = NY ; 20 = NY late/close
# Two condition flavours: (a) is the bar in the LONDON+NY active window (8/12/16) where
# directional follow-through is historically richest; (b) momentum-of-session (the active
# session aligns with d). Both are pure functions of T[i].hour + bar i.
_SESSION = {0:"asia",4:"asia",8:"london",12:"overlap",16:"ny",20:"nylate"}
_ACTIVE_HOURS = {8,12,16}   # London open .. NY

def c_session_active(ctx, i, d):
    """Time-of-day: bar i opened in the active London/NY window (richest follow-through).
    Direction-agnostic regime flag (returns the same for long/short) — it gates WHEN, the
    other conditions gate WHICH WAY. Independent of price structure."""
    T = _ctx_T(ctx)
    return T[i].hour in _ACTIVE_HOURS

def c_session_momentum(ctx, i, d):
    """Session momentum: during the active window, the bar itself closed in the trade
    direction with range (an active-session impulse aligned with d). Couples time-of-day
    with intrabar drive, leak-free (bar i only)."""
    T = _ctx_T(ctx)
    if T[i].hour not in _ACTIVE_HOURS:
        return False
    b = ctx.B[i]; a = ctx.atrs[i]
    if a <= 0:
        return False
    body = b.c - b.o
    if d > 0:
        return body >= 0.15*a
    return body <= -0.15*a


# --- 3. DXY -> FX DIRECTIONAL BIAS -----------------------------------------
# Intermarket: the dollar index (synthetic proxy) leads the FX laggard. If the dollar is
# rising and the pair is a USD-denominator (EURUSD), the dollar bias is SHORT the pair;
# if USD-numerator (USDJPY), bias LONG. The condition AGREES with d when the dollar bias
# matches the trade direction. Only fires on dollar-clean pairs; returns False otherwise
# (so it never falsely lifts non-FX symbols).
def c_dxy_bias(ctx, i, d):
    sign = _FX_DOLLAR_SIGN.get(ctx.sym)
    if sign is None:
        return False
    dxy = LEAD.dxy_log()
    if not dxy:
        return False
    T = _ctx_T(ctx)
    dollar_dir = _leader_dir_at(dxy, T, i, lb=6, k=0.5)
    if dollar_dir == 0:
        return False
    pair_bias = dollar_dir * sign   # +1 -> pair-up bias, -1 -> pair-down bias
    return (pair_bias > 0 and d > 0) or (pair_bias < 0 and d < 0)


# --- 4. OIL -> CAD DIRECTIONAL BIAS ----------------------------------------
# Intermarket: crude leads the petro-currency. Oil rising -> CAD strengthens ->
# USDCAD falls. Condition AGREES with d when the oil-implied CAD bias matches d.
# Only fires on CAD-exposed symbols in the universe.
def c_oil_cad_bias(ctx, i, d):
    sign = _OIL_CAD_SIGN.get(ctx.sym)
    if sign is None:
        return False
    oil = LEAD.oil_close()
    if not oil:
        return False
    T = _ctx_T(ctx)
    oil_dir = _leader_dir_at(oil, T, i, lb=6, k=0.5)
    if oil_dir == 0:
        return False
    pair_bias = oil_dir * sign      # oil-up -> USDCAD-down (sign=-1)
    return (pair_bias > 0 and d > 0) or (pair_bias < 0 and d < 0)


# Registry in confluence.CONDITIONS shape.
EXTRA_CONDITIONS = [
    ("round_magnet",  c_round_magnet),
    ("round_reject",  c_round_reject),
    ("sess_active",   c_session_active),
    ("sess_mom",      c_session_momentum),
    ("dxy_bias",      c_dxy_bias),
    ("oil_cad_bias",  c_oil_cad_bias),
]
EXTRA_NAMES = [c[0] for c in EXTRA_CONDITIONS]
