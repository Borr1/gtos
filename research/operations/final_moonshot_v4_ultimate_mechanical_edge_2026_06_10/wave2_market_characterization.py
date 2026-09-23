"""
wave2_market_characterization.py
================================
THRUST: market_characterization — GROUND TRUTH measurement, NO strategy.

Goal (from the brief): per symbol, MEASURE the H4 structural properties that
repeat across years, so the FVG-retest continuation entry (validated, but
regime-beta: positive only 3/12 years) can be ROUTED onto symbols whose
structure is PERSISTENT and CROSS-YEAR-STABLE. Facts that repeat, not forecasts.

We measure, per symbol, on H4 log returns r_t = ln(c_t / c_{t-1}) and on ATR:

  1. RETURN DISTRIBUTION         skew, excess kurtosis (fat tails)
  2. RETURN AUTOCORRELATION      lags 1..10 (momentum vs mean-reversion in returns)
  3. VOL CLUSTERING PERSISTENCE  autocorr of ATR and of |r| (GARCH-like memory)
  4. TREND vs REVERT             variance ratio VR(q) for q in {2,5,10,20}
                                 VR>1 => trending/persistent; VR<1 => mean-reverting
  5. REAL MFE/MAE + TIME-TO-TGT  realized favorable/adverse excursion in ATR units
                                 over a fixed forward horizon, and bars to hit +1 ATR
                                 (these are model-free path facts, not a strategy)

CROSS-YEAR STABILITY is the deliverable. For each property we:
  - compute it PER YEAR (2015..2026, whatever exists),
  - report the per-year vector,
  - score stability = sign-consistency across years (fraction of years agreeing
    with the full-sample sign) and the year-to-year std,
  - flag a property as PERSISTENT for a symbol only if it agrees in a MAJORITY
    of years AND the full-sample magnitude clears a noise floor.

NEGATIVE / SANITY CONTROLS (mandatory, no theater):
  - PHASE-RANDOMIZED surrogate per symbol: shuffle returns (destroys autocorr &
    VR structure but preserves the unconditional distribution). Any "persistent"
    autocorr/VR must DISAPPEAR on the shuffled control, else it is an artifact.
  - VR sanity: a pure i.i.d. series must give VR ~ 1; we report the surrogate VR.

NO FORWARD PEEKING: every per-year stat uses only that year's bars. Stability is
measured across the historical panel; we do NOT use 2025-2026 to select — we
REPORT 2025-2026 separately so the reader can see the persistent properties held
forward without having been chosen on the forward window.

Output: WAVE2_MARKET_CHARACTERIZATION_RESULT.json + console tables.
"""
from __future__ import annotations
import sys, os, csv, json, math, random
from datetime import datetime
from collections import defaultdict

import numpy as np

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14   # tested primitives

random.seed(7); np.random.seed(7)

# ----------------------------------------------------------------------
# data loading: concatenate + dedupe both bridge files (same as wave1)
# ----------------------------------------------------------------------
def syms_in(d):
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")} if os.path.isdir(d) else set()
SYMBOLS = sorted(syms_in(D1) | syms_in(D2))

def _load_one(p):
    T, B = [], []
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
    for t, b in zip(T2, B2): merged[t] = b   # later file wins on overlap
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

# ----------------------------------------------------------------------
# core statistics (numpy, model-free)
# ----------------------------------------------------------------------
def log_returns(closes):
    c = np.asarray(closes, float)
    c = np.where(c <= 0, np.nan, c)
    r = np.diff(np.log(c))
    return r[np.isfinite(r)]

def skew_kurt(r):
    r = r[np.isfinite(r)]
    if len(r) < 30: return float("nan"), float("nan")
    m = r.mean(); s = r.std(ddof=0)
    if s == 0: return 0.0, 0.0
    z = (r - m) / s
    skew = float(np.mean(z**3))
    exkurt = float(np.mean(z**4) - 3.0)
    return skew, exkurt

def autocorr(x, lag):
    x = x[np.isfinite(x)]
    n = len(x)
    if n <= lag + 5: return float("nan")
    x = x - x.mean()
    denom = np.dot(x, x)
    if denom == 0: return 0.0
    return float(np.dot(x[:-lag], x[lag:]) / denom)

def variance_ratio(r, q):
    """Lo-MacKinlay VR(q) on log returns. VR>1 trend/persistent, <1 mean-revert.
    Overlapping q-period variance / (q * 1-period variance), bias-corrected."""
    r = r[np.isfinite(r)]
    n = len(r)
    if n < q * 5 + 5: return float("nan")
    mu = r.mean()
    var1 = np.sum((r - mu) ** 2) / (n - 1)
    if var1 == 0: return float("nan")
    # overlapping q-sums
    csum = np.cumsum(r)
    # q-period returns: csum[i+q-1] - csum[i-1]; build via slicing
    qr = csum[q - 1:] - np.concatenate(([0.0], csum[:-q]))
    m = len(qr)
    # bias correction factor (Lo-MacKinlay)
    varq = np.sum((qr - q * mu) ** 2) / (q * (m) * (1 - q / n)) if (1 - q / n) > 0 else np.nan
    if not np.isfinite(varq) or var1 == 0: return float("nan")
    return float(varq / var1)

def atr_series(bars):
    n = len(bars)
    return np.array([atr14(bars, i) for i in range(n)], float)

# ----------------------------------------------------------------------
# MFE / MAE / time-to-target — model-free PATH facts (no entry rule, no cost)
# Direction-agnostic: we measure the UPSIDE and DOWNSIDE excursion from each
# bar's close over a fixed forward horizon, normalized by that bar's ATR.
# This says "how far does price reach" structurally — pure measurement.
# ----------------------------------------------------------------------
def excursions(bars, horizon=20):
    n = len(bars)
    a = atr_series(bars)
    mfe_up, mae_dn = [], []
    t2u, t2d = [], []   # bars to reach +1 ATR (up) / -1 ATR (down)
    for i in range(14, n - 1):
        atr = a[i]
        if atr <= 0: continue
        entry = bars[i].c
        end = min(i + horizon, n - 1)
        hh = max(bars[j].h for j in range(i + 1, end + 1))
        ll = min(bars[j].l for j in range(i + 1, end + 1))
        mfe_up.append((hh - entry) / atr)
        mae_dn.append((entry - ll) / atr)
        # time to +1 ATR up
        tu = None; td = None
        for j in range(i + 1, end + 1):
            if tu is None and bars[j].h >= entry + atr: tu = j - i
            if td is None and bars[j].l <= entry - atr: td = j - i
            if tu is not None and td is not None: break
        t2u.append(tu if tu is not None else horizon + 1)
        t2d.append(td if td is not None else horizon + 1)
    return (np.array(mfe_up), np.array(mae_dn), np.array(t2u, float), np.array(t2d, float))

# ----------------------------------------------------------------------
# per-symbol characterization, sliced by calendar year (no forward peeking)
# ----------------------------------------------------------------------
VR_QS = [2, 5, 10, 20]
AC_LAGS = list(range(1, 11))

def characterize_symbol(sym):
    T, B = load(sym)
    if len(B) < 300: return None
    cls = ASSET_CLASS_BY_SYMBOL.get(sym, "unknown")
    years = sorted({t.year for t in T})

    # group bar indices by year (contiguous)
    idx_by_year = defaultdict(list)
    for i, t in enumerate(T):
        idx_by_year[t.year].append(i)

    # full-sample series
    closes_all = [b.c for b in B]
    r_all = log_returns(closes_all)
    atr_all = atr_series(B)
    absr_all = np.abs(r_all)

    full = {
        "skew": skew_kurt(r_all)[0],
        "exkurt": skew_kurt(r_all)[1],
        "ac_ret": {str(L): autocorr(r_all, L) for L in AC_LAGS},
        "ac_absret": {str(L): autocorr(absr_all, L) for L in AC_LAGS},
        "ac_atr": {str(L): autocorr(atr_all[14:], L) for L in [1, 2, 5, 10]},
        "vr": {str(q): variance_ratio(r_all, q) for q in VR_QS},
    }

    # path facts full-sample
    mfe, mae, t2u, t2d = excursions(B, horizon=20)
    full["mfe20_med"] = float(np.median(mfe)) if len(mfe) else float("nan")
    full["mae20_med"] = float(np.median(mae)) if len(mae) else float("nan")
    full["mfe_mae_ratio"] = (full["mfe20_med"] / full["mae20_med"]
                             if full["mae20_med"] and full["mae20_med"] > 0 else float("nan"))
    full["t2up_med"] = float(np.median(t2u)) if len(t2u) else float("nan")
    full["t2dn_med"] = float(np.median(t2d)) if len(t2d) else float("nan")

    # ---- per-year vectors (only that year's bars) ----
    per_year = {}
    for y in years:
        idx = idx_by_year[y]
        if len(idx) < 120:   # need enough H4 bars (~ a few weeks min); skip thin years
            continue
        ys_closes = [B[i].c for i in idx]
        ry = log_returns(ys_closes)
        if len(ry) < 60: continue
        atry = atr_all[idx[0]:idx[-1] + 1]
        absy = np.abs(ry)
        py = {
            "n_bars": len(idx),
            "skew": skew_kurt(ry)[0],
            "exkurt": skew_kurt(ry)[1],
            "ac_ret_1": autocorr(ry, 1),
            "ac_ret_2": autocorr(ry, 2),
            "ac_ret_5": autocorr(ry, 5),
            "ac_absret_1": autocorr(absy, 1),
            "ac_absret_5": autocorr(absy, 5),
            "ac_atr_1": autocorr(atry[14:], 1) if len(atry) > 40 else float("nan"),
            "vr2": variance_ratio(ry, 2),
            "vr5": variance_ratio(ry, 5),
            "vr10": variance_ratio(ry, 10),
        }
        per_year[str(y)] = {k: (round(v, 5) if isinstance(v, float) and np.isfinite(v) else v)
                            for k, v in py.items()}

    # ---- surrogate control: shuffle returns -> kills serial structure ----
    rsh = r_all.copy(); np.random.shuffle(rsh)
    surrogate = {
        "ac_ret_1": autocorr(rsh, 1),
        "ac_ret_5": autocorr(rsh, 5),
        "ac_absret_1": autocorr(np.abs(rsh), 1),
        "vr2": variance_ratio(rsh, 2),
        "vr5": variance_ratio(rsh, 5),
        "vr10": variance_ratio(rsh, 10),
    }

    return {
        "symbol": sym, "asset_class": cls,
        "n_bars": len(B), "years": years,
        "full": full, "per_year": per_year, "surrogate": surrogate,
    }

# ----------------------------------------------------------------------
# stability scoring across years (the deliverable)
# ----------------------------------------------------------------------
def stability_for(per_year, key):
    """Across years, return (full_sign_agreement_fraction, mean, std, n_years, sign_majority)."""
    vals = [py[key] for py in per_year.values()
            if key in py and isinstance(py[key], (int, float)) and np.isfinite(py[key])]
    if len(vals) < 3:
        return None
    arr = np.array(vals, float)
    mean = float(arr.mean()); std = float(arr.std(ddof=0))
    sign = np.sign(mean) if mean != 0 else 0
    if sign == 0:
        agree = float(np.mean(np.abs(arr) < 1e-9))
    else:
        agree = float(np.mean(np.sign(arr) == sign))
    return {"agree": round(agree, 3), "mean": round(mean, 5),
            "std": round(std, 5), "n_years": len(vals),
            "majority": agree >= 0.6}

# Variance-ratio is measured relative to 1.0 (random walk), not 0.
def stability_vr(per_year, key):
    vals = [py[key] for py in per_year.values()
            if key in py and isinstance(py[key], (int, float)) and np.isfinite(py[key])]
    if len(vals) < 3: return None
    arr = np.array(vals, float)
    mean = float(arr.mean()); std = float(arr.std(ddof=0))
    full_sign = 1 if mean > 1.0 else (-1 if mean < 1.0 else 0)  # trend vs revert
    if full_sign == 0:
        agree = 0.0
    elif full_sign == 1:
        agree = float(np.mean(arr > 1.0))
    else:
        agree = float(np.mean(arr < 1.0))
    return {"agree": round(agree, 3), "mean": round(mean, 5), "std": round(std, 5),
            "n_years": len(vals), "direction": ("trend" if full_sign == 1 else "revert"),
            "majority": agree >= 0.6}

# ----------------------------------------------------------------------
def main():
    print(f"Symbols: {len(SYMBOLS)}")
    results = {}
    for sym in SYMBOLS:
        c = characterize_symbol(sym)
        if c is None:
            print(f"  skip {sym} (insufficient data)")
            continue
        results[sym] = c

    # ---------- build stability panel ----------
    panel = {}
    for sym, c in results.items():
        py = c["per_year"]
        panel[sym] = {
            "asset_class": c["asset_class"],
            "n_years_used": len(py),
            "ac_ret_1":   stability_for(py, "ac_ret_1"),
            "ac_ret_5":   stability_for(py, "ac_ret_5"),
            "ac_absret_1":stability_for(py, "ac_absret_1"),
            "ac_atr_1":   stability_for(py, "ac_atr_1"),
            "skew":       stability_for(py, "skew"),
            "exkurt":     stability_for(py, "exkurt"),
            "vr2":        stability_vr(py, "vr2"),
            "vr5":        stability_vr(py, "vr5"),
            "vr10":       stability_vr(py, "vr10"),
            "surrogate":  c["surrogate"],
            "full_vr5":   c["full"]["vr"]["5"],
            "full_vr10":  c["full"]["vr"]["10"],
            "full_ac1":   c["full"]["ac_ret"]["1"],
            "full_absac1":c["full"]["ac_absret"]["1"],
            "mfe_mae_ratio": c["full"]["mfe_mae_ratio"],
            "t2up_med":   c["full"]["t2up_med"],
            "t2dn_med":   c["full"]["t2dn_med"],
        }

    # ---------- console: vol-clustering (the most universally persistent fact) ----------
    print("\n" + "=" * 96)
    print("VOL CLUSTERING PERSISTENCE  (|return| autocorr lag1)  — sorted by cross-year agreement")
    print("  symbol        class     full_|r|ac1  yr_mean   yr_std  yrs  agree  surrogate_|r|ac1  PERSIST")
    rows = sorted(panel.items(),
                  key=lambda kv: (kv[1]["ac_absret_1"]["agree"] if kv[1]["ac_absret_1"] else 0),
                  reverse=True)
    for sym, p in rows:
        s = p["ac_absret_1"]
        if not s: continue
        sur = p["surrogate"]["ac_absret_1"]
        persist = "YES" if (s["majority"] and abs(s["mean"]) > 0.02 and abs(sur) < abs(s["mean"]) / 2) else "no"
        print(f"  {sym:12s} {p['asset_class']:8s}  {p['full_absac1']:+.3f}      {s['mean']:+.3f}  {s['std']:.3f}  {s['n_years']:3d}  {s['agree']:.2f}   {sur:+.3f}             {persist}")

    # ---------- console: trend vs revert (VR5) ----------
    print("\n" + "=" * 96)
    print("TREND vs REVERT  (variance ratio VR(5); >1 trend, <1 revert) — cross-year stable?")
    print("  symbol        class     full_VR5  yr_mean  yr_std  yrs  agree  dir      surrogate_VR5  STABLE")
    rows = sorted(panel.items(),
                  key=lambda kv: (kv[1]["vr5"]["agree"] if kv[1]["vr5"] else 0), reverse=True)
    for sym, p in rows:
        s = p["vr5"]
        if not s: continue
        sur = p["surrogate"]["vr5"]
        # stable if majority-consistent AND surrogate is near 1 (structure is real, not artifact)
        stable = "YES" if (s["majority"] and abs(s["mean"] - 1.0) > 0.03 and abs(sur - 1.0) < abs(s["mean"] - 1.0) / 1.5) else "no"
        print(f"  {sym:12s} {p['asset_class']:8s}  {p['full_vr5']:+.3f}   {s['mean']:+.3f}  {s['std']:.3f}  {s['n_years']:3d}  {s['agree']:.2f}  {s['direction']:7s}  {sur:+.3f}          {stable}")

    # ---------- console: return autocorr lag1 (short-term momentum/revert in returns) ----------
    print("\n" + "=" * 96)
    print("RETURN AUTOCORR lag1  (>0 short momentum, <0 short mean-revert) — cross-year stable?")
    print("  symbol        class     full_ac1  yr_mean  yr_std  yrs  agree  surrogate_ac1  STABLE")
    rows = sorted(panel.items(),
                  key=lambda kv: (kv[1]["ac_ret_1"]["agree"] if kv[1]["ac_ret_1"] else 0), reverse=True)
    for sym, p in rows:
        s = p["ac_ret_1"]
        if not s: continue
        sur = p["surrogate"]["ac_ret_1"]
        stable = "YES" if (s["majority"] and abs(s["mean"]) > 0.02 and abs(sur) < abs(s["mean"]) / 2) else "no"
        print(f"  {sym:12s} {p['asset_class']:8s}  {p['full_ac1']:+.3f}   {s['mean']:+.3f}  {s['std']:.3f}  {s['n_years']:3d}  {s['agree']:.2f}  {sur:+.3f}        {stable}")

    # ---------- console: MFE/MAE asymmetry + time-to-target (path facts) ----------
    print("\n" + "=" * 96)
    print("PATH FACTS  (20-bar horizon, ATR units)  MFE/MAE>1 => upside-skewed reach; time-to +/-1ATR")
    print("  symbol        class     mfe20  mae20  mfe/mae  t2+1ATR  t2-1ATR")
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["full"]["mfe_mae_ratio"]
                         if np.isfinite(kv[1]["full"]["mfe_mae_ratio"]) else 0, reverse=True):
        f = c["full"]
        print(f"  {sym:12s} {c['asset_class']:8s}  {f['mfe20_med']:.2f}   {f['mae20_med']:.2f}   {f['mfe_mae_ratio']:.3f}    {f['t2up_med']:.1f}      {f['t2dn_med']:.1f}")

    # ---------- SELECTABLE SET: persistent structure we can ROUTE on ----------
    print("\n" + "=" * 96)
    print("SELECTABLE SYMBOLS: persistent + cross-year-stable structural properties")
    print("(majority-of-years agreement, full-sample magnitude clears noise, survives surrogate)")
    print("  confidence: HIGH >=6 yrs | MED 4-5 yrs | LOW 3 yrs (few-year flags are weak evidence)")

    def conf(n_years):
        return "HIGH" if n_years >= 6 else ("MED" if n_years >= 4 else "LOW")

    selectable = {}
    for sym, p in panel.items():
        flags = []
        # vol clustering persistent?
        s = p["ac_absret_1"]; sur = p["surrogate"]["ac_absret_1"]
        if s and s["majority"] and abs(s["mean"]) > 0.02 and abs(sur) < abs(s["mean"]) / 2:
            flags.append({"prop": "volcluster", "metric": "|r|ac1", "mean": s["mean"],
                          "agree": s["agree"], "n_years": s["n_years"], "confidence": conf(s["n_years"])})
        # trend or revert persistent (VR5)?
        s = p["vr5"]; sur = p["surrogate"]["vr5"]
        if s and s["majority"] and abs(s["mean"] - 1.0) > 0.03 and abs(sur - 1.0) < abs(s["mean"] - 1.0) / 1.5:
            flags.append({"prop": s["direction"], "metric": "VR5", "mean": s["mean"],
                          "agree": s["agree"], "n_years": s["n_years"], "confidence": conf(s["n_years"])})
        # return autocorr lag1 persistent?
        s = p["ac_ret_1"]; sur = p["surrogate"]["ac_ret_1"]
        if s and s["majority"] and abs(s["mean"]) > 0.02 and abs(sur) < abs(s["mean"]) / 2:
            sgn = "ret_ac1_mom" if s["mean"] > 0 else "ret_ac1_revert"
            flags.append({"prop": sgn, "metric": "ac1", "mean": s["mean"],
                          "agree": s["agree"], "n_years": s["n_years"], "confidence": conf(s["n_years"])})
        if flags:
            tier_rank = {"HIGH": 0, "MED": 1, "LOW": 2}
            top_conf = min(flags, key=lambda f: tier_rank[f["confidence"]])["confidence"]
            selectable[sym] = {"asset_class": p["asset_class"], "top_confidence": top_conf,
                               "properties": flags}
    for sym, v in sorted(selectable.items(),
                         key=lambda kv: (kv[1]["asset_class"], kv[1]["top_confidence"])):
        desc = " | ".join(f"{f['prop']}({f['metric']}={f['mean']:+.3f},agree={f['agree']:.2f},"
                          f"{f['n_years']}yr,{f['confidence']})" for f in v["properties"])
        print(f"  {sym:12s} [{v['asset_class']:8s}] <{v['top_confidence']:4s}>  {desc}")

    # ---------- forward-window REPORT (2025-2026) — not used for selection ----------
    print("\n" + "=" * 96)
    print("FORWARD CHECK (2025-2026): did the selected properties HOLD without being chosen on forward?")
    print("  symbol        VR5_2025  VR5_2026   |r|ac1_2025  |r|ac1_2026  (compare to persistent sign)")
    for sym in sorted(selectable):
        py = results[sym]["per_year"]
        def g(y, k):
            return py.get(str(y), {}).get(k, float("nan"))
        print(f"  {sym:12s}  {g(2025,'vr5'):+.3f}    {g(2026,'vr5'):+.3f}     {g(2025,'ac_absret_1'):+.3f}       {g(2026,'ac_absret_1'):+.3f}")

    # ---------- persist ----------
    out = {
        "_thrust": "market_characterization",
        "_note": "GROUND-TRUTH measurement; per-year (no forward peek); surrogate-controlled.",
        "n_symbols": len(results),
        "panel": panel,
        "selectable": selectable,
        "per_symbol": results,
    }
    with open(EDGE + "/WAVE2_MARKET_CHARACTERIZATION_RESULT.json", "w") as f:
        json.dump(out, f, indent=1, default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else o)
    print("\nWROTE WAVE2_MARKET_CHARACTERIZATION_RESULT.json")
    print(f"Selectable symbols (>=1 persistent property): {len(selectable)}/{len(results)}")

if __name__ == "__main__":
    main()
