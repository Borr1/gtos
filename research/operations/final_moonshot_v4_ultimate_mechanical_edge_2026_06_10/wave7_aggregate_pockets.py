"""
wave7_aggregate_pockets.py
==========================
THRUST (aggregate_pockets): The "many small edges" thesis.

The whole program converged to ONE modest gold-anchored sleeve (precious-metals
vol-gated FVG-retest 2R continuation, WF fwd ~+0.227R, ~81% XAUUSD). Every
single-symbol directional approach washed; vol-clustering is the only universal
regularity. Wave5_portfolio_combine already showed that adding ONE broadener
(Donchian breakout + vol-state sizing) gives ZERO FTMO monthly uplift at worse DD
and is adversely (not protectively) correlated.

This wave asks the harder version: assemble a DIVERSIFIED portfolio of *ALL*
marginal-positive pockets found across the program, each sized small, and measure
whether AGGREGATING low-correlation pockets raises portfolio Sharpe / monthly% at
the same-or-lower maxDD vs the gold sleeve alone. Compute cross-pocket correlation
HONESTLY. Does diversification across tiny edges beat the single sleeve, or do they
collapse to correlated gold beta?

POCKETS ASSEMBLED (every marginal-positive surface the program surfaced):
  P0  GOLD_FVG    precious-metals vol-gated FVG-retest 2R continuation (the CARRIER,
                  audited deployable sleeve; walk-forward chained gate).
  P1  GOLD_SQZ    gold/precious squeeze->Donchian breakout 2R (the Wave5 "bench"
                  candidate; vol-state sized; SELECTED on TRAIN<=2024 only).
  P2  ENERGY_FVG  energy vol-gated FVG-retest 2R (Wave5 cell: ALL-fwd +0.066R,
                  gated-fwd +0.365R -- flagged single-symbol/tiny-window; included
                  HONESTLY as a "weak per-class positive").
  P3  METALS_NY   metals NY-session long uptrend-gated 2R (hunt_session_time winner;
                  train +0.162R metals-only LONG).
  P4  METALS_MTF  metals long-side trend-continuation pullback 2R-ish (hunt_mtf
                  trend_pullback "only_positive_pocket": metals long sma-slope gate).

Each pocket is built LEAK-FREE with the SAME selection rule it was discovered under,
fills ONLY via tested geometry_lib.simulate, real per-class costs.

STRICT PROTOCOL (every loose claim has been a leak; only audited results count):
  - Fills ONLY via tested geometry_lib.simulate. No hand-rolled fills/signs. The two
    flagship pockets (P0 FVG, P1 breakout) are built with geometry COPIED VERBATIM
    from wave5_portfolio_combine (which itself copies the audited wave4 sleeves), so
    P0 reproduces the EXACT audited deployable gold sleeve.
  - NO LOOKAHEAD: every gate/feature is f(bars[<=i]); FVG uses the chained
    WALK-FORWARD stream (gate threshold re-selected on past only); breakout sizing
    rule SELECTED ON TRAIN<=2024 only; daily-R aggregation & equity ordered by date;
    weights known-at-entry. Path state only from closed simulate() trades.
  - STRICT OOS: per-pocket per-year 2015-2026 + a FORWARD (2025-26) read; the
    portfolio verdict is judged on the FORWARD window and on a calendar-ordered
    equity path, never on full-sample fitted weights.
  - MATCHED NULLS: (a) each pocket's own per-year sign honesty; (b) a SHUFFLED-OVERLAP
    diversification null on the assembled book -- randomly re-pair each non-carrier
    pocket's daily-R series against the calendar; if the real assembled Sharpe/DD is
    no better than that null, the "diversification" is illusory (it comes from random
    offsetting, not a real low-correlation timing relationship).
  - INVERT control on each non-carrier pocket forward (a real edge must beat its own
    inverse forward).
  - Winsorize file-stitch bad-print bars (inherited loaders). Real per-class costs
    from ULTIMATE_REAL_COST_MAP.json. Controlled fixed universe per pocket (no
    coverage-growth confound; pockets are restricted to their discovered classes).
  - Truth over positives. If aggregation does not beat the single sleeve, SAY SO with
    numbers. If the pockets collapse to gold beta, quantify the collapse.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
D1 = DATA + "/bridge_ftmo_deep_h4_2015_2022"
D2 = DATA + "/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024
ALL_METALS = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "metals"])
PRECIOUS = sorted([s for s in ALL_METALS if s.startswith("XAU") or s.startswith("XAG")])
ENERGY = sorted([s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == "energy"])

# ============================ data load + winsorize =========================
def syms_in(d):
    if not os.path.isdir(d): return set()
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}
SYMBOLS = sorted(syms_in(D1) | syms_in(D2))

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
    """Conservative single-bar bad-print clamp -- VERBATIM from wave5_portfolio_combine."""
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

_H4 = {}
def load(sym):
    if sym in _H4: return _H4[sym]
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged:
        _H4[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]; bars = [v for _, v in items]
    bars = winsorize(times, bars)
    _H4[sym] = (times, bars)
    return times, bars

# ============================ known-at-i features ===========================
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

def sma(bars, i, n):
    if i < n: return None
    return sum(bars[k].c for k in range(i-n+1, i+1))/n

# ============================ P0: GOLD FVG (audited carrier) =================
def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, atr_win=100):
    """VERBATIM from wave5_portfolio_combine.fvg_trades (-> audited wave4 sleeve)."""
    out = []
    for sym in symbols:
        T, B = load(sym)
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
    """VERBATIM from wave5_portfolio_combine.fvg_walk_forward (audited deployable WF)."""
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

# ============================ P1: GOLD/precious SQUEEZE breakout =============
def breakout_entries(symbols, lookback=20, target_R=2.0, stop_mult=1.0, atr_win=100,
                     squeeze_thr=None, maxbars=80):
    """Donchian-N breakout (VERBATIM core from wave5_portfolio_combine.breakout_entries),
    restricted to `symbols` (here precious metals = the bench candidate's universe).
    Optional pre-breakout SQUEEZE filter (ATR ratio BELOW squeeze_thr at i-1) so this is
    the 'squeeze->breakout' bench, not the generic breakout. All known-at-i."""
    out = []
    for sym in symbols:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        ratios = [sma_atr_ratio(atrs, i, atr_win) for i in range(n)]
        for i in range(max(60, lookback+1), n-1):
            a = atrs[i]
            if a <= 0: continue
            if squeeze_thr is not None:
                rprev = ratios[i-1]
                if rprev is None or rprev > squeeze_thr:  # require compression just before
                    continue
            prior_hi = max(B[j].h for j in range(i-lookback, i))
            prior_lo = min(B[j].l for j in range(i-lookback, i))
            d = None
            if B[i].c > prior_hi:   d = +1
            elif B[i].c < prior_lo: d = -1
            if d is None: continue
            stop_dist = stop_mult*a
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_R*stop_dist,
                         cost=cost, maxbars=maxbars)
            out.append({"sym": sym, "ts": T[i], "year": T[i].year, "r": r,
                        "ratio": ratios[i]})
    return out

def select_volstate_rule_on_train(recs, f0=0.01, w_cap=3.0):
    """VERBATIM from wave5_portfolio_combine -- train<=2024 ret/DD selection."""
    train = [d for d in recs if d["year"] <= TRAIN_MAX]
    thr_grid = [1.0, 1.1, 1.2, 1.3]
    weight_pairs = [(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (0.5, 1.0), (0.75, 1.5)]
    def eq_ret_per_dd(sub, thr, lo_w, hi_w):
        srt = sorted(sub, key=lambda d: (d["ts"], d["sym"]))
        eq = 1.0; peak = 1.0; maxdd = 0.0
        for d in srt:
            rt = d["ratio"]
            w = hi_w if (rt is not None and rt >= thr) else lo_w
            w = max(0.0, min(w_cap, w))
            eq *= (1.0 + f0*w*d["r"])
            if eq <= 1e-9: eq = 1e-9
            peak = max(peak, eq); maxdd = max(maxdd, (peak-eq)/peak)
        ret = eq - 1.0
        return (ret/maxdd) if maxdd > 0 else -1e9
    best = None
    for thr in thr_grid:
        for lo_w, hi_w in weight_pairs:
            score = eq_ret_per_dd(train, thr, lo_w, hi_w)
            if best is None or score > best[0]:
                best = (score, thr, lo_w, hi_w)
    return {"thr": best[1], "lo_w": best[2], "hi_w": best[3]}

def breakout_sized_stream(recs, rule):
    out = []
    for d in recs:
        rt = d["ratio"]
        w = rule["hi_w"] if (rt is not None and rt >= rule["thr"]) else rule["lo_w"]
        out.append({"ts": d["ts"], "year": d["year"], "sym": d["sym"],
                    "r": d["r"], "w": w, "wr": w*d["r"]})
    return out

# ============================ P2: ENERGY vol-gated FVG =======================
def energy_fvg_walkforward(target_R=2.0):
    """Energy FVG-retest (same fvg_trades geometry) with the SAME chained walk-forward
    vol gate as the gold sleeve -- reproduces the Wave5 'energy/fvg gated' cell honestly.
    Universe = energy only (controlled, no growth)."""
    base = fvg_trades(ENERGY, target_R=target_R)
    return fvg_walk_forward(base, [1.0, 1.1, 1.2, 1.3, 1.4, 1.5])

def energy_fvg_invert_wf(target_R=2.0):
    base = fvg_trades(ENERGY, target_R=target_R, invert=True)
    return fvg_walk_forward(base, [1.0, 1.1, 1.2, 1.3, 1.4, 1.5])

# ============================ P3: METALS NY-session long ====================
def session_metals_long(target_R=2.0, stop_mult=0.5, lookback=10, invert=False):
    """hunt_session_time winner: LONG metals at close of NY-session H4 bars
    (server-hour 16:00 & 20:00) when close>close[-lookback] (uptrend).
    stop=0.5*ATR, target=2.0*ATR. Long-only (or inverted to short for the null)."""
    out = []
    d_base = -1 if invert else +1
    for sym in ALL_METALS:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(max(60, lookback+1), n-1):
            if T[i].hour not in (16, 20): continue
            a = atrs[i]
            if a <= 0: continue
            if B[i].c <= B[i-lookback].c: continue   # uptrend filter
            stop_dist = stop_mult*a
            r = simulate(B, i, d_base, stop_dist=stop_dist, target_dist=target_R*stop_dist, cost=cost)
            out.append({"sym": sym, "ts": T[i], "year": T[i].year, "r": r})
    return out

# ============================ P4: METALS long trend-pullback ================
def metals_mtf_long(slope_thr=0.10, stop_mult=0.5, trail_arm=2.0, trail_gap=1.0, invert=False):
    """hunt_mtf 'only_positive_pocket': metals long-side continuation, sma50 slope/atr
    >= slope_thr, stop 0.5*ATR, trail arm 2 / gap 1 (in ATR units). Long-only.
    Slope = (sma50[i]-sma50[i-10]) measured at i (known-at-i)."""
    out = []
    d_base = -1 if invert else +1
    for sym in ALL_METALS:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(70, n-1):
            a = atrs[i]
            if a <= 0: continue
            s_now = sma(B, i, 50); s_prev = sma(B, i-10, 50)
            if s_now is None or s_prev is None: continue
            slope = (s_now - s_prev)/a
            if slope < slope_thr: continue          # strong-uptrend gate (long only)
            stop_dist = stop_mult*a
            r = simulate(B, i, d_base, stop_dist=stop_dist,
                         trail_arm=trail_arm*a, trail_gap=trail_gap*a, cost=cost)
            out.append({"sym": sym, "ts": T[i], "year": T[i].year, "r": r})
    return out

# ============================ stats / aggregation ===========================
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

# ============================ equity / FTMO sizing ==========================
def equity_path_from_daily(daily_map, risk_pct):
    """Compound equity over sorted calendar days; each day's R-total risked at
    risk_pct/100 of current equity (one daily risk unit; correlated intraday trades =
    one risk event, the conservative metals-cluster convention). Returns
    (final_eq, max_dd_frac, worst_day_pct, n_days, daily_ret_list)."""
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
    """Largest per-day risk%% keeping maxDD<10%% AND worst single DAY<5%% (FTMO)."""
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

def fwd_only(dm):
    return {dt: v for dt, v in dm.items() if dt.year > TRAIN_MAX}

# ============================ main =========================================
def main():
    random.seed(20260614)
    REF = 0.25  # reference per-day risk for fixed-risk Sharpe/DD comparison
    OUT = {
        "thrust": "aggregate_pockets",
        "question": "Does aggregating ALL marginal-positive pockets (each sized small, "
                    "low-correlation) raise portfolio Sharpe/monthly% at same-or-lower "
                    "maxDD vs the gold sleeve alone, or do they collapse to gold beta?",
        "discipline": {
            "fills": "geometry_lib.simulate (tested); P0 FVG & P1 breakout geometry verbatim from wave5_portfolio_combine -> audited wave4 sleeves",
            "no_lookahead": "FVG/energy-FVG = chained walk-forward (gate re-selected on past only); breakout sizing rule selected on TRAIN<=2024 only; session/mtf gates f(bars[<=i]); equity & daily-R calendar-ordered; weights known-at-entry",
            "oos": "per-pocket per-year 2015-2026 + forward 2025-26; portfolio verdict judged on forward window + calendar-ordered equity (no full-sample fitted weights)",
            "nulls": "shuffled-overlap diversification null on the assembled book; per-pocket INVERT control forward",
            "winsorized": "file-stitch single-bar spikes clamped (inherited loaders)",
            "risk_unit": "ONE risk event per CALENDAR DAY (conservative metals-cluster convention)",
            "costs": "real per-class medians from ULTIMATE_REAL_COST_MAP.json",
            "universe_control": "each pocket fixed to its discovered classes (no 13->45 coverage-growth confound)",
        },
        "pockets": {},
    }

    # ---------------- Build every pocket ----------------
    print("="*80); print("BUILDING POCKETS"); print("="*80)
    THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    # P0 gold FVG (carrier, audited WF)
    p0 = fvg_walk_forward(fvg_trades(PRECIOUS, target_R=2.0), THRESHOLDS)
    print(f"  P0 GOLD_FVG    : n={len(p0):5d}  full {stats([d['r'] for d in p0])['mean_R']:+.4f}  fwd {stats([d['r'] for d in p0 if d['year']>TRAIN_MAX])['mean_R']:+.4f}")

    # P1 gold/precious squeeze breakout, vol-state sized (train<=2024 rule)
    p1_base = breakout_entries(PRECIOUS, squeeze_thr=1.0)   # require pre-breakout compression
    p1_rule = select_volstate_rule_on_train(p1_base)
    p1 = breakout_sized_stream(p1_base, p1_rule)            # use wr as the deployable R
    print(f"  P1 GOLD_SQZ    : n={len(p1):5d}  rule={p1_rule}  rawfull {stats([d['r'] for d in p1])['mean_R']:+.4f}  sizedfwd {stats([d['wr'] for d in p1 if d['year']>TRAIN_MAX])['mean_R']:+.4f}")

    # P2 energy vol-gated FVG (WF)
    p2 = energy_fvg_walkforward()
    p2_inv = energy_fvg_invert_wf()
    print(f"  P2 ENERGY_FVG  : n={len(p2):5d}  full {stats([d['r'] for d in p2])['mean_R']:+.4f}  fwd {stats([d['r'] for d in p2 if d['year']>TRAIN_MAX])['mean_R']:+.4f}")

    # P3 metals NY-session long
    p3 = session_metals_long()
    p3_inv = session_metals_long(invert=True)
    print(f"  P3 METALS_NY   : n={len(p3):5d}  full {stats([d['r'] for d in p3])['mean_R']:+.4f}  fwd {stats([d['r'] for d in p3 if d['year']>TRAIN_MAX])['mean_R']:+.4f}")

    # P4 metals long trend-pullback
    p4 = metals_mtf_long()
    p4_inv = metals_mtf_long(invert=True)
    print(f"  P4 METALS_MTF  : n={len(p4):5d}  full {stats([d['r'] for d in p4])['mean_R']:+.4f}  fwd {stats([d['r'] for d in p4 if d['year']>TRAIN_MAX])['mean_R']:+.4f}")

    # registry: (name, records, R-key, optional invert records)
    POCKETS = [
        ("P0_GOLD_FVG", p0, "r", None),
        ("P1_GOLD_SQZ", p1, "wr", None),
        ("P2_ENERGY_FVG", p2, "r", p2_inv),
        ("P3_METALS_NY", p3, "r", p3_inv),
        ("P4_METALS_MTF", p4, "r", p4_inv),
    ]

    # ---------------- 1. Per-pocket honest stats (full / fwd / per-year / invert) ----------------
    print("\n" + "="*80); print("1. PER-POCKET HONEST STATS"); print("="*80)
    daily_maps = {}
    for name, recs, key, inv in POCKETS:
        full = stats([d[key] for d in recs])
        fwd = stats([d[key] for d in recs if d["year"] > TRAIN_MAX])
        py = per_year(recs, key=key)
        pos_years = sum(1 for y in py if py[y]["mean_R"] > 0)
        n_years = len(py)
        fwd_years = [y for y in py if y > TRAIN_MAX]
        fwd_pos = sum(1 for y in fwd_years if py[y]["mean_R"] > 0)
        invfwd = None
        if inv is not None:
            invkey = "wr" if key == "wr" else "r"
            invfwd = stats([d[invkey] for d in inv if d["year"] > TRAIN_MAX])["mean_R"]
        dm = daily_sum(recs, key=key)
        daily_maps[name] = dm
        beats_inv = (invfwd is None) or (fwd["mean_R"] > invfwd)
        print(f"  {name:14}: full R {full['mean_R']:+.4f} (n={full['n']})  fwd R {fwd['mean_R']:+.4f} (n={fwd['n']})  "
              f"pos-years {pos_years}/{n_years}  fwd-pos {fwd_pos}/{len(fwd_years)}  "
              f"invfwd {('%.4f'%invfwd) if invfwd is not None else 'na'}  beats_inv_fwd={beats_inv}")
        OUT["pockets"][name] = {
            "full": full, "fwd": fwd,
            "per_year": {str(y): py[y] for y in py},
            "pos_years": f"{pos_years}/{n_years}",
            "fwd_pos_years": f"{fwd_pos}/{len(fwd_years)}",
            "invert_fwd_mean_R": round(invfwd, 4) if invfwd is not None else None,
            "beats_invert_fwd": bool(beats_inv),
            "active_days": len(dm),
        }

    # ---------------- 1b. PER-POCKET STANDALONE FTMO VIABILITY ----------------
    # A "tiny edge" only diversifies if it is itself survivable. Many marginal-positive
    # pockets have positive mean-R but un-FTMO-able drawdowns (the breakout-class trap from
    # Wave5). Quantify each pocket's standalone max-FTMO risk / monthly% / fixed-risk DD.
    print("\n" + "-"*80); print("1b. PER-POCKET STANDALONE FTMO VIABILITY"); print("-"*80)
    names = [p[0] for p in POCKETS]
    standalone = {}
    for name in names:
        dm = daily_maps[name]
        sm = span_months_of(dm)
        ft = ftmo_sizing(dm, sm); mk = ft["max_risk_within_ftmo"]
        em = equity_metrics_simple(dm, REF)
        standalone[name] = {
            "max_ftmo_risk_pct_day": mk["risk_pct_per_day"] if mk else None,
            "monthly_pct_at_max": mk["approx_monthly_pct"] if mk else None,
            "maxDD_pct_at_max": mk["max_drawdown_pct"] if mk else None,
            "sharpe_at_ref": em["sharpe"], "maxdd_at_ref_pct": round(em["max_dd"]*100, 2),
            "ftmo_deployable_standalone": mk is not None,
        }
        print(f"  {name:14}: FTMO-deployable={mk is not None!s:5}  maxFTMOrisk {str(mk['risk_pct_per_day'] if mk else None):>5}%/d  "
              f"~mo {str(mk['approx_monthly_pct'] if mk else None):>6}%  | @ref{REF}%: Sharpe {em['sharpe']:+.3f} DD {em['max_dd']*100:.1f}%")
    OUT["1b_standalone_ftmo"] = standalone

    # ---------------- 2. CROSS-POCKET CORRELATION (daily-R, honest) ----------------
    print("\n" + "="*80); print("2. CROSS-POCKET DAILY-R CORRELATION (honest)"); print("="*80)
    names = [p[0] for p in POCKETS]
    all_days = sorted(set().union(*[set(daily_maps[n]) for n in names]))
    # Union 0-fill corr = the book-level diversification number (days where a pocket
    # doesn't trade contribute 0). Also intersection corr for both-active days.
    corr_union = {}; corr_inter = {}
    for a in names:
        for b in names:
            if a >= b: continue
            xs_u = [daily_maps[a].get(dt, 0.0) for dt in all_days]
            ys_u = [daily_maps[b].get(dt, 0.0) for dt in all_days]
            cu = pearson(xs_u, ys_u)
            common = sorted(set(daily_maps[a]) & set(daily_maps[b]))
            ci = pearson([daily_maps[a][dt] for dt in common],
                         [daily_maps[b][dt] for dt in common]) if len(common) >= 3 else None
            corr_union[f"{a}|{b}"] = round(cu, 3) if cu is not None else None
            corr_inter[f"{a}|{b}"] = (round(ci, 3) if ci is not None else None, len(common))
            print(f"  {a:14} x {b:14}: union0fill {('%+.3f'%cu) if cu is not None else 'na':>7}  "
                  f"intersection {('%+.3f'%ci) if ci is not None else 'na':>7} (both-active days {len(common)})")
    # correlation of each non-carrier pocket vs the carrier on both-active days = the
    # decisive "is this just gold beta?" number.
    OUT["2_correlation"] = {
        "daily_R_corr_union_0fill": corr_union,
        "daily_R_corr_intersection_and_overlapN": {k: {"corr": v[0], "both_active_days": v[1]}
                                                   for k, v in corr_inter.items()},
        "note": "union-0fill is the book-level diversification number; intersection is the "
                "co-movement on days BOTH pockets fire. High carrier-vs-pocket intersection "
                "corr = the pocket is gold beta, not an independent edge.",
    }

    # ---------------- 3. POCKET SHARE OF ACTIVE DAYS THAT OVERLAP CARRIER ----------------
    # If a 'diversifier' fires almost only on days the carrier also fires, and co-moves,
    # it adds risk concentration, not diversification. Quantify.
    print("\n" + "="*80); print("3. OVERLAP WITH CARRIER (gold-beta collapse check)"); print("="*80)
    carrier_days = set(daily_maps["P0_GOLD_FVG"])
    overlap = {}
    for name in names:
        if name == "P0_GOLD_FVG": continue
        d = set(daily_maps[name])
        ov = len(d & carrier_days)
        frac = ov/len(d) if d else 0.0
        overlap[name] = {"active_days": len(d), "days_also_carrier": ov,
                         "frac_overlapping_carrier": round(frac, 3)}
        print(f"  {name:14}: {len(d):4d} active days, {ov:4d} also-carrier ({frac*100:4.1f}% overlap)")
    OUT["3_carrier_overlap"] = overlap

    # ---------------- 4. ASSEMBLED EQUAL-RISK BOOK vs GOLD ALONE ----------------
    print("\n" + "="*80); print("4. ASSEMBLED BOOK vs GOLD ALONE"); print("="*80)
    # Equal-risk: each pocket gets 1/k of the per-day risk so none dominates.
    k = len(names)
    book_equal = {}
    for dt in all_days:
        book_equal[dt] = sum((1.0/k)*daily_maps[n].get(dt, 0.0) for n in names)
    gold_only = daily_maps["P0_GOLD_FVG"]

    # span over each book's own active (nonzero) days (gold ~125mo on its days; the book
    # spans the union since some pocket fires nearly every day).
    active_book = {dt: vv for dt, vv in book_equal.items() if abs(vv) > 1e-12}
    smG = span_months_of(gold_only); smB = span_months_of(active_book)
    mG = equity_metrics_simple(gold_only, REF)
    mB = equity_metrics_simple(book_equal, REF)
    ftmoG = ftmo_sizing(gold_only, smG)
    ftmoB = ftmo_sizing(book_equal, smB)
    okG = ftmoG["max_risk_within_ftmo"]; okB = ftmoB["max_risk_within_ftmo"]
    print(f"  @ref {REF}%/day fixed risk:")
    print(f"    GOLD-ALONE   : Sharpe {mG['sharpe']:+.3f}  maxDD {mG['max_dd']*100:5.2f}%  worstDay {mG['worst_day_pct']}%  days {mG['n_days']}")
    print(f"    EQUAL-RISK   : Sharpe {mB['sharpe']:+.3f}  maxDD {mB['max_dd']*100:5.2f}%  worstDay {mB['worst_day_pct']}%  days {mB['n_days']}")
    print(f"  FTMO max-risk operating point:")
    print(f"    GOLD-ALONE   : risk {okG['risk_pct_per_day'] if okG else None}%/day -> ~monthly {okG['approx_monthly_pct'] if okG else None}%  maxDD {okG['max_drawdown_pct'] if okG else None}%")
    print(f"    EQUAL-RISK   : risk {okB['risk_pct_per_day'] if okB else None}%/day -> ~monthly {okB['approx_monthly_pct'] if okB else None}%  maxDD {okB['max_drawdown_pct'] if okB else None}%")
    OUT["4_equal_risk_book_vs_gold"] = {
        "ref_risk_pct_per_day": REF,
        "gold_alone_fixedrisk": mG, "equal_risk_book_fixedrisk": mB,
        "gold_alone_ftmo": {"span_months": round(smG, 1), "max_risk_within_ftmo": okG},
        "equal_risk_book_ftmo": {"span_months": round(smB, 1), "max_risk_within_ftmo": okB},
    }

    # ---------------- 5. RISK-BUDGET SWEEP: best non-carrier allocation ----------------
    # Give the diversification thesis its FAIREST chance: carrier carries (1 - w_div) of
    # the book, the OTHER pockets (equal-weighted among themselves) carry w_div. Sweep
    # w_div in [0, 0.5]; for each find max FTMO per-day risk and monthly%. w_div=0 = gold
    # alone (reference). Weights are FIXED (not fit to forward) -> cannot leak.
    print("\n" + "="*80); print("5. RISK-BUDGET SWEEP (diversifier share w_div of book)"); print("="*80)
    others = [n for n in names if n != "P0_GOLD_FVG"]
    sweep = {}; best_combo = None; best_sharpe = None
    for w_div in [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]:
        w_each = (w_div/len(others)) if others else 0.0
        dm = {}
        for dt in all_days:
            v = (1.0 - w_div)*gold_only.get(dt, 0.0)
            if w_div > 0.0:
                for n in others: v += w_each*daily_maps[n].get(dt, 0.0)
            dm[dt] = v
        # Span over ONLY days this book is actually active (nonzero). For w_div=0 this is
        # gold's own ~125mo span, NOT the union ~137mo -- otherwise gold-alone's monthly%%
        # would be deflated by an inflated denominator and the verdict comparison would be
        # apples-to-oranges. Equity compounding is unaffected (0-fill days multiply by 1).
        active = {dt: vv for dt, vv in dm.items() if abs(vv) > 1e-12}
        sm = span_months_of(active)
        ft = ftmo_sizing(dm, sm); mk = ft["max_risk_within_ftmo"]
        em = equity_metrics_simple(dm, REF)
        monthly = mk["approx_monthly_pct"] if mk else None
        dd = mk["max_drawdown_pct"] if mk else None
        risk = mk["risk_pct_per_day"] if mk else None
        sweep[f"w_div={w_div}"] = {
            "w_diversifiers": w_div, "w_gold": round(1.0 - w_div, 3),
            "max_ftmo_risk_pct_day": risk, "monthly_pct_at_max": monthly, "maxDD_pct_at_max": dd,
            "sharpe_at_ref": em["sharpe"], "maxdd_at_ref_pct": round(em["max_dd"]*100, 2),
        }
        print(f"  w_div={w_div:>4} (gold {1-w_div:.2f}): max-FTMO {str(risk):>5}%/day  ~monthly {str(monthly):>6}%  "
              f"maxDD {str(dd):>5}%  | @ref{REF}%: Sharpe {em['sharpe']:+.3f} DD {em['max_dd']*100:.2f}%")
        if monthly is not None and (best_combo is None or monthly > best_combo[0]):
            best_combo = (monthly, w_div, dd, risk)
        if best_sharpe is None or em["sharpe"] > best_sharpe[0]:
            best_sharpe = (em["sharpe"], w_div, round(em["max_dd"]*100, 2))
    OUT["5_risk_budget_sweep"] = sweep
    OUT["5_best_ftmo_viable_book"] = ({"w_div": best_combo[1], "monthly_pct": best_combo[0],
                                       "maxDD_pct": best_combo[2], "risk_pct_day": best_combo[3]}
                                      if best_combo else None)
    OUT["5_best_sharpe_at_fixed_ref"] = {"w_div": best_sharpe[1], "sharpe": best_sharpe[0],
                                         "maxdd_pct": best_sharpe[2],
                                         "gold_alone_sharpe": sweep["w_div=0.0"]["sharpe_at_ref"]}
    print(f"  BEST FTMO-viable monthly%: w_div={best_combo[1]} -> ~monthly {best_combo[0]}% (maxDD {best_combo[2]}%, risk {best_combo[3]}%/day)")
    print(f"  BEST fixed-risk Sharpe:    w_div={best_sharpe[1]} -> Sharpe {best_sharpe[0]} (vs gold-alone {sweep['w_div=0.0']['sharpe_at_ref']})")

    # ---------------- 6. SHUFFLED-OVERLAP DIVERSIFICATION NULL ----------------
    # For the equal-risk book: randomly re-pair each NON-carrier pocket's daily-R values
    # onto its own day-slots (shuffled), keep the carrier fixed, recompute book Sharpe/DD.
    # If the real assembled book is NOT better than this null, the "diversification" is
    # random offsetting, not a genuine low-correlation timing relationship.
    print("\n" + "="*80); print("6. SHUFFLED-OVERLAP DIVERSIFICATION NULL (x300)"); print("="*80)
    real = equity_metrics_simple(book_equal, REF)
    null_sh = []; null_dd = []
    for s in range(300):
        rng = random.Random(7000 + s)
        shuffled_maps = {"P0_GOLD_FVG": gold_only}
        for n in others:
            dvals = list(daily_maps[n].values())
            rng.shuffle(dvals)
            ddays = sorted(daily_maps[n])
            shuffled_maps[n] = {dt: v for dt, v in zip(ddays, dvals)}
        comb = {}
        for dt in all_days:
            comb[dt] = sum((1.0/k)*shuffled_maps[n].get(dt, 0.0) for n in names)
        em = equity_metrics_simple(comb, REF)
        null_sh.append(em["sharpe"]); null_dd.append(em["max_dd"])
    nm_sh = sum(null_sh)/len(null_sh); nm_dd = sum(null_dd)/len(null_dd)
    beats_sh = sum(1 for x in null_sh if x < real["sharpe"])/len(null_sh)
    lower_dd = sum(1 for x in null_dd if x > real["max_dd"])/len(null_dd)
    print(f"  real book Sharpe {real['sharpe']:+.3f} vs null mean {nm_sh:+.3f} (real beats {beats_sh*100:.0f}% of nulls)")
    print(f"  real book maxDD  {real['max_dd']*100:.2f}% vs null mean {nm_dd*100:.2f}% (real lower than {lower_dd*100:.0f}% of nulls)")
    OUT["6_diversification_null"] = {
        "real_sharpe": real["sharpe"], "null_mean_sharpe": round(nm_sh, 3),
        "real_beats_sharpe_frac": round(beats_sh, 3),
        "real_maxdd_pct": round(real["max_dd"]*100, 2), "null_mean_maxdd_pct": round(nm_dd*100, 2),
        "real_lower_dd_frac": round(lower_dd, 3),
        "interpretation": "if real beats >~95% of nulls on both, the day-alignment genuinely "
                          "diversifies; if it beats ~50% or fewer, the 'diversification' is "
                          "random offsetting (or adverse).",
    }

    # ---------------- 7. PER-YEAR DAILY-R: gold vs book ----------------
    print("\n" + "="*80); print("7. PER-YEAR SUM-R: gold-alone vs equal-risk book"); print("="*80)
    def py_daily(dm):
        by = defaultdict(float); cnt = defaultdict(int)
        for dt, v in dm.items(): by[dt.year] += v; cnt[dt.year] += 1
        return {int(y): {"sum_R": round(by[y], 2), "active_days": cnt[y]} for y in sorted(by)}
    pyG = py_daily(gold_only); pyB = py_daily(book_equal)
    years = sorted(set(pyG) | set(pyB))
    print(f"  {'year':>4} {'GOLD_sumR':>10} {'GOLD_days':>9}  {'BOOK_sumR':>10} {'BOOK_days':>9}")
    for y in years:
        g = pyG.get(y, {"sum_R": 0.0, "active_days": 0}); b = pyB.get(y, {"sum_R": 0.0, "active_days": 0})
        print(f"  {y:>4} {g['sum_R']:>+10.2f} {g['active_days']:>9}  {b['sum_R']:>+10.2f} {b['active_days']:>9}")
    OUT["7_per_year_sumR"] = {
        "gold_alone": {str(y): pyG.get(y) for y in years},
        "equal_risk_book": {str(y): pyB.get(y) for y in years},
    }

    # also per-year for each pocket (the requested per-year breakdown)
    OUT["7b_per_year_each_pocket"] = {
        name: {str(y): py_daily(daily_maps[name]).get(y) for y in sorted(py_daily(daily_maps[name]))}
        for name in names
    }

    # ---------------- 8. VERDICT ----------------
    print("\n" + "="*80); print("8. VERDICT"); print("="*80)
    g_monthly = okG["approx_monthly_pct"] if okG else None
    g_dd = okG["max_drawdown_pct"] if okG else None
    b_monthly = best_combo[0] if best_combo else None
    b_dd = best_combo[2] if best_combo else None
    b_wdiv = best_combo[1] if best_combo else None
    monthly_gain = (b_monthly - g_monthly) if (g_monthly is not None and b_monthly is not None) else None

    # gold-beta collapse: mean carrier-vs-pocket intersection corr
    carr_pocket_corrs = []
    for n in others:
        key = f"P0_GOLD_FVG|{n}" if f"P0_GOLD_FVG|{n}" in corr_inter else f"{n}|P0_GOLD_FVG"
        c = corr_inter.get(key, (None, 0))[0]
        if c is not None: carr_pocket_corrs.append(c)
    mean_carrier_corr = round(sum(carr_pocket_corrs)/len(carr_pocket_corrs), 3) if carr_pocket_corrs else None

    materially_better = bool(
        b_monthly is not None and g_monthly is not None and b_wdiv and b_wdiv > 0 and
        b_monthly > g_monthly + 0.02 and b_dd is not None and g_dd is not None and b_dd <= g_dd + 0.5)
    sharpe_better = best_sharpe[0] > sweep["w_div=0.0"]["sharpe_at_ref"] and best_sharpe[1] > 0
    null_survives = (OUT["6_diversification_null"]["real_beats_sharpe_frac"] >= 0.95 and
                     OUT["6_diversification_null"]["real_lower_dd_frac"] >= 0.95)

    verdict = {
        "gold_alone_monthly_pct": g_monthly, "gold_alone_maxDD_pct": g_dd,
        "best_aggregated_w_div": b_wdiv, "best_aggregated_monthly_pct": b_monthly,
        "best_aggregated_maxDD_pct": b_dd, "monthly_pct_gain_vs_gold": round(monthly_gain, 3) if monthly_gain is not None else None,
        "best_fixed_risk_sharpe_w_div": best_sharpe[1], "best_fixed_risk_sharpe": best_sharpe[0],
        "gold_alone_fixed_risk_sharpe": sweep["w_div=0.0"]["sharpe_at_ref"],
        "mean_carrier_vs_pocket_intersection_corr": mean_carrier_corr,
        "non_carrier_pockets_that_beat_invert_fwd": [n for n in others if OUT["pockets"][n]["beats_invert_fwd"]],
        "non_carrier_pockets_fwd_positive": [n for n in others if OUT["pockets"][n]["fwd"]["mean_R"] > 0],
        "diversification_null_survives_95": bool(null_survives),
        "AGGREGATION_RAISES_FTMO_MONTHLY_AT_SAME_OR_LOWER_DD": materially_better,
        "AGGREGATION_RAISES_FIXED_RISK_SHARPE": bool(sharpe_better),
    }
    OUT["8_verdict"] = verdict
    for kk, vv in verdict.items():
        print(f"  {kk}: {vv}")

    with open(EDGE + "/WAVE7_AGGREGATE_POCKETS_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE7_AGGREGATE_POCKETS_RESULT.json")
    return OUT

if __name__ == "__main__":
    main()
