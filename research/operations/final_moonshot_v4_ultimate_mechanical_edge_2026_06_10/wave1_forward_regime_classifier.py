"""WAVE 1 — FORWARD REGIME CLASSIFIER (the timing problem).

Thesis under test: continuation (Donchian breakout + ATR trail) is regime-beta —
it pays in trend/expansion years and bleeds in chop. The unsolved problem is
TIMING: knowing *when* the next ~20 bars will trend/expand vs chop, using
PAST-ONLY features. If we can predict that with real skill, then deploying
continuation ONLY when predicted-trend should turn the strategy forward-positive
across MOST years (regime-robust), not just the recent trending window.

This file:
  1. Loads + concats + dedupes each symbol across 2015-2022 and 2022-2026 (up to 11y H4).
  2. Builds PAST-ONLY regime features (no lookahead): ATR trend, Donchian width slope,
     return autocorrelation, efficiency ratio, realized-vol term structure, etc.
  3. Labels each bar by the REALIZED character of the NEXT ~20 bars (trend/expand vs chop).
     Label is used ONLY for training/evaluation; it never enters the feature vector.
  4. Trains a logistic-regression forward predictor on TRAIN<=2024, pooled across symbols,
     standardized on TRAIN stats only. Reports classifier SKILL (AUC, lift) per year and forward.
  5. Deploys continuation gated by predicted-trend; simulates fills via the TESTED geometry_lib.
     Reports per-year R for: GATED, UNGATED baseline, ANTI-GATE negative control, and RANDOM-GATE.

Honest bar: forward-positive (2025-2026) AND positive in a MAJORITY of all available years.
No acceptance theater. Negative controls included. If nothing is cross-year robust, it says so.
"""
from __future__ import annotations
import sys, os, csv, math, json
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR = os.path.join(REPO, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, REPO)
sys.path.insert(0, OPDIR)

import numpy as np
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

D1 = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
D2 = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")

with open(os.path.join(OPDIR, "ULTIMATE_REAL_COST_MAP.json")) as f:
    COSTMAP = json.load(f)
GLOBAL_COST = COSTMAP["_global_median"]

def cost_for(sym):
    cls = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    return COSTMAP.get(cls, GLOBAL_COST)

# Symbols with FULL history (present in both 2015-2022 and 2022-2026) so per-year
# robustness can actually be judged over a cycle. These span fx/jpy_fx/metals/energy.
FULL_HISTORY_SYMS = [
    "AUDJPY","AUDUSD","CHFJPY","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD",
    "NZDUSD","UKOIL_cash","USDCAD","USDCHF","USDJPY","USOIL_cash","XAGUSD","XAUUSD",
]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _read_csv(path):
    rows = []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append((
                row["time"],
                float(row["open"]), float(row["high"]),
                float(row["low"]), float(row["close"]),
                float(row["volume"]),
            ))
    return rows

def load_symbol(sym):
    """Concat + dedupe by time across both ranges. Returns (times list, bars list)."""
    seen = {}
    for d in (D1, D2):
        p = os.path.join(d, f"{sym}_H4.csv")
        if not os.path.exists(p):
            continue
        for t, o, h, l, c, v in _read_csv(p):
            seen[t] = (o, h, l, c, v)   # later (2022-2026) overrides on the overlap bar
    times = sorted(seen.keys())
    bars = [Bar(*seen[t]) for t in times]
    return times, bars

def year_of(t):
    return int(t[:4])

# ---------------------------------------------------------------------------
# PAST-ONLY features (computed at bar i from data <= i). No lookahead.
# ---------------------------------------------------------------------------
def efficiency_ratio(closes, i, n):
    if i < n: return None
    net = abs(closes[i] - closes[i-n])
    path = 0.0
    for j in range(i-n+1, i+1):
        path += abs(closes[j] - closes[j-1])
    if path == 0: return 0.0
    return net / path

def autocorr1(rets, i, n):
    if i < n+1: return None
    x = rets[i-n+1:i+1]
    if len(x) < 3: return None
    a = np.asarray(x, dtype=float)
    a0 = a[:-1] - a[:-1].mean()
    a1 = a[1:] - a[1:].mean()
    denom = math.sqrt((a0*a0).sum() * (a1*a1).sum())
    if denom == 0: return 0.0
    return float((a0*a1).sum() / denom)

def build_features(bars, times):
    """Return dict: feature_name -> np.array length N (np.nan where undefined),
    plus the realized forward-regime label array and per-bar atr.
    """
    N = len(bars)
    closes = np.array([b.c for b in bars])
    highs = np.array([b.h for b in bars])
    lows  = np.array([b.l for b in bars])
    rets = np.zeros(N)
    rets[1:] = np.diff(closes)
    logret = np.zeros(N)
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.log(closes[1:] / closes[:-1])
    logret[1:] = np.nan_to_num(lr)

    atr = np.array([atr14(bars, i) for i in range(N)])

    F = {}
    nanv = np.full(N, np.nan)

    # 1. ATR trend: current atr vs its own 20-bar mean (expansion vs contraction)
    f = nanv.copy()
    for i in range(34, N):
        base = atr[i-20:i].mean()
        if base > 0:
            f[i] = atr[i] / base - 1.0
    F["atr_trend"] = f

    # 2. ATR slope: short atr (atr14 now) vs longer realized vol (40-bar std of logret)
    f = nanv.copy()
    for i in range(40, N):
        longvol = logret[i-40:i].std()
        shortvol = logret[i-10:i].std()
        if longvol > 0:
            f[i] = shortvol / longvol - 1.0
    F["vol_term_structure"] = f

    # 3. Donchian width slope: change in 20-bar (high-low) channel width
    f = nanv.copy()
    width = nanv.copy()
    for i in range(20, N):
        width[i] = highs[i-20:i+1].max() - lows[i-20:i+1].min()
    for i in range(40, N):
        if width[i-10] and not math.isnan(width[i-10]) and width[i-10] > 0:
            f[i] = width[i] / width[i-10] - 1.0
    F["donchian_width_slope"] = f

    # 4. Efficiency ratio over 20 bars (directional persistence)
    f = nanv.copy()
    for i in range(20, N):
        er = efficiency_ratio(closes, i, 20)
        if er is not None: f[i] = er
    F["er20"] = f

    # 5. Efficiency ratio over 10 bars (faster)
    f = nanv.copy()
    for i in range(10, N):
        er = efficiency_ratio(closes, i, 10)
        if er is not None: f[i] = er
    F["er10"] = f

    # 6. Return autocorrelation (lag1) over 20 bars (mean-reversion vs momentum)
    f = nanv.copy()
    for i in range(22, N):
        ac = autocorr1(list(rets/ (atr+1e-12)), i, 20)
        if ac is not None: f[i] = ac
    F["autocorr1"] = f

    # 7. Realized vol level (40-bar std of logret) — vol regime
    f = nanv.copy()
    for i in range(40, N):
        f[i] = logret[i-40:i].std()
    F["rv40"] = f

    # 8. Recent abs move vs atr (range expansion intensity, 5-bar)
    f = nanv.copy()
    for i in range(20, N):
        if atr[i] > 0:
            f[i] = abs(closes[i] - closes[i-5]) / atr[i]
    F["move5_atr"] = f

    # ---- LABEL: realized character of NEXT H bars (lookahead ONLY for label) ----
    H = 20
    label = np.full(N, np.nan)
    fwd_er = np.full(N, np.nan)
    for i in range(0, N - H - 1):
        # efficiency ratio of the FUTURE path i..i+H (directional trend strength)
        net = abs(closes[i+H] - closes[i])
        path = 0.0
        for j in range(i+1, i+H+1):
            path += abs(closes[j] - closes[j-1])
        er_fut = (net / path) if path > 0 else 0.0
        fwd_er[i] = er_fut
    F["_atr"] = atr
    F["_fwd_er"] = fwd_er
    F["_label"] = label  # filled after global threshold chosen
    return F

FEATURE_NAMES = ["atr_trend","vol_term_structure","donchian_width_slope",
                 "er20","er10","autocorr1","rv40","move5_atr"]

# ---------------------------------------------------------------------------
# Continuation entry generator (Donchian breakout). Past-only trigger at bar i.
# ---------------------------------------------------------------------------
def donchian_signals(bars, lookback=20):
    """Yield (i, direction) where bar i closes beyond the prior `lookback` channel."""
    highs = [b.h for b in bars]; lows = [b.l for b in bars]; closes=[b.c for b in bars]
    sigs = []
    for i in range(lookback+1, len(bars)-1):
        prior_high = max(highs[i-lookback:i])
        prior_low  = min(lows[i-lookback:i])
        if closes[i] > prior_high:
            sigs.append((i, +1))
        elif closes[i] < prior_low:
            sigs.append((i, -1))
    return sigs

# ---------------------------------------------------------------------------
# Logistic regression (numpy, L2) — fit on TRAIN, no sklearn dependency.
# ---------------------------------------------------------------------------
def fit_logistic(X, y, l2=1.0, iters=300, lr=0.5):
    n, d = X.shape
    Xb = np.hstack([np.ones((n,1)), X])
    w = np.zeros(d+1)
    for _ in range(iters):
        z = Xb @ w
        p = 1.0/(1.0+np.exp(-np.clip(z,-30,30)))
        g = Xb.T @ (p - y) / n
        g[1:] += l2 * w[1:] / n
        w -= lr * g
    return w

def predict_proba(w, X):
    Xb = np.hstack([np.ones((X.shape[0],1)), X])
    z = Xb @ w
    return 1.0/(1.0+np.exp(-np.clip(z,-30,30)))

def auc(y, p):
    # rank-based AUC
    order = np.argsort(p)
    y = y[order]
    n_pos = y.sum(); n_neg = len(y)-n_pos
    if n_pos==0 or n_neg==0: return float("nan")
    ranks = np.argsort(np.argsort(p)) + 1
    return float((ranks[y==1].sum() - n_pos*(n_pos+1)/2) / (n_pos*n_neg))

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("Loading symbols (concat+dedupe across 2015-2022 & 2022-2026)...")
    data = {}
    for sym in FULL_HISTORY_SYMS:
        times, bars = load_symbol(sym)
        if len(bars) < 500: continue
        data[sym] = (times, bars)
        print(f"  {sym:12s} bars={len(bars):6d}  {times[0]} -> {times[-1]}  class={ASSET_CLASS_BY_SYMBOL.get(sym)}")

    # ---- Build features per symbol; collect forward-ER distribution to set label threshold on TRAIN only.
    feats = {}
    train_fwd_er = []
    for sym,(times,bars) in data.items():
        F = build_features(bars, times)
        feats[sym] = (times, bars, F)
        for i in range(len(bars)):
            if not math.isnan(F["_fwd_er"][i]) and year_of(times[i]) <= 2024:
                train_fwd_er.append(F["_fwd_er"][i])
    train_fwd_er = np.array(train_fwd_er)
    # TREND label = future efficiency ratio in the top tercile (most directional / trending paths).
    thr = float(np.quantile(train_fwd_er, 0.66))
    print(f"\nLabel threshold (fwd_er top-tercile, TRAIN<=2024): {thr:.4f}  "
          f"(median train fwd_er={np.median(train_fwd_er):.4f})")

    # Assign labels everywhere using TRAIN-derived threshold (no leakage: threshold from train only).
    for sym,(times,bars,F) in feats.items():
        lab = F["_label"]
        for i in range(len(bars)):
            if not math.isnan(F["_fwd_er"][i]):
                lab[i] = 1.0 if F["_fwd_er"][i] >= thr else 0.0

    # ---- Assemble pooled TRAIN matrix (rows with all features + label defined, year<=2024)
    def row_ok(F, i):
        if math.isnan(F["_label"][i]): return False
        for fn in FEATURE_NAMES:
            if math.isnan(F[fn][i]): return False
        return True

    Xtr, ytr = [], []
    for sym,(times,bars,F) in feats.items():
        for i in range(len(bars)):
            if year_of(times[i]) <= 2024 and row_ok(F,i):
                Xtr.append([F[fn][i] for fn in FEATURE_NAMES]); ytr.append(F["_label"][i])
    Xtr = np.array(Xtr); ytr = np.array(ytr)
    mu = Xtr.mean(0); sd = Xtr.std(0); sd[sd==0]=1.0
    Xtr_s = (Xtr-mu)/sd
    print(f"\nTRAIN rows={len(ytr)}  pos_rate={ytr.mean():.3f}")
    w = fit_logistic(Xtr_s, ytr, l2=2.0, iters=600, lr=0.4)
    print("Logistic weights (std features):")
    for fn,wi in zip(["intercept"]+FEATURE_NAMES, w):
        print(f"   {fn:22s} {wi:+.4f}")

    # ---- Classifier SKILL per year (in + out of sample) -----------------------
    print("\n=== REGIME CLASSIFIER SKILL (does it predict trend?) ===")
    by_year_rows = defaultdict(lambda: ([],[]))   # year -> (probs, labels)
    for sym,(times,bars,F) in feats.items():
        for i in range(len(bars)):
            if row_ok(F,i):
                x = (np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd
                p = predict_proba(w, x.reshape(1,-1))[0]
                yy = F["_label"][i]
                yr = year_of(times[i])
                by_year_rows[yr][0].append(p); by_year_rows[yr][1].append(yy)
    skill = {}
    for yr in sorted(by_year_rows):
        ps, ys = by_year_rows[yr]
        ps=np.array(ps); ys=np.array(ys)
        a = auc(ys, ps)
        # lift: pos-rate among top-tercile predicted vs base rate
        if len(ps) > 30:
            cut = np.quantile(ps, 0.66)
            top = ys[ps>=cut]
            lift = (top.mean()/ys.mean()) if (len(top)>0 and ys.mean()>0) else float("nan")
        else:
            lift = float("nan")
        tag = "TRAIN" if yr<=2024 else "FWD  "
        skill[yr] = {"auc":a, "lift":lift, "n":int(len(ps)), "base":float(ys.mean())}
        print(f"  {yr} [{tag}]  AUC={a:.3f}  top-tercile lift={lift:.2f}x  base={ys.mean():.3f}  n={len(ps)}")

    # Choose deployment probability threshold from TRAIN (top ~40% predicted-trend).
    tr_probs = []
    for sym,(times,bars,F) in feats.items():
        for i in range(len(bars)):
            if year_of(times[i])<=2024 and row_ok(F,i):
                x=(np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd
                tr_probs.append(predict_proba(w,x.reshape(1,-1))[0])
    tr_probs=np.array(tr_probs)
    p_gate = float(np.quantile(tr_probs, 0.60))   # deploy continuation in top 40% predicted-trend
    print(f"\nDeployment gate prob threshold (TRAIN q60): {p_gate:.4f}")

    # ---- STRATEGY: continuation gated by predicted-trend -----------------------
    # entry = Donchian-20 breakout in breakout direction; trail exit; stop=0.5*atr.
    # Compare GATED vs UNGATED vs ANTI-GATE (predicted-chop) vs RANDOM-GATE.
    print("\n=== GATED CONTINUATION (Donchian-20 breakout + ATR trail, stop=0.5*atr) ===")
    rng = np.random.default_rng(7)

    def run_strategy(mode):
        # mode in {"gated","ungated","anti","random"}
        per_year = defaultdict(list)
        for sym,(times,bars,F) in feats.items():
            cost = cost_for(sym)
            atr = F["_atr"]
            sigs = donchian_signals(bars, lookback=20)
            for (i,direction) in sigs:
                if i>=len(bars)-2: continue
                if math.isnan(atr[i]) or atr[i]<=0: continue
                if not row_ok(F,i):
                    # still allow ungated to use bar even if some feature missing? require features for fairness
                    if mode in ("gated","anti","random"): continue
                if mode in ("gated","anti","random"):
                    x=(np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd
                    p=predict_proba(w,x.reshape(1,-1))[0]
                    if mode=="gated" and not (p>=p_gate): continue
                    if mode=="anti"  and not (p< p_gate): continue
                    if mode=="random" and rng.random() > 0.40: continue
                stop = 0.5*atr[i]
                r = simulate(bars, i, direction,
                             stop_dist=stop,
                             trail_arm=1.0*atr[i], trail_gap=1.5*atr[i],
                             maxbars=60, cost=cost)
                per_year[year_of(times[i])].append(r)
        return per_year

    results = {}
    for mode in ["ungated","gated","anti","random"]:
        py = run_strategy(mode)
        results[mode]=py

    years_all = sorted(set().union(*[set(results[m].keys()) for m in results]))
    print(f"\n{'year':6s} | {'UNGATED n/meanR/sumR':28s} | {'GATED n/meanR/sumR':28s} | {'ANTI':14s} | {'RANDOM':14s}")
    summary={}
    for m in results:
        summary[m]={}
    for yr in years_all:
        line=f"{yr:6d} | "
        for m in ["ungated","gated"]:
            rs=results[m].get(yr,[])
            if rs:
                arr=np.array(rs)
                summary[m][yr]={"n":len(rs),"mean":float(arr.mean()),"sum":float(arr.sum())}
                line+=f"n={len(rs):4d} mean={arr.mean():+.4f} sum={arr.sum():+8.2f} | "
            else:
                summary[m][yr]={"n":0,"mean":0.0,"sum":0.0}; line+=f"{'--':26s} | "
        for m in ["anti","random"]:
            rs=results[m].get(yr,[])
            arr=np.array(rs) if rs else np.array([0.0])
            summary[m][yr]={"n":len(rs),"mean":float(arr.mean()) if rs else 0.0,"sum":float(arr.sum()) if rs else 0.0}
            line+=f"{arr.mean() if rs else 0:+.3f}({len(rs)}) | "
        print(line)

    # ---- Verdict ---------------------------------------------------------------
    def verdict(m):
        years = [y for y in summary[m] if summary[m][y]["n"]>0]
        means = {y:summary[m][y]["mean"] for y in years}
        pos = sum(1 for y in years if means[y]>0)
        fwd_years=[y for y in years if y>=2025]
        fwd_trades=[]
        for y in fwd_years:
            fwd_trades += results[m].get(y,[])
        fwd_mean = float(np.mean(fwd_trades)) if fwd_trades else float("nan")
        total_trades=[]
        for y in years: total_trades+=results[m].get(y,[])
        return {"years_pos":pos,"years_total":len(years),"fwd_mean":fwd_mean,
                "fwd_n":len(fwd_trades),"all_mean":float(np.mean(total_trades)) if total_trades else float("nan"),
                "all_n":len(total_trades),"means_by_year":means}

    print("\n=== VERDICT ===")
    verdicts={}
    for m in ["ungated","gated","anti","random"]:
        v=verdict(m); verdicts[m]=v
        print(f"{m:8s}: years_pos={v['years_pos']}/{v['years_total']}  "
              f"fwd_meanR={v['fwd_mean']:+.4f} (n={v['fwd_n']})  "
              f"all_meanR={v['all_mean']:+.4f} (n={v['all_n']})")

    g=verdicts["gated"]; u=verdicts["ungated"]
    robust = (g["fwd_mean"]>0) and (g["years_pos"] > g["years_total"]/2)
    beats_ungated = g["fwd_mean"] > u["fwd_mean"]
    beats_anti = g["fwd_mean"] > verdicts["anti"]["fwd_mean"]
    print(f"\nGATED forward-positive: {g['fwd_mean']>0}")
    print(f"GATED positive in majority of years: {g['years_pos']>g['years_total']/2} ({g['years_pos']}/{g['years_total']})")
    print(f"GATED beats UNGATED forward: {beats_ungated}  ({g['fwd_mean']:+.4f} vs {u['fwd_mean']:+.4f})")
    print(f"GATED beats ANTI-GATE (neg control) forward: {beats_anti}")
    print(f"\n>>> REGIME-ROBUST (fwd+ AND majority-years+): {robust}")

    out={"label_threshold":thr,"gate_prob":p_gate,"logistic_weights":dict(zip(['intercept']+FEATURE_NAMES,[float(x) for x in w])),
         "classifier_skill":{int(k):v for k,v in skill.items()},
         "strategy_verdicts":{m:{**verdicts[m],"means_by_year":{int(k):float(vv) for k,vv in verdicts[m]['means_by_year'].items()}} for m in verdicts},
         "robust":bool(robust),"beats_ungated_fwd":bool(beats_ungated),"beats_anti_fwd":bool(beats_anti)}
    with open(os.path.join(OPDIR,"wave1_forward_regime_classifier_RESULT.json"),"w") as f:
        json.dump(out,f,indent=2)
    print("\nWrote wave1_forward_regime_classifier_RESULT.json")
    return out

if __name__=="__main__":
    main()
