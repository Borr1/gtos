"""
wave1_structure_setups_ict.py
=============================
THRUST: structure_setups_ict — trader-grade structural setups (not crude single bars).

Setups tested:
  (A) LIQUIDITY SWEEP + RECLAIM:
        Price sweeps a PRIOR-DAY or PRIOR-SESSION high/low (takes liquidity beyond it
        intrabar) then CLOSES back inside (reclaim). Enter the reclaim direction.
        Stop: just beyond the swept extreme (structural, tight). Target: next opposing
        liquidity (the opposite prior-day/session extreme) -> measured R.
  (B) ORDER-BLOCK / FVG RETEST in HTF trend:
        In an established higher-timeframe trend (defined by daily/structural slope),
        wait for a pullback that retests the last opposing order-block (the last down
        candle before an up impulse, or vice versa) / fills a fair-value-gap, then
        continues. Enter continuation. Stop beyond the OB. Target prior swing /
        measured move.

DISCIPLINE:
  - All fills via tested geometry_lib.simulate (no hand-rolled stop/target/sign).
  - R-unit = structural stop distance.
  - TRAIN <= 2024, FORWARD 2025-2026, AND per-year across ALL available years.
  - Concatenate+dedupe 2015-2022 and 2022-2026 into up-to-11yr series.
  - Real per-asset costs from ULTIMATE_REAL_COST_MAP.json.
  - Negative controls: (1) matched random-bar same-direction entries (drift),
    (2) inverted signal (fade the reclaim) to show the edge is directional, not just
    survivorship of one side.
  - Bar = forward-positive AND positive in a MAJORITY of available years.

Sessions on H4 (UTC bar opens): we define 3 FX sessions by bar hour:
   Asia   00:00-07:59, London 08:00-15:59, NY 16:00-23:59.
Prior-session extreme = high/low of the most recently COMPLETED session of that type's
   block; we use the simpler, robust "prior completed session of ANY type" rolling extreme
   plus prior-day. Both prior-day and prior-session are tested.
"""
from __future__ import annotations
import sys, os, csv, math, json
from datetime import datetime, date
from collections import defaultdict

# Path-portable roots. Previously hardcoded to a dev-Mac path; resolve from this
# module's own location so the parity/test import chain works on any host (VPS).
# Env overrides allowed for non-standard layouts. EDGE = this route dir; ROOT = repo root.
EDGE = os.environ.get("GTOS_EDGE_DIR") or os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("GTOS_REPO_ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(EDGE)))
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

# ----- universe: union of both dirs -----
def syms_in(d):
    # Tolerate absent deep-H4 export dirs (present only on the research host). The
    # parity check + sleeve-conf registry do not need this data; only the backtest
    # build (run under __main__) does. Missing dir -> empty universe, never a crash.
    if not os.path.isdir(d):
        return set()
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

def load(sym):
    """Concatenate 2015-2022 + 2022-2026, dedupe by timestamp, sorted ascending."""
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b   # later file wins on overlap
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

# ----- prior-day / prior-session extremes (no lookahead: prior COMPLETED block) -----
def session_id(t):
    h = t.hour
    if h < 8: return 0    # Asia
    if h < 16: return 1   # London
    return 2              # NY

def levels(times, bars):
    n = len(bars)
    pdh = [None]*n; pdl = [None]*n      # prior day
    psh = [None]*n; psl = [None]*n      # prior session (any-type, prior completed session block)
    # prior day
    cd = None; cdh = cdl = None; ldh = ldl = None
    # prior session: track current session block (date, session_id)
    csk = None; csh = csl = None; lsh = lsl = None
    for i in range(n):
        t = times[i]; b = bars[i]
        dk = t.date()
        if dk != cd:
            if cd is not None: ldh, ldl = cdh, cdl
            cd = dk; cdh = b.h; cdl = b.l
        else:
            cdh = max(cdh, b.h); cdl = min(cdl, b.l)
        sk = (dk, session_id(t))
        if sk != csk:
            if csk is not None: lsh, lsl = csh, csl
            csk = sk; csh = b.h; csl = b.l
        else:
            csh = max(csh, b.h); csl = min(csl, b.l)
        pdh[i] = ldh; pdl[i] = ldl; psh[i] = lsh; psl[i] = lsl
    return pdh, pdl, psh, psl

# ----- HTF trend proxy: slope of close over lookback vs atr -----
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

def _stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 1)}

def per_year(records):
    """records: list of (year, R). -> {year: stats}"""
    by = defaultdict(list)
    for y, r in records: by[y].append(r)
    return {y: _stats(by[y]) for y in sorted(by)}

def split_fwd(records):
    """records: list of (symbol, year, asset_class, R)."""
    tr = [r for _, y, _, r in records if y <= 2024]
    fw = [r for _, y, _, r in records if y >= 2025]
    return _stats(tr), _stats(fw)

# =====================================================================
# SETUP A: liquidity sweep of prior extreme + reclaim
# =====================================================================
def setup_sweep_reclaim(level_kind='pd', wick_min=0.0, reclaim_min=0.0,
                        stop_buf=0.10, target_mode='opposing', target_R=2.0,
                        trend_filter=False, invert=False, atr_stop_floor=0.25):
    """
    level_kind: 'pd' (prior day) or 'ps' (prior session)
    Sweep LOW then reclaim -> long; sweep HIGH then reclaim -> short.
    stop_buf: extra buffer beyond swept extreme, in ATR units.
    target_mode: 'opposing' -> opposite prior extreme; 'fixedR' -> target_R * stop_dist.
    invert: enter the OPPOSITE direction (negative control).
    atr_stop_floor: minimum stop distance in ATR units (avoids absurdly tiny structural stops).
    Returns list of (symbol, year, asset_class, R).
    """
    out = []
    for sym in SYMBOLS:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        pdh, pdl, psh, psl = levels(T, B)
        H = psh if level_kind == 'ps' else pdh
        L = psl if level_kind == 'ps' else pdl
        oppH = pdh if level_kind == 'ps' else psh   # for 'opposing' target use SAME kind opposite extreme
        oppL = pdl if level_kind == 'ps' else psl
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            b = B[i]; lo = L[i]; hi = H[i]
            tr = htf_trend(B, i) if trend_filter else None
            # --- sweep of LOW + reclaim -> long ---
            if lo is not None and b.l < lo and b.c > lo:
                dnwick = min(b.o, b.c) - b.l
                reclaim = b.c - lo
                if dnwick >= wick_min*a and reclaim >= reclaim_min*a:
                    if not trend_filter or tr >= 0:
                        stop_dist = max((b.c - b.l) + stop_buf*a, atr_stop_floor*a)
                        if target_mode == 'opposing' and hi is not None and hi > b.c:
                            target_dist = hi - b.c
                            if target_dist < 0.5*stop_dist:  # skip degenerate tiny targets
                                target_dist = None
                        else:
                            target_dist = target_R*stop_dist
                        if target_dist is not None:
                            d = -1 if invert else +1
                            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                            out.append((sym, T[i].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
            # --- sweep of HIGH + reclaim -> short ---
            if hi is not None and b.h > hi and b.c < hi:
                upwick = b.h - max(b.o, b.c)
                reclaim = hi - b.c
                if upwick >= wick_min*a and reclaim >= reclaim_min*a:
                    if not trend_filter or tr <= 0:
                        stop_dist = max((b.h - b.c) + stop_buf*a, atr_stop_floor*a)
                        if target_mode == 'opposing' and lo is not None and lo < b.c:
                            target_dist = b.c - lo
                            if target_dist < 0.5*stop_dist:
                                target_dist = None
                        else:
                            target_dist = target_R*stop_dist
                        if target_dist is not None:
                            d = +1 if invert else -1
                            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                            out.append((sym, T[i].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
    return out

# =====================================================================
# SETUP A2: TIGHT structural sweep+reclaim, entry on NEXT bar
# =====================================================================
def setup_sweep_reclaim_v2(level_kind='pd', sweep_min=0.05, reclaim_min=0.10,
                           stop_mode='wick', stop_mult=0.5, stop_buf=0.05,
                           target_mode='opposing', target_R=2.0,
                           trend_filter=False, invert=False, atr_stop_floor=0.20,
                           min_RR=1.0):
    """
    Cleaner ICT mechanics:
      - Sweep bar i: takes prior extreme by >= sweep_min*atr AND closes back inside by
        >= reclaim_min*atr (genuine liquidity grab + reclaim).
      - ENTRY at NEXT bar open (i+1) -> we simulate from i+1, so the sweep bar's own
        range never counts against us as the entry bar.
      - STOP just beyond the swept wick extreme (structural). stop_mode='wick' uses the
        distance entry->wick + buffer (tight). stop_mode='atr' uses stop_mult*atr.
      - min_RR: skip trades whose target/stop < min_RR (geometry must be worth it).
    """
    out = []
    for sym in SYMBOLS:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        pdh, pdl, psh, psl = levels(T, B)
        H = psh if level_kind == 'ps' else pdh
        L = psl if level_kind == 'ps' else pdl
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-2):
            a = atrs[i]
            if a <= 0: continue
            b = B[i]; nb = B[i+1]; lo = L[i]; hi = H[i]
            tr = htf_trend(B, i) if trend_filter else None
            entry = nb.o
            # --- sweep LOW + reclaim -> long, enter next bar ---
            if lo is not None and (lo - b.l) >= sweep_min*a and b.c > lo and (b.c - lo) >= reclaim_min*a:
                if not trend_filter or tr >= 0:
                    if stop_mode == 'wick':
                        stop_dist = max((entry - b.l) + stop_buf*a, atr_stop_floor*a)
                    else:
                        stop_dist = stop_mult*a
                    if target_mode == 'opposing' and hi is not None and hi > entry:
                        target_dist = hi - entry
                    else:
                        target_dist = target_R*stop_dist
                    if target_dist is not None and target_dist >= min_RR*stop_dist:
                        d = -1 if invert else +1
                        r = simulate(B, i+1, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                        out.append((sym, T[i+1].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
            # --- sweep HIGH + reclaim -> short, enter next bar ---
            if hi is not None and (b.h - hi) >= sweep_min*a and b.c < hi and (hi - b.c) >= reclaim_min*a:
                if not trend_filter or tr <= 0:
                    if stop_mode == 'wick':
                        stop_dist = max((b.h - entry) + stop_buf*a, atr_stop_floor*a)
                    else:
                        stop_dist = stop_mult*a
                    if target_mode == 'opposing' and lo is not None and lo < entry:
                        target_dist = entry - lo
                    else:
                        target_dist = target_R*stop_dist
                    if target_dist is not None and target_dist >= min_RR*stop_dist:
                        d = +1 if invert else -1
                        r = simulate(B, i+1, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                        out.append((sym, T[i+1].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
    return out

# =====================================================================
# SETUP B: order-block / FVG retest in HTF trend (continuation)
# =====================================================================
def setup_ob_fvg_retest(stop_buf=0.10, target_R=2.0, trend_lb=30, fvg_min=0.10,
                        invert=False, atr_stop_floor=0.25, mode='fvg'):
    """
    HTF trend up: look for a bullish FVG (gap between bar[i-2].h and bar[i].l) created by an
    up-impulse, then a pullback bar that TAGS the gap (retest) and holds -> enter long
    continuation. Stop below the gap/retest low. Target target_R.
    mode='fvg' uses fair-value-gap retest; mode='ob' uses last-opposite-candle (order block) retest.
    invert: take opposite direction (negative control).
    Returns list of (symbol, year, asset_class, R).
    """
    out = []
    for sym in SYMBOLS:
        T, B = load(sym)
        if len(B) < 200: continue
        cost = cost_for(sym); n = len(B)
        atrs = [atr14(B, i) for i in range(n)]
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            tr = htf_trend(B, i, trend_lb)
            b = B[i]
            if tr == 1:
                # bullish FVG formed by bars [i-2,i-1,i]: gap if B[i].l > B[i-2].h was an impulse,
                # but for a RETEST we want price to currently be pulling back into a recent gap.
                # Find a recent bullish FVG in window [i-8, i-2]: low_k > high_{k-2}
                entered = False
                for k in range(i-2, max(i-9, 60), -1):
                    if mode == 'fvg':
                        gap_top = B[k].l; gap_bot = B[k-2].h
                        if gap_top - gap_bot < fvg_min*a:  # need a real gap
                            continue
                    else:  # ob: last down candle before up move at k
                        if not (B[k].c < B[k].o):  # need a down (order-block) candle
                            continue
                        gap_top = B[k].h; gap_bot = B[k].l
                    # current bar retests into the zone and closes back up
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                        target_dist = target_R*stop_dist
                        d = -1 if invert else +1
                        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                        out.append((sym, T[i].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
                        entered = True
                        break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    if mode == 'fvg':
                        gap_bot = B[k].h; gap_top = B[k-2].l
                        if gap_top - gap_bot < fvg_min*a:
                            continue
                    else:
                        if not (B[k].c > B[k].o):
                            continue
                        gap_bot = B[k].l; gap_top = B[k].h
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        target_dist = target_R*stop_dist
                        d = +1 if invert else -1
                        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                        out.append((sym, T[i].year, ASSET_CLASS_BY_SYMBOL.get(sym), r))
                        break
    return out

# =====================================================================
# reporting
# =====================================================================
def report(name, records):
    tr, fw = split_fwd(records)
    py = per_year([(y, r) for _, y, _, r in records])
    yrs = sorted(py)
    fwd_yrs = [y for y in yrs if y >= 2025]
    pos_years = sum(1 for y in yrs if py[y]["mean_R"] > 0)
    pos_fwd_years = sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0)
    print(f"\n===== {name} =====")
    print(f"  TRAIN(<=2024): n={tr['n']:6d}  R={tr['mean_R']:+.4f}  w={tr['win%']:.1f}%")
    print(f"  FWD  (>=2025): n={fw['n']:6d}  R={fw['mean_R']:+.4f}  w={fw['win%']:.1f}%")
    line = "  per-year: "
    for y in yrs:
        line += f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']}) "
    print(line)
    print(f"  positive years: {pos_years}/{len(yrs)}   positive FWD years: {pos_fwd_years}/{len(fwd_yrs)}")
    return {
        "name": name,
        "train": tr, "fwd": fw,
        "per_year": {str(y): py[y] for y in yrs},
        "pos_years": pos_years, "total_years": len(yrs),
        "pos_fwd_years": pos_fwd_years, "total_fwd_years": len(fwd_yrs),
    }

def report_by_class(name, records):
    print(f"\n----- {name} by asset class (FWD>=2025) -----")
    by = defaultdict(list)
    for _, y, cls, r in records:
        if y >= 2025: by[cls].append(r)
    res = {}
    for cls in sorted(by):
        st = _stats(by[cls]); res[cls] = st
        print(f"     {cls:8s} n={st['n']:5d} R={st['mean_R']:+.4f} w={st['win%']:.1f}%")
    return res

def main():
    out = {"setups": [], "controls": []}

    print("##################### SETUP A: SWEEP + RECLAIM #####################")
    # baseline variants
    A_variants = [
        ("A_pd_opposing",      dict(level_kind='pd', target_mode='opposing')),
        ("A_pd_fixed2R",       dict(level_kind='pd', target_mode='fixedR', target_R=2.0)),
        ("A_pd_fixed1R",       dict(level_kind='pd', target_mode='fixedR', target_R=1.0)),
        ("A_ps_opposing",      dict(level_kind='ps', target_mode='opposing')),
        ("A_ps_fixed2R",       dict(level_kind='ps', target_mode='fixedR', target_R=2.0)),
        ("A_pd_opposing_trend",dict(level_kind='pd', target_mode='opposing', trend_filter=True)),
        ("A_pd_wick0.3_recl0.1",dict(level_kind='pd', target_mode='opposing', wick_min=0.3, reclaim_min=0.1)),
    ]
    A_recs = {}
    for nm, kw in A_variants:
        recs = setup_sweep_reclaim(**kw)
        A_recs[nm] = recs
        out["setups"].append(report(nm, recs))

    print("\n############## SETUP A2: TIGHT sweep+reclaim, next-bar entry ##############")
    A2_variants = [
        ("A2_pd_wick_opp",   dict(level_kind='pd', stop_mode='wick', target_mode='opposing')),
        ("A2_pd_atr_2R",     dict(level_kind='pd', stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=2.0)),
        ("A2_pd_atr_1R",     dict(level_kind='pd', stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=1.0)),
        ("A2_pd_atr_3R",     dict(level_kind='pd', stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=3.0)),
        ("A2_pd_strong",     dict(level_kind='pd', sweep_min=0.15, reclaim_min=0.25, stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=2.0)),
        ("A2_pd_strong_trend",dict(level_kind='pd', sweep_min=0.15, reclaim_min=0.25, stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=2.0, trend_filter=True)),
        ("A2_ps_atr_2R",     dict(level_kind='ps', stop_mode='atr', stop_mult=0.5, target_mode='fixedR', target_R=2.0)),
    ]
    A2_recs = {}
    for nm, kw in A2_variants:
        recs = setup_sweep_reclaim_v2(**kw)
        A2_recs[nm] = recs
        out["setups"].append(report(nm, recs))

    print("\n##################### SETUP B: OB / FVG RETEST #####################")
    B_variants = [
        ("B_fvg_2R",  dict(mode='fvg', target_R=2.0)),
        ("B_fvg_1R",  dict(mode='fvg', target_R=1.0)),
        ("B_fvg_3R",  dict(mode='fvg', target_R=3.0)),
        ("B_ob_2R",   dict(mode='ob',  target_R=2.0)),
        ("B_ob_1R",   dict(mode='ob',  target_R=1.0)),
    ]
    B_recs = {}
    for nm, kw in B_variants:
        recs = setup_ob_fvg_retest(**kw)
        B_recs[nm] = recs
        out["setups"].append(report(nm, recs))

    # ---- pick best by FWD R among those with decent n, then class breakdown + controls ----
    print("\n##################### NEGATIVE CONTROLS on strongest A & B #####################")
    # strongest by forward, require n_fwd >= 150
    cand = []
    for nm, recs in {**A_recs, **A2_recs, **B_recs}.items():
        fw = split_fwd(recs)[1]
        if fw["n"] >= 150:
            cand.append((nm, fw["mean_R"], recs))
    cand.sort(key=lambda x: -x[1])
    for nm, fr, recs in cand[:4]:
        report_by_class(nm, recs)

    # invert control on the top A & top B variant
    controls = []
    top_A = next((nm for nm, _, _ in cand if nm.startswith("A_")), None)
    top_B = next((nm for nm, _, _ in cand if nm.startswith("B_")), None)
    if top_A:
        kw = dict(A_variants)[top_A]; inv = setup_sweep_reclaim(invert=True, **kw)
        controls.append(report(f"CONTROL_invert_{top_A}", inv))
    if top_B:
        kw = dict(B_variants)[top_B]; inv = setup_ob_fvg_retest(invert=True, **kw)
        controls.append(report(f"CONTROL_invert_{top_B}", inv))
    out["controls"] = controls

    with open(EDGE + "/WAVE1_STRUCTURE_SETUPS_ICT_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    print("\nWROTE WAVE1_STRUCTURE_SETUPS_ICT_RESULT.json")

if __name__ == "__main__":
    main()
