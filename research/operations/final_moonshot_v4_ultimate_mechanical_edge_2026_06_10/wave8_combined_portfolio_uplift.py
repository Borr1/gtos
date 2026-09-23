"""
wave8_combined_portfolio_uplift.py
==================================
THRUST (combined_portfolio_uplift):

  STEP A -- RE-VALIDATE THE MICROSTRUCTURE BOOK WITH CLEAN CODE.
    The prior microstructure_engine.py PREDATES geometry_lib and reported its
    numbers as "edge_r" = (setup mean R) minus a same-class regime baseline,
    via a hand-rolled exit_net() that mixes stop/target logic and is the exact
    code-family that carried the short-side sign bug. Those numbers are NOT a
    clean tradable per-trade R and cannot be trusted. Here S4 (absorption-
    reversal) and S5 (volume-delta-divergence) are RE-IMPLEMENTED from scratch,
    fills ONLY via tested geometry_lib.simulate, features f(bars[<=i]) only,
    signed tick-volume = V*(C-O)/range known-at-i. The question is the HONEST
    tradable one: does the raw net-of-cost per-trade R survive on a strict OOS
    split with matched RANDOM + INVERT nulls under the SAME selection?

  STEP B -- IF (and only if) microstructure survives AND is uncorrelated to the
    gold sleeve, run the EXACT Wave-7 combined test: assemble gold-sleeve +
    surviving microstructure pockets, risk-budget sweep + shuffled-overlap
    diversification null, FTMO-safe sizing + monthly%. Does adding micro raise
    monthly%/Sharpe at EQUAL-or-lower maxDD AND beat >95% of nulls (the bar the
    Wave-7 diversifiers ALL failed)? If micro does not survive Step A, the
    combined test is MOOT and we report that plainly.

STRICT PROTOCOL (the same gauntlet that caught 5 prior leaks):
  - Fills ONLY via tested geometry_lib.simulate / simulate_detail. No hand-rolled
    fills, no sign tricks. R-unit = stop_dist; cost = real per-class median.
  - NO LOOKAHEAD: every entry gate/feature uses ONLY bars at/<=decision bar i;
    signed-vol, rel-vol, range-extreme, SMA trend all f(bars[<=i]); path state
    only from CLOSED simulate() trades; entries de-overlapped per symbol (no
    re-entry until the prior trade on that symbol has CLOSED -> no overlap
    peeking); bad-print bars winsorized (verbatim wave7 clamp).
  - STRICT OOS: SELECT cells on TRAIN<=2024 ONLY (which class x side x exit cells
    are positive on train); FORWARD 2025-26 = untouched readout. Per-year
    2015-2026. The carrier (gold) is the audited WF stream, verbatim from wave7.
  - MATCHED NULLS under the SAME selection:
      (a) RANDOM null: for each kept cell, draw the SAME number of random entry
          bars in the SAME symbols/side/exit; a real edge must beat its random-
          entry twin on FORWARD.
      (b) INVERT null: flip the side of each kept cell; a real edge must beat its
          own inverse on FORWARD.
  - The combined test (Step B) is wave7's machinery VERBATIM (equity path, FTMO
    sizing, risk-budget sweep, shuffled-overlap null) so the bar is identical.
  - Truth over positives. If micro washes on clean code, say so with numbers.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
D1 = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D1M = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
D2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024
ALL_METALS = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "metals"])
PRECIOUS = sorted([s for s in ALL_METALS if s.startswith("XAU") or s.startswith("XAG")])
ENERGY = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "energy"])

STOP_ATR = 2.5      # microstructure R-unit (matches prior engine's stop convention)
TARGET_R = 1.0      # fixed-target reversion exit: 1R target on a 2.5*ATR stop
MAXBARS = 24        # H4 reversion horizon cap (matches prior engine's h=24 winners)

# ============================ data load + winsorize =========================
def syms_in(d):
    if not os.path.isdir(d): return set()
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}
SYMBOLS = sorted(syms_in(D1) | syms_in(D1M) | syms_in(D2))

def _load_one(p):
    T = []; B = []
    if not os.path.exists(p): return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
                T.append(t); B.append(b)
            except Exception:
                continue
    return T, B

def winsorize(times, bars):
    """Conservative single-bar bad-print clamp -- VERBATIM from wave7_aggregate_pockets."""
    n = len(bars)
    if n < 20: return bars
    out = [Bar(b.o, b.h, b.l, b.c, b.v) for b in bars]
    for i in range(2, n-1):
        rng = sorted((bars[k].h - bars[k].l) for k in range(i-10, i) if bars[k].h > bars[k].l)
        if not rng: continue
        med = rng[len(rng)//2]
        if med <= 0: continue
        prev = bars[i-1]; nxt = bars[i+1]; b = bars[i]
        up_exc = b.h - max(prev.h, nxt.h)
        if up_exc > 8*med and nxt.h < b.h - 4*med and b.c < b.h - 4*med:
            out[i].h = max(b.o, b.c, prev.h, nxt.h) + 1.0*med
        dn_exc = min(prev.l, nxt.l) - b.l
        if dn_exc > 8*med and nxt.l > b.l + 4*med and b.c > b.l + 4*med:
            out[i].l = min(b.o, b.c, prev.l, nxt.l) - 1.0*med
    return out

def _load_dirs(sym, dirs):
    merged = {}
    for d in dirs:
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B): merged[t] = b
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    return times, winsorize(times, bars)

_H4 = {}
def load(sym):
    """Microstructure universe loader: D1 + D1M (extra metals history) + D2."""
    if sym in _H4: return _H4[sym]
    _H4[sym] = _load_dirs(sym, (D1, D1M, D2))
    return _H4[sym]

_H4C = {}
def load_carrier(sym):
    """Carrier loader: D1 + D2 ONLY -- byte-identical to wave7_aggregate_pockets so the
    gold sleeve reproduces the audited P0 stream exactly (the Wave-7 comparison bar)."""
    if sym in _H4C: return _H4C[sym]
    _H4C[sym] = _load_dirs(sym, (D1, D2))
    return _H4C[sym]

# ============================ known-at-i features ===========================
def sma_c(bars, i, n):
    if i < n - 1: return None
    return sum(bars[k].c for k in range(i-n+1, i+1))/n

def precompute(B):
    """All series f(bars[<=i]). Returns dict of arrays aligned to bar index."""
    n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    rng = [max(B[i].h - B[i].l, 1e-12) for i in range(n)]
    # signed tick-volume proxy (volume = tick/quote count, NOT traded volume; we use
    # it only as a participation weight on the bar's directional close): known-at-i.
    vd = [B[i].v * (B[i].c - B[i].o) / rng[i] for i in range(n)]
    return atrs, rng, vd

def rolling_mean(arr, i, n):
    if i < n - 1: return None
    s = 0.0
    for k in range(i-n+1, i+1): s += arr[k]
    return s/n

# ============================ S4 / S5 clean entry signals ===================
# Each returns the entry DIRECTION (+1 long / -1 short) or None at bar i, using
# only bars[<=i]. Reversal/fade setups: at a 48-bar range extreme.
def s4_absorption(B, atrs, rng, vd, i, relv_min=1.5, rng_max=0.7, pos_x=0.85, vbar_arr=None):
    """ABSORPTION-reversal: big tick-volume + small range at a 48-bar range extreme
    -> fade. big-vol = V[i] >= relv_min * mean(V[i-19..i]); small range = rng[i] <=
    rng_max*ATR (absorption = a lot of participation moving price little)."""
    if i < 60: return None
    a = atrs[i]
    if a <= 0: return None
    vbar = vbar_arr[i] if vbar_arr is not None else rolling_mean([b.v for b in B], i, 20)
    if vbar is None or vbar <= 0: return None
    if B[i].v / vbar < relv_min: return None        # big participation
    if rng[i] > rng_max * a: return None            # small range vs ATR (absorption)
    hi = max(B[k].h for k in range(i-47, i+1))
    lo = min(B[k].l for k in range(i-47, i+1))
    if hi <= lo: return None
    pos = (B[i].c - lo) / (hi - lo)
    if pos >= pos_x: return -1                       # at top -> fade short
    if pos <= (1.0 - pos_x): return +1              # at bottom -> fade long
    return None

def s5_vdelta(B, atrs, rng, vd, i, lb=48, **_):
    """VOLUME-DELTA-divergence: NEW price extreme on WEAKENING 3-bar signed tick-
    volume -> fade. New extreme = bar i prints the highest high (or lowest low) of
    the last lb bars; weakening = 3-bar signed-vol sum moves AGAINST the new extreme."""
    if i < lb + 12: return None
    a = atrs[i]
    if a <= 0: return None
    hi_prev = max(B[k].h for k in range(i-lb+1, i))  # excludes i (no lookahead)
    lo_prev = min(B[k].l for k in range(i-lb+1, i))
    vd3 = vd[i] + vd[i-1] + vd[i-2]                  # 3-bar signed participation, <=i
    if B[i].h >= hi_prev and B[i].c > B[i].o:        # new high made this bar
        if vd3 <= 0: return -1                        # but signed-vol not bullish -> fade short
    if B[i].l <= lo_prev and B[i].c < B[i].o:        # new low made this bar
        if vd3 >= 0: return +1                        # but signed-vol not bearish -> fade long
    return None

SETUPS = {"S4_absorption": s4_absorption, "S5_vdelta": s5_vdelta}
# TRAIN-only parameter grids (so an over-strict gate can't manufacture a false negative;
# the BEST-ON-TRAIN parameterization is selected, then read forward with matched nulls).
PARAM_GRID = {
    "S4_absorption": [{"relv_min": rv, "rng_max": rm, "pos_x": px}
                      for rv in (1.3, 1.5, 2.0) for rm in (0.6, 0.8, 1.0) for px in (0.8, 0.85)],
    "S5_vdelta": [{"lb": lb} for lb in (24, 36, 48, 60)],
}

# ============================ exit modes (all via simulate) =================
def micro_trade_r(B, i, d, cost, mode):
    """Net R via tested simulate(). All exits two-sided, pessimistic same-bar.
    fixed   : 1R target on STOP_ATR*ATR stop, capped at MAXBARS.
    trail   : ATR trail (arm 1*ATR, gap 1.5*ATR) -- reversion-friendly runner.
    Returns (r, exit_index)."""
    a = atr14(B, i)
    if a <= 0: return None
    sd = STOP_ATR * a
    if mode == "fixed":
        return simulate_detail(B, i, d, stop_dist=sd, target_dist=TARGET_R*sd,
                               cost=cost, maxbars=MAXBARS)
    else:  # trail
        return simulate_detail(B, i, d, stop_dist=sd, trail_arm=1.0*a, trail_gap=1.5*a,
                               cost=cost, maxbars=MAXBARS)

# ============================ build microstructure trade streams ============
def build_micro(setup_name, side_sign, mode, classes=None, invert=False, random_entries=False,
                rng_seed=0, params=None):
    """Build a de-overlapped (per-symbol, no re-entry until prior trade closed)
    trade stream for ONE (setup, side, exit) cell, restricted to `classes`.
    side_sign filters the raw signal to a single tradable side (+1 long / -1 short).
    invert flips the executed direction. random_entries replaces the signal with
    randomly-chosen entry bars (same count per symbol) for the matched RANDOM null.
    params = setup parameterization (selected on train). Returns list of dicts."""
    fn = SETUPS[setup_name]
    params = params or {}
    out = []
    rnd = random.Random(rng_seed)
    for sym in SYMBOLS:
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if classes is not None and ac not in classes: continue
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs, rng, vd = precompute(B)
        vbar_arr = [rolling_mean([b.v for b in B], i, 20) if i >= 19 else None for i in range(n)] \
            if setup_name == "S4_absorption" else None
        # First pass: collect signal bars for this side (so RANDOM null can match count).
        sig_bars = []
        for i in range(60, n-1):
            d = fn(B, atrs, rng, vd, i, vbar_arr=vbar_arr, **params) if setup_name == "S4_absorption" \
                else fn(B, atrs, rng, vd, i, **params)
            if d is None or d != side_sign: continue
            sig_bars.append(i)
        if not sig_bars: continue
        if random_entries:
            # draw same number of random eligible bars (atr>0), de-overlapped below.
            elig = [i for i in range(60, n-1) if atrs[i] > 0]
            rnd.shuffle(elig)
            entry_bars = sorted(elig[:len(sig_bars)])
        else:
            entry_bars = sig_bars
        # Second pass: de-overlap -- skip an entry if prior trade on this symbol still open.
        next_free = -1
        for i in entry_bars:
            if i <= next_free: continue
            d_exec = (-side_sign if invert else side_sign)
            res = micro_trade_r(B, i, d_exec, cost, mode)
            if res is None: continue
            r, xi = res
            next_free = xi
            out.append({"sym": sym, "ts": T[i], "year": T[i].year, "dir": d_exec, "r": r})
    return out

# ============================ stats helpers (verbatim wave7) =================
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(recs, key="r"):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d[key])
    return {int(y): stats(by[y]) for y in sorted(by)}

def daily_sum(recs, key="r"):
    by = defaultdict(float)
    for d in recs: by[d["ts"].date()] += d[key]
    return dict(by)

def pearson(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx = sum(xs)/n; my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0: return 0.0
    return sxy/math.sqrt(sxx*syy)

# ============================ equity / FTMO (verbatim wave7) =================
def equity_path_from_daily(daily_map, risk_pct):
    days = sorted(daily_map)
    eq = 1.0; peak = 1.0; maxdd = 0.0; worst_day = 0.0; rets = []
    for dt in days:
        dr = daily_map[dt]
        step_ret = (risk_pct/100.0) * dr
        before = eq
        eq *= (1.0 + step_ret)
        if eq <= 1e-9: eq = 1e-9
        day_pct = (eq - before)
        worst_day = min(worst_day, day_pct)
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak-eq)/peak)
        rets.append(step_ret)
    return eq, maxdd, -worst_day*100.0, len(days), rets

def ftmo_sizing(daily_map, span_months, risk_grid=None):
    if risk_grid is None:
        risk_grid = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0]
    grid = {}; best_ok = None
    for risk in risk_grid:
        eq, maxdd, worst_day_pct, ndays, _ = equity_path_from_daily(daily_map, risk)
        total_ret = (eq - 1.0)*100.0
        monthly = ((eq)**(1.0/span_months) - 1.0)*100.0 if span_months > 0 and eq > 0 else None
        ok = (maxdd*100.0 < 10.0) and (worst_day_pct < 5.0)
        grid[str(risk)] = {
            "risk_pct_per_day": risk,
            "max_drawdown_pct": round(maxdd*100.0, 2),
            "worst_day_pct": round(worst_day_pct, 2),
            "total_return_pct": round(total_ret, 1),
            "approx_monthly_pct": round(monthly, 3) if monthly is not None else None,
            "within_ftmo": ok,
        }
        if ok: best_ok = grid[str(risk)]
    return {"grid": grid, "max_risk_within_ftmo": best_ok}

def equity_metrics_simple(daily_map, risk_pct):
    eq, maxdd, worst_day_pct, ndays, rets = equity_path_from_daily(daily_map, risk_pct)
    if not rets: return {"sharpe": 0.0, "max_dd": 0.0, "final_eq": 1.0, "worst_day_pct": 0.0, "n_days": 0}
    steps = [math.log(1+r) if (1+r) > 1e-9 else -20 for r in rets]
    m = sum(steps)/len(steps)
    sd = math.sqrt(sum((s-m)**2 for s in steps)/len(steps)) if len(steps) > 1 else 0.0
    sharpe = (m/sd*math.sqrt(len(steps))) if sd > 0 else 0.0
    return {"sharpe": round(sharpe, 3), "max_dd": round(maxdd, 4),
            "final_eq": round(eq, 4), "worst_day_pct": round(worst_day_pct, 2), "n_days": ndays}

def span_months_of(dm):
    days = sorted(dm)
    if len(days) < 2: return 1.0
    return ((datetime.combine(days[-1], datetime.min.time()) -
             datetime.combine(days[0], datetime.min.time())).days or 1)/30.44

# ============================ carrier (gold sleeve) verbatim wave7 ==========
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

def sma_atr_ratio(atrs, i, win=100):
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, atr_win=100):
    out = []
    for sym in symbols:
        T, B = load_carrier(sym)   # carrier = wave7-identical universe (D1+D2)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            tr = htf_trend(B, i, trend_lb)
            b = B[i]
            d = None; stop_dist = None
            if tr == 1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_top = B[k].l; gap_bot = B[k-2].h
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                        d = -1 if invert else +1
                        break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a: continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        d = +1 if invert else -1
                        break
            if d is None: continue
            target_dist = target_R*stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
            ratio = sma_atr_ratio(atrs, i, atr_win)
            out.append({"sym": sym, "year": T[i].year, "ts": T[i], "dir": d, "r": r,
                        "atr_ratio": ratio, "cost": cost})
    return out

def fvg_walk_forward(base, thresholds, anchor_year=2016, end_year=2026, min_past_n=60):
    by_year = defaultdict(list)
    for d in base: by_year[d["year"]].append(d)
    chained = []
    for Y in range(anchor_year, end_year+1):
        past = [d for d in base if d["year"] < Y]
        best_thr = None; best_R = -1e9
        for thr in thresholds:
            sub = [d["r"] for d in past if d["atr_ratio"] is not None and d["atr_ratio"] >= thr]
            if len(sub) >= min_past_n:
                m = sum(sub)/len(sub)
                if m > best_R: best_R = m; best_thr = thr
        if best_thr is None: best_thr = 1.2
        taken = [d for d in by_year.get(Y, [])
                 if d["atr_ratio"] is not None and d["atr_ratio"] >= best_thr]
        for d in taken:
            chained.append({"ts": d["ts"], "year": Y, "sym": d["sym"], "r": d["r"]})
    return chained

# ============================ MAIN =========================================
def main():
    random.seed(20260614)
    REF = 0.25
    PRIOR_CLASSES = ["index", "metals", "jpy_fx", "crypto"]  # prior survivors' classes
    OUT = {
        "thrust": "combined_portfolio_uplift",
        "question": "STEP A: do S4 absorption-reversal / S5 vdelta-divergence survive a CLEAN "
                    "re-implementation (geometry_lib.simulate) on strict OOS with matched RANDOM "
                    "+ INVERT nulls? STEP B (only if A passes & uncorrelated to gold): does adding "
                    "microstructure to the gold sleeve raise monthly%/Sharpe at <=DD AND beat >95% "
                    "of shuffled-overlap nulls (the bar Wave-7 diversifiers all failed)?",
        "discipline": {
            "fills": "geometry_lib.simulate / simulate_detail (tested two-sided); carrier verbatim wave7",
            "no_lookahead": "S4/S5 features f(bars[<=i]); signed-vol=V*(C-O)/range@i; de-overlap via simulate_detail exit index; winsorized",
            "oos": "cells SELECTED on TRAIN<=2024 positivity; FORWARD 2025-26 readout; per-year 2015-2026",
            "nulls": "matched RANDOM (same count/symbols/side/exit) + INVERT, judged on FORWARD; combined test = wave7 shuffled-overlap null verbatim",
            "costs": "real per-class medians ULTIMATE_REAL_COST_MAP.json",
        },
    }

    print("="*80); print("STEP A: CLEAN RE-VALIDATION OF MICROSTRUCTURE (S4/S5)"); print("="*80)

    # Scan ALL classes x both setups x both sides x both exits. SELECT cells positive
    # on TRAIN<=2024; then read FORWARD with matched nulls. Restrict the *book* to the
    # prior-survivor classes (index/metals/jpy/crypto) but report the full scan honestly.
    CLASSES = sorted(set(ASSET_CLASS_BY_SYMBOL.values()))
    MIN_RAW, MIN_TRAIN, MIN_FWD = 25, 20, 8
    cells = []   # each: dict with full stream + train/fwd + selected params
    for setup in ("S4_absorption", "S5_vdelta"):
        for side in (+1, -1):
            for mode in ("fixed", "trail"):
                for ac in CLASSES:
                    # TRAIN-only parameter sweep: pick the params with best TRAIN mean_R
                    # (>= MIN_TRAIN train trades). Forward never touched in selection.
                    best = None
                    for p in PARAM_GRID[setup]:
                        recs = build_micro(setup, side, mode, classes={ac}, params=p)
                        tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
                        if len(tr) < MIN_TRAIN: continue
                        m = sum(tr)/len(tr)
                        if best is None or m > best[0]:
                            best = (m, p, recs)
                    if best is None: continue
                    recs = best[2]; p = best[1]
                    if len(recs) < MIN_RAW: continue
                    train = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
                    fwd = [d["r"] for d in recs if d["year"] > TRAIN_MAX]
                    if len(train) < MIN_TRAIN or len(fwd) < MIN_FWD: continue
                    cells.append({
                        "setup": setup, "side": "long" if side == +1 else "short",
                        "side_sign": side, "mode": mode, "class": ac, "params": p,
                        "recs": recs,
                        "train": stats(train), "fwd": stats(fwd),
                        "per_year": {str(y): v for y, v in per_year(recs).items()},
                    })

    # SELECTION on train only.
    selected = [c for c in cells if c["train"]["mean_R"] > 0 and c["train"]["n"] >= MIN_TRAIN]
    selected.sort(key=lambda c: -c["train"]["mean_R"])
    print(f"  cells scanned: {len(cells)}   selected (train mean_R>0, n>={MIN_TRAIN}): {len(selected)}")

    # Matched nulls on the SELECTED cells (judged on FORWARD).
    book_records = []     # surviving micro records (for Step B), restricted to prior classes
    survivor_rows = []
    for c in selected:
        side = c["side_sign"]; setup = c["setup"]; mode = c["mode"]; ac = c["class"]; pp = c["params"]
        fwd_real = c["fwd"]["mean_R"]
        # RANDOM null (forward) -- average of several seeds for stability, SAME params
        rnd_fwd = []
        for sd in range(5):
            rrecs = build_micro(setup, side, mode, classes={ac}, random_entries=True,
                                rng_seed=1000+sd, params=pp)
            rf = [d["r"] for d in rrecs if d["year"] > TRAIN_MAX]
            if rf: rnd_fwd.append(sum(rf)/len(rf))
        rnd_fwd_mean = round(sum(rnd_fwd)/len(rnd_fwd), 4) if rnd_fwd else None
        # INVERT null (forward), SAME params
        irecs = build_micro(setup, side, mode, classes={ac}, invert=True, params=pp)
        inv_fwd = [d["r"] for d in irecs if d["year"] > TRAIN_MAX]
        inv_fwd_mean = round(sum(inv_fwd)/len(inv_fwd), 4) if inv_fwd else None
        fwd_years = [y for y in per_year(c["recs"]) if y > TRAIN_MAX]
        fwd_pos = sum(1 for y in fwd_years if per_year(c["recs"])[y]["mean_R"] > 0)
        beats_random = (rnd_fwd_mean is None) or (fwd_real > rnd_fwd_mean)
        beats_invert = (inv_fwd_mean is None) or (fwd_real > inv_fwd_mean)
        survives = (fwd_real > 0) and beats_random and beats_invert and (fwd_pos >= max(1, len(fwd_years)-0))
        row = {
            "setup": setup, "side": c["side"], "mode": mode, "class": ac, "params": pp,
            "train_mean_R": c["train"]["mean_R"], "train_n": c["train"]["n"],
            "fwd_mean_R": fwd_real, "fwd_n": c["fwd"]["n"],
            "fwd_pos_years": f"{fwd_pos}/{len(fwd_years)}",
            "random_null_fwd_mean_R": rnd_fwd_mean, "beats_random_fwd": bool(beats_random),
            "invert_null_fwd_mean_R": inv_fwd_mean, "beats_invert_fwd": bool(beats_invert),
            "survives": bool(survives),
            "in_prior_class": ac in PRIOR_CLASSES,
            "per_year": c["per_year"],
        }
        survivor_rows.append(row)
        print(f"  {setup:14} {c['side']:5} {mode:5} {ac:8}: train {c['train']['mean_R']:+.4f}(n{c['train']['n']:>4}) "
              f"fwd {fwd_real:+.4f}(n{c['fwd']['n']:>4}) rnd {str(rnd_fwd_mean):>8} inv {str(inv_fwd_mean):>8} "
              f"fwdpos {fwd_pos}/{len(fwd_years)} -> {'SURVIVES' if survives else 'wash'}")
        if survives and ac in PRIOR_CLASSES:
            book_records += c["recs"]

    survivors = [r for r in survivor_rows if r["survives"]]
    survivors_prior = [r for r in survivors if r["in_prior_class"]]
    OUT["A_clean_revalidation"] = {
        "cells_scanned": len(cells),
        "cells_selected_on_train": len(selected),
        "all_selected_rows": survivor_rows,
        "n_survivors_any_class": len(survivors),
        "n_survivors_prior_classes": len(survivors_prior),
        "survivor_cells": [{k: r[k] for k in ("setup","side","mode","class","train_mean_R",
                            "fwd_mean_R","fwd_n","fwd_pos_years","random_null_fwd_mean_R",
                            "invert_null_fwd_mean_R")} for r in survivors],
    }
    micro_survives = len(survivors_prior) > 0 and len(book_records) >= 30

    print("\n" + "="*80)
    print(f"STEP A VERDICT: microstructure survives clean re-validation = {micro_survives}")
    print(f"  survivors (any class): {len(survivors)} ; in prior classes: {len(survivors_prior)} ; "
          f"book trades for combine: {len(book_records)}")
    print("="*80)

    # ---------------- Carrier (gold sleeve) ----------------
    THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    p0 = fvg_walk_forward(fvg_trades(PRECIOUS, target_R=2.0), THRESHOLDS)
    gold_only = daily_sum(p0, key="r")
    c_full = stats([d["r"] for d in p0]); c_fwd = stats([d["r"] for d in p0 if d["year"] > TRAIN_MAX])
    # Reproduction proof against the audited wave7 P0 carrier.
    repro = None
    try:
        with open(EDGE + "/WAVE7_AGGREGATE_POCKETS_RESULT.json") as f:
            w7 = json.load(f)
        w7p0 = w7["pockets"]["P0_GOLD_FVG"]
        repro = {"wave7_full_n": w7p0["full"]["n"], "wave7_full_mean_R": w7p0["full"]["mean_R"],
                 "wave7_fwd_mean_R": w7p0["fwd"]["mean_R"],
                 "this_full_n": c_full["n"], "this_full_mean_R": c_full["mean_R"],
                 "this_fwd_mean_R": c_fwd["mean_R"],
                 "matches_wave7": (c_full["n"] == w7p0["full"]["n"] and
                                   abs(c_full["mean_R"] - w7p0["full"]["mean_R"]) < 1e-6)}
    except Exception as e:
        repro = {"error": str(e)}
    OUT["carrier_gold_sleeve"] = {"full": c_full, "fwd": c_fwd, "active_days": len(gold_only),
                                  "wave7_reproduction": repro}
    print(f"\n  CARRIER gold sleeve: full {c_full['mean_R']:+.4f} (n={c_full['n']}) "
          f"fwd {c_fwd['mean_R']:+.4f} days {len(gold_only)}  "
          f"reproduces_wave7={repro.get('matches_wave7')}")

    if not micro_survives:
        OUT["B_combined_test"] = {
            "status": "MOOT",
            "reason": "microstructure (S4/S5) did NOT survive clean re-implementation on strict OOS "
                      "with matched RANDOM+INVERT nulls; there is no surviving uncorrelated edge to add "
                      "to the gold sleeve, so the Wave-7 combined uplift test is moot.",
        }
        OUT["FINAL_VERDICT"] = {
            "microstructure_survives_clean_revalidation": False,
            "combined_uplift_test_run": False,
            "adding_microstructure_helps": False,
            "summary": "Combined test moot: no surviving microstructure edge.",
        }
        with open(EDGE + "/WAVE8_COMBINED_PORTFOLIO_UPLIFT_RESULT.json", "w") as f:
            json.dump(OUT, f, indent=1, default=str)
        print("\nMicrostructure washed -> combined test MOOT. WROTE result.")
        _print_final(OUT); return OUT

    # ================= STEP B: COMBINED PORTFOLIO (wave7 machinery verbatim) =====
    print("\n" + "="*80); print("STEP B: COMBINED PORTFOLIO UPLIFT (Wave-7 test)"); print("="*80)
    micro_daily = daily_sum(book_records, key="r")

    # ---- correlation micro vs gold (decisive 'is it just gold?' number) ----
    all_days = sorted(set(gold_only) | set(micro_daily))
    common = sorted(set(gold_only) & set(micro_daily))
    corr_union = pearson([gold_only.get(dt, 0.0) for dt in all_days],
                         [micro_daily.get(dt, 0.0) for dt in all_days])
    corr_inter = pearson([gold_only[dt] for dt in common],
                         [micro_daily[dt] for dt in common]) if len(common) >= 3 else None
    uncorrelated = (corr_inter is None) or (abs(corr_inter) < 0.3)
    OUT["B_correlation_micro_vs_gold"] = {
        "union_0fill_corr": round(corr_union, 3),
        "intersection_corr": round(corr_inter, 3) if corr_inter is not None else None,
        "both_active_days": len(common),
        "uncorrelated_to_gold": bool(uncorrelated),
    }
    print(f"  micro vs gold daily-R corr: union0fill {corr_union:+.3f}  intersection "
          f"{('%+.3f'%corr_inter) if corr_inter is not None else 'na'} (both-active {len(common)}) "
          f"-> uncorrelated={uncorrelated}")

    # ---- gold alone vs micro alone vs equal-risk book (fixed REF risk + FTMO) ----
    book_equal = {dt: 0.5*gold_only.get(dt, 0.0) + 0.5*micro_daily.get(dt, 0.0) for dt in all_days}
    active_book = {dt: v for dt, v in book_equal.items() if abs(v) > 1e-12}
    smG = span_months_of(gold_only); smB = span_months_of(active_book); smM = span_months_of(micro_daily)
    mG = equity_metrics_simple(gold_only, REF)
    mM = equity_metrics_simple(micro_daily, REF)
    mB = equity_metrics_simple(book_equal, REF)
    okG = ftmo_sizing(gold_only, smG)["max_risk_within_ftmo"]
    okM = ftmo_sizing(micro_daily, smM)["max_risk_within_ftmo"]
    okB = ftmo_sizing(book_equal, smB)["max_risk_within_ftmo"]
    print(f"  @ref {REF}%/day: GOLD Sharpe {mG['sharpe']:+.3f} DD {mG['max_dd']*100:.2f}% | "
          f"MICRO Sharpe {mM['sharpe']:+.3f} DD {mM['max_dd']*100:.2f}% | "
          f"BOOK Sharpe {mB['sharpe']:+.3f} DD {mB['max_dd']*100:.2f}%")
    OUT["B_fixed_risk_and_ftmo"] = {
        "ref_risk_pct_per_day": REF,
        "gold_alone": {"fixedrisk": mG, "ftmo_max": okG},
        "micro_alone": {"fixedrisk": mM, "ftmo_max": okM},
        "equal_risk_book": {"fixedrisk": mB, "ftmo_max": okB},
    }

    # ---- RISK-BUDGET SWEEP (diversifier share w_div) ----
    sweep = {}; best_combo = None; best_sharpe = None
    for w_div in [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]:
        dm = {}
        for dt in all_days:
            dm[dt] = (1.0 - w_div)*gold_only.get(dt, 0.0) + w_div*micro_daily.get(dt, 0.0)
        active = {dt: v for dt, v in dm.items() if abs(v) > 1e-12}
        sm = span_months_of(active)
        mk = ftmo_sizing(dm, sm)["max_risk_within_ftmo"]
        em = equity_metrics_simple(dm, REF)
        monthly = mk["approx_monthly_pct"] if mk else None
        dd = mk["max_drawdown_pct"] if mk else None
        risk = mk["risk_pct_per_day"] if mk else None
        sweep[f"w_div={w_div}"] = {
            "w_micro": w_div, "w_gold": round(1.0-w_div, 3),
            "max_ftmo_risk_pct_day": risk, "monthly_pct_at_max": monthly, "maxDD_pct_at_max": dd,
            "sharpe_at_ref": em["sharpe"], "maxdd_at_ref_pct": round(em["max_dd"]*100, 2),
        }
        print(f"  w_div={w_div:>4} (gold {1-w_div:.2f}): max-FTMO {str(risk):>5}%/d ~mo {str(monthly):>6}% "
              f"maxDD {str(dd):>5}% | @ref Sharpe {em['sharpe']:+.3f} DD {em['max_dd']*100:.2f}%")
        if monthly is not None and (best_combo is None or monthly > best_combo[0]):
            best_combo = (monthly, w_div, dd, risk)
        if best_sharpe is None or em["sharpe"] > best_sharpe[0]:
            best_sharpe = (em["sharpe"], w_div, round(em["max_dd"]*100, 2))
    OUT["B_risk_budget_sweep"] = sweep

    # ---- SHUFFLED-OVERLAP DIVERSIFICATION NULL (x300, equal-risk book) ----
    real = equity_metrics_simple(book_equal, REF)
    null_sh = []; null_dd = []
    micro_days = sorted(micro_daily); micro_vals = list(micro_daily.values())
    for s in range(300):
        rng = random.Random(7000 + s)
        dvals = micro_vals[:]; rng.shuffle(dvals)
        shuf_micro = {dt: v for dt, v in zip(micro_days, dvals)}
        comb = {dt: 0.5*gold_only.get(dt, 0.0) + 0.5*shuf_micro.get(dt, 0.0) for dt in all_days}
        em = equity_metrics_simple(comb, REF)
        null_sh.append(em["sharpe"]); null_dd.append(em["max_dd"])
    nm_sh = sum(null_sh)/len(null_sh); nm_dd = sum(null_dd)/len(null_dd)
    beats_sh = sum(1 for x in null_sh if x < real["sharpe"])/len(null_sh)
    lower_dd = sum(1 for x in null_dd if x > real["max_dd"])/len(null_dd)
    OUT["B_diversification_null"] = {
        "real_sharpe": real["sharpe"], "null_mean_sharpe": round(nm_sh, 3),
        "real_beats_sharpe_frac": round(beats_sh, 3),
        "real_maxdd_pct": round(real["max_dd"]*100, 2), "null_mean_maxdd_pct": round(nm_dd*100, 2),
        "real_lower_dd_frac": round(lower_dd, 3),
    }
    print(f"\n  shuffled-overlap null: real Sharpe {real['sharpe']:+.3f} beats {beats_sh*100:.0f}% of nulls; "
          f"real DD {real['max_dd']*100:.2f}% lower than {lower_dd*100:.0f}% of nulls")

    # ---- per-year sum-R: gold vs book ----
    def py_daily(dm):
        by = defaultdict(float); cnt = defaultdict(int)
        for dt, v in dm.items(): by[dt.year] += v; cnt[dt.year] += 1
        return {int(y): {"sum_R": round(by[y], 2), "active_days": cnt[y]} for y in sorted(by)}
    pyG = py_daily(gold_only); pyM = py_daily(micro_daily); pyB = py_daily(book_equal)
    years = sorted(set(pyG) | set(pyM) | set(pyB))
    print(f"\n  {'year':>4} {'GOLD_R':>9} {'MICRO_R':>9} {'BOOK_R':>9}")
    for y in years:
        g = pyG.get(y, {"sum_R": 0.0}); m = pyM.get(y, {"sum_R": 0.0}); b = pyB.get(y, {"sum_R": 0.0})
        print(f"  {y:>4} {g['sum_R']:>+9.2f} {m['sum_R']:>+9.2f} {b['sum_R']:>+9.2f}")
    OUT["B_per_year_sumR"] = {
        "gold_alone": {str(y): pyG.get(y) for y in years},
        "micro_alone": {str(y): pyM.get(y) for y in years},
        "equal_risk_book": {str(y): pyB.get(y) for y in years},
    }

    # ---- VERDICT (same bar as wave7) ----
    g_monthly = okG["approx_monthly_pct"] if okG else None
    g_dd = okG["max_drawdown_pct"] if okG else None
    b_monthly = best_combo[0] if best_combo else None
    b_dd = best_combo[2] if best_combo else None
    b_wdiv = best_combo[1] if best_combo else None
    monthly_gain = (b_monthly - g_monthly) if (g_monthly is not None and b_monthly is not None) else None
    materially_better = bool(
        b_monthly is not None and g_monthly is not None and b_wdiv and b_wdiv > 0 and
        b_monthly > g_monthly + 0.02 and b_dd is not None and g_dd is not None and b_dd <= g_dd + 0.5)
    sharpe_better = bool(best_sharpe[0] > sweep["w_div=0.0"]["sharpe_at_ref"] and best_sharpe[1] > 0)
    null_survives = (OUT["B_diversification_null"]["real_beats_sharpe_frac"] >= 0.95 and
                     OUT["B_diversification_null"]["real_lower_dd_frac"] >= 0.95)
    OUT["B_combined_test"] = {"status": "RAN"}
    OUT["B_verdict"] = {
        "gold_alone_monthly_pct": g_monthly, "gold_alone_maxDD_pct": g_dd,
        "best_combined_w_micro": b_wdiv, "best_combined_monthly_pct": b_monthly,
        "best_combined_maxDD_pct": b_dd, "monthly_pct_gain_vs_gold": round(monthly_gain, 3) if monthly_gain is not None else None,
        "best_fixed_risk_sharpe_w_div": best_sharpe[1], "best_fixed_risk_sharpe": best_sharpe[0],
        "gold_alone_fixed_risk_sharpe": sweep["w_div=0.0"]["sharpe_at_ref"],
        "micro_vs_gold_intersection_corr": OUT["B_correlation_micro_vs_gold"]["intersection_corr"],
        "diversification_null_survives_95": bool(null_survives),
        "ADDING_MICRO_RAISES_FTMO_MONTHLY_AT_SAME_OR_LOWER_DD": materially_better,
        "ADDING_MICRO_RAISES_FIXED_RISK_SHARPE": sharpe_better,
    }
    helps = bool((materially_better or sharpe_better) and null_survives)
    OUT["FINAL_VERDICT"] = {
        "microstructure_survives_clean_revalidation": True,
        "combined_uplift_test_run": True,
        "microstructure_uncorrelated_to_gold": OUT["B_correlation_micro_vs_gold"]["uncorrelated_to_gold"],
        "adding_microstructure_helps": helps,
        "summary": ("Adding microstructure raises monthly%/Sharpe at <=DD AND beats >95% of nulls."
                    if helps else
                    "Adding microstructure does NOT clear the Wave-7 bar (uplift and/or >95% null not met)."),
    }
    with open(EDGE + "/WAVE8_COMBINED_PORTFOLIO_UPLIFT_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE8_COMBINED_PORTFOLIO_UPLIFT_RESULT.json")
    _print_final(OUT)
    return OUT

def _print_final(OUT):
    print("\n" + "="*80); print("FINAL VERDICT"); print("="*80)
    for k, v in OUT["FINAL_VERDICT"].items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
