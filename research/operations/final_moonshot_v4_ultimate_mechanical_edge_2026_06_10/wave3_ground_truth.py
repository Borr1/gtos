"""
wave3_ground_truth.py
=====================
THRUST: ground_truth — PURE MEASUREMENT of H4 market structure per symbol,
2015-2026. NO strategy, NO entry rule, NO selection logic on the measurements.
Because there is no trade-construction here, there is nothing to leak: every
number is a model-free statistic of the bar series. (The two prior subagent
"wins" leaked via a short-side sign bug and a lookahead gate; this file makes
NO trades at all for the core measurements, so that whole class is excluded.)

WHAT WE MEASURE, per symbol:
  1. RETURN DISTRIBUTION       mean, std, skew, excess kurtosis of H4 log returns
                               (full-sample + per-year), annualized drift for context
  2. RETURN AUTOCORRELATION    lags 1..10 (full-sample + per-year lag1/lag5);
                               sign tells trend(+) vs revert(-) at the bar scale;
                               cross-year sign-stability is the deliverable
  3. VOL-CLUSTERING PERSISTENCE autocorr of ATR14 and of |return| at lags 1,2,5,10
                               (GARCH-like memory; near-universal, used as a sanity
                                anchor that the pipeline detects REAL structure)
  4. VARIANCE-RATIO TEST       Lo-MacKinlay VR(q) for q in {2,5,10,20}, PER YEAR.
                               VR>1 trending/persistent, VR<1 mean-reverting,
                               VR~=1 random walk. Per-year so we can see stability.
  5. REAL MFE/MAE + TIME-TO-TARGET  direction-agnostic path facts over a 20-bar
                               forward horizon in ATR units: how far price reaches
                               up vs down, the full distribution (p25/med/p75/p90),
                               and bars-to-reach +/-1 ATR. These ARE a forward look
                               by construction (they describe future excursion) and
                               are therefore DESCRIPTIVE PATH FACTS only, never fed
                               back into any same-period decision.

CROSS-YEAR CONFIDENCE is the point. For each directional property we compute it
per calendar year, then score:
  - agree  = fraction of years whose sign matches the full-sample sign
             (for VR, sign is relative to 1.0: trend vs revert)
  - n_years= number of usable years (>=120 H4 bars and >=60 returns)
  - confidence tier: HIGH >=6 yrs, MED 4-5 yrs, LOW 3 yrs, NONE <3 yrs.

NEGATIVE / SANITY CONTROLS (mandatory):
  - SHUFFLE surrogate: shuffle the return series, recompute autocorr & VR.
    A real serial-structure stat must collapse toward its null (ac->0, VR->1)
    under shuffling. If the surrogate is as large as the real stat, the "edge"
    is a small-sample artifact and we say so.
  - Each symbol gets a VERDICT: TRENDING / REVERTING / RANDOM, decided ONLY from
    the cross-year-stable, surrogate-surviving evidence. RANDOM is a legitimate
    and common answer; we do not manufacture a verdict.

TRAIN/FORWARD HYGIENE: the VERDICT for each symbol is computed on TRAIN years
(<=2024) only. FORWARD years (2025-2026) are reported as a separate read-out
column ("did it still hold?") and never used to assign the verdict. Full-sample
moments are also reported but the verdict ignores them where forward years exist.

Output: WAVE3_GROUND_TRUTH_RESULT.json + console fact sheet.
"""
from __future__ import annotations
import sys, os, csv, json, math
from datetime import datetime
from collections import defaultdict

import numpy as np

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
D1 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
D2 = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT)
sys.path.insert(0, EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14  # tested primitive (ATR only; no simulate -> no fills -> no leak)

SEED = 7
np.random.seed(SEED)

TRAIN_MAX_YEAR = 2024          # parameters/verdict locked on <=2024
FORWARD_YEARS = {2025, 2026}   # read-out only
VR_QS = [2, 5, 10, 20]
AC_LAGS = list(range(1, 11))
HORIZON = 20                   # H4 bars (~ 3.3 trading days) for path-fact excursions
MIN_TOTAL_BARS = 300
MIN_YEAR_BARS = 120
MIN_YEAR_RETS = 60

# ----------------------------------------------------------------------
# DATA LOADING: concat + dedupe both bridge files (later file wins on overlap)
# ----------------------------------------------------------------------
def syms_in(d):
    return {fn[:-7] for fn in os.listdir(d) if fn.endswith("_H4.csv")} if os.path.isdir(d) else set()

SYMBOLS = sorted(syms_in(D1) | syms_in(D2))

def _load_one(p):
    T, B = [], []
    if not os.path.exists(p):
        return T, B
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
            except Exception:
                continue
            T.append(t)
            B.append(b)
    return T, B

def load(sym):
    T1, B1 = _load_one(f"{D1}/{sym}_H4.csv")
    T2, B2 = _load_one(f"{D2}/{sym}_H4.csv")
    merged = {}
    for t, b in zip(T1, B1):
        merged[t] = b
    for t, b in zip(T2, B2):
        merged[t] = b  # later file wins on overlapping timestamps
    if not merged:
        return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

# ----------------------------------------------------------------------
# MODEL-FREE STATISTICS (numpy)
# ----------------------------------------------------------------------
def log_returns(closes):
    c = np.asarray(closes, float)
    c = np.where(c <= 0, np.nan, c)
    r = np.diff(np.log(c))
    return r[np.isfinite(r)]

def _moment_calc(r):
    m = float(r.mean()); s = float(r.std(ddof=0))
    if s == 0:
        return m, 0.0, 0.0, 0.0
    z = (r - m) / s
    return m, s, float(np.mean(z ** 3)), float(np.mean(z ** 4) - 3.0)

def moments(r):
    """Return-distribution moments. RAW moments are dominated by isolated bad-print
    bars (single-bar quote glitches at the file-stitch boundary blow up skew/kurt),
    so we ALSO report robust moments after winsorizing returns at the 0.1/99.9
    percentiles. The robust set is the honest description of distribution SHAPE;
    raw skew/exkurt are kept only to flag glitch contamination (raw_exkurt huge
    while wins_exkurt moderate == data spikes, not real fat tails)."""
    r = r[np.isfinite(r)]
    if len(r) < 30:
        nan = float("nan")
        return dict(n=len(r), mean=nan, std=nan, skew=nan, exkurt=nan,
                    wins_skew=nan, wins_exkurt=nan, wins_std=nan, n_clipped=0)
    m, s, sk, ek = _moment_calc(r)
    lo, hi = np.percentile(r, 0.1), np.percentile(r, 99.9)
    rw = np.clip(r, lo, hi)
    n_clipped = int(np.sum((r < lo) | (r > hi)))
    _, sw, skw, ekw = _moment_calc(rw)
    return dict(n=len(r), mean=m, std=s, skew=sk, exkurt=ek,
                wins_std=sw, wins_skew=skw, wins_exkurt=ekw, n_clipped=n_clipped)

def autocorr(x, lag):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n <= lag + 5:
        return float("nan")
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom == 0:
        return 0.0
    return float(np.dot(x[:-lag], x[lag:]) / denom)

def variance_ratio(r, q):
    """Lo-MacKinlay VR(q) on log returns. VR>1 => trend/persistent, <1 => revert,
    ~=1 => random walk. Overlapping q-period variance / (q * 1-period variance),
    heteroskedasticity-consistent bias correction."""
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    n = len(r)
    if n < q * 5 + 5:
        return float("nan")
    mu = r.mean()
    var1 = np.sum((r - mu) ** 2) / (n - 1)
    if var1 == 0:
        return float("nan")
    csum = np.cumsum(r)
    qr = csum[q - 1:] - np.concatenate(([0.0], csum[:-q]))  # overlapping q-sums
    m = len(qr)
    denom = q * m * (1.0 - q / n)
    if denom <= 0:
        return float("nan")
    varq = np.sum((qr - q * mu) ** 2) / denom
    if not np.isfinite(varq):
        return float("nan")
    return float(varq / var1)

def atr_series(bars):
    return np.array([atr14(bars, i) for i in range(len(bars))], float)

# ----------------------------------------------------------------------
# MFE / MAE / TIME-TO-TARGET — direction-agnostic path facts (no rule, no cost).
# Pure description of how far price reaches from each bar's close over HORIZON
# bars, normalized by that bar's ATR. These are inherently forward-looking
# (that's their definition) and are reported as descriptive facts ONLY.
# ----------------------------------------------------------------------
def excursions(bars, atr, horizon=HORIZON):
    n = len(bars)
    mfe_up, mae_dn, t2u, t2d = [], [], [], []
    for i in range(14, n - 1):
        a = atr[i]
        if a <= 0:
            continue
        entry = bars[i].c
        end = min(i + horizon, n - 1)
        hh = max(bars[j].h for j in range(i + 1, end + 1))
        ll = min(bars[j].l for j in range(i + 1, end + 1))
        mfe_up.append((hh - entry) / a)
        mae_dn.append((entry - ll) / a)
        tu = td = None
        for j in range(i + 1, end + 1):
            if tu is None and bars[j].h >= entry + a:
                tu = j - i
            if td is None and bars[j].l <= entry - a:
                td = j - i
            if tu is not None and td is not None:
                break
        t2u.append(tu if tu is not None else horizon + 1)
        t2d.append(td if td is not None else horizon + 1)
    return (np.array(mfe_up), np.array(mae_dn),
            np.array(t2u, float), np.array(t2d, float))

def dist_summary(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return dict(n=0, p25=float("nan"), med=float("nan"),
                    p75=float("nan"), p90=float("nan"), mean=float("nan"))
    return dict(n=int(len(x)),
                p25=float(np.percentile(x, 25)), med=float(np.median(x)),
                p75=float(np.percentile(x, 75)), p90=float(np.percentile(x, 90)),
                mean=float(np.mean(x)))

# ----------------------------------------------------------------------
# PER-SYMBOL CHARACTERIZATION (per-year, no forward peek in the verdict)
# ----------------------------------------------------------------------
def characterize(sym):
    T, B = load(sym)
    if len(B) < MIN_TOTAL_BARS:
        return None
    cls = ASSET_CLASS_BY_SYMBOL.get(sym, "unknown")
    years = sorted({t.year for t in T})
    idx_by_year = defaultdict(list)
    for i, t in enumerate(T):
        idx_by_year[t.year].append(i)

    closes_all = [b.c for b in B]
    r_all = log_returns(closes_all)
    atr_all = atr_series(B)
    absr_all = np.abs(r_all)

    full = {
        "moments": moments(r_all),
        "ann_drift_pct": float(np.nanmean(r_all) * (6 * 252) * 100) if len(r_all) else float("nan"),  # ~6 H4 bars/day
        "ac_ret": {str(L): autocorr(r_all, L) for L in AC_LAGS},
        "ac_absret": {str(L): autocorr(absr_all, L) for L in [1, 2, 5, 10]},
        "ac_atr": {str(L): autocorr(atr_all[14:], L) for L in [1, 2, 5, 10]},
        "vr": {str(q): variance_ratio(r_all, q) for q in VR_QS},
    }

    mfe, mae, t2u, t2d = excursions(B, atr_all, HORIZON)
    full["mfe20"] = dist_summary(mfe)
    full["mae20"] = dist_summary(mae)
    mr = (full["mfe20"]["med"] / full["mae20"]["med"]
          if full["mae20"]["med"] and full["mae20"]["med"] > 0 else float("nan"))
    full["mfe_mae_ratio"] = mr
    full["t2up"] = dist_summary(t2u)
    full["t2dn"] = dist_summary(t2d)

    # per-year vectors
    per_year = {}
    for y in years:
        idx = idx_by_year[y]
        if len(idx) < MIN_YEAR_BARS:
            continue
        cy = [B[i].c for i in idx]
        ry = log_returns(cy)
        if len(ry) < MIN_YEAR_RETS:
            continue
        absy = np.abs(ry)
        atry = atr_all[idx[0]:idx[-1] + 1]
        mom = moments(ry)
        per_year[str(y)] = {
            "n_bars": len(idx),
            "is_forward": (y in FORWARD_YEARS),
            "mean": mom["mean"], "std": mom["std"],
            "skew": mom["skew"], "exkurt": mom["exkurt"],
            "ac_ret_1": autocorr(ry, 1), "ac_ret_2": autocorr(ry, 2),
            "ac_ret_5": autocorr(ry, 5),
            "ac_absret_1": autocorr(absy, 1), "ac_absret_5": autocorr(absy, 5),
            "ac_atr_1": autocorr(atry[14:], 1) if len(atry) > 40 else float("nan"),
            "vr2": variance_ratio(ry, 2), "vr5": variance_ratio(ry, 5),
            "vr10": variance_ratio(ry, 10), "vr20": variance_ratio(ry, 20),
        }

    # shuffle surrogate (full-sample) — serial structure must collapse
    rsh = r_all.copy()
    np.random.shuffle(rsh)
    surrogate = {
        "ac_ret_1": autocorr(rsh, 1), "ac_ret_5": autocorr(rsh, 5),
        "ac_absret_1": autocorr(np.abs(rsh), 1),
        "vr2": variance_ratio(rsh, 2), "vr5": variance_ratio(rsh, 5),
        "vr10": variance_ratio(rsh, 10),
    }

    return {
        "symbol": sym, "asset_class": cls, "n_bars": len(B),
        "years": years, "full": full, "per_year": per_year, "surrogate": surrogate,
    }

# ----------------------------------------------------------------------
# CROSS-YEAR STABILITY (TRAIN years <=2024 for the verdict)
# ----------------------------------------------------------------------
def _train_year_keys(per_year):
    return [yk for yk in per_year if int(yk) <= TRAIN_MAX_YEAR]

def stability_sign(per_year, key, *, center=0.0, train_only=True):
    """Agreement of per-year sign (relative to `center`) with the full-train mean sign."""
    keys = _train_year_keys(per_year) if train_only else list(per_year)
    vals = [per_year[yk][key] for yk in keys
            if key in per_year[yk] and isinstance(per_year[yk][key], (int, float))
            and np.isfinite(per_year[yk][key])]
    if len(vals) < 3:
        return None
    arr = np.array(vals, float) - center
    mean = float(arr.mean())
    std = float(arr.std(ddof=0))
    sign = np.sign(mean) if mean != 0 else 0
    if sign == 0:
        agree = float(np.mean(np.abs(arr) < 1e-12))
    else:
        agree = float(np.mean(np.sign(arr) == sign))
    return {"agree": round(agree, 3), "mean": round(mean + center, 6),
            "centered_mean": round(mean, 6), "std": round(std, 6),
            "n_years": len(vals), "majority": agree >= 0.6}

def conf_tier(n_years):
    if n_years is None or n_years < 3:
        return "NONE"
    return "HIGH" if n_years >= 6 else ("MED" if n_years >= 4 else "LOW")

# ----------------------------------------------------------------------
# VERDICT per symbol: TRENDING / REVERTING / RANDOM, on TRAIN evidence only.
# Decision uses VR5 (the workhorse) confirmed by VR10 and return-ac1, all
# requiring cross-year majority + surviving the shuffle surrogate.
# ----------------------------------------------------------------------
def verdict_for(c):
    py = c["per_year"]
    sur = c["surrogate"]

    vr5 = stability_sign(py, "vr5", center=1.0)
    vr10 = stability_sign(py, "vr10", center=1.0)
    vr2 = stability_sign(py, "vr2", center=1.0)
    ac1 = stability_sign(py, "ac_ret_1", center=0.0)

    reasons = []
    score_trend = 0.0
    score_revert = 0.0

    def vr_signal(stab, sur_vr, qname, weight):
        nonlocal score_trend, score_revert
        if not stab or not stab["majority"]:
            return
        mag = abs(stab["mean"] - 1.0)
        sur_mag = abs((sur_vr - 1.0)) if (sur_vr is not None and np.isfinite(sur_vr)) else 0.0
        # require real magnitude AND clearly beyond the shuffle null
        if mag <= 0.03 or sur_mag >= mag / 1.5:
            return
        direction = "trend" if stab["mean"] > 1.0 else "revert"
        if direction == "trend":
            score_trend += weight
        else:
            score_revert += weight
        reasons.append(f"{qname}={stab['mean']:.3f}({direction},agree={stab['agree']:.2f},"
                       f"{stab['n_years']}yr,sur={sur_vr:.3f})")

    vr_signal(vr5, sur.get("vr5"), "VR5", 1.0)
    vr_signal(vr10, sur.get("vr10"), "VR10", 0.7)
    vr_signal(vr2, sur.get("vr2"), "VR2", 0.5)

    # return autocorr lag1 confirmation
    if ac1 and ac1["majority"] and abs(ac1["mean"]) > 0.02:
        sa = sur.get("ac_ret_1")
        sa_mag = abs(sa) if (sa is not None and np.isfinite(sa)) else 0.0
        if sa_mag < abs(ac1["mean"]) / 2:
            if ac1["mean"] > 0:
                score_trend += 0.6
            else:
                score_revert += 0.6
            reasons.append(f"ret_ac1={ac1['mean']:+.3f}(agree={ac1['agree']:.2f},"
                           f"{ac1['n_years']}yr,sur={sa:+.3f})")

    n_train_years = len(_train_year_keys(py))
    base_conf = conf_tier(n_train_years)

    if score_trend == 0 and score_revert == 0:
        verdict = "RANDOM"
    elif score_trend > score_revert:
        verdict = "TRENDING"
    elif score_revert > score_trend:
        verdict = "REVERTING"
    else:
        verdict = "MIXED"  # conflicting signals of equal weight -> not durable

    return {
        "verdict": verdict,
        "confidence": base_conf if verdict not in ("RANDOM", "MIXED") else (
            "n/a" if verdict == "RANDOM" else base_conf),
        "score_trend": round(score_trend, 2),
        "score_revert": round(score_revert, 2),
        "n_train_years": n_train_years,
        "reasons": reasons,
        "vr5_train": vr5, "vr10_train": vr10, "ac1_train": ac1,
    }

# ----------------------------------------------------------------------
# FORWARD READ-OUT (2025-2026): did the verdict's leading property hold?
# ----------------------------------------------------------------------
def forward_holds(c, verdict):
    py = c["per_year"]
    fwd = {yk: py[yk] for yk in py if int(yk) in FORWARD_YEARS}
    if not fwd or verdict["verdict"] in ("RANDOM", "MIXED"):
        return {"available": bool(fwd), "held": None, "detail": {}}
    want_trend = verdict["verdict"] == "TRENDING"
    detail = {}
    hits = 0; tot = 0
    for yk, d in sorted(fwd.items()):
        vr5 = d.get("vr5")
        detail[yk] = {"vr5": vr5, "ac_ret_1": d.get("ac_ret_1")}
        if vr5 is not None and np.isfinite(vr5):
            tot += 1
            if want_trend and vr5 > 1.0:
                hits += 1
            elif (not want_trend) and vr5 < 1.0:
                hits += 1
    held = (hits == tot and tot > 0)
    return {"available": True, "held": held, "hits": hits, "tot": tot, "detail": detail}

# ----------------------------------------------------------------------
def main():
    print(f"H4 ground-truth measurement | symbols in union: {len(SYMBOLS)} | seed={SEED}")
    print(f"TRAIN<= {TRAIN_MAX_YEAR}  | FORWARD read-out: {sorted(FORWARD_YEARS)}\n")

    results = {}
    for sym in SYMBOLS:
        c = characterize(sym)
        if c is None:
            print(f"  skip {sym} (insufficient data)")
            continue
        results[sym] = c

    # assemble verdicts + forward
    for sym, c in results.items():
        c["verdict"] = verdict_for(c)
        c["forward"] = forward_holds(c, c["verdict"])

    # ============ CONSOLE FACT SHEET ============
    def first_last_train_year(c):
        ty = [int(y) for y in c["per_year"] if int(y) <= TRAIN_MAX_YEAR]
        return (min(ty), max(ty)) if ty else (None, None)

    # ---- 1. return distribution ----
    print("=" * 120)
    print("1) RETURN DISTRIBUTION (H4 log returns, full sample). RAW skew/kurt are glitch-contaminated;")
    print("   WINS = winsorized at 0.1/99.9pct = honest shape. clip = # bad-print bars removed by winsor.")
    print(f"  {'symbol':12s} {'class':7s} {'n':>7s} {'mean_bp':>8s} {'std_bp':>7s} {'rawSkew':>8s} {'rawKurt':>9s} {'winSkew':>8s} {'winKurt':>8s} {'clip':>5s} {'annDr%':>7s}")
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["asset_class"]):
        m = c["full"]["moments"]
        print(f"  {sym:12s} {c['asset_class']:7s} {m['n']:7d} {m['mean']*1e4:8.2f} {m['std']*1e4:7.1f} "
              f"{m['skew']:8.2f} {m['exkurt']:9.1f} {m['wins_skew']:8.2f} {m['wins_exkurt']:8.1f} "
              f"{m['n_clipped']:5d} {c['full']['ann_drift_pct']:7.1f}")

    # ---- 2. return autocorr lags 1-10 (full sample) ----
    print("\n" + "=" * 110)
    print("2) RETURN AUTOCORRELATION lags 1..10 (full sample)  (+)=momentum (-)=mean-revert at bar scale")
    print(f"  {'symbol':12s} {'class':7s} " + " ".join(f"L{L:<2d}" for L in AC_LAGS))
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["asset_class"]):
        ac = c["full"]["ac_ret"]
        cells = " ".join(f"{ac[str(L)]:+.2f}" for L in AC_LAGS)
        print(f"  {sym:12s} {c['asset_class']:7s} {cells}")

    # ---- 3. vol clustering persistence ----
    print("\n" + "=" * 110)
    print("3) VOL-CLUSTERING PERSISTENCE  ATR14 autocorr & |return| autocorr (full sample)")
    print(f"  {'symbol':12s} {'class':7s} {'atrAC1':>7s} {'atrAC5':>7s} {'atrAC10':>8s} {'|r|AC1':>7s} {'|r|AC5':>7s}  surr|r|AC1")
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["asset_class"]):
        a = c["full"]["ac_atr"]; r = c["full"]["ac_absret"]; s = c["surrogate"]["ac_absret_1"]
        print(f"  {sym:12s} {c['asset_class']:7s} {a['1']:7.2f} {a['5']:7.2f} {a['10']:8.2f} "
              f"{r['1']:7.2f} {r['5']:7.2f}    {s:+.3f}")

    # ---- 4. variance ratio (full sample) + per-year stability VR5 ----
    print("\n" + "=" * 110)
    print("4) VARIANCE RATIO (full sample VR2/5/10/20; >1 trend, <1 revert) + per-TRAIN-year VR5 stability")
    print(f"  {'symbol':12s} {'class':7s} {'VR2':>6s} {'VR5':>6s} {'VR10':>6s} {'VR20':>6s} | {'VR5_yrMean':>10s} {'agree':>6s} {'yrs':>4s} {'surVR5':>7s}")
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["asset_class"]):
        v = c["full"]["vr"]; st = c["verdict"]["vr5_train"]; sur = c["surrogate"]["vr5"]
        if st:
            print(f"  {sym:12s} {c['asset_class']:7s} {v['2']:6.2f} {v['5']:6.2f} {v['10']:6.2f} {v['20']:6.2f} | "
                  f"{st['mean']:10.3f} {st['agree']:6.2f} {st['n_years']:4d} {sur:7.3f}")
        else:
            print(f"  {sym:12s} {c['asset_class']:7s} {v['2']:6.2f} {v['5']:6.2f} {v['10']:6.2f} {v['20']:6.2f} |  (insufficient train years)")

    # ---- 5. path facts MFE/MAE + time-to-target ----
    print("\n" + "=" * 110)
    print("5) PATH FACTS (20-bar fwd horizon, ATR units)  MFE/MAE>1 => upside reaches further; t2 = median bars to +/-1ATR")
    print(f"  {'symbol':12s} {'class':7s} {'MFEmed':>7s} {'MFEp90':>7s} {'MAEmed':>7s} {'MAEp90':>7s} {'MFE/MAE':>8s} {'t2+1ATR':>8s} {'t2-1ATR':>8s}")
    for sym, c in sorted(results.items(), key=lambda kv: kv[1]["asset_class"]):
        f = c["full"]
        print(f"  {sym:12s} {c['asset_class']:7s} {f['mfe20']['med']:7.2f} {f['mfe20']['p90']:7.2f} "
              f"{f['mae20']['med']:7.2f} {f['mae20']['p90']:7.2f} {f['mfe_mae_ratio']:8.3f} "
              f"{f['t2up']['med']:8.1f} {f['t2dn']['med']:8.1f}")

    # ---- VERDICT TABLE ----
    print("\n" + "=" * 110)
    print("VERDICT (TRAIN<=2024 only; surrogate-controlled)  TRENDING / REVERTING / RANDOM / MIXED")
    print(f"  {'symbol':12s} {'class':7s} {'verdict':10s} {'conf':5s} {'sT':>4s} {'sR':>4s} {'fwdHeld':8s}  reasons")
    order = {"TRENDING": 0, "REVERTING": 1, "MIXED": 2, "RANDOM": 3}
    for sym, c in sorted(results.items(), key=lambda kv: (order.get(kv[1]["verdict"]["verdict"], 9),
                                                          kv[1]["asset_class"], kv[0])):
        v = c["verdict"]; fw = c["forward"]
        held = ("yes" if fw["held"] else "no") if fw["held"] is not None else "-"
        if fw["held"] is not None:
            held = f"{held}({fw.get('hits',0)}/{fw.get('tot',0)})"
        reasons = "; ".join(v["reasons"]) if v["reasons"] else "no durable serial structure beyond shuffle null"
        print(f"  {sym:12s} {c['asset_class']:7s} {v['verdict']:10s} {v['confidence']:5s} "
              f"{v['score_trend']:4.1f} {v['score_revert']:4.1f} {held:8s}  {reasons}")

    # ---- summary counts ----
    from collections import Counter
    vc = Counter(c["verdict"]["verdict"] for c in results.values())
    print("\n" + "=" * 110)
    print(f"SUMMARY  symbols measured={len(results)}  verdicts={dict(vc)}")
    durable = [s for s, c in results.items()
               if c["verdict"]["verdict"] in ("TRENDING", "REVERTING")
               and c["verdict"]["confidence"] in ("HIGH", "MED")]
    fwd_confirmed = [s for s in durable if results[s]["forward"]["held"]]
    print(f"  durable directional (HIGH/MED conf): {len(durable)} -> {sorted(durable)}")
    print(f"  of those, forward-2025/26 confirmed: {len(fwd_confirmed)} -> {sorted(fwd_confirmed)}")

    # ---- persist ----
    out = {
        "_thrust": "ground_truth",
        "_note": ("Pure model-free measurement of H4 structure. No strategy => no fills => "
                  "this measurement layer cannot leak. Verdict on TRAIN<=2024; forward 2025-26 read-out only."),
        "_params": {"seed": SEED, "train_max_year": TRAIN_MAX_YEAR,
                    "forward_years": sorted(FORWARD_YEARS), "horizon_bars": HORIZON,
                    "vr_qs": VR_QS, "ac_lags": AC_LAGS},
        "n_symbols": len(results),
        "verdict_counts": dict(vc),
        "durable_directional": sorted(durable),
        "forward_confirmed": sorted(fwd_confirmed),
        "per_symbol": results,
    }
    path = EDGE + "/WAVE3_GROUND_TRUTH_RESULT.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1,
                  default=lambda o: None if (isinstance(o, float) and not np.isfinite(o)) else o)
    print(f"\nWROTE {path}")

if __name__ == "__main__":
    main()
