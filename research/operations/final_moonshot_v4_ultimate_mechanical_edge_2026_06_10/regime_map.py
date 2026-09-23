"""
regime_map.py — LAYER: empirical regime discovery + Hurst/timescale momentum-vs-reversion map.
================================================================================================
A reusable, importable intelligence layer for the GTOS ultimate-mechanical-edge substrate.

WHAT THIS BUILDS
  (a) Empirical regime discovery: a leak-free per-bar STATE feature vector (vol level, vol-of-vol,
      trend strength, return autocorrelation, realized-range skew) is clustered (KMeans) per
      instrument into K=4 data-driven regimes (not hand-labeled gates).
  (b) Hurst / variance-ratio timescale map: a rolling Hurst exponent H per bar (variance-ratio
      estimator on log returns inside a closed window). H>0.5 => trending/momentum timescale,
      H<0.5 => mean-reverting timescale. Sign is the momentum-vs-reversion compass.
  (c) Forward-EV miner: at each bar, simulate BOTH a momentum entry (breakout continuation in the
      direction of trend) and a reversion entry (fade the recent extreme) with the leak-free
      pessimistic labeler geometry_lib.simulate and REAL per-asset cost. Bucket realized R by
      (discovered regime, Hurst sign). Report TRAIN(<=2024) vs FORWARD(2025-26) odds + n, per-year,
      per-regime. NEVER an average-as-verdict.

NO-LOOKAHEAD GUARANTEES
  - Every feature at index i uses ONLY bars[:i+1] (closed bars index<=i). The cluster model is fit
    ONLY on TRAIN-era feature rows (year<=2024) then APPLIED forward — the forward rows never train
    the model. Standardization stats (mean/std) are computed on TRAIN rows only.
  - Entries are decided from state at i (close of bar i is the entry); outcome via simulate over
    i+1.. (strictly future bars). Hurst/vol/trend all from closed bars.
  - simulate() is the pessimistic same-bar labeler (stop wins ties); cost = w1.cost_for(sym).

ENGINES EXPORTED (importable)
  - Bar features:        feature_row(B, atrs, i) -> dict | None
  - Hurst:               hurst_vr(closes, i, w=128) -> float | None  (H estimate at bar i)
  - Regime model:        RegimeModel.fit(feature_rows) ; .label(row) -> int in [0,K)
  - Per-instrument map:  build_instrument_map(sym, ...) -> dict (regimes, hurst, forward-EV cells)
  - Full universe map:   build_map(symbols=...) -> dict + writes JSON artifact
  - Query helper:        regime_at(sym, B, atrs, i, model, scaler) -> (regime_id, hurst, hurst_sign)

Doctrine: build & improve, map WHERE/WHEN momentum vs reversion works; no averages-as-verdicts;
forward-holdout mandatory; trust a cell only if it holds FORWARD and n>=~40.
"""
from __future__ import annotations
import sys, os, json, math
from collections import defaultdict
from datetime import datetime

import numpy as np

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import atr14, simulate            # leak-free pessimistic labeler
import wave1_structure_setups_ict as w1             # load, cost_for, SYMBOLS
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

try:
    from sklearn.cluster import KMeans
    _HAVE_SK = True
except Exception:                                   # pragma: no cover
    _HAVE_SK = False

K_REGIMES = 4
HURST_W = 128            # closed-window length for the Hurst/variance-ratio estimator
TRAIN_MAX_YEAR = 2024
FWD_MIN_YEAR = 2025
MIN_CELL_N = 40         # trust threshold for a forward cell

# --------------------------------------------------------------------------- #
# Hurst via variance ratio (leak-free: uses only closes[i-w+1 : i+1])
# --------------------------------------------------------------------------- #
def hurst_vr(closes, i, w=HURST_W):
    """Hurst exponent estimate at bar i from the variance-ratio scaling of log returns.
    var(sum of k consecutive returns) ~ k^(2H)  =>  H = slope/2 in log-log space.
    Uses ONLY closes up to and including i. Returns None if insufficient/degenerate."""
    if i < w:
        return None
    seg = closes[i - w + 1 : i + 1]
    if np.any(seg <= 0):
        seg = seg - seg.min() + 1.0          # guard for index price levels that can't go log-neg
    lr = np.diff(np.log(seg))
    if lr.size < 16:
        return None
    lags = [1, 2, 4, 8, 16, 32]
    xs, ys = [], []
    for k in lags:
        if lr.size < k * 4:
            continue
        m = (lr.size // k) * k
        agg = lr[:m].reshape(-1, k).sum(axis=1)
        if agg.size < 3:
            continue
        v = float(np.var(agg))
        if v <= 0:
            continue
        xs.append(math.log(k)); ys.append(math.log(v))
    if len(xs) < 3:
        return None
    slope = float(np.polyfit(xs, ys, 1)[0])
    h = slope / 2.0
    # numerical guard: keep in a sane band
    return max(0.05, min(0.95, h))


# --------------------------------------------------------------------------- #
# Leak-free per-bar STATE feature vector
# --------------------------------------------------------------------------- #
def _autocorr(closes, i, n=40):
    if i < n + 1:
        return 0.0
    rets = np.diff(closes[i - n : i + 1])
    if rets.size < 3:
        return 0.0
    m = rets.mean()
    num = float(np.sum((rets[1:] - m) * (rets[:-1] - m)))
    den = float(np.sum((rets - m) ** 2))
    return num / den if den > 0 else 0.0


def feature_row(B, closes, atrs, i):
    """Leak-free state features at bar i (uses bars[:i+1] only). Returns dict or None.
    Features chosen to span the regime axes: VOL LEVEL, VOL-OF-VOL, TREND STRENGTH,
    RETURN AUTOCORRELATION, RANGE EXPANSION."""
    if i < 110:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    px = closes[i]
    if px <= 0:
        return None
    # vol level: ATR normalized by its own 100-bar mean (regime-relative, unit-free)
    atr_window = atrs[i - 99 : i + 1]
    atr_window = atr_window[atr_window > 0]
    if atr_window.size < 20:
        return None
    vol_ratio = a / float(atr_window.mean())
    # vol-of-vol: std of recent atr / mean atr
    vov = float(atr_window.std()) / float(atr_window.mean())
    # trend strength: |close - close_30| / atr  (unsigned magnitude of directional drift)
    trend_mag = abs(closes[i] - closes[i - 30]) / a
    # signed trend slope normalized
    trend_sign = (closes[i] - closes[i - 30]) / a
    # return autocorrelation (momentum vs reversion micro-signal)
    ac = _autocorr(closes, i, 40)
    # range expansion: today's true range vs atr
    tr = max(B[i].h - B[i].l, abs(B[i].h - closes[i - 1]), abs(B[i].l - closes[i - 1]))
    rng_exp = tr / a
    return {
        "vol_ratio": vol_ratio,
        "vov": vov,
        "trend_mag": trend_mag,
        "trend_sign": trend_sign,
        "ac": ac,
        "rng_exp": rng_exp,
    }


FEAT_KEYS = ["vol_ratio", "vov", "trend_mag", "ac", "rng_exp"]   # trend_sign excluded from clustering (we cluster on |trend|, keep sign for entry direction)


# --------------------------------------------------------------------------- #
# Regime model: standardize on TRAIN rows, KMeans on TRAIN, apply forward
# --------------------------------------------------------------------------- #
class RegimeModel:
    def __init__(self, k=K_REGIMES):
        self.k = k
        self.mean = None
        self.std = None
        self.km = None
        self.centroids = None

    def _mat(self, rows):
        return np.array([[r[key] for key in FEAT_KEYS] for r in rows], dtype=float)

    def fit(self, train_rows, seed=42):
        """Fit standardizer + KMeans on TRAIN-era rows ONLY."""
        X = self._mat(train_rows)
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std == 0] = 1.0
        Xs = (X - self.mean) / self.std
        if _HAVE_SK:
            self.km = KMeans(n_clusters=self.k, n_init=10, random_state=seed)
            self.km.fit(Xs)
            self.centroids = self.km.cluster_centers_
        else:                                        # pragma: no cover - fallback
            self.centroids = self._lloyd(Xs, self.k, seed)
        return self

    @staticmethod
    def _lloyd(Xs, k, seed):                          # pragma: no cover - only if sklearn missing
        rng = np.random.default_rng(seed)
        cent = Xs[rng.choice(Xs.shape[0], k, replace=False)]
        for _ in range(50):
            d = ((Xs[:, None, :] - cent[None, :, :]) ** 2).sum(axis=2)
            lab = d.argmin(axis=1)
            new = np.array([Xs[lab == j].mean(axis=0) if np.any(lab == j) else cent[j] for j in range(k)])
            if np.allclose(new, cent):
                break
            cent = new
        return cent

    def label(self, row):
        x = np.array([row[key] for key in FEAT_KEYS], dtype=float)
        xs = (x - self.mean) / self.std
        d = ((self.centroids - xs) ** 2).sum(axis=1)
        return int(d.argmin())

    def describe(self):
        """Return centroids in ORIGINAL feature units (interpretable regime taxonomy)."""
        out = {}
        for j in range(self.k):
            orig = self.centroids[j] * self.std + self.mean
            out[j] = {key: round(float(v), 3) for key, v in zip(FEAT_KEYS, orig)}
        return out


# --------------------------------------------------------------------------- #
# Entry definitions (leak-free). Both use bar i close as entry, future bars to resolve.
#   momentum  : continuation in direction of 30-bar trend; stop=1.0*atr, target=2.0*atr
#   reversion : fade — if close is extended above/below recent range, take the opposite side;
#               stop=1.0*atr, target=1.5*atr (reversion targets are nearer by nature)
# --------------------------------------------------------------------------- #
def momentum_entry(B, closes, atrs, i):
    """Returns (direction, stop_dist, target_dist) or None."""
    a = atrs[i]
    if a <= 0 or i < 31:
        return None
    drift = closes[i] - closes[i - 30]
    if abs(drift) < 0.5 * a:                       # need a real trend to ride
        return None
    d = 1 if drift > 0 else -1
    return d, 1.0 * a, 2.0 * a


def reversion_entry(B, closes, atrs, i, lb=20):
    """Fade a stretched move: if close is the highest/lowest of the last lb bars by a margin,
    fade it. Returns (direction, stop_dist, target_dist) or None."""
    a = atrs[i]
    if a <= 0 or i < lb + 1:
        return None
    window = closes[i - lb : i + 1]
    hi = window.max(); lo = window.min()
    # stretched up -> fade short; stretched down -> fade long
    if closes[i] >= hi - 1e-9 and (closes[i] - closes[i - lb]) > 0.8 * a:
        return -1, 1.0 * a, 1.5 * a
    if closes[i] <= lo + 1e-9 and (closes[i - lb] - closes[i]) > 0.8 * a:
        return 1, 1.0 * a, 1.5 * a
    return None


def _stats(rs):
    if not rs:
        return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = float(sum(rs)); w = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s / n, 4), "win%": round(100.0 * w / n, 1), "sum_R": round(s, 1)}


# --------------------------------------------------------------------------- #
# Per-instrument map builder
# --------------------------------------------------------------------------- #
def build_instrument_map(sym, k=K_REGIMES, maxbars=60, min_train_rows=300):
    """Build the regime+Hurst+forward-EV map for ONE instrument. Leak-free; forward-holdout."""
    T, B = w1.load(sym)
    if len(B) < 600:
        return {"symbol": sym, "skip": "too_short", "n_bars": len(B)}
    closes = np.array([b.c for b in B], dtype=float)
    atrs = np.array([atr14(B, i) for i in range(len(B))], dtype=float)
    cost = w1.cost_for(sym)

    # 1) build leak-free feature rows + per-bar Hurst
    rows = []        # list of dict(i, year, feats..., hurst)
    for i in range(110, len(B) - 1):              # need a future bar to resolve trades
        fr = feature_row(B, closes, atrs, i)
        if fr is None:
            continue
        h = hurst_vr(closes, i, HURST_W)
        if h is None:
            continue
        fr = dict(fr); fr["i"] = i; fr["year"] = T[i].year; fr["hurst"] = h
        rows.append(fr)
    if len(rows) < 400:
        return {"symbol": sym, "skip": "few_feature_rows", "n_rows": len(rows)}

    train_rows = [r for r in rows if r["year"] <= TRAIN_MAX_YEAR]
    has_train = len(train_rows) >= min_train_rows

    # 2) fit regime model on TRAIN rows only (or all rows if no train -> forward-only flag)
    model = RegimeModel(k=k)
    fit_rows = train_rows if has_train else rows
    model.fit(fit_rows)

    # 3) walk every bar: label regime, hurst sign, simulate BOTH entries, bucket forward R
    #    cell key = (entry_kind, regime_id, hurst_sign)
    cells = defaultdict(lambda: {"train": [], "fwd": [], "peryear": defaultdict(list)})
    regime_year_counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        i = r["i"]; yr = r["year"]; reg = model.label(r); hs = "trend" if r["hurst"] >= 0.5 else "revert"
        regime_year_counts[reg][yr] += 1
        for kind, entry_fn in (("mom", momentum_entry), ("rev", reversion_entry)):
            e = entry_fn(B, closes, atrs, i)
            if e is None:
                continue
            d, sd, td = e
            if sd <= 0:
                continue
            R = simulate(B, i, d, stop_dist=sd, target_dist=td, maxbars=maxbars, cost=cost)
            key = (kind, reg, hs)
            bucket = cells[key]
            if yr <= TRAIN_MAX_YEAR:
                bucket["train"].append(R)
            else:
                bucket["fwd"].append(R)
            bucket["peryear"][yr].append(R)

    # 4) assemble
    cell_out = {}
    for (kind, reg, hs), b in cells.items():
        tr = _stats(b["train"]); fw = _stats(b["fwd"])
        py = {str(y): _stats(v) for y, v in sorted(b["peryear"].items())}
        pos_years = sum(1 for y, v in b["peryear"].items() if _stats(v)["mean_R"] > 0)
        tot_years = len(b["peryear"])
        # TRUE forward-validation requires an out-of-sample holdout: the model was fit on
        # TRAIN rows, the cell is positive on the held-out FORWARD rows, AND TRAIN was not a
        # disaster (edge is not a forward-only artifact). Symbols with no TRAIN history can
        # only be flagged forward_only_insample (NOT trustworthy — no holdout).
        fv = bool(has_train and fw["n"] >= MIN_CELL_N and fw["mean_R"] > 0 and tr["mean_R"] > -0.05)
        cell_out[f"{kind}|reg{reg}|{hs}"] = {
            "entry": kind, "regime": reg, "hurst_sign": hs,
            "train": tr, "fwd": fw,
            "pos_years": pos_years, "tot_years": tot_years,
            "per_year": py,
            "forward_validated": fv,
            "forward_only_insample": bool(not has_train and fw["n"] >= MIN_CELL_N and fw["mean_R"] > 0),
        }

    return {
        "symbol": sym,
        "asset_class": AC.get(sym, "?"),
        "n_bars": len(B),
        "n_feature_rows": len(rows),
        "has_train": has_train,
        "cost_R_per_atr_unit": round(cost, 4),
        "regime_taxonomy": model.describe(),
        "regime_year_counts": {str(reg): {str(y): c for y, c in sorted(yc.items())}
                               for reg, yc in regime_year_counts.items()},
        "cells": cell_out,
    }


# --------------------------------------------------------------------------- #
# Convenience query: regime + hurst at a single bar (for downstream sleeves)
# --------------------------------------------------------------------------- #
def regime_at(B, closes, atrs, i, model):
    fr = feature_row(B, closes, atrs, i)
    if fr is None:
        return None
    h = hurst_vr(closes, i, HURST_W)
    if h is None:
        return None
    reg = model.label(fr)
    return {"regime": reg, "hurst": h, "hurst_sign": "trend" if h >= 0.5 else "revert"}


# --------------------------------------------------------------------------- #
# Full universe map
# --------------------------------------------------------------------------- #
def build_map(symbols=None, out_path=None, verbose=True):
    if symbols is None:
        symbols = w1.SYMBOLS
    results = {}
    for s in symbols:
        try:
            r = build_instrument_map(s)
        except Exception as ex:
            r = {"symbol": s, "error": repr(ex)}
        results[s] = r
        if verbose:
            if "cells" in r:
                ncells = len(r["cells"]); nfv = sum(1 for c in r["cells"].values() if c["forward_validated"])
                print(f"  {s:14} bars={r['n_bars']:6d} train={r['has_train']} cells={ncells:3d} fwd_valid={nfv}")
            else:
                print(f"  {s:14} {r.get('skip') or r.get('error')}")
    out = {"layer": "regime_hurst_map", "k_regimes": K_REGIMES, "hurst_window": HURST_W,
           "train_max_year": TRAIN_MAX_YEAR, "min_cell_n": MIN_CELL_N, "instruments": results}
    if out_path:
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)
        if verbose:
            print(f"WROTE {out_path}")
    return out


# --------------------------------------------------------------------------- #
# Cross-instrument aggregation — the SCIENCE: does Hurst sign / regime discriminate
# momentum vs reversion EV out-of-sample? Pools per-trade R across TRAIN-history
# instruments (true holdout) and reports per-(entry, hurst_sign) and per-(entry, regime-archetype).
# Regimes are per-instrument KMeans ids (not comparable across symbols by number), so we
# additionally map each instrument-regime to a GLOBAL ARCHETYPE by its centroid features.
# --------------------------------------------------------------------------- #
ARCHETYPES = ["calm_trend", "calm_chop", "vol_expansion", "range_spike"]

def _archetype(centroid):
    """Map a centroid (original feature units) to a human regime archetype."""
    vr = centroid["vol_ratio"]; vov = centroid["vov"]; tm = centroid["trend_mag"]; re = centroid["rng_exp"]
    if vr >= 1.25 or vov >= 0.28:
        return "vol_expansion"
    if re >= 1.5:
        return "range_spike"
    if tm >= 3.0:
        return "calm_trend"
    return "calm_chop"


def aggregate(map_obj):
    """Pool TRAIN-history instruments only (true holdout). Returns nested dicts of pooled
    TRAIN vs FORWARD stats for: (a) entry x hurst_sign, (b) entry x archetype,
    (c) entry x archetype x hurst_sign."""
    by_hs = defaultdict(lambda: {"train": [], "fwd": []})        # key (kind, hs)
    by_arch = defaultdict(lambda: {"train": [], "fwd": []})       # key (kind, arch)
    by_arch_hs = defaultdict(lambda: {"train": [], "fwd": []})    # key (kind, arch, hs)
    # we only have per-cell aggregate stats in the JSON, but we kept sum/n/win — to pool
    # correctly we need per-trade R. Re-pool from per-cell n & mean via reconstruction is
    # lossy; instead pool means weighted by n (mean-of-means weighted) and track n.
    # For exactness we pool n and sum_R (both preserved in _stats).
    def add(store, key, st_tr, st_fw):
        store[key]["train"].append((st_tr["n"], st_tr["sum_R"]))
        store[key]["fwd"].append((st_fw["n"], st_fw["sum_R"]))

    for sym, r in map_obj["instruments"].items():
        if "cells" not in r or not r.get("has_train"):
            continue
        tax = r["regime_taxonomy"]
        arch_of = {int(reg): _archetype(c) for reg, c in tax.items()}
        for name, c in r["cells"].items():
            kind = c["entry"]; hs = c["hurst_sign"]; reg = c["regime"]
            arch = arch_of.get(reg, "calm_chop")
            add(by_hs, (kind, hs), c["train"], c["fwd"])
            add(by_arch, (kind, arch), c["train"], c["fwd"])
            add(by_arch_hs, (kind, arch, hs), c["train"], c["fwd"])

    def pool(store):
        out = {}
        for key, d in store.items():
            tn = sum(n for n, _ in d["train"]); ts = sum(s for _, s in d["train"])
            fn = sum(n for n, _ in d["fwd"]);  fs = sum(s for _, s in d["fwd"])
            out["|".join(map(str, key))] = {
                "train": {"n": tn, "mean_R": round(ts / tn, 4) if tn else 0.0},
                "fwd": {"n": fn, "mean_R": round(fs / fn, 4) if fn else 0.0},
            }
        return dict(sorted(out.items(), key=lambda kv: -kv[1]["fwd"]["mean_R"]))

    return {
        "note": "Pooled across TRAIN-history instruments only (true out-of-sample forward holdout). "
                "mean_R is sum_R/n pooled per-trade across symbols. Regime ids are per-instrument; "
                "archetype is the cross-symbol comparable label derived from centroid features.",
        "by_entry_x_hurst_sign": pool(by_hs),
        "by_entry_x_archetype": pool(by_arch),
        "by_entry_x_archetype_x_hurst_sign": pool(by_arch_hs),
    }


def top_forward_cells(map_obj, min_n=MIN_CELL_N, top=25):
    """Rank all TRUE forward-validated per-instrument cells by forward mean_R."""
    rows = []
    for sym, r in map_obj["instruments"].items():
        if "cells" not in r:
            continue
        for name, c in r["cells"].items():
            if c["forward_validated"] and c["fwd"]["n"] >= min_n:
                rows.append({
                    "symbol": sym, "class": r["asset_class"], "cell": name,
                    "train_n": c["train"]["n"], "train_mR": c["train"]["mean_R"],
                    "fwd_n": c["fwd"]["n"], "fwd_mR": c["fwd"]["mean_R"], "fwd_win": c["fwd"]["win%"],
                    "pos_years": c["pos_years"], "tot_years": c["tot_years"],
                })
    rows.sort(key=lambda x: -x["fwd_mR"])
    return rows[:top]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--out", default=EDGE + "/KB4_REGIME_HURST_MAP.json")
    args = ap.parse_args()
    print(f"sklearn available: {_HAVE_SK}")
    m = build_map(symbols=args.symbols, out_path=args.out)
    agg = aggregate(m)
    agg_path = EDGE + "/KB4_REGIME_HURST_AGGREGATE.json"
    with open(agg_path, "w") as f:
        json.dump({"aggregate": agg, "top_forward_cells": top_forward_cells(m)}, f, indent=2)
    print(f"WROTE {agg_path}")
