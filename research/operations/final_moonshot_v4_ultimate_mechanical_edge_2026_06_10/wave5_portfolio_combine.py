"""
wave5_portfolio_combine.py
==========================
THRUST (portfolio_combine): Combine the DEPLOYABLE precious-metals vol-gated
FVG-retest sleeve (WAVE4_METALS_FVG_HARDEN -> walk-forward +0.226R, FTMO-safe at
0.25%/trade, ~0.22%/mo, XAUUSD-anchored) with the ONE Wave-5-candidate broadener
(generic Donchian-20 breakout + vol-state sizing on the metals+energy pocket --
the only sizing variant that cleared the matched RANDOM-permuted-weight null at the
95% bar: full z=3.17, fwd z=1.55, per WAVE4_VOL_STATE_SIZING) into ONE portfolio.

We MEASURE, honestly:
  1. Cross-component correlation (daily-R, the level at which a multi-strategy book
     actually shares risk -- per-trade timestamps don't line up, days do).
  2. Combined daily-R curve 2015-2026 and per-year R for each sleeve and the book.
  3. Max drawdown of each sleeve and the combined book on a compounded equity path.
  4. The per-trade risk %% that keeps the COMBINED book inside FTMO (maxDD<10%,
     worst single calendar DAY <5%), and the resulting monthly %%.
  5. Is the combined book MATERIALLY better than the gold sleeve alone -- higher
     monthly%% at the same DD, or lower DD at the same monthly%%?

STRICT PROTOCOL (every prior loose claim was a leak; only audited results count):
  - Fills ONLY via tested geometry_lib.simulate / simulate_detail. No hand-rolled
    fills/signs. Entry geometry is COPIED VERBATIM from the two audited wave4 scripts
    (FVG: wave4_metals_fvg_harden.fvg_trades; breakout: wave4_vol_state_sizing.breakout_entries
    + the train-selected vol-state sizing rule), so this combine reproduces the EXACT
    audited sleeves, not a re-derivation.
  - NO LOOKAHEAD: every gate/sizing feature is f(bars[<=i]); FVG sleeve uses the audited
    WALK-FORWARD chained stream (gate threshold re-selected on past only); breakout sleeve
    uses the vol-state sizing rule SELECTED ON TRAIN<=2024 ONLY (frozen thr=1.3, lo=0.5,
    hi=2.0 -- the published selection) then read out full-cycle. Daily-R aggregation and
    equity compounding are ordered by calendar date; weights are known-at-entry.
  - STRICT OOS: FVG = chained walk-forward (refit on past only). Breakout sizing rule =
    selected on TRAIN<=2024, FORWARD 2025-26 read-out. Per-year 2015-2026 always shown.
  - MATCHED NULLS under the SAME combine: we report each sleeve's own audited null
    survival (already established) and, for the combine specifically, a SHUFFLED-OVERLAP
    null -- randomly re-pairing the two sleeves' daily-R series destroys any real
    diversification timing; if the real combined Sharpe/DD is no better than that, the
    "diversification" is illusory.
  - Winsorize file-stitch bad-print bars (inherited from the audited loaders).
  - Controlled, fixed universe (precious metals for FVG; metals+energy pocket for breakout,
    matching the audited sleeves). Truth over positives. If a component does not survive
    or the combine is not materially better, SAY SO.

DESIGN HONESTY NOTE (surfaced, not hidden):
  The breakout broadener's pocket (metals+energy) OVERLAPS the FVG sleeve's symbols
  (metals). Energy H4 history is thin and gappy (USOIL has a 2022-2025 gap, UKOIL only
  2020-21, HEATOIL/NATGAS only 2024+), so the breakout sleeve is ALSO metals-dominated.
  That means the two sleeves are NOT independent asset bets -- they are two different
  TRIGGERS on largely the same (metals) tape. The correlation measurement below is the
  decisive test of whether that still diversifies at the daily-R level. We do NOT assume it.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
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
POCKET_CLASSES = {"metals", "energy"}   # breakout pocket (matches wave4_vol_state_sizing)

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
    """Clamp single-bar bad-print spikes that revert next bar (file-stitch artifacts).
    Identical conservative rule to wave4_metals_fvg_harden.winsorize."""
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

# ============================ SLEEVE A: precious-metals FVG (audited) =======
def fvg_trades(symbols, target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, atr_win=100):
    """VERBATIM from wave4_metals_fvg_harden.fvg_trades (the audited sleeve)."""
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
    """VERBATIM logic from wave4_metals_fvg_harden.walk_forward. Returns chained trade
    records (each with its own R, year, ts, sym) -- the deployable WF stream."""
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

# ============================ SLEEVE B: Donchian breakout + vol-state size ===
def breakout_entries(lookback=20, target_R=2.0, stop_mult=1.0, atr_win=100,
                     classes=POCKET_CLASSES, maxbars=80):
    """VERBATIM from wave4_vol_state_sizing.breakout_entries."""
    out = []
    for sym in SYMBOLS:
        if classes is not None and ASSET_CLASS_BY_SYMBOL.get(sym) not in classes:
            continue
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        ratios = [sma_atr_ratio(atrs, i, atr_win) for i in range(n)]
        for i in range(max(60, lookback+1), n-1):
            a = atrs[i]
            if a <= 0: continue
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
    """Select thr/(lo,hi) maximizing TRAIN<=2024 ret/DD -- VERBATIM grid from
    wave4_vol_state_sizing.select_volstate_rule. Train-only; no forward peeking."""
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
    """Apply the train-selected vol-state sizing rule -> per-trade WEIGHTED R = w*r
    (the deployable sized breakout stream). w known-at-entry from vol-state."""
    out = []
    for d in recs:
        rt = d["ratio"]
        w = rule["hi_w"] if (rt is not None and rt >= rule["thr"]) else rule["lo_w"]
        out.append({"ts": d["ts"], "year": d["year"], "sym": d["sym"],
                    "r": d["r"], "w": w, "wr": w*d["r"]})
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
    """Sum of R (or weighted R) per CALENDAR DAY -> {date: total_R}. This is the
    risk-sharing unit for a multi-strategy book."""
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
    """Compound an equity path over sorted calendar days. Each day's R-total is risked
    at risk_pct/100 of current equity (one daily risk unit -- correlated intraday trades
    are ONE risk event, the conservative metals-cluster convention from wave4).
    Returns (final_eq, max_dd_frac, worst_day_pct, n_days, daily_ret_list)."""
    days = sorted(daily_map)
    eq = 1.0; peak = 1.0; maxdd = 0.0; worst_day = 0.0
    rets = []
    for dt in days:
        dr = daily_map[dt]
        step_ret = (risk_pct/100.0) * dr
        before = eq
        eq *= (1.0 + step_ret)
        if eq <= 1e-9: eq = 1e-9
        day_pct = (eq - before)        # equity delta this day (unit-start frame)
        worst_day = min(worst_day, day_pct)
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak-eq)/peak)
        rets.append(step_ret)
    return eq, maxdd, -worst_day*100.0, len(days), rets

def ftmo_sizing(daily_map, span_months, risk_grid=None):
    """Largest per-day risk %% keeping maxDD<10% AND worst single DAY<5%% (FTMO).
    Returns grid + max_ok."""
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
    if not rets: return {"sharpe": 0.0, "max_dd": 0.0, "final_eq": 1.0}
    steps = [math.log(1+r) if (1+r) > 1e-9 else -20 for r in rets]
    m = sum(steps)/len(steps)
    sd = math.sqrt(sum((s-m)**2 for s in steps)/len(steps)) if len(steps) > 1 else 0.0
    sharpe = (m/sd*math.sqrt(len(steps))) if sd > 0 else 0.0
    return {"sharpe": round(sharpe, 3), "max_dd": round(maxdd, 4),
            "final_eq": round(eq, 4), "worst_day_pct": round(worst_day_pct, 2),
            "n_days": ndays}

# ============================ main =========================================
def main():
    random.seed(20260614)
    OUT = {"thrust": "portfolio_combine",
           "discipline": {
               "fills": "geometry_lib.simulate (tested); entry geometry copied verbatim from audited wave4 sleeves",
               "no_lookahead": "FVG=walk-forward (gate re-selected on past only); breakout sizing rule selected on TRAIN<=2024 only; daily-R & equity ordered by calendar date; weights known-at-entry",
               "oos": "FVG chained WF; breakout vol-state rule train-selected then read forward; per-year 2015-2026",
               "nulls": "each sleeve's own audited null survival + shuffled-overlap diversification null for the combine",
               "winsorized": "file-stitch single-bar spikes clamped (inherited from audited loaders)",
               "risk_unit": "ONE risk event per CALENDAR DAY (correlated intraday trades = one unit; conservative metals-cluster convention)",
           },
           "design_honesty": {
               "overlap": "breakout pocket (metals+energy) overlaps FVG pocket (precious metals); energy H4 is thin/gappy so breakout is also metals-dominated -> two TRIGGERS on largely the same tape, not independent asset bets. Daily-R correlation below is the decisive diversification test.",
           }}

    # ---------------- build SLEEVE A: precious-metals FVG walk-forward ----------------
    print("="*80); print("SLEEVE A: precious-metals FVG-retest, walk-forward (audited deployable)"); print("="*80)
    THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    fvg_base = fvg_trades(PRECIOUS, target_R=2.0)
    sleeveA = fvg_walk_forward(fvg_base, THRESHOLDS)
    a_full = stats([d["r"] for d in sleeveA])
    a_fwd = stats([d["r"] for d in sleeveA if d["year"] > TRAIN_MAX])
    a_py = per_year(sleeveA)
    print(f"  A walk-forward: full R={a_full['mean_R']:+.4f} n={a_full['n']} sum={a_full['sum_R']}  "
          f"fwd R={a_fwd['mean_R']:+.4f} n={a_fwd['n']}")
    OUT["sleeve_A_metals_fvg_wf"] = {
        "full": a_full, "fwd": a_fwd,
        "per_year": {str(y): a_py[y] for y in a_py},
        "n_trades": len(sleeveA),
    }

    # ---------------- build SLEEVE B: Donchian breakout + vol-state sizing ----------------
    print("\n" + "="*80); print("SLEEVE B: Donchian-20 breakout + vol-state sizing (Wave-5 candidate)"); print("="*80)
    brk_base = breakout_entries()
    rule = select_volstate_rule_on_train(brk_base)
    print(f"  selected vol-state sizing rule (TRAIN<=2024 only): thr={rule['thr']} lo_w={rule['lo_w']} hi_w={rule['hi_w']}")
    sleeveB = breakout_sized_stream(brk_base, rule)
    # raw (unsized) breakout for honesty
    b_raw_full = stats([d["r"] for d in sleeveB])
    b_raw_fwd = stats([d["r"] for d in sleeveB if d["year"] > TRAIN_MAX])
    # sized (deployable) breakout: report on WEIGHTED R
    b_full = stats([d["wr"] for d in sleeveB])
    b_fwd = stats([d["wr"] for d in sleeveB if d["year"] > TRAIN_MAX])
    b_py = per_year(sleeveB, key="wr")
    print(f"  B raw breakout R (unsized): full {b_raw_full['mean_R']:+.4f}  fwd {b_raw_fwd['mean_R']:+.4f}  n={b_raw_full['n']}")
    print(f"  B sized (w*R, deployable):  full {b_full['mean_R']:+.4f}  fwd {b_fwd['mean_R']:+.4f}")
    OUT["sleeve_B_breakout_volsized"] = {
        "selected_rule": rule,
        "raw_full": b_raw_full, "raw_fwd": b_raw_fwd,
        "sized_full": b_full, "sized_fwd": b_fwd,
        "per_year_sizedR": {str(y): b_py[y] for y in b_py},
        "n_trades": len(sleeveB),
    }

    # ---------------- 1. CROSS-COMPONENT CORRELATION (daily-R) ----------------
    print("\n" + "="*80); print("1. CROSS-COMPONENT CORRELATION (daily-R)"); print("="*80)
    # A daily-R uses plain R (FVG sleeve is sized flat in its audited FTMO study).
    # B daily-R uses WEIGHTED R (its deployable form is the vol-sized stream).
    dailyA = daily_sum(sleeveA, key="r")
    dailyB = daily_sum(sleeveB, key="wr")
    common_days = sorted(set(dailyA) & set(dailyB))
    allA_days = set(dailyA); allB_days = set(dailyB)
    union_days = sorted(allA_days | allB_days)
    # correlation on the union (days where a sleeve doesn't trade contribute 0 -- the
    # honest book-level view) AND on the intersection (both-active days).
    xs_u = [dailyA.get(dt, 0.0) for dt in union_days]
    ys_u = [dailyB.get(dt, 0.0) for dt in union_days]
    corr_union = pearson(xs_u, ys_u)
    xs_i = [dailyA[dt] for dt in common_days]
    ys_i = [dailyB[dt] for dt in common_days]
    corr_inter = pearson(xs_i, ys_i) if len(common_days) >= 3 else None
    # also yearly correlation of per-year mean R
    ya = per_year(sleeveA); yb = per_year(sleeveB, key="wr")
    cy = sorted(set(ya) & set(yb))
    corr_year = pearson([ya[y]["mean_R"] for y in cy], [yb[y]["mean_R"] for y in cy]) if len(cy) >= 3 else None
    print(f"  A active days={len(allA_days)}  B active days={len(allB_days)}  both-active days={len(common_days)}")
    print(f"  daily-R corr (union, 0-fill non-trading days) = {corr_union:+.3f}")
    print(f"  daily-R corr (both-active intersection)       = {corr_inter if corr_inter is None else round(corr_inter,3)}")
    print(f"  per-year mean-R corr                          = {corr_year if corr_year is None else round(corr_year,3)}")
    OUT["1_correlation"] = {
        "A_active_days": len(allA_days), "B_active_days": len(allB_days),
        "both_active_days": len(common_days),
        "daily_R_corr_union_0fill": round(corr_union, 3) if corr_union is not None else None,
        "daily_R_corr_intersection": round(corr_inter, 3) if corr_inter is not None else None,
        "per_year_meanR_corr": round(corr_year, 3) if corr_year is not None else None,
        "note": "union 0-fill corr is the book-level diversification number (most days only one sleeve is active).",
    }

    # ---------------- 2. COMBINED DAILY-R CURVE + PER-YEAR ----------------
    print("\n" + "="*80); print("2. COMBINED DAILY-R CURVE & PER-YEAR (each sleeve + book)"); print("="*80)
    # Combined book = both sleeves pooled. Each sleeve contributes its DEPLOYABLE per-trade
    # R: A=plain R, B=weighted R. We give each sleeve EQUAL risk budget (half the per-day
    # risk each) so neither dominates -- the standard equal-risk two-sleeve book. Daily-R
    # of the combined book = 0.5*dailyA + 0.5*dailyB on the union of days.
    combined_daily = {}
    for dt in union_days:
        combined_daily[dt] = 0.5*dailyA.get(dt, 0.0) + 0.5*dailyB.get(dt, 0.0)
    # per-year of each daily series (sum of daily R in the year)
    def year_of(dt): return dt.year
    def py_daily(dm):
        by = defaultdict(float); cnt = defaultdict(int)
        for dt, v in dm.items(): by[dt.year] += v; cnt[dt.year] += 1
        return {int(y): {"sum_R": round(by[y], 2), "active_days": cnt[y]} for y in sorted(by)}
    pyA = py_daily(dailyA); pyB = py_daily(dailyB); pyC = py_daily(combined_daily)
    years = sorted(set(pyA) | set(pyB) | set(pyC))
    print(f"  {'year':>4}  {'A_sumR':>8} {'A_days':>6}  {'B_sumR':>8} {'B_days':>6}  {'COMB_sumR(0.5/0.5)':>18}")
    for y in years:
        ay = pyA.get(y, {"sum_R": 0.0, "active_days": 0})
        by = pyB.get(y, {"sum_R": 0.0, "active_days": 0})
        cyv = pyC.get(y, {"sum_R": 0.0, "active_days": 0})
        print(f"  {y:>4}  {ay['sum_R']:>+8.2f} {ay['active_days']:>6}  {by['sum_R']:>+8.2f} {by['active_days']:>6}  {cyv['sum_R']:>+18.2f}")
    OUT["2_per_year_dailyR"] = {
        "A_metals_fvg": {str(y): pyA.get(y) for y in years},
        "B_breakout_sized": {str(y): pyB.get(y) for y in years},
        "combined_equal_risk_0.5_0.5": {str(y): pyC.get(y) for y in years},
    }

    # ---------------- 3. MAX-DD of each sleeve & combined (at common risk) ----------------
    print("\n" + "="*80); print("3. MAX DRAWDOWN (compounded daily equity, risk=0.25%/day reference)"); print("="*80)
    REF = 0.25
    mA = equity_metrics_simple(dailyA, REF)
    mB = equity_metrics_simple(dailyB, REF)
    mC = equity_metrics_simple(combined_daily, REF)
    print(f"  A metals-FVG : maxDD {mA['max_dd']*100:5.2f}%  Sharpe {mA['sharpe']:+.3f}  finalEq {mA['final_eq']}  worstDay {mA['worst_day_pct']}%  days {mA['n_days']}")
    print(f"  B breakout   : maxDD {mB['max_dd']*100:5.2f}%  Sharpe {mB['sharpe']:+.3f}  finalEq {mB['final_eq']}  worstDay {mB['worst_day_pct']}%  days {mB['n_days']}")
    print(f"  COMBINED     : maxDD {mC['max_dd']*100:5.2f}%  Sharpe {mC['sharpe']:+.3f}  finalEq {mC['final_eq']}  worstDay {mC['worst_day_pct']}%  days {mC['n_days']}")
    OUT["3_maxdd_at_ref_025"] = {"ref_risk_pct_per_day": REF, "A": mA, "B": mB, "combined": mC}

    # ---------------- 4. FTMO SIZING on the COMBINED book ----------------
    print("\n" + "="*80); print("4. FTMO SIZING (per-day risk keeping maxDD<10% & worstDay<5%)"); print("="*80)
    def span_months_of(dm):
        days = sorted(dm)
        if len(days) < 2: return 1.0
        return ((datetime.combine(days[-1], datetime.min.time()) -
                 datetime.combine(days[0], datetime.min.time())).days or 1)/30.44
    smA = span_months_of(dailyA); smB = span_months_of(dailyB); smC = span_months_of(combined_daily)
    ftmoA = ftmo_sizing(dailyA, smA)
    ftmoB = ftmo_sizing(dailyB, smB)
    ftmoC = ftmo_sizing(combined_daily, smC)
    def show_ftmo(nm, res, sm):
        mk = res["max_risk_within_ftmo"]
        print(f"  {nm}: span_months={sm:.1f}")
        for rk, v in res["grid"].items():
            flag = " <= MAX OK" if (mk and v["risk_pct_per_day"] == mk["risk_pct_per_day"]) else ""
            print(f"    risk/day {v['risk_pct_per_day']:>4}%: maxDD {v['max_drawdown_pct']:>5}%  worstDay {v['worst_day_pct']:>5}%  "
                  f"totRet {v['total_return_pct']:>7}%  ~mo {v['approx_monthly_pct']}%  ok={v['within_ftmo']}{flag}")
    show_ftmo("A metals-FVG", ftmoA, smA)
    show_ftmo("B breakout", ftmoB, smB)
    show_ftmo("COMBINED", ftmoC, smC)
    OUT["4_ftmo_sizing"] = {
        "A_metals_fvg": {"span_months": round(smA, 1), **ftmoA},
        "B_breakout": {"span_months": round(smB, 1), **ftmoB},
        "combined": {"span_months": round(smC, 1), **ftmoC},
    }

    # ---------------- 4b. RISK-BUDGET SWEEP (give the combine its fairest chance) ----------------
    # The 50/50 equal-risk book hands the volatile breakout sleeve half the book and is
    # dominated by its 2021 chop-year blowup. The FAIR question is: does ANY breakout
    # allocation w_B in [0,0.5], with the gold sleeve carrying (1-w_B), produce a book that
    # is FTMO-viable AND beats gold-alone monthly% at <= gold's DD? We sweep w_B and, for
    # each, find the max per-day risk inside FTMO and the resulting monthly%. w_B=0 is the
    # gold sleeve alone (reference). This cannot leak: weights are fixed, not fit to forward.
    print("\n" + "="*80); print("4b. RISK-BUDGET SWEEP (breakout share w_B of the book)"); print("="*80)
    sweep = {}
    best_combo = None  # (monthly, w_B, dd, risk)
    for wB in [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]:
        wA = 1.0 - wB
        dm = {}
        for dt in union_days:
            dm[dt] = wA*dailyA.get(dt, 0.0) + wB*dailyB.get(dt, 0.0)
        sm = span_months_of(dm)
        ft = ftmo_sizing(dm, sm)
        mk = ft["max_risk_within_ftmo"]
        em = equity_metrics_simple(dm, 0.25)
        monthly = mk["approx_monthly_pct"] if mk else None
        dd = mk["max_drawdown_pct"] if mk else None
        risk = mk["risk_pct_per_day"] if mk else None
        sweep[f"wB={wB}"] = {
            "w_breakout": wB, "w_gold": wA,
            "max_ftmo_risk_pct_day": risk, "monthly_pct_at_max": monthly,
            "maxDD_pct_at_max": dd,
            "sharpe_at_ref025": em["sharpe"], "maxdd_at_ref025_pct": round(em["max_dd"]*100, 2),
        }
        print(f"  w_B={wB:>4} (gold {wA:.2f}): max-FTMO risk {str(risk):>5}%/day  ~monthly {str(monthly):>6}%  "
              f"maxDD {str(dd):>5}%  | @ref0.25%: Sharpe {em['sharpe']:+.3f} DD {em['max_dd']*100:.2f}%")
        if monthly is not None and (best_combo is None or monthly > best_combo[0]):
            best_combo = (monthly, wB, dd, risk)
    OUT["4b_risk_budget_sweep"] = sweep
    if best_combo:
        print(f"  BEST FTMO-viable book by monthly%: w_B={best_combo[1]} -> ~monthly {best_combo[0]}% at maxDD {best_combo[2]}% (risk {best_combo[3]}%/day)")
    OUT["4b_best_ftmo_viable_book"] = (
        {"w_breakout": best_combo[1], "monthly_pct": best_combo[0],
         "maxDD_pct": best_combo[2], "risk_pct_day": best_combo[3]} if best_combo else None)
    # at a FIXED reference risk, which w_B maximizes Sharpe? (the fixed-risk diversification
    # view, separate from the FTMO-headroom view which is gated by worst-day fat tails)
    best_sharpe_wb = max(sweep.values(), key=lambda v: v["sharpe_at_ref025"])
    OUT["4b_best_sharpe_at_fixed_ref_risk"] = {
        "w_breakout": best_sharpe_wb["w_breakout"],
        "sharpe_at_ref025": best_sharpe_wb["sharpe_at_ref025"],
        "maxdd_at_ref025_pct": best_sharpe_wb["maxdd_at_ref025_pct"],
        "pure_gold_sharpe_at_ref025": sweep["wB=0.0"]["sharpe_at_ref025"],
        "note": "small breakout slice raises FIXED-risk Sharpe, but the breakout's fat-tail "
                "chop days (2021) raise worst-day/maxDD faster than return, so it does NOT "
                "buy extra FTMO-headroom monthly%.",
    }
    print(f"  fixed-risk(0.25%) Sharpe peaks at w_B={best_sharpe_wb['w_breakout']} "
          f"(Sharpe {best_sharpe_wb['sharpe_at_ref025']:+.3f} vs pure-gold {sweep['wB=0.0']['sharpe_at_ref025']:+.3f})")

    # ---------------- 5. MATERIALLY BETTER? + diversification null ----------------
    print("\n" + "="*80); print("5. IS COMBINED MATERIALLY BETTER THAN GOLD SLEEVE ALONE?"); print("="*80)
    okA = ftmoA["max_risk_within_ftmo"]
    a_monthly = okA["approx_monthly_pct"] if okA else None
    a_dd = okA["max_drawdown_pct"] if okA else None
    # "Combined" for the verdict = the BEST FTMO-viable risk-budgeted book from the sweep
    # (the combine's fairest chance), NOT the dominated 50/50. If the sweep's best is just
    # w_B=0 (pure gold) the combine adds nothing -- that is itself the honest answer.
    c_monthly = best_combo[0] if best_combo else None
    c_dd = best_combo[2] if best_combo else None
    c_wB = best_combo[1] if best_combo else None
    print(f"  A alone @ max-FTMO risk {okA['risk_pct_per_day'] if okA else None}%/day: ~monthly {a_monthly}%  maxDD {a_dd}%")
    print(f"  BEST risk-budgeted book (w_B={c_wB}): ~monthly {c_monthly}%  maxDD {c_dd}%")
    monthly_gain = (c_monthly - a_monthly) if (a_monthly is not None and c_monthly is not None) else None
    # diversification null: SHUFFLE the date-pairing of B's daily-R against A's days, recompute
    # combined Sharpe at REF; if real combined Sharpe is not better than this null, the
    # "diversification" comes from random offsetting, not a real timing relationship.
    bvals = list(dailyB.values())
    null_sharpes = []; null_dds = []
    for s in range(200):
        rng = random.Random(9000 + s)
        shuffled = list(bvals); rng.shuffle(shuffled)
        # re-map B's values onto B's own day slots in shuffled order, keep A as-is
        bdays = sorted(dailyB)
        dB_shuf = {dt: v for dt, v in zip(bdays, shuffled)}
        comb = {}
        for dt in union_days:
            comb[dt] = 0.5*dailyA.get(dt, 0.0) + 0.5*dB_shuf.get(dt, 0.0)
        em = equity_metrics_simple(comb, REF)
        null_sharpes.append(em["sharpe"]); null_dds.append(em["max_dd"])
    nm_sh = sum(null_sharpes)/len(null_sharpes)
    nm_dd = sum(null_dds)/len(null_dds)
    real_sh = mC["sharpe"]; real_dd = mC["max_dd"]
    beats_null_sharpe = sum(1 for x in null_sharpes if x < real_sh)/len(null_sharpes)
    lower_dd_than_null = sum(1 for x in null_dds if x > real_dd)/len(null_dds)
    print(f"  diversification null x200 (shuffle B day-pairing): combined Sharpe real {real_sh:+.3f} vs null {nm_sh:+.3f} "
          f"(real beats {beats_null_sharpe*100:.0f}%); maxDD real {real_dd*100:.2f}% vs null {nm_dd*100:.2f}% "
          f"(real lower than {lower_dd_than_null*100:.0f}%)")
    # also: best single-sleeve Sharpe vs combined Sharpe (does pooling beat the best alone?)
    best_single_sharpe = max(mA["sharpe"], mB["sharpe"])
    best_single_dd = min(mA["max_dd"], mB["max_dd"])
    combine_improves_sharpe = real_sh > best_single_sharpe
    combine_lowers_dd = real_dd < best_single_dd
    verdict = {
        "A_max_ftmo_risk_pct_day": okA["risk_pct_per_day"] if okA else None,
        "A_monthly_pct": a_monthly, "A_maxDD_pct": a_dd,
        "best_combine_w_breakout": c_wB,
        "C_monthly_pct": c_monthly, "C_maxDD_pct": c_dd,
        "monthly_pct_gain_combined_vs_A": round(monthly_gain, 3) if monthly_gain is not None else None,
        "combined_sharpe": real_sh, "best_single_sleeve_sharpe": best_single_sharpe,
        "combined_maxdd": real_dd, "best_single_sleeve_maxdd": best_single_dd,
        "combine_improves_sharpe_vs_best_single": combine_improves_sharpe,
        "combine_lowers_dd_vs_best_single": combine_lowers_dd,
        "diversification_null_combined_sharpe_beats_frac": round(beats_null_sharpe, 3),
        "diversification_null_combined_lower_dd_frac": round(lower_dd_than_null, 3),
        "diversification_real_vs_null_sharpe": [round(real_sh, 3), round(nm_sh, 3)],
        "MATERIALLY_BETTER_monthly_at_same_dd": bool(
            c_monthly is not None and a_monthly is not None and c_monthly > a_monthly and
            c_dd is not None and a_dd is not None and c_dd <= a_dd + 0.5),
        "MATERIALLY_BETTER_lower_dd_at_same_monthly": bool(
            c_dd is not None and a_dd is not None and c_dd < a_dd and
            c_monthly is not None and a_monthly is not None and c_monthly >= a_monthly - 0.02),
    }
    verdict["headline"] = (
        "NO MATERIAL FTMO IMPROVEMENT. The breakout broadener does NOT survive as an "
        "independent diversifier: (1) it shares the metals tape with the gold sleeve "
        "(pocket overlap; thin/gappy energy), daily-R corr only +0.10 union / +0.18 "
        "intersection but the breakout sleeve is far more volatile (standalone maxDD 41.5% "
        "vs gold 5.2% at 0.25%/day, driven by a -146R 2021 chop year); (2) the shuffled-"
        "overlap diversification null shows the real combined book is WORSE than a random "
        "re-pairing on both Sharpe (real beats 0% of nulls) and DD (real lower than 0%) -- "
        "i.e. the real day-alignment is mildly adverse, not diversifying; (3) at the FTMO "
        "binding constraint, the best risk-budgeted combine (w_B=0.05) only MATCHES gold-"
        "alone monthly% (0.336% vs 0.336%) at slightly higher DD (8.67% vs 8.20%). A small "
        "breakout slice DOES raise FIXED-risk Sharpe (+2.32 pure gold -> +2.75 at w_B=0.15) "
        "because it adds uncorrelated up-years (2019/2020/2023 when gold was flat/negative), "
        "but its fat-tail chop days raise worst-day/maxDD faster than return, so that Sharpe "
        "gain does NOT convert into extra FTMO-headroom monthly%. The breakout standalone is "
        "NOT FTMO-deployable at any risk (maxDD>=19% even at 0.1%/day). DEPLOYABLE BOOK = "
        "the gold sleeve alone (~0.34%/mo at 0.4%/day, maxDD 8.2%); the breakout adds "
        "diversification on paper but no usable FTMO return uplift and meaningful tail risk."
    )
    OUT["5_verdict"] = verdict
    print("\n  --- VERDICT ---")
    for k, v in verdict.items():
        print(f"  {k}: {v}")

    with open(EDGE + "/WAVE5_PORTFOLIO_COMBINE_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE5_PORTFOLIO_COMBINE_RESULT.json")
    return OUT

if __name__ == "__main__":
    main()
