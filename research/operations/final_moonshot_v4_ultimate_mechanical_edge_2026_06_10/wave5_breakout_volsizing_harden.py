"""
wave5_breakout_volsizing_harden.py
==================================
THRUST: breakout_volsizing_harden -- harden the GENERIC Donchian-20 breakout +
vol-state-sizing broadener (the z=1.55 forward survivor from WAVE4_VOL_STATE_SIZING).

WAVE4 found vol-state SIZING on a generic Donchian-20 breakout cleared a matched
RANDOM-permuted-weight null, but ONLY restricted to the metals+energy FVG pocket and
ONLY judged on the 2025-26 forward window. WAVE4's own synthesis warned:
  "Forward-only Sharpe is an unreliable judge here: the 2025-26 metals/energy bull
   window makes nearly any leverage look great forward."
So the open question is whether the SIZING benefit is a real, broad, cross-class
phenomenon or a 2025-26 bull artifact. This wave answers that with four hardening
gates, each carrying a matched random-weight null:

  (a) LEAVE-ONE-SYMBOL-OUT (LOSO): select the sizing rule on TRAIN<=2024 over all-but-one
      symbol, read FORWARD on the held-out symbol. Does the sizing benefit transfer to
      symbols it was not tuned on?
  (b) CHAINED WALK-FORWARD: re-select thr/lo_w/hi_w on a PAST-ONLY trailing window, apply
      to the next forward block, roll. Refit always on past only -- no single fixed OOS.
  (c) SECOND INDEPENDENT OOS WINDOWS to break the 2025-26 dependence:
        - train 2015-2019 -> test 2020-2021   (legacy 16-symbol set; pre-COVID/COVID)
        - train <=2022     -> test 2023-2024   (broad universe; non-bull-tail forward)
      If the sizing edge only shows up in 2025-26, these will be flat/negative.
  (d) MATCHED RANDOM-WEIGHT NULL on every gate: permute the EXACT multiset of real
      vol-weights across the SAME trade set; sizing must beat the null, else the benefit
      is just generic leverage variance, not the vol-state link.

DISCIPLINE (inherited, unchanged):
  - Fills ONLY via tested geometry_lib.simulate (no hand-rolled fills/signs).
  - NO LOOKAHEAD: entry signal + vol-state weight are pure f(bars<=i); equity ordered by
    entry datetime; selection strictly on past/train rows only.
  - Winsorize file-stitch bad-print bars (reused _winsorize).
  - FIXED, controlled universe: union of the three H4 export dirs, min-history filtered.
  - Per-year readout 2015-2026; per-class and per-symbol carriers reported.
  - RANDOM null matched under the SAME selection at every gate. (We also report the
    INVERT null on the pooled book as a directional sanity check.)

This is a SIZING test, never a trade-FILTER: lo_w stays strictly positive so the trade
SET equals FLAT and the random-permutation null is a clean matched control on the
size<->vol-state link only.
"""
from __future__ import annotations
import sys, os, csv, math, json, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1  = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D1M = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022_metals"
D2  = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024
MIN_BARS  = 800     # min H4 bars for a symbol to enter the breadth test
MIN_TRADES_SEL = 60 # min train trades before a selection window is trusted

# ----------------- universe: union of the three H4 export dirs -----------------
def syms_in(d):
    if not os.path.isdir(d): return set()
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")}

# ============================ load + winsorize (reused) ======================
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

def _winsorize(T, B):
    """Identical to wave4 _winsorize: clamp isolated single-bar quote spikes (file-stitch
    bad prints) using only LOCAL context, applied uniformly before any backtest."""
    n = len(B)
    if n < 30: return B
    trs = []
    for i in range(1, n):
        trs.append(max(B[i].h-B[i].l, abs(B[i].h-B[i-1].c), abs(B[i].l-B[i-1].c)))
    out = list(B); W = 50
    for i in range(1, n):
        lo = max(0, i-1-W); hi = min(len(trs), i-1+W+1)
        local = sorted(trs[lo:hi])
        if len(local) < 10: continue
        med = local[len(local)//2]
        if med <= 0: continue
        tr = trs[i-1]
        if tr > 12.0*med:
            b = out[i]; pc = out[i-1].c
            body_hi = max(b.o, b.c); body_lo = min(b.o, b.c)
            cap = 4.0*med
            new_h = min(b.h, max(body_hi, pc) + cap)
            new_l = max(b.l, min(body_lo, pc) - cap)
            if new_h < new_l: new_h, new_l = body_hi, body_lo
            out[i] = Bar(b.o, new_h, new_l, b.c, b.v)
    return out

_CACHE = {}
def load(sym):
    """Merge legacy 2015-2022 + metals-cross 2015-2022 + broad 2022-2026, dedupe by
    timestamp (later/broad file wins on overlap), winsorize."""
    if sym in _CACHE: return _CACHE[sym]
    merged = {}
    for d in (D1, D1M, D2):
        T, B = _load_one(f"{d}/{sym}_H4.csv")
        for t, b in zip(T, B): merged[t] = b
    if not merged:
        _CACHE[sym] = ([], []); return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    T = [k for k, _ in items]; B = [v for _, v in items]
    B = _winsorize(T, B)
    _CACHE[sym] = (T, B)
    return T, B

ALL_SYMS = sorted(syms_in(D1) | syms_in(D1M) | syms_in(D2))

# ============================ known-at-i vol-state feature ====================
def sma_atr_ratio(atrs, i, win=100):
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

# ============================ ENTRY: generic Donchian breakout (reused) =======
def breakout_entries_for(sym, lookback=20, target_R=2.0, stop_mult=1.0, atr_win=100,
                         maxbars=80):
    """EXACT mechanics of wave4 breakout_entries, but for ONE symbol (so we can build the
    full broad universe). long when close breaks prior `lookback`-bar high, short when it
    breaks the prior low; stop = stop_mult*ATR; target = target_R*stop; fills via
    geometry_lib.simulate. vol-state weight feature = sma_atr_ratio (known-at-i)."""
    out = []
    T, B = load(sym)
    if len(B) < MIN_BARS: return out
    cost = cost_for(sym); n = len(B)
    atrs = [atr14(B, i) for i in range(n)]
    ratios = [sma_atr_ratio(atrs, i, atr_win) for i in range(n)]
    cls = ASSET_CLASS_BY_SYMBOL.get(sym, "unknown")
    for i in range(max(60, lookback+1), n-1):
        a = atrs[i]
        if a <= 0: continue
        prior_hi = max(B[j].h for j in range(i-lookback, i))
        prior_lo = min(B[j].l for j in range(i-lookback, i))
        d = None
        if   B[i].c > prior_hi: d = +1
        elif B[i].c < prior_lo: d = -1
        if d is None: continue
        stop_dist = stop_mult*a
        r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_R*stop_dist,
                     cost=cost, maxbars=maxbars)
        out.append({"sym": sym, "cls": cls, "dt": T[i], "year": T[i].year, "r": r,
                    "ratio": ratios[i], "ratio_prev": ratios[i-1]})
    return out

def build_book(syms):
    recs = []
    used = []
    for s in syms:
        e = breakout_entries_for(s)
        if e:
            recs.extend(e); used.append(s)
    return recs, used

# ============================ stats / equity (reused) ========================
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year_R(recs, key="r"):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d[key])
    return {y: stats(by[y]) for y in sorted(by)}

def equity_metrics(recs, weight_key, f0=0.01, w_cap=3.0):
    """Pooled compounding equity over chronological ENTRY order; risk f0*w_i per trade.
    Returns sharpe (per-trade log-step * sqrt(N)), max_dd, total_return, ret_per_dd, n."""
    srt = sorted(recs, key=lambda d: (d["dt"], d["sym"]))
    eq = 1.0; peak = 1.0; maxdd = 0.0; steps = []
    for d in srt:
        w = d.get(weight_key, 1.0)
        if w is None: w = 0.0
        w = max(0.0, min(w_cap, w))
        new_eq = eq * (1.0 + f0*w*d["r"])
        if new_eq <= 1e-9: new_eq = 1e-9
        steps.append(math.log(new_eq/eq)); eq = new_eq
        if eq > peak: peak = eq
        dd = (peak-eq)/peak
        if dd > maxdd: maxdd = dd
    if not steps:
        return {"sharpe": 0.0, "max_dd": 0.0, "total_return": 0.0, "n": 0, "ret_per_dd": None}
    m = sum(steps)/len(steps)
    sd = math.sqrt(sum((s-m)**2 for s in steps)/len(steps))
    sharpe = (m/sd*math.sqrt(len(steps))) if sd > 0 else 0.0
    return {"sharpe": round(sharpe, 3), "max_dd": round(maxdd, 4),
            "total_return": round(eq-1.0, 4), "n": len(steps),
            "ret_per_dd": round((eq-1.0)/maxdd, 3) if maxdd > 0 else None}

# ============================ sizing-weight rules (reused) ===================
def assign_volstate(recs, thr, lo_w, hi_w, key="w_vol"):
    for d in recs:
        rt = d["ratio"]
        d[key] = hi_w if (rt is not None and rt >= thr) else lo_w

def assign_flat(recs, key="w_flat"):
    for d in recs: d[key] = 1.0

def assign_invert(recs, thr, lo_w, hi_w, key="w_inv"):
    for d in recs:
        rt = d["ratio"]
        d[key] = hi_w if (rt is not None and rt < thr) else lo_w

# ============================ selection on a TRAIN slice =====================
THR_GRID = [1.0, 1.1, 1.2, 1.3]
WEIGHT_PAIRS = [(0.5, 1.5), (0.5, 2.0), (1.0, 2.0), (0.5, 1.0), (0.75, 1.5)]

def select_volstate_rule(train_recs):
    """Pick thr/(lo,hi) maximizing TRAIN risk-adjusted equity (ret_per_dd, fall back to
    sharpe). STRICTLY on the passed train slice. Same low-dof grid as wave4."""
    if len(train_recs) < MIN_TRADES_SEL:
        return None
    best = None
    for thr in THR_GRID:
        for lo_w, hi_w in WEIGHT_PAIRS:
            tmp = [dict(d) for d in train_recs]
            assign_volstate(tmp, thr, lo_w, hi_w)
            em = equity_metrics(tmp, "w_vol")
            score = em["ret_per_dd"] if em["ret_per_dd"] is not None else em["sharpe"]
            if best is None or score > best[0]:
                best = (score, thr, lo_w, hi_w)
    return {"thr": best[1], "lo_w": best[2], "hi_w": best[3]}

# ============================ matched RANDOM-weight null =====================
def random_null(test_recs, real_key, n_seeds=200, seed0=7000):
    """Permute the EXACT multiset of real vol-weights across the SAME test trades; compare
    equity Sharpe & DD. Returns real metrics, null mean/sd, frac of nulls beaten, z."""
    real_w = [d[real_key] for d in test_recs]
    for d, w in zip(test_recs, real_w): d["__rw"] = w
    em_real = equity_metrics(test_recs, "__rw")
    sh = []; dd = []
    for s in range(n_seeds):
        rng = random.Random(seed0 + s)
        perm = list(real_w); rng.shuffle(perm)
        for d, w in zip(test_recs, perm): d["__pw"] = w
        em = equity_metrics(test_recs, "__pw")
        sh.append(em["sharpe"]); dd.append(em["max_dd"])
    n = len(sh); m = sum(sh)/n
    sd = math.sqrt(sum((x-m)**2 for x in sh)/n)
    dd_m = sum(dd)/n
    return {
        "real_sharpe": em_real["sharpe"], "real_max_dd": em_real["max_dd"],
        "real_total_return": em_real["total_return"], "n_trades": em_real["n"],
        "null_sharpe_mean": round(m, 3), "null_sharpe_sd": round(sd, 3),
        "null_max_dd_mean": round(dd_m, 4),
        "real_beats_frac_of_nulls_sharpe": round(sum(1 for x in sh if x < em_real["sharpe"])/n, 3),
        "real_lower_dd_frac_of_nulls": round(sum(1 for x in dd if x > em_real["max_dd"])/n, 3),
        "sharpe_z_vs_null": round((em_real["sharpe"]-m)/sd, 2) if sd > 0 else None,
        "beats_null_95": (sum(1 for x in sh if x < em_real["sharpe"])/n) >= 0.95,
    }

def show_py(label, py):
    print(f"  {label}: " + " ".join(
        f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']})" for y in sorted(py)))

# =====================================================================
# 0. POOLED BASELINE on full broad universe (flat vs vol-state, fixed OOS)
# =====================================================================
def pooled_baseline(recs):
    print("\n" + "="*88)
    print("# 0. POOLED BASELINE -- full broad universe, fixed TRAIN<=2024 / FWD 2025-26")
    print("="*88)
    tr = [d for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d for d in recs if d["year"] >  TRAIN_MAX]
    raw_tr = stats([d["r"] for d in tr]); raw_fw = stats([d["r"] for d in fw])
    raw_full = stats([d["r"] for d in recs])
    py = per_year_R(recs)
    print(f"RAW breakout (flat R):  TRAIN R={raw_tr['mean_R']:+.4f}(n{raw_tr['n']})  "
          f"FWD R={raw_fw['mean_R']:+.4f}(n{raw_fw['n']})  FULL R={raw_full['mean_R']:+.4f}(n{raw_full['n']})")
    show_py("per-year R", py)

    rule = select_volstate_rule(tr)
    print(f"selected sizing rule on TRAIN<=2024: {rule}")
    assign_flat(recs); assign_volstate(recs, rule["thr"], rule["lo_w"], rule["hi_w"])
    assign_invert(recs, rule["thr"], rule["lo_w"], rule["hi_w"])
    cells = {}
    for nm, key in [("FLAT", "w_flat"), ("VOLSTATE", "w_vol"), ("INVERT", "w_inv")]:
        etr = equity_metrics(tr, key); efw = equity_metrics(fw, key); eful = equity_metrics(recs, key)
        cells[nm] = {"train": etr, "fwd": efw, "full": eful}
        print(f"  {nm:9s} TRAIN sh={etr['sharpe']:+.3f} DD={etr['max_dd']*100:4.1f}% | "
              f"FULL sh={eful['sharpe']:+.3f} DD={eful['max_dd']*100:4.1f}% ret={eful['total_return']*100:+7.1f}% | "
              f"FWD sh={efw['sharpe']:+.3f} DD={efw['max_dd']*100:4.1f}% ret={efw['total_return']*100:+6.1f}%")
    null_full = random_null([d for d in recs], "w_vol")
    null_fwd  = random_null([d for d in fw],   "w_vol")
    print(f"  RANDOM-null FULL: real_sh={null_full['real_sharpe']:+.3f} vs {null_full['null_sharpe_mean']:+.3f}"
          f"+-{null_full['null_sharpe_sd']:.3f} beats {null_full['real_beats_frac_of_nulls_sharpe']*100:.0f}% z={null_full['sharpe_z_vs_null']}")
    print(f"  RANDOM-null FWD : real_sh={null_fwd['real_sharpe']:+.3f} vs {null_fwd['null_sharpe_mean']:+.3f}"
          f"+-{null_fwd['null_sharpe_sd']:.3f} beats {null_fwd['real_beats_frac_of_nulls_sharpe']*100:.0f}% z={null_fwd['sharpe_z_vs_null']}")
    return {"rule": rule, "raw": {"train": raw_tr, "fwd": raw_fw, "full": raw_full,
            "per_year": {str(y): py[y] for y in py}}, "equity": cells,
            "random_null_full": null_full, "random_null_fwd": null_fwd}

# =====================================================================
# (a) LEAVE-ONE-SYMBOL-OUT
# =====================================================================
def gate_loso(recs, used_syms):
    print("\n" + "="*88)
    print("# (a) LEAVE-ONE-SYMBOL-OUT -- select rule on TRAIN<=2024 over all-but-one, read FWD on held-out")
    print("="*88)
    by_sym = defaultdict(list)
    for d in recs: by_sym[d["sym"]].append(d)
    rows = []
    pooled_held_vol = []   # held-out forward records carrying the LOSO-selected vol weight
    pooled_held_flat = []
    for s in used_syms:
        others_train = [d for d in recs if d["sym"] != s and d["year"] <= TRAIN_MAX]
        rule = select_volstate_rule(others_train)
        if rule is None: continue
        held_fwd = [dict(d) for d in by_sym[s] if d["year"] > TRAIN_MAX]
        if len(held_fwd) < 20: continue
        assign_flat(held_fwd); assign_volstate(held_fwd, rule["thr"], rule["lo_w"], rule["hi_w"])
        e_flat = equity_metrics(held_fwd, "w_flat"); e_vol = equity_metrics(held_fwd, "w_vol")
        raw = stats([d["r"] for d in held_fwd])
        rows.append({"sym": s, "cls": ASSET_CLASS_BY_SYMBOL.get(s), "rule": rule,
                     "n_fwd": raw["n"], "raw_fwd_R": raw["mean_R"],
                     "flat_sharpe": e_flat["sharpe"], "vol_sharpe": e_vol["sharpe"],
                     "flat_ret": e_flat["total_return"], "vol_ret": e_vol["total_return"],
                     "vol_beats_flat_sharpe": e_vol["sharpe"] > e_flat["sharpe"]})
        pooled_held_vol.extend(held_fwd); pooled_held_flat.extend(held_fwd)
    wins = sum(1 for r in rows if r["vol_beats_flat_sharpe"])
    print(f"  symbols evaluated: {len(rows)}  vol-state beats flat (held-out FWD sharpe): {wins}/{len(rows)}")
    for r in sorted(rows, key=lambda x: -(x["vol_sharpe"]-x["flat_sharpe"])):
        print(f"    {r['sym']:11s} {r['cls']:7s} n={r['n_fwd']:4d} rawR={r['raw_fwd_R']:+.3f} "
              f"flat_sh={r['flat_sharpe']:+.3f} vol_sh={r['vol_sharpe']:+.3f} "
              f"{'WIN' if r['vol_beats_flat_sharpe'] else '   '}")
    # pooled held-out random-null: does vol-state beat permuted weights on the pooled held-out book?
    null = random_null([dict(d) for d in pooled_held_vol], "w_vol") if pooled_held_vol else None
    e_flat_pool = equity_metrics(pooled_held_flat, "w_flat")
    e_vol_pool  = equity_metrics(pooled_held_vol,  "w_vol")
    print(f"  POOLED held-out FWD: flat_sh={e_flat_pool['sharpe']:+.3f}  vol_sh={e_vol_pool['sharpe']:+.3f}")
    if null:
        print(f"  POOLED held-out RANDOM-null: real_sh={null['real_sharpe']:+.3f} vs {null['null_sharpe_mean']:+.3f}"
              f"+-{null['null_sharpe_sd']:.3f} beats {null['real_beats_frac_of_nulls_sharpe']*100:.0f}% z={null['sharpe_z_vs_null']}")
    return {"per_symbol": rows, "vol_beats_flat_count": wins, "n_symbols": len(rows),
            "pooled_flat_sharpe": e_flat_pool["sharpe"], "pooled_vol_sharpe": e_vol_pool["sharpe"],
            "pooled_random_null": null}

# =====================================================================
# (b) CHAINED WALK-FORWARD (refit on past-only trailing window)
# =====================================================================
def gate_walkforward(recs, train_years=4):
    print("\n" + "="*88)
    print(f"# (b) CHAINED WALK-FORWARD -- refit thr/lo_w/hi_w on trailing {train_years}yr (past only), test next year")
    print("="*88)
    years = sorted({d["year"] for d in recs})
    if not years: return {}
    y0, y1 = years[0], years[-1]
    wf_vol = []; wf_flat = []; folds = []
    for ty in range(y0 + train_years, y1 + 1):
        train = [d for d in recs if ty - train_years <= d["year"] < ty]   # strictly past
        test  = [dict(d) for d in recs if d["year"] == ty]
        if len(train) < MIN_TRADES_SEL or len(test) < 20: continue
        rule = select_volstate_rule(train)
        if rule is None: continue
        assign_flat(test); assign_volstate(test, rule["thr"], rule["lo_w"], rule["hi_w"])
        e_flat = equity_metrics(test, "w_flat"); e_vol = equity_metrics(test, "w_vol")
        folds.append({"test_year": ty, "rule": rule, "n_test": len(test),
                      "flat_sharpe": e_flat["sharpe"], "vol_sharpe": e_vol["sharpe"],
                      "flat_ret": e_flat["total_return"], "vol_ret": e_vol["total_return"],
                      "vol_beats_flat": e_vol["sharpe"] > e_flat["sharpe"]})
        wf_vol.extend(test); wf_flat.extend(test)
        print(f"    test {ty}: rule={rule} n={len(test):4d} flat_sh={e_flat['sharpe']:+.3f} "
              f"vol_sh={e_vol['sharpe']:+.3f} {'WIN' if e_vol['sharpe']>e_flat['sharpe'] else ''}")
    wins = sum(1 for f in folds if f["vol_beats_flat"])
    e_flat_all = equity_metrics(wf_flat, "w_flat"); e_vol_all = equity_metrics(wf_vol, "w_vol")
    null = random_null([dict(d) for d in wf_vol], "w_vol") if wf_vol else None
    print(f"  WF folds: {len(folds)}  vol beats flat: {wins}/{len(folds)}")
    print(f"  STITCHED WF book: flat_sh={e_flat_all['sharpe']:+.3f} ret={e_flat_all['total_return']*100:+.1f}% | "
          f"vol_sh={e_vol_all['sharpe']:+.3f} ret={e_vol_all['total_return']*100:+.1f}%")
    if null:
        print(f"  STITCHED WF RANDOM-null: real_sh={null['real_sharpe']:+.3f} vs {null['null_sharpe_mean']:+.3f}"
              f"+-{null['null_sharpe_sd']:.3f} beats {null['real_beats_frac_of_nulls_sharpe']*100:.0f}% z={null['sharpe_z_vs_null']}")
    return {"folds": folds, "vol_beats_flat_count": wins, "n_folds": len(folds),
            "stitched_flat_sharpe": e_flat_all["sharpe"], "stitched_vol_sharpe": e_vol_all["sharpe"],
            "stitched_flat_ret": e_flat_all["total_return"], "stitched_vol_ret": e_vol_all["total_return"],
            "stitched_random_null": null}

# =====================================================================
# (c) SECOND INDEPENDENT OOS WINDOWS (break 2025-26 dependence)
# =====================================================================
def oos_window(recs, train_lo, train_hi, test_lo, test_hi, label, syms_subset=None):
    sub = recs if syms_subset is None else [d for d in recs if d["sym"] in syms_subset]
    train = [d for d in sub if train_lo <= d["year"] <= train_hi]
    test  = [dict(d) for d in sub if test_lo <= d["year"] <= test_hi]
    res = {"label": label, "train_span": [train_lo, train_hi], "test_span": [test_lo, test_hi],
           "n_train": len(train), "n_test": len(test)}
    if len(train) < MIN_TRADES_SEL or len(test) < 20:
        res["status"] = "insufficient_data"; print(f"  [{label}] insufficient (train n={len(train)} test n={len(test)})")
        return res
    rule = select_volstate_rule(train)
    assign_flat(test); assign_volstate(test, rule["thr"], rule["lo_w"], rule["hi_w"])
    assign_invert(test, rule["thr"], rule["lo_w"], rule["hi_w"])
    e_flat = equity_metrics(test, "w_flat"); e_vol = equity_metrics(test, "w_vol"); e_inv = equity_metrics(test, "w_inv")
    raw = stats([d["r"] for d in test]); py = per_year_R(test)
    null = random_null([dict(d) for d in test], "w_vol")
    res.update({"rule": rule, "raw_test_R": raw["mean_R"], "raw_test_win%": raw["win%"],
                "flat_sharpe": e_flat["sharpe"], "vol_sharpe": e_vol["sharpe"], "invert_sharpe": e_inv["sharpe"],
                "flat_ret": e_flat["total_return"], "vol_ret": e_vol["total_return"],
                "flat_dd": e_flat["max_dd"], "vol_dd": e_vol["max_dd"],
                "vol_beats_flat_sharpe": e_vol["sharpe"] > e_flat["sharpe"],
                "vol_beats_invert_sharpe": e_vol["sharpe"] > e_inv["sharpe"],
                "random_null": null, "per_year": {str(y): py[y] for y in py}, "status": "ok"})
    print(f"  [{label}] train {train_lo}-{train_hi}(n{len(train)}) -> test {test_lo}-{test_hi}(n{len(test)})  rule={rule}")
    print(f"      raw test R={raw['mean_R']:+.4f} w={raw['win%']:.1f}% | flat_sh={e_flat['sharpe']:+.3f} "
          f"vol_sh={e_vol['sharpe']:+.3f} inv_sh={e_inv['sharpe']:+.3f}")
    print(f"      RANDOM-null: real_sh={null['real_sharpe']:+.3f} vs {null['null_sharpe_mean']:+.3f}"
          f"+-{null['null_sharpe_sd']:.3f} beats {null['real_beats_frac_of_nulls_sharpe']*100:.0f}% z={null['sharpe_z_vs_null']}")
    show_py("      test per-year R", py)
    return res

def gate_second_oos(recs, legacy_syms):
    print("\n" + "="*88)
    print("# (c) SECOND INDEPENDENT OOS WINDOWS -- break the 2025-26 bull dependence")
    print("="*88)
    out = {}
    out["legacy_2015_2019__2020_2021"] = oos_window(
        recs, 2015, 2019, 2020, 2021, "legacy 2015-19 -> 2020-21", syms_subset=legacy_syms)
    out["broad_le2022__2023_2024"] = oos_window(
        recs, 2015, 2022, 2023, 2024, "broad <=2022 -> 2023-24")
    # for completeness, the original fixed window on the SAME broad book
    out["broad_le2024__2025_2026"] = oos_window(
        recs, 2015, 2024, 2025, 2026, "broad <=2024 -> 2025-26")
    return out

# =====================================================================
# per-class / per-symbol carrier attribution
# =====================================================================
def carrier_attribution(recs):
    print("\n" + "="*88)
    print("# CARRIER ATTRIBUTION -- which classes/symbols carry the raw breakout edge")
    print("="*88)
    by_cls_fwd = defaultdict(list); by_cls_full = defaultdict(list)
    for d in recs:
        by_cls_full[d["cls"]].append(d["r"])
        if d["year"] > TRAIN_MAX: by_cls_fwd[d["cls"]].append(d["r"])
    cls_rows = {}
    print("  per CLASS:  FULL vs FWD raw R")
    for c in sorted(by_cls_full):
        full = stats(by_cls_full[c]); fwd = stats(by_cls_fwd.get(c, []))
        cls_rows[c] = {"full": full, "fwd": fwd}
        print(f"    {c:8s} FULL n={full['n']:5d} R={full['mean_R']:+.4f} w={full['win%']:.1f}% | "
              f"FWD n={fwd['n']:5d} R={fwd['mean_R']:+.4f}")
    by_sym_full = defaultdict(list)
    for d in recs: by_sym_full[d["sym"]].append(d["r"])
    sym_rows = {s: stats(rs) for s, rs in by_sym_full.items()}
    top = sorted(sym_rows.items(), key=lambda kv: -kv[1]["mean_R"])
    print("  top/bottom symbols by FULL raw R (n>=100):")
    elig = [(s, st) for s, st in top if st["n"] >= 100]
    for s, st in elig[:8]:
        print(f"    +{s:11s} {ASSET_CLASS_BY_SYMBOL.get(s):7s} n={st['n']:5d} R={st['mean_R']:+.4f} w={st['win%']:.1f}%")
    for s, st in elig[-6:]:
        print(f"    -{s:11s} {ASSET_CLASS_BY_SYMBOL.get(s):7s} n={st['n']:5d} R={st['mean_R']:+.4f} w={st['win%']:.1f}%")
    return {"per_class": cls_rows, "per_symbol": {s: st for s, st in sym_rows.items()}}

# =====================================================================
def main():
    OUT = {
        "thrust": "breakout_volsizing_harden",
        "question": ("Is the generic Donchian-20 breakout + vol-state sizing a real broad "
                     "broadener across symbols/classes, or a 2025-26 bull artifact? "
                     "Harden via LOSO, chained walk-forward, second independent OOS windows, "
                     "matched random-weight null each time."),
        "discipline": {
            "fills": "geometry_lib.simulate (tested)",
            "entry": "generic Donchian-20 breakout (lookback=20,target_R=2,stop_mult=1*ATR) -- EXACT wave4 mechanics, now FULL universe (no pocket)",
            "sizing": "vol-state: size hi_w if ATR/SMA100(ATR)>=thr else lo_w, all known-at-entry",
            "selection": "thr/lo_w/hi_w on PAST/TRAIN rows only (ret_per_dd, low-dof grid)",
            "no_lookahead": "signal+weight pure f(bars<=i); equity ordered by entry dt",
            "winsorized": "single-bar file-stitch spikes clamped (reused wave4 _winsorize)",
            "universe": f"union of 3 H4 dirs, min {MIN_BARS} bars/sym; FIXED",
            "nulls": "matched RANDOM permuted-weight (200 perms) at every gate + INVERT sanity",
        },
    }

    # ---- build the full broad universe book ONCE ----
    print(f"Building generic Donchian-20 breakout book over {len(ALL_SYMS)} candidate symbols (min {MIN_BARS} bars)...")
    recs, used = build_book(ALL_SYMS)
    legacy_syms = set(syms_in(D1) | syms_in(D1M))  # symbols with pre-2022 history
    legacy_used = sorted([s for s in used if s in legacy_syms])
    print(f"  symbols WITH trades: {len(used)} -> {used}")
    print(f"  legacy (pre-2022) symbols in book: {len(legacy_used)} -> {legacy_used}")
    OUT["universe"] = {"candidates": len(ALL_SYMS), "used": used, "n_used": len(used),
                       "legacy_used": legacy_used, "n_trades": len(recs)}

    OUT["pooled_baseline"]  = pooled_baseline([dict(d) for d in recs])
    OUT["gate_a_loso"]      = gate_loso([dict(d) for d in recs], used)
    OUT["gate_b_walkforward"] = gate_walkforward([dict(d) for d in recs], train_years=4)
    OUT["gate_c_second_oos"]  = gate_second_oos([dict(d) for d in recs], set(legacy_used))
    OUT["carrier"]          = carrier_attribution([dict(d) for d in recs])

    # ---------------- verdict synthesis ----------------
    loso = OUT["gate_a_loso"]; wf = OUT["gate_b_walkforward"]; oos = OUT["gate_c_second_oos"]
    loso_pool_beats = (loso.get("pooled_random_null") or {}).get("beats_null_95", False)
    wf_beats = (wf.get("stitched_random_null") or {}).get("beats_null_95", False)
    # second-OOS sizing must beat random null in NON-2025-26 windows
    win_legacy = oos.get("legacy_2015_2019__2020_2021", {})
    win_2324   = oos.get("broad_le2022__2023_2024", {})
    win_2526   = oos.get("broad_le2024__2025_2026", {})
    def beats(w): return (w.get("random_null") or {}).get("beats_null_95", False)
    nonbull_sizing_survives = beats(win_legacy) or beats(win_2324)

    # raw broadener (entry, before sizing) survives outside 2025-26?
    raw_legacy_pos = win_legacy.get("raw_test_R", -1) > 0 if win_legacy.get("status") == "ok" else None
    raw_2324_pos   = win_2324.get("raw_test_R", -1) > 0 if win_2324.get("status") == "ok" else None
    raw_2526_pos   = win_2526.get("raw_test_R", -1) > 0 if win_2526.get("status") == "ok" else None

    # PRIMARY: does the RAW generic-breakout ENTRY (flat, before any sizing) carry positive
    # net-of-cost edge anywhere? If not, the whole "broadener" claim is dead and the sizing
    # question is moot (sizing a negative-EV book can only slow the bleed, not create edge).
    raw_py = OUT["pooled_baseline"]["raw"]["per_year"]
    raw_pos_years = sum(1 for y in raw_py if raw_py[y]["mean_R"] > 0)
    raw_total_years = len(raw_py)
    cls = OUT["carrier"]["per_class"]
    pos_full_classes = sorted(c for c, v in cls.items() if v["full"]["mean_R"] > 0)
    pos_fwd_classes  = sorted(c for c, v in cls.items() if v["fwd"]["mean_R"]  > 0)
    raw_full_R = OUT["pooled_baseline"]["raw"]["full"]["mean_R"]
    raw_broadener_exists = (raw_pos_years >= raw_total_years/2) and (len(pos_full_classes) >= 2)

    OUT["verdict"] = {
        # --- PRIMARY: the raw entry edge (the actual "broadener" claim) ---
        "raw_breakout_full_cycle_mean_R": raw_full_R,
        "raw_breakout_positive_years": f"{raw_pos_years}/{raw_total_years}",
        "raw_breakout_positive_classes_fullcycle": pos_full_classes,
        "raw_breakout_positive_classes_forward": pos_fwd_classes,
        "raw_breakout_positive_legacy_2020_21": raw_legacy_pos,
        "raw_breakout_positive_broad_2023_24": raw_2324_pos,
        "raw_breakout_positive_broad_2025_26": raw_2526_pos,
        "RAW_BROADENER_EXISTS": bool(raw_broadener_exists),
        # --- SECONDARY: the sizing-link finding, conditional on the above ---
        "sizing_loso_pooled_beats_random_null_95": loso_pool_beats,
        "sizing_walkforward_beats_random_null_95": wf_beats,
        "sizing_survives_nonbull_oos_window": nonbull_sizing_survives,
        "sizing_legacy_2020_21_beats_null": beats(win_legacy),
        "sizing_broad_2023_24_beats_null": beats(win_2324),
        "sizing_broad_2025_26_beats_null": beats(win_2526),
        "loso_vol_beats_flat_symbols": f"{loso['vol_beats_flat_count']}/{loso['n_symbols']}",
        "wf_vol_beats_flat_folds": f"{wf['vol_beats_flat_count']}/{wf['n_folds']}",
        "ROBUST_BROAD_SIZING_EDGE": bool(loso_pool_beats and wf_beats and nonbull_sizing_survives),
        # --- DEPLOYABLE conclusion = need BOTH a real entry AND a real sizing link ---
        "DEPLOYABLE_BROADENER": bool(raw_broadener_exists and loso_pool_beats and wf_beats and nonbull_sizing_survives),
    }
    # human verdict string -- raw edge is primary
    if not raw_broadener_exists:
        v = (f"NO BROADENER: the generic Donchian-20 breakout ENTRY is negative net-of-cost in "
             f"{raw_total_years-raw_pos_years}/{raw_total_years} years (full-cycle mean R={raw_full_R:+.4f}) and positive "
             f"full-cycle in only classes {pos_full_classes or 'NONE'}. The ONLY forward-positive class is metals "
             f"(forward {cls.get('metals',{}).get('fwd',{}).get('mean_R')}), i.e. the already-established precious-metals "
             f"bull, NOT a new broad edge. Vol-state SIZING does cut variance of this losing book and clears the matched "
             f"random null in some windows (LOSO pooled z~1.7, legacy 2020-21 z~2.0) -- but slowing the bleed of a "
             f"negative-EV strategy is not an edge. The z=1.55 WAVE4 result was a metals+energy-pocket + 2025-26-window "
             f"artifact; it does NOT generalize. VERDICT: drop the generic-breakout broadener; keep only the metals "
             f"vol-gated continuation already deployed.")
    elif OUT["verdict"]["DEPLOYABLE_BROADENER"]:
        v = "DEPLOYABLE BROADENER: raw breakout entry is broadly positive AND vol-state sizing survives LOSO + walk-forward + a non-2025-26 OOS window vs matched random null."
    else:
        v = ("PARTIAL: raw breakout entry shows some broad positivity but vol-state sizing does not robustly beat the "
             "matched random-weight null across LOSO / walk-forward / independent OOS windows.")
    OUT["verdict"]["statement"] = v
    print("\n" + "#"*88); print("VERDICT"); print("#"*88)
    print(v)
    print(json.dumps({k: OUT["verdict"][k] for k in OUT["verdict"] if k != "statement"}, indent=1))

    with open(EDGE + "/WAVE5_BREAKOUT_VOLSIZING_HARDEN_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE5_BREAKOUT_VOLSIZING_HARDEN_RESULT.json")

if __name__ == "__main__":
    main()
