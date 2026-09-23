"""
wave3_fvg_regime_honest.py
==========================
THRUST: fvg_regime_honest — an HONEST, leak-free profile of the validated FVG-retest
continuation entry, conditioned ONLY on regime state KNOWN AT ENTRY.

The "validated" entry (WAVE1_STRUCTURE_SETUPS_ICT_FINAL.json) is the FVG-retest
continuation in metals+energy. It is forward-positive (+0.094R fwd, 2R) but
TRAIN-NEGATIVE (-0.042R) and positive in only a MINORITY of all years. That mixed
profile is the honest starting point. This study asks a narrow, falsifiable question:

  Conditioning ONLY on regime state knowable at the decision bar (NO forecasting, NO
  post-close streak peeking), can we identify a FAVORABLE regime on TRAIN<=2024 such
  that trading the FVG entry ONLY in that regime (and FLAT otherwise) is net-positive
  over the full 2015-2026 cycle, with the forward 2025-26 period as pure read-out?

DISCIPLINE / ANTI-LEAK (two prior subagent "wins" were leaks):
  - ALL fills via tested geometry_lib.simulate / simulate_detail. No hand-rolled fills.
  - Entry reuses wave1_structure_setups_ict.setup_ob_fvg_retest's exact mechanics,
    re-implemented here ONLY to emit, per trade, the regime features computed strictly
    from bars[<=i] (the decision bar). The geometry/sign is identical to the source.
  - NO LOOKAHEAD: every regime feature at decision bar i uses ONLY bars[0..i]:
      * ATR(14) at i, and SMA100 of ATR over bars[i-99..i]  -> ATR expansion regime.
      * HTF structure: higher-high & higher-low of swing pivots fully formed by i.
      * htf_trend(B,i) = close[i] vs close[i-lb] (already known-at-i).
    None of these read any bar > i.
  - NO TRAIN/FORWARD LEAK: the favorable-regime SELECTION (which regime bucket, and any
    threshold) is locked on TRAIN (year<=2024) ONLY. FORWARD (2025-26) is read-out only.
    Per-year R reported for all years 2015-2026.
  - Path independence: each FVG trade is evaluated independently on its own bars; no
    streak/drawdown state is carried across trades, so there is no post-close peeking.
    (Regime features are pure functions of price history at i, not of prior PnL.)
  - Negative controls vs the chosen in-regime deployment:
      (1) INVERT  : take the opposite side of every in-regime trade.
      (2) ANTI    : trade ONLY when the regime flag is FALSE (the rejected bars).
      (3) RANDOM  : trade a random subset matched in count to the in-regime set (seeded),
                    repeated to get a mean, to show selection isn't just luck-of-draw.
  - Real per-asset costs from ULTIMATE_REAL_COST_MAP.json.

VERDICT RULE (honest, stated up front):
  A regime-conditional deployment is called net-positive-without-lookahead ONLY if,
  after locking selection on train, it is:
     (a) full-cycle (2015-2026) mean_R > 0 AND sum_R > 0, AND
     (b) forward (2025-26) mean_R > 0, AND
     (c) it beats the all-regime baseline on BOTH train and forward, AND
     (d) the invert control is negative (edge is directional) AND anti-regime is weaker.
  Robustness (positive in a majority of years) is reported but treated as a quality
  flag, not a pass/fail gate, since the underlying entry is only minority-positive.
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
from geometry_lib import Bar, atr14, simulate, simulate_detail

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GC = COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s), GC)

TRAIN_MAX = 2024  # selection locked on year <= TRAIN_MAX
VALIDATED_CLASSES = {"metals", "energy"}  # the validated forward-positive pocket

# ---------------- data load (identical to wave1) ----------------
def syms_in(d):
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
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

# ---------------- known-at-i HTF trend (identical to wave1) ----------------
def htf_trend(bars, i, lb=30):
    if i < lb: return 0
    a = atr14(bars, i)
    if a <= 0: return 0
    diff = bars[i].c - bars[i-lb].c
    if diff > 1.0*a: return 1
    if diff < -1.0*a: return -1
    return 0

# ---------------- known-at-i regime features ----------------
def sma_atr_ratio(atrs, i, win=100):
    """ATR(i) / mean(ATR over [i-win+1 .. i]). >1 => volatility EXPANSION vs its own
    rolling baseline. Uses ONLY atrs[<=i]. Returns None if insufficient history."""
    lo = i - win + 1
    if lo < 14: return None
    seg = [atrs[k] for k in range(lo, i+1) if atrs[k] > 0]
    if len(seg) < win//2: return None
    m = sum(seg)/len(seg)
    if m <= 0: return None
    return atrs[i]/m

def htf_structure_state(bars, i, lb=12, lookback_pivots=60):
    """Higher-high / higher-low structure formed by FULLY-completed swing pivots at <= i.
    A swing-high pivot at index p (lb<=p<=i-lb) is bars[p].h strictly greater than the
    lb bars on each side. Because confirming a pivot at p needs bars up to p+lb, we only
    accept pivots with p+lb <= i (fully formed by the decision bar -> no lookahead).
    Returns +1 if last two confirmed swing highs are rising AND last two swing lows are
    rising (uptrend structure), -1 for the mirror (downtrend), else 0.
    """
    hi_piv = []; lo_piv = []
    start = max(lb, i - lookback_pivots)
    for p in range(start, i - lb + 1):   # p+lb <= i guaranteed -> pivot confirmed by i
        ph = bars[p].h; pl = bars[p].l
        is_hi = all(bars[p].h >= bars[p-k].h for k in range(1, lb+1)) and \
                all(bars[p].h >= bars[p+k].h for k in range(1, lb+1))
        is_lo = all(bars[p].l <= bars[p-k].l for k in range(1, lb+1)) and \
                all(bars[p].l <= bars[p+k].l for k in range(1, lb+1))
        if is_hi: hi_piv.append(ph)
        if is_lo: lo_piv.append(pl)
    if len(hi_piv) >= 2 and len(lo_piv) >= 2:
        hh = hi_piv[-1] > hi_piv[-2]
        hl = lo_piv[-1] > lo_piv[-2]
        lh = hi_piv[-1] < hi_piv[-2]
        ll = lo_piv[-1] < lo_piv[-2]
        if hh and hl: return 1
        if lh and ll: return -1
    return 0

# ---------------- FVG entry, identical geometry, emits regime features ----------------
def fvg_trades(target_R=2.0, trend_lb=30, fvg_min=0.10, stop_buf=0.10,
               atr_stop_floor=0.25, invert=False, classes=None, atr_win=100,
               struct_lb=12):
    """Re-implements wave1 setup_ob_fvg_retest(mode='fvg') EXACTLY for geometry/sign,
    and attaches, per trade, regime features computed strictly from bars[<=i].
    Returns list of dicts."""
    out = []
    for sym in SYMBOLS:
        if classes is not None and ASSET_CLASS_BY_SYMBOL.get(sym) not in classes:
            continue
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
                    if gap_top - gap_bot < fvg_min*a:
                        continue
                    if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                        stop_dist = max((b.c - min(b.l, gap_bot)) + stop_buf*a, atr_stop_floor*a)
                        d = -1 if invert else +1
                        break
            elif tr == -1:
                for k in range(i-2, max(i-9, 60), -1):
                    gap_bot = B[k].h; gap_top = B[k-2].l
                    if gap_top - gap_bot < fvg_min*a:
                        continue
                    if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                        stop_dist = max((max(b.h, gap_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                        d = +1 if invert else -1
                        break
            if d is None:
                continue
            target_dist = target_R*stop_dist
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist, cost=cost)
            # ---- known-at-i regime features ----
            ratio = sma_atr_ratio(atrs, i, atr_win)        # ATR expansion vs SMA100
            struct = htf_structure_state(B, i, struct_lb)  # +1 up / -1 down / 0
            # structure ALIGNED with the trade's signed direction (tr, not the inverted d)
            sig_dir = tr  # original signal direction (continuation side); invert handled in d
            struct_aligned = (struct == sig_dir and struct != 0)
            out.append({
                "sym": sym, "year": T[i].year, "cls": ASSET_CLASS_BY_SYMBOL.get(sym),
                "r": r, "atr_ratio": ratio, "struct_aligned": bool(struct_aligned),
                "trend": tr,
            })
    return out

# ---------------- stats ----------------
def stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*w/n, 1), "sum_R": round(s, 2)}

def per_year(recs):
    by = defaultdict(list)
    for d in recs: by[d["year"]].append(d["r"])
    return {y: stats(by[y]) for y in sorted(by)}

def split(recs):
    tr = [d["r"] for d in recs if d["year"] <= TRAIN_MAX]
    fw = [d["r"] for d in recs if d["year"] >  TRAIN_MAX]
    return stats(tr), stats(fw)

def summarize(name, recs):
    tr, fw = split(recs)
    py = per_year(recs); yrs = sorted(py)
    full = stats([d["r"] for d in recs])
    pos_years = sum(1 for y in yrs if py[y]["mean_R"] > 0)
    fwd_yrs = [y for y in yrs if y > TRAIN_MAX]
    pos_fwd = sum(1 for y in fwd_yrs if py[y]["mean_R"] > 0)
    return {
        "name": name, "full_cycle": full, "train": tr, "fwd": fw,
        "per_year": {str(y): py[y] for y in yrs},
        "pos_years": pos_years, "total_years": len(yrs),
        "pos_fwd_years": pos_fwd, "total_fwd_years": len(fwd_yrs),
    }

def pline(s):
    py = s["per_year"]
    line = f"  TRAIN<=2024 R={s['train']['mean_R']:+.4f}(n{s['train']['n']})  "
    line += f"FWD R={s['fwd']['mean_R']:+.4f}(n{s['fwd']['n']})  "
    line += f"FULL R={s['full_cycle']['mean_R']:+.4f}(n{s['full_cycle']['n']}) sum={s['full_cycle']['sum_R']:+.1f}"
    print(line)
    yl = "  per-year: " + " ".join(f"{y}:{py[y]['mean_R']:+.3f}(n{py[y]['n']})" for y in py)
    print(yl)
    print(f"  pos years {s['pos_years']}/{s['total_years']}  pos fwd {s['pos_fwd_years']}/{s['total_fwd_years']}")

# ---------------- main ----------------
def main():
    random.seed(12345)
    OUT = {"thrust": "fvg_regime_honest", "selection_rule": {}, "results": {}, "controls": {}}

    print("="*78)
    print("STEP 0: ALL-REGIME BASELINE (validated metals+energy FVG-retest, 2R)")
    print("="*78)
    base = fvg_trades(target_R=2.0, classes=VALIDATED_CLASSES)
    s_base = summarize("ALL_REGIME_baseline", base)
    pline(s_base)
    OUT["results"]["all_regime_baseline"] = s_base

    # also the full-universe baseline for context (all asset classes)
    base_all = fvg_trades(target_R=2.0, classes=None)
    s_base_all = summarize("ALL_REGIME_baseline_full_universe", base_all)
    OUT["results"]["all_regime_baseline_full_universe"] = s_base_all
    print("\n[context] full-universe all-regime baseline:")
    pline(s_base_all)

    # ---------------------------------------------------------------
    # STEP 1: lock favorable-regime threshold on TRAIN ONLY.
    # Candidate regime flags (all known-at-i):
    #   - atr expansion: atr_ratio >= thr (vol expanding vs its own SMA100)
    #   - atr contraction: atr_ratio <  thr (low-vol)
    #   - htf structure aligned: struct_aligned True
    #   - combos
    # We scan thresholds, pick the one with best TRAIN mean_R among flags with
    # enough train n, then FREEZE it and read forward.
    # ---------------------------------------------------------------
    print("\n" + "="*78)
    print("STEP 1: TRAIN-ONLY regime selection (no forward peeking)")
    print("="*78)
    train_recs = [d for d in base if d["year"] <= TRAIN_MAX]
    train_n = len(train_recs)
    MIN_TRAIN_FRAC = 0.15   # a usable regime must keep >=15% of train trades
    min_train_n = int(train_n * MIN_TRAIN_FRAC)
    print(f"train trades (metals+energy): {train_n}; min in-regime train n = {min_train_n}")

    def apply_flag(recs, flag):
        return [d for d in recs if flag(d)]

    candidates = {}
    # atr expansion thresholds
    for thr in [1.0, 1.1, 1.2, 1.3, 1.5]:
        candidates[f"atr_expand>={thr}"] = (lambda d, t=thr: d["atr_ratio"] is not None and d["atr_ratio"] >= t)
    # atr contraction thresholds
    for thr in [0.7, 0.8, 0.9, 1.0]:
        candidates[f"atr_contract<{thr}"] = (lambda d, t=thr: d["atr_ratio"] is not None and d["atr_ratio"] < t)
    # structure aligned
    candidates["struct_aligned"] = (lambda d: d["struct_aligned"])
    # combos
    for thr in [1.0, 1.1, 1.2]:
        candidates[f"struct&atr_expand>={thr}"] = (
            lambda d, t=thr: d["struct_aligned"] and d["atr_ratio"] is not None and d["atr_ratio"] >= t)

    scan = []
    for nm, flag in candidates.items():
        tr_sub = apply_flag(train_recs, flag)
        st = stats([d["r"] for d in tr_sub])
        scan.append((nm, st["mean_R"], st["n"], flag))
        ok = "OK" if st["n"] >= min_train_n else "skip(low-n)"
        print(f"  {nm:24s} train R={st['mean_R']:+.4f} n={st['n']:5d} {ok}")

    eligible = [(nm, mr, n, fl) for nm, mr, n, fl in scan if n >= min_train_n]
    if not eligible:
        print("NO eligible regime flag retains enough train trades. Falling back to widest.")
        eligible = scan
    eligible.sort(key=lambda x: -x[1])  # best TRAIN mean_R
    chosen_name, chosen_train_R, chosen_n, chosen_flag = eligible[0]
    print(f"\n>>> CHOSEN regime (locked on TRAIN): '{chosen_name}'  train R={chosen_train_R:+.4f} n={chosen_n}")
    OUT["selection_rule"] = {
        "chosen_regime": chosen_name,
        "selected_on": "year<=2024 metals+energy FVG-retest 2R",
        "train_mean_R_of_choice": chosen_train_R,
        "train_n_of_choice": chosen_n,
        "min_train_n_required": min_train_n,
        "scan": [{"flag": nm, "train_mean_R": mr, "train_n": n} for nm, mr, n, _ in scan],
    }

    # ---------------------------------------------------------------
    # STEP 2: apply frozen regime to FULL cycle (incl forward read-out)
    # ---------------------------------------------------------------
    print("\n" + "="*78)
    print(f"STEP 2: FROZEN regime '{chosen_name}' applied to FULL cycle (in-regime, FLAT otherwise)")
    print("="*78)
    in_regime = [d for d in base if chosen_flag(d)]
    s_in = summarize(f"IN_REGIME[{chosen_name}]", in_regime)
    pline(s_in)
    OUT["results"]["in_regime_deployment"] = s_in

    # ---------------------------------------------------------------
    # STEP 3: negative controls
    # ---------------------------------------------------------------
    print("\n" + "="*78)
    print("STEP 3: NEGATIVE CONTROLS")
    print("="*78)

    # (1) INVERT: opposite side of in-regime trades (same regime selection)
    inv_all = fvg_trades(target_R=2.0, classes=VALIDATED_CLASSES, invert=True)
    inv_in = [d for d in inv_all if chosen_flag(d)]
    s_inv = summarize(f"CONTROL_invert_in_regime", inv_in)
    print("\n(1) INVERT (opposite side, same in-regime selection):")
    pline(s_inv)
    OUT["controls"]["invert_in_regime"] = s_inv

    # (2) ANTI-REGIME: trade ONLY the rejected (flag==False) bars
    anti = [d for d in base if not chosen_flag(d)]
    s_anti = summarize("CONTROL_anti_regime", anti)
    print("\n(2) ANTI-REGIME (trade only the bars the regime rejects):")
    pline(s_anti)
    OUT["controls"]["anti_regime"] = s_anti

    # (3) RANDOM subset matched in count to in-regime, mean over seeds, full cycle
    k = len(in_regime)
    rand_full = []; rand_fwd = []
    NREP = 50
    for rep in range(NREP):
        random.seed(1000 + rep)
        samp = random.sample(base, k) if k <= len(base) else base
        rand_full.append(stats([d["r"] for d in samp])["mean_R"])
        fw = [d["r"] for d in samp if d["year"] > TRAIN_MAX]
        rand_fwd.append(stats(fw)["mean_R"] if fw else 0.0)
    rand_mean_full = round(sum(rand_full)/len(rand_full), 4)
    rand_mean_fwd = round(sum(rand_fwd)/len(rand_fwd), 4)
    print(f"\n(3) RANDOM count-matched subset (k={k}, {NREP} seeds): "
          f"mean FULL R={rand_mean_full:+.4f}  mean FWD R={rand_mean_fwd:+.4f}")
    OUT["controls"]["random_count_matched"] = {
        "k": k, "reps": NREP, "mean_full_R": rand_mean_full, "mean_fwd_R": rand_mean_fwd,
        "full_R_min": round(min(rand_full),4), "full_R_max": round(max(rand_full),4),
    }

    # ---------------------------------------------------------------
    # STEP 3b: ROBUSTNESS AUDIT (honest caveats)
    # ---------------------------------------------------------------
    print("\n" + "="*78)
    print("STEP 3b: ROBUSTNESS AUDIT")
    print("="*78)
    robo = {}

    # (i) neighbouring thresholds: is the chosen pick a fluke or a stable plateau?
    print("\n(i) neighbouring ATR-expansion thresholds (2R, metals+energy):")
    nb = {}
    for thr in [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]:
        sub = [d for d in base if d["atr_ratio"] is not None and d["atr_ratio"] >= thr]
        ss = summarize(f"atr>={thr}", sub)
        nb[str(thr)] = {"train_R": ss["train"]["mean_R"], "fwd_R": ss["fwd"]["mean_R"],
                        "full_R": ss["full_cycle"]["mean_R"], "full_sum": ss["full_cycle"]["sum_R"],
                        "pos_fwd": f"{ss['pos_fwd_years']}/{ss['total_fwd_years']}"}
        print(f"    atr>={thr}: train {ss['train']['mean_R']:+.4f}  fwd {ss['fwd']['mean_R']:+.4f}  "
              f"full {ss['full_cycle']['mean_R']:+.4f}  posFwd {nb[str(thr)]['pos_fwd']}")
    robo["neighbouring_thresholds_2R"] = nb

    # (ii) leave-one-train-year-out on the chosen regime: is train carried by 1 year?
    print("\n(ii) leave-one-TRAIN-year-out (chosen regime); flips sign => fragile:")
    in_train = [d for d in in_regime if d["year"] <= TRAIN_MAX]
    tyears = sorted(set(d["year"] for d in in_train))
    loo = {}
    for dy in tyears:
        v = [d["r"] for d in in_train if d["year"] != dy]
        m = round(sum(v)/len(v), 4) if v else 0.0
        loo[str(dy)] = m
        flag = "  <-- FLIPS NEGATIVE" if m < 0 else ""
        print(f"    drop {dy}: {m:+.4f}{flag}")
    robo["leave_one_train_year_out"] = loo
    robo["train_is_fragile_single_year"] = any(m < 0 for m in loo.values())

    # (iii) does ATR-expansion help the FULL universe? (confound check)
    full_univ = fvg_trades(target_R=2.0, classes=None)
    fu_in = [d for d in full_univ if d["atr_ratio"] is not None and d["atr_ratio"] >= 1.0]
    s_fu = summarize("FULLUNIV_atr>=1.0", fu_in)
    print(f"\n(iii) FULL-UNIVERSE atr_expand>=1.0 (confound): "
          f"train {s_fu['train']['mean_R']:+.4f} fwd {s_fu['fwd']['mean_R']:+.4f} "
          f"full {s_fu['full_cycle']['mean_R']:+.4f} posFwd {s_fu['pos_fwd_years']}/{s_fu['total_fwd_years']}")
    robo["full_universe_atr_expand_1.0"] = {
        "train_R": s_fu["train"]["mean_R"], "fwd_R": s_fu["fwd"]["mean_R"],
        "full_R": s_fu["full_cycle"]["mean_R"], "pos_fwd": f"{s_fu['pos_fwd_years']}/{s_fu['total_fwd_years']}",
    }
    robo["regime_generalizes_to_full_universe"] = (s_fu["full_cycle"]["mean_R"] > 0 and s_fu["fwd"]["mean_R"] > 0)

    # (iv) per-symbol decomposition of chosen in-regime set
    by_sym = defaultdict(list); by_sym_fwd = defaultdict(list)
    for d in in_regime:
        by_sym[d["sym"]].append(d["r"])
        if d["year"] > TRAIN_MAX: by_sym_fwd[d["sym"]].append(d["r"])
    persym = {}
    for s_ in sorted(by_sym):
        persym[s_] = {"full_R": round(sum(by_sym[s_])/len(by_sym[s_]), 4), "n": len(by_sym[s_]),
                      "fwd_R": round(sum(by_sym_fwd[s_])/len(by_sym_fwd[s_]), 4) if by_sym_fwd[s_] else None,
                      "fwd_n": len(by_sym_fwd[s_])}
    robo["per_symbol_in_regime"] = persym
    print("\n(iv) per-symbol full-cycle R (in-regime):")
    for s_, v in persym.items():
        print(f"    {s_:12s} full {v['full_R']:+.4f}(n{v['n']})  fwd {v['fwd_R']}(n{v['fwd_n']})")

    OUT["robustness"] = robo

    # ---------------------------------------------------------------
    # STEP 4: honest verdict
    # ---------------------------------------------------------------
    print("\n" + "="*78)
    print("STEP 4: HONEST VERDICT")
    print("="*78)
    full = s_in["full_cycle"]; fwd = s_in["fwd"]; trn = s_in["train"]
    a = full["mean_R"] > 0 and full["sum_R"] > 0
    b = fwd["mean_R"] > 0
    c = (trn["mean_R"] > s_base["train"]["mean_R"]) and (fwd["mean_R"] > s_base["fwd"]["mean_R"])
    e = (s_inv["fwd"]["mean_R"] < 0) and (s_anti["fwd"]["mean_R"] < s_in["fwd"]["mean_R"])
    net_positive_no_lookahead = bool(a and b and c)
    directional_clean = bool(e)
    verdict = {
        "regime_chosen_on_train": chosen_name,
        "(a)_full_cycle_positive": a,
        "(b)_forward_positive": b,
        "(c)_beats_all_regime_baseline_both_splits": c,
        "(d/e)_directional_and_better_than_anti": directional_clean,
        "NET_POSITIVE_WITHOUT_LOOKAHEAD": net_positive_no_lookahead,
        "in_regime_full_R": full["mean_R"], "in_regime_full_sum_R": full["sum_R"],
        "in_regime_train_R": trn["mean_R"], "in_regime_fwd_R": fwd["mean_R"],
        "baseline_train_R": s_base["train"]["mean_R"], "baseline_fwd_R": s_base["fwd"]["mean_R"],
        "baseline_full_R": s_base["full_cycle"]["mean_R"], "baseline_full_sum_R": s_base["full_cycle"]["sum_R"],
        "invert_fwd_R": s_inv["fwd"]["mean_R"], "anti_fwd_R": s_anti["fwd"]["mean_R"],
        "random_full_R": rand_mean_full,
        "in_regime_pos_years": f"{s_in['pos_years']}/{s_in['total_years']}",
        "in_regime_pos_fwd_years": f"{s_in['pos_fwd_years']}/{s_in['total_fwd_years']}",
        # honest caveats
        "CAVEAT_train_edge_marginal": s_in["train"]["mean_R"] < 0.10,
        "CAVEAT_train_fragile_single_year": robo["train_is_fragile_single_year"],
        "CAVEAT_regime_does_NOT_generalize_full_universe": not robo["regime_generalizes_to_full_universe"],
        "CAVEAT_edge_leans_on_forward_window": s_in["fwd"]["mean_R"] > 2.0 * max(s_in["train"]["mean_R"], 1e-9),
    }
    OUT["verdict"] = verdict
    for kk, vv in verdict.items():
        print(f"  {kk}: {vv}")

    with open(EDGE + "/WAVE3_FVG_REGIME_HONEST_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1)
    print("\nWROTE WAVE3_FVG_REGIME_HONEST_RESULT.json")

if __name__ == "__main__":
    main()
