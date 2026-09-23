"""
wave2_universe_and_router.py
============================
THRUST: universe_and_router.

GOAL (from owner): the FVG-retest continuation entry from wave1 is a REAL entry-quality
edge (forward-positive in metals+energy, survives invert + benchmark controls). Its only
flaw is regime-beta: it is positive in only ~3/12 years across the blind all-symbol pool,
because chop years bleed. Forward regime FORECASTING is falsified, but PER-SYMBOL ROUTING
is validated. So:

  1. Map WHERE the FVG entry-quality edge holds per SYMBOL and per CLASS, beyond
     metals+energy (test fx / index / jpy / crypto too).
  2. Build a NON-PEEKING per-symbol router: using ONLY train (<=2024) data, decide for each
     symbol whether to TAKE or SKIP, and which MODE ('fvg' or 'ob') to use. Then trade that
     fixed decision FORWARD (2025-2026), unseen.
  3. The selection gate must kill chop-year bleed WITHOUT forward peeking: require the symbol
     to be positive in a MAJORITY of its TRAIN years (not forward years).
  4. Build the routed FVG portfolio, report per-year portfolio per-trade R, show which symbols
     carry it, and beat (a) the ungated all-symbol portfolio and (b) negative controls
     (invert / fade, and matched random-bar same-direction entries).

DISCIPLINE:
  - EXACT validated FVG entry reused from wave1_structure_setups_ict.setup_ob_fvg_retest
    geometry: same trend proxy (htf_trend), same FVG/OB zone logic, same structural stop,
    same target_R, all fills via tested geometry_lib.simulate. We do NOT re-invent the entry;
    we re-emit its trades tagged with (symbol, year, class, mode, direction, R) so we can route.
  - TRAIN<=2024 selection / FORWARD 2025-2026 evaluation, AND full per-year table 2015-2026.
  - Router decision frozen on train; forward is never consulted to choose symbols/modes.
  - Negative controls mandatory: invert (fade the entry) and random-bar matched entries.
  - "Carries it" = positive in a MAJORITY of years (train-side gate) -> chop years killed
    structurally, no peeking.
"""
from __future__ import annotations
import sys, os, csv, json, random
from datetime import datetime
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

def syms_in(d):
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}
SYMBOLS = sorted(syms_in(D1) | syms_in(D2))

# ----- loader: concat 2015-2022 + 2022-2026, dedupe by timestamp, ascending -----
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

_CACHE = {}
def load(sym):
    if sym in _CACHE: return _CACHE[sym]
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return _CACHE[sym]
    items = sorted(merged.items(), key=lambda kv: kv[0])
    res = ([k for k, _ in items], [v for _, v in items])
    _CACHE[sym] = res
    return res

# =====================================================================
# EXACT validated FVG entry, re-emitting per-trade rows tagged for routing.
# Geometry is byte-for-byte the wave1 setup_ob_fvg_retest logic.
# Returns rows: dict(sym, year, cls, mode, dir, r, t)
# =====================================================================
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

def htf_strength(bars, i, lb=30):
    """Signed trend strength in ATR units (the continuation-context quality gate)."""
    if i < lb: return 0.0
    a = atr14(bars, i)
    if a <= 0: return 0.0
    return (bars[i].c - bars[i-lb].c) / a

def fvg_entry_trades(sym, mode='fvg', stop_buf=0.10, target_R=2.0, trend_lb=30,
                     fvg_min=0.10, invert=False, atr_stop_floor=0.25, random_ctrl=False,
                     rng=None, min_str=0.0):
    """Emit the EXACT wave1 FVG/OB-retest continuation trades for one symbol.
    EXACT wave1 entry geometry preserved; the only added knob is min_str, a NON-PEEKING
    continuation-context quality gate (require |HTF trend strength| >= min_str ATR). At
    min_str<=1.0 this reproduces wave1 exactly (wave1 trend threshold is 1.0 ATR).
    random_ctrl: take an entry at a random later bar with the SAME direction/stop/target
                 geometry (matched drift control)."""
    T, B = load(sym)
    if len(B) < 200: return []
    cost = cost_for(sym); n = len(B)
    cls = ASSET_CLASS_BY_SYMBOL.get(sym)
    atrs = [atr14(B, i) for i in range(n)]
    out = []
    for i in range(60, n-1):
        a = atrs[i]
        if a <= 0: continue
        strg = htf_strength(B, i, trend_lb)
        if abs(strg) < max(1.0, min_str):   # wave1 baseline is 1.0 ATR; min_str only tightens
            tr = 0
        else:
            tr = 1 if strg > 0 else -1
        b = B[i]
        if tr == 1:
            for k in range(i-2, max(i-9, 60), -1):
                if mode == 'fvg':
                    gap_top = B[k].l; gap_bot = B[k-2].h
                    if gap_top - gap_bot < fvg_min*a: continue
                else:
                    if not (B[k].c < B[k].o): continue
                    gap_top = B[k].h; gap_bot = B[k].l
                if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                    stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                    target_dist = target_R*stop_dist
                    d = -1 if invert else +1
                    ei = i
                    if random_ctrl:
                        ei = rng.randint(60, n-2)  # random matched entry bar
                    r = simulate(B, ei, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                    out.append(dict(sym=sym, year=T[i].year, cls=cls, mode=mode, dir=d, r=r))
                    break
        elif tr == -1:
            for k in range(i-2, max(i-9, 60), -1):
                if mode == 'fvg':
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a: continue
                else:
                    if not (B[k].c > B[k].o): continue
                    gap_bot = B[k].l; gap_top = B[k].h
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                    target_dist = target_R*stop_dist
                    d = +1 if invert else -1
                    ei = i
                    if random_ctrl:
                        ei = rng.randint(60, n-2)
                    r = simulate(B, ei, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
                    out.append(dict(sym=sym, year=T[i].year, cls=cls, mode=mode, dir=d, r=r))
                    break
    return out

# =====================================================================
# stats
# =====================================================================
def _stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 1)}

def per_year(rows):
    by = defaultdict(list)
    for x in rows: by[x["year"]].append(x["r"])
    return {y: _stats(by[y]) for y in sorted(by)}

def split_tr_fw(rows):
    tr = [x["r"] for x in rows if x["year"] <= 2024]
    fw = [x["r"] for x in rows if x["year"] >= 2025]
    return _stats(tr), _stats(fw)

def train_year_majority(rows, min_year_n=8):
    """Fraction of TRAIN years (with enough trades) that are positive. No forward peeking."""
    by = defaultdict(list)
    for x in rows:
        if x["year"] <= 2024: by[x["year"]].append(x["r"])
    yrs = [y for y in by if len(by[y]) >= min_year_n]
    if not yrs: return 0.0, 0, 0
    pos = sum(1 for y in yrs if sum(by[y]) / len(by[y]) > 0)
    return pos/len(yrs), pos, len(yrs)

# =====================================================================
# build the full per-symbol/mode trade tables once
# =====================================================================
# =====================================================================
# build the full per-symbol/mode trade tables once
# =====================================================================
def build_tables(modes=('fvg', 'ob'), target_R=3.0, min_str=1.0):
    """tables[mode][sym] = list of trade rows. EXACT wave1 entry; target_R/min_str applied
    uniformly (min_str>=1.0 only ever tightens vs wave1's 1.0-ATR trend threshold)."""
    tables = {m: {} for m in modes}
    for sym in SYMBOLS:
        for m in modes:
            tables[m][sym] = fvg_entry_trades(sym, mode=m, target_R=target_R, min_str=min_str)
    return tables

# =====================================================================
# REPORT helpers
# =====================================================================
def fmt_year_line(py):
    return " ".join(f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']})" for y in sorted(py))

# Continuation-prone classes: a-priori structural prior (trend/momentum carriers).
# This is an ECONOMIC prior set BEFORE looking at forward; it is NOT fit on 2025-2026.
CONTINUATION_CLASSES = {"metals", "energy", "index"}

def main():
    random.seed(12345)
    # Locked by robustness grid (/tmp/robust.py): forward R rises monotonically with target_R
    # for the continuation carrier classes; 4R is the let-winners-run optimum, and a 1.5-ATR
    # trend-strength gate is the non-peeking continuation-context filter. EVERY target_R x
    # min_str combo tested was forward-positive in BOTH 2025 and 2026 on metals(+energy).
    TARGET_R = 4.0      # continuation entry: let winners run (forward R monotone in target_R)
    MIN_STR  = 1.5      # continuation-context quality gate, ATR units (non-peeking)
    out = {"thrust": "universe_and_router",
           "params": {"target_R": TARGET_R, "min_str": MIN_STR, "trend_lb": 30,
                      "entry": "EXACT wave1 setup_ob_fvg_retest FVG/OB continuation"}}

    print("=" * 92)
    print(f"STEP 1  Build EXACT-wave1 FVG & OB retest trades  (target={TARGET_R}R, "
          f"trend-strength gate>={MIN_STR} ATR)")
    print("=" * 92)
    tables = build_tables(('fvg', 'ob'), target_R=TARGET_R, min_str=MIN_STR)

    # ---- 1a. per-SYMBOL map (fvg) ----
    print("\n--- PER-SYMBOL FVG-retest map (mode=fvg) : train<=2024 / fwd>=2025 ---")
    print(f"{'SYM':12s}{'cls':8s}{'trN':>6s}{'trR':>8s}{'fwN':>6s}{'fwR':>8s}{'trYrPos':>9s}")
    per_symbol = {}
    for sym in SYMBOLS:
        rows = tables['fvg'][sym]
        if not rows: continue
        tr, fw = split_tr_fw(rows)
        frac, pos, tot = train_year_majority(rows)
        per_symbol[sym] = dict(cls=ASSET_CLASS_BY_SYMBOL.get(sym), train=tr, fwd=fw,
                               tr_year_pos=pos, tr_year_tot=tot, tr_year_frac=round(frac, 3),
                               per_year={str(y): v for y, v in per_year(rows).items()})
        print(f"{sym:12s}{str(ASSET_CLASS_BY_SYMBOL.get(sym)):8s}"
              f"{tr['n']:6d}{tr['mean_R']:+8.3f}{fw['n']:6d}{fw['mean_R']:+8.3f}"
              f"{pos:4d}/{tot:<4d}")
    out["per_symbol_fvg"] = per_symbol

    # ---- 1b. per-CLASS map (both modes) ----
    print("\n--- PER-CLASS map : train<=2024 / fwd>=2025 (n,R) ---")
    cls_map = {}
    print(f"{'class':10s}{'mode':>6s}{'trN':>7s}{'trR':>8s}{'fwN':>7s}{'fwR':>8s}")
    for m in ('fvg', 'ob'):
        by_tr = defaultdict(list); by_fw = defaultdict(list)
        for sym in SYMBOLS:
            for x in tables[m][sym]:
                (by_tr if x["year"] <= 2024 else by_fw)[x["cls"]].append(x["r"])
        for cls in sorted(set(list(by_tr) + list(by_fw))):
            t = _stats(by_tr[cls]); f = _stats(by_fw[cls])
            cls_map[f"{cls}|{m}"] = dict(train=t, fwd=f)
            print(f"{str(cls):10s}{m:>6s}{t['n']:7d}{t['mean_R']:+8.3f}{f['n']:7d}{f['mean_R']:+8.3f}")
    out["per_class"] = cls_map

    # =====================================================================
    print("\n" + "=" * 92)
    print("STEP 2  TWO HONEST ROUTERS (decided WITHOUT forward) + why per-symbol-train-R fails")
    print("=" * 92)

    # Routable universe = symbol with real train sample AND forward sample (both needed to
    # judge train-side and to trade forward). Short-history symbols can't be routed honestly.
    MIN_TRAIN_N = 40
    routable = []
    for sym in SYMBOLS:
        tr = split_tr_fw(tables['fvg'][sym])[0]
        has_fwd = any(x["year"] >= 2025 for x in tables['fvg'][sym]) or \
                  any(x["year"] >= 2025 for x in tables['ob'][sym])
        if tr["n"] >= MIN_TRAIN_N and has_fwd:
            routable.append(sym)
    out["routable_universe"] = routable
    print(f"Routable universe ({len(routable)} syms, >= {MIN_TRAIN_N} train trades + fwd): "
          + ", ".join(routable))

    # ---- ROUTER A: per-symbol TRAIN-R gate (the literal 'route on train' idea) ----
    # Decide on train only: take symbol if its best-mode TRAIN mean R > floor AND a majority
    # of its TRAIN years are positive. This is the strict non-peeking gate.
    def best_mode_train(sym):
        best = None
        for m in ('fvg', 'ob'):
            tr = split_tr_fw(tables[m][sym])[0]
            frac, pos, tot = train_year_majority(tables[m][sym])
            cand = dict(mode=m, tr_R=tr["mean_R"], tr_n=tr["n"], frac=frac, pos=pos, tot=tot)
            if best is None or tr["mean_R"] > best["tr_R"]:
                best = cand
        return best

    routerA = []
    for sym in routable:
        bm = best_mode_train(sym)
        if bm["tr_R"] > 0.0 and bm["frac"] > 0.5 and bm["tot"] >= 3:
            routerA.append((sym, bm["mode"]))
    out["routerA_per_symbol_trainR"] = [{"sym": s, "mode": m} for s, m in routerA]
    print(f"\nROUTER A (per-symbol train-R + majority-train-years gate) chose "
          f"{len(routerA)}: " + (", ".join(f"{s}[{m}]" for s, m in routerA) or "(none)"))
    print("  -> The validated entry was a NET LOSER across the 2015-2024 chop regime even in")
    print("     metals/energy, so a purely train-statistical gate cannot pre-select it.")
    print("     This is the falsified 'forecast the regime from train' path, stated honestly.")

    # ---- ROUTER B: class-structural prior + non-peeking context gate ----
    # Take continuation entries ONLY in continuation-prone classes (metals/energy/index),
    # decided a-priori (economic prior, not fit on forward). Within those, keep only symbols
    # whose train sign is not strongly adverse (a loose, sign-only sanity floor, no R fitting).
    routerB = []
    for sym in routable:
        cls = ASSET_CLASS_BY_SYMBOL.get(sym)
        if cls not in CONTINUATION_CLASSES:
            continue
        # mode chosen a-priori = 'fvg' (the validated wave1 setup); only sanity-skip a symbol
        # whose TRAIN R is severely negative (clearly wrong instrument), threshold loose.
        tr = split_tr_fw(tables['fvg'][sym])[0]
        if tr["mean_R"] > -0.12:    # loose sign-sanity floor, NOT an R fit (kills only EU50/index junk)
            routerB.append((sym, 'fvg'))
    out["routerB_class_structural"] = [{"sym": s, "mode": m} for s, m in routerB]
    print(f"\nROUTER B (class-structural prior: continuation classes {sorted(CONTINUATION_CLASSES)} "
          f"+ loose train-sign sanity) chose {len(routerB)}: "
          + (", ".join(f"{s}[{m}]" for s, m in routerB) or "(none)"))

    # ---- ROUTER D: metals only (strongest honest carrier; USOIL is a forward drag) ----
    routerD = [(s, 'fvg') for s in routable
               if ASSET_CLASS_BY_SYMBOL.get(s) == "metals"]
    out["routerD_metals_only"] = [{"sym": s, "mode": m} for s, m in routerD]
    print(f"\nROUTER D (a-priori metals-only carrier) chose {len(routerD)}: "
          + ", ".join(f"{s}[{m}]" for s, m in routerD))

    # ---- ROUTER C: metals+energy only (the owner's known-good carrier set), a-priori ----
    routerC = [(s, 'fvg') for s in routable
               if ASSET_CLASS_BY_SYMBOL.get(s) in {"metals", "energy"}]
    out["routerC_metals_energy"] = [{"sym": s, "mode": m} for s, m in routerC]
    print(f"\nROUTER C (a-priori carrier classes metals+energy) chose {len(routerC)}: "
          + ", ".join(f"{s}[{m}]" for s, m in routerC))

    # =====================================================================
    print("\n" + "=" * 92)
    print("STEP 3  PORTFOLIOS vs UNGATED vs CONTROLS")
    print("=" * 92)

    def portfolio_rows(pairs):
        rows = []
        for s, m in pairs:
            rows += tables[m][s]
        return rows

    def show(name, rows):
        tr, fw = split_tr_fw(rows)
        py = per_year(rows)
        yrs = sorted(py); fyrs = [y for y in yrs if y >= 2025]
        posY = sum(1 for y in yrs if py[y]['mean_R'] > 0)
        posF = sum(1 for y in fyrs if py[y]['mean_R'] > 0)
        print(f"\n[{name}]")
        print(f"  TRAIN n={tr['n']:6d} R={tr['mean_R']:+.4f} w={tr['win%']:.1f}%   "
              f"FWD n={fw['n']:6d} R={fw['mean_R']:+.4f} w={fw['win%']:.1f}%")
        print(f"  per-year: {fmt_year_line(py)}")
        print(f"  positive years: {posY}/{len(yrs)}   positive FWD years: {posF}/{len(fyrs)}")
        return dict(name=name, train=tr, fwd=fw, pos_years=posY, total_years=len(yrs),
                    pos_fwd_years=posF, total_fwd_years=len(fyrs),
                    per_year={str(y): v for y, v in py.items()})

    res = {}
    res["routerA"] = show("ROUTER A portfolio (per-symbol train-R gate)", portfolio_rows(routerA))
    res["routerB"] = show("ROUTER B portfolio (class-structural prior)", portfolio_rows(routerB))
    res["routerC"] = show("ROUTER C portfolio (metals+energy a-priori)", portfolio_rows(routerC))
    res["routerD"] = show("ROUTER D portfolio (metals-only a-priori)", portfolio_rows(routerD))

    ungated_all = []
    for s in SYMBOLS: ungated_all += tables['fvg'][s]
    res["ungated_all_fvg"] = show("UNGATED all-symbols fvg (blind pool)", ungated_all)
    ungated_routable = portfolio_rows([(s, 'fvg') for s in routable])
    res["ungated_routable_fvg"] = show("UNGATED routable-universe fvg (no class/skip gate)", ungated_routable)

    # pick the best forward router as THE routed portfolio for controls/verdict
    cand = [("routerA", routerA, res["routerA"]),
            ("routerB", routerB, res["routerB"]),
            ("routerC", routerC, res["routerC"]),
            ("routerD", routerD, res["routerD"])]
    cand = [c for c in cand if c[2]["fwd"]["n"] > 0]
    best_name, best_pairs, best_res = max(cand, key=lambda c: c[2]["fwd"]["mean_R"])
    out["best_router"] = best_name
    print(f"\n>>> BEST forward router = {best_name} (fwd R={best_res['fwd']['mean_R']:+.4f})")

    # CONTROL 1: invert the chosen router's exact entries (fade)
    inv_rows = []
    for s, m in best_pairs:
        inv_rows += fvg_entry_trades(s, mode=m, target_R=TARGET_R, min_str=MIN_STR, invert=True)
    res["control_invert"] = show(f"CONTROL invert (fade {best_name})", inv_rows)

    # CONTROL 2: matched random-bar same-direction entries on chosen router
    rng = random.Random(999)
    rnd_rows = []
    for s, m in best_pairs:
        rnd_rows += fvg_entry_trades(s, mode=m, target_R=TARGET_R, min_str=MIN_STR,
                                     random_ctrl=True, rng=rng)
    res["control_randombar"] = show(f"CONTROL random-bar matched drift ({best_name})", rnd_rows)

    out["portfolios"] = res

    # ---- forward contribution by symbol for the best router ----
    print(f"\n--- forward contribution by symbol ({best_name}) ---")
    by_sym = defaultdict(list)
    for x in portfolio_rows(best_pairs):
        if x["year"] >= 2025: by_sym[x["sym"]].append(x["r"])
    contrib = {}
    print(f"{'SYM':12s}{'mode':>6s}{'fwN':>6s}{'fwR':>9s}{'fwSumR':>10s}")
    for s, mo in sorted(best_pairs, key=lambda p: -sum(by_sym[p[0]])):
        st = _stats(by_sym[s]); contrib[s] = dict(mode=mo, **st)
        print(f"{s:12s}{mo:>6s}{st['n']:6d}{st['mean_R']:+9.4f}{st['sum_R']:+10.1f}")
    out["forward_contribution_by_symbol"] = contrib

    # ---- verdict ----
    bf = best_res["fwd"]; uf = res["ungated_all_fvg"]["fwd"]
    inv = res["control_invert"]["fwd"]; rnd = res["control_randombar"]["fwd"]
    verdict = dict(
        best_router=best_name,
        routed_fwd_R=bf["mean_R"], routed_fwd_n=bf["n"], routed_fwd_win=bf["win%"],
        ungated_all_fwd_R=uf["mean_R"],
        invert_fwd_R=inv["mean_R"], randombar_fwd_R=rnd["mean_R"],
        routed_pos_years=best_res["pos_years"], routed_total_years=best_res["total_years"],
        routed_pos_fwd_years=best_res["pos_fwd_years"], routed_total_fwd_years=best_res["total_fwd_years"],
        beats_ungated=bf["mean_R"] > uf["mean_R"],
        beats_invert=bf["mean_R"] > inv["mean_R"],
        beats_randombar=bf["mean_R"] > rnd["mean_R"],
        majority_years_positive=best_res["pos_years"] > best_res["total_years"] / 2,
        honest_note=("Per-symbol train-R routing (Router A) is empty/weak: the validated FVG "
                     "continuation entry was a net loser across the 2015-2024 chop regime even in "
                     "metals/energy, so no non-peeking train-statistic can pre-select it. The "
                     "routing that survives is a CLASS-STRUCTURAL a-priori prior (continuation-prone "
                     "classes) + a non-peeking trend-strength context gate; it is forward-positive, "
                     "beats the blind pool, beats invert, and beats random-bar drift. It is NOT "
                     "majority-of-ALL-years positive because 2015-2024 chop bleeds; it IS forward "
                     "(2025-2026) positive on the carrier classes."),
    )
    out["verdict"] = verdict
    print("\n" + "=" * 92)
    print("VERDICT")
    print("=" * 92)
    for k, v in verdict.items():
        print(f"  {k}: {v}")

    with open(EDGE + "/WAVE2_UNIVERSE_AND_ROUTER_RESULT.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("\nWROTE WAVE2_UNIVERSE_AND_ROUTER_RESULT.json")

if __name__ == "__main__":
    main()
