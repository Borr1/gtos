#!/usr/bin/env python3
"""F2 shared library -- the excursion label set, the join, and the walk-forward.

Bound by PREREG_V1.json payload_sha256
8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4

Design note on speed and on discipline.  B3's protocol refits from scratch on
every one of the 100 scored days.  F2 has ~25 targets, not one, so a naive
implementation is 25x B3's cost.  Ridge with a fixed alpha admits an exact
shortcut: on each day the design matrix is built ONCE, the normal-equation
Gram matrix G = X'X + alpha*I is formed ONCE, and every target is solved by
back-substitution against the same Cholesky factor.  This is the same estimator
sklearn's Ridge computes, not an approximation -- verified against
sklearn.linear_model.Ridge in f2_selftest.py.  Nothing else about the protocol
changes: training is bootstrap + strictly prior days, weights are the frozen
1/(candidates in window), no hyperparameter is searched.
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import scipy.sparse as sp

B3OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b3/out")
F2 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2")
OA = Path(__file__).resolve().parents[3]
PREREG_SHA = "8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4"

MONTHS = ("feb", "apr", "may", "jun", "jul")
BOOTS = ("dev", "jan")
LADDER = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0]
RIDGE_ALPHA = 10.0
SEED = 20260812
MIN_EXPECTED_NET_R = 0.10
RATIO_EPS = 0.05          # declared in PREREG_V1, never tuned

# The frozen 43. Identical to b3_lib.CAT0 + b3_lib.NUM0.
CAT0 = ["symbol", "side", "origin_family", "utc_session", "proposed_order_type",
        "utc_hour", "weekday", "symbol_x_family", "family_x_session",
        "symbol_x_side", "poi_mitigation_status", "limit_marketable_at_decision",
        "trend_state_m15", "trend_transition_flag"]
NUM0 = ["cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
        "distance_to_limit_atr", "distance_to_limit_risk", "risk_over_atr",
        "risk_fraction_of_entry", "poi_age_hours", "poi_distance_to_midpoint_atr",
        "poi_distance_to_zone_atr", "poi_touch_count", "poi_max_mitigation_fraction",
        "poi_touch_episode_count", "poi_overlap_bar_count",
        "atr14_over_atr50", "stop_distance_atr", "target_distance_atr",
        "close_position_in_lookback_range", "dist_to_prior_high20_atr",
        "dist_to_prior_low20_atr", "trigger_bar_range_atr",
        "trigger_bar_body_atr", "compression_ratio_prior_bar",
        "bars_since_session_open", "close_to_close_vol_8_over_48",
        "sweep_depth_atr", "session_open_range_width_atr"]

# Every quantity below is a TRAINING TARGET. None may enter the feature side.
LABELS_L = ["tnr", "mfe", "mae", "ratio", "tmfe", "mfe_capped", "mfe_collapse"]
POLICY_COLS = [f"pol_{k}" for k in LADDER]
ALL_TARGETS = LABELS_L + POLICY_COLS


def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


# ============================ excursion census ==============================
def load_census():
    """key -> compact excursion record, over all months incl. bootstrap."""
    out = {}
    for m in list(MONTHS) + list(BOOTS):
        p = F2 / f"exc_{m}.pkl.gz"
        if not p.exists():
            continue
        with gzip.open(p, "rb") as fh:
            E = pickle.load(fh)
        n = len(E["key"])
        hits = np.stack([E[f"hit_{k}"] for k in LADDER], axis=1)
        for i in range(n):
            if E["disp"][i] != "FILLED":
                continue
            out[E["key"][i]] = (
                E["mfe_pre"][i], E["mfe_incl"][i], E["mae_pre"][i], E["mae_incl"][i],
                E["t_mfe"][i], E["mfe_capped_h1"][i], E["mark_h1"][i], E["stop_min"][i],
                E["stop_gross"][i], E["hz1"][i], E["ded"][i], hits[i],
            )
    return out


def policy_gross(rec, k_index):
    """Realized GROSS R under a take-profit at LADDER[k_index], stop and sealed
    horizon unchanged.  Deterministic from the census -- no model involved.

    hit  : first-passage minute of the level (0 = never reached in the scan)
    stop : minute the stop was hit (0 = never)
    hz   : the sealed mark-out minute
    """
    (_mfe_pre, _mfe_incl, _mae_pre, _mae_incl, _tmfe, _cap, mark, stop,
     stop_gross, hz, _ded, hits) = rec
    hit = hits[k_index]
    took_target = hit > 0 and hit <= hz and (stop == 0 or hit <= stop)
    if took_target:
        return LADDER[k_index]
    if stop > 0 and stop <= hz:
        return stop_gross
    return mark


# ============================ dataset =======================================
def build_dataset():
    """B3's frozen 43-feature frame, joined to the F2 excursion census.

    Returns (meta, X_csr, colnames, targets) where `targets` is a dict of float
    arrays aligned with meta; NaN where the target is undefined for that row.
    """
    with (B3OUT / "dataset.pkl").open("rb") as fh:
        D = pickle.load(fh)
    meta, frame = D["meta"], D["frame"]
    n = len(meta)

    cen = load_census()
    tgt = {k: np.full(n, np.nan, dtype=np.float64) for k in ALL_TARGETS}
    filled = np.zeros(n, dtype=bool)
    ded = np.zeros(n, dtype=np.float64)
    have = 0
    for i, mrow in enumerate(meta):
        rec = cen.get(mrow["key"])
        if rec is None:
            continue
        have += 1
        filled[i] = True
        (mfe_pre, mfe_incl, mae_pre, mae_incl, tmfe, cap, mark, stop,
         stop_gross, hz, d, hits) = rec
        ded[i] = d
        tgt["mfe"][i] = mfe_pre
        tgt["mae"][i] = mae_pre
        tgt["ratio"][i] = mfe_pre / (abs(mae_pre) + RATIO_EPS)
        tgt["tmfe"][i] = math.log1p(max(0.0, float(tmfe)))
        tgt["mfe_capped"][i] = cap
        for kk in range(len(LADDER)):
            tgt[f"pol_{LADDER[kk]}"][i] = policy_gross(rec, kk) - d
    # the shipped label, on every RESOLVED row (no-fill books exactly 0.0)
    for i, mrow in enumerate(meta):
        if mrow["res"]:
            tgt["tnr"][i] = mrow["net"]
            # C-COLLAPSE: the excursion label with non-fills folded in as 0.0 --
            # exactly the structure terminal_net_r already has, applied to MFE.
            tgt["mfe_collapse"][i] = tgt["mfe"][i] if filled[i] else 0.0

    # ---- design matrix: one-hot categoricals + imputed/scaled numerics ------
    blocks, names = [], []
    for c in CAT0:
        codes = frame[c].cat.codes.to_numpy()
        cats = list(frame[c].cat.categories)
        k = len(cats)
        keep = codes >= 0
        M = sp.csr_matrix((np.ones(keep.sum()), (np.nonzero(keep)[0], codes[keep])),
                          shape=(n, k))
        blocks.append(M)
        names += [f"{c}={v}" for v in cats]
    NUMV = np.empty((n, len(NUM0)), dtype=np.float64)
    for jj, c in enumerate(NUM0):
        NUMV[:, jj] = frame[c].to_numpy(dtype=np.float64)
    miss = ~np.isfinite(NUMV)
    NUMV[miss] = 0.0
    blocks.append(sp.csr_matrix(NUMV))
    names += list(NUM0)
    blocks.append(sp.csr_matrix(miss.astype(np.float64)))
    names += [f"{c}__isnan" for c in NUM0]
    X = sp.hstack(blocks, format="csr")
    return meta, X, names, tgt, filled, ded, {"census_joined": have, "n_rows": n}


# ============================ ridge, exact, multi-target =====================
class MultiRidge:
    """Ridge(alpha) on a shared design matrix, for many targets at once.

    Reproduces b3_lib.make_ridge exactly:
      * categorical block -- one-hot, NOT scaled (sklearn's ColumnTransformer
        applies StandardScaler only to the numeric block);
      * numeric + missingness-indicator block -- standardised with the
        UNWEIGHTED mean and population sd, because a Pipeline routes
        `ridge__sample_weight` to the estimator only, never to the scaler;
      * Ridge itself -- weighted centering of Z and y, then
        (Zc'W Zc + alpha I) b = Zc'W yc, matching sklearn's treatment of
        sample_weight (weights the loss, not the penalty).

    Targets sharing a training-row mask share one Cholesky factor, which is the
    whole reason F2 can afford ~25 targets under B3's daily-refit protocol.
    Equality with sklearn is asserted in f2_selftest.py.
    """

    def __init__(self, alpha=RIDGE_ALPHA, scale_cols=None):
        self.alpha = alpha
        self.scale_cols = scale_cols

    def fit(self, X, Y, w, mask):
        """X csr (n,p); Y (n,K) with NaN allowed; w (n,); mask (n,K) bool."""
        self.p = X.shape[1]
        K = Y.shape[1]
        self.coef = np.zeros((self.p, K))
        self.icpt = np.zeros(K)
        self.fitted = np.zeros(K, dtype=bool)
        self.ntrain = np.zeros(K, dtype=np.int64)
        self.ybar = np.full(K, np.nan)
        sig = {}
        for k in range(K):
            sig.setdefault(mask[:, k].tobytes(), []).append(k)
        for key, ks in sig.items():
            idx = np.nonzero(np.frombuffer(key, dtype=bool))[0]
            if len(idx) < 50:
                continue
            Xs = X[idx].astype(np.float64)
            ws = w[idx]
            n = len(idx)
            # --- unweighted standardisation of the declared columns ----------
            cm = np.asarray(Xs.sum(axis=0)).ravel() / n
            cv = np.asarray(Xs.multiply(Xs).sum(axis=0)).ravel() / n - cm ** 2
            csd = np.sqrt(np.maximum(cv, 0.0))
            sc = np.zeros(self.p, dtype=bool) if self.scale_cols is None else self.scale_cols
            shift = np.where(sc, cm, 0.0)
            scale = np.where(sc & (csd > 1e-12), csd, 1.0)
            # --- weighted ridge on Z = (X - shift)/scale ---------------------
            sw = ws.sum()
            XtW = Xs.T.multiply(ws)
            A = np.asarray((XtW @ Xs).todense())
            s = np.asarray(Xs.multiply(ws[:, None]).sum(axis=0)).ravel()
            zbar = (s / sw - shift) / scale                     # weighted mean of Z
            # Z'WZ = (X'WX - shift*s' - s*shift' + sw*shift*shift') / (scale scale')
            G0 = A - np.outer(shift, s) - np.outer(s, shift) + sw * np.outer(shift, shift)
            G0 /= np.outer(scale, scale)
            G = G0 - sw * np.outer(zbar, zbar)                  # centre Z
            G[np.diag_indices_from(G)] += self.alpha
            L = np.linalg.cholesky(G)
            Yk = Y[np.ix_(idx, ks)]
            ybar = (Yk * ws[:, None]).sum(axis=0) / sw
            Yc = Yk - ybar
            WY = Yc * ws[:, None]
            B = np.asarray(Xs.T @ WY)
            B = (B - np.outer(shift, WY.sum(axis=0))) / scale[:, None]
            B -= np.outer(zbar, WY.sum(axis=0))
            Wb = np.linalg.solve(L.T, np.linalg.solve(L, B))
            coef = Wb / scale[:, None]
            for c, k in enumerate(ks):
                self.coef[:, k] = coef[:, c]
                self.icpt[k] = ybar[c] - float(zbar @ Wb[:, c]) - float(shift @ coef[:, c])
                self.fitted[k] = True
                self.ntrain[k] = n
                self.ybar[k] = ybar[c]
        return self

    def predict(self, X):
        out = np.asarray(X @ self.coef) + self.icpt
        out[:, ~self.fitted] = np.nan
        return out


class MultiLPM(MultiRidge):
    """Linear probability model -- Ridge on a 0/1 target. Used for P(fill);
    declared in PREREG as the fill estimator so that the fill and excursion
    stages share one estimator family and one solver."""


# ============================ walk-forward ==================================
def day_chain(meta):
    """The frozen chain: bootstrap first, then the 100 scored days in order."""
    cdays = sorted({m["cday"] for m in meta})
    scored = [d for d in cdays if d.startswith("0002-")]
    return cdays, scored


def window_weights(meta, idx):
    counts = defaultdict(int)
    for i in idx:
        counts[meta[i]["win"]] += 1
    return np.asarray([1.0 / counts[meta[i]["win"]] for i in idx], dtype=np.float64)


def boot_day(values, days, nboot=4000, seed=SEED):
    values = list(values)
    if not values:
        return None
    rng = np.random.default_rng(seed)
    grouped = defaultdict(list)
    for v, d in zip(values, days):
        grouped[d].append(v)
    keys = sorted(grouped)
    arrays = [np.asarray(grouped[k], dtype=float) for k in keys]
    nk = len(keys)
    draws = np.empty(nboot)
    for i in range(nboot):
        pick = rng.integers(0, nk, nk)
        draws[i] = np.concatenate([arrays[j] for j in pick]).mean()
    return {"point": float(np.mean(np.asarray(values, dtype=float))),
            "ci95_lo": float(np.percentile(draws, 2.5)),
            "ci95_hi": float(np.percentile(draws, 97.5)),
            "p_two_sided_sign": float(2 * min((draws <= 0).mean(), (draws >= 0).mean())),
            "n": len(values)}


def within_window_spearman(meta, idx, pred, truth):
    """Mean per-decision-window Spearman between prediction and truth.

    This is the decision-relevant statistic: the funnel ranks INSIDE a window,
    so a label's usefulness is its within-window rank information, not its
    pooled correlation.
    """
    by = defaultdict(list)
    for i in idx:
        p, t = pred[i], truth[i]
        if math.isfinite(p) and math.isfinite(t):
            by[meta[i]["win"]].append((p, t))
    rhos, days, ns = [], [], []
    for win, vals in by.items():
        if len(vals) < 5:
            continue
        a = np.asarray([v[0] for v in vals]); b = np.asarray([v[1] for v in vals])
        if len(np.unique(b)) < 2 or len(np.unique(a)) < 2:
            continue
        ra = _rank(a); rb = _rank(b)
        ra -= ra.mean(); rb -= rb.mean()
        den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
        if den <= 0:
            continue
        rhos.append(float((ra * rb).sum() / den))
        days.append(vals and win)
        ns.append(len(vals))
    return rhos, ns


def _rank(a):
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), dtype=np.float64)
    r[order] = np.arange(len(a), dtype=np.float64)
    # average ties
    s = a[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 10:
        return float("nan")
    ra, rb = _rank(a[ok]), _rank(b[ok])
    ra = ra - ra.mean(); rb = rb - rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def pearson(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 10:
        return float("nan")
    x, y = a[ok] - a[ok].mean(), b[ok] - b[ok].mean()
    den = math.sqrt(float((x ** 2).sum()) * float((y ** 2).sum()))
    return float((x * y).sum() / den) if den > 0 else float("nan")


def r2_oos(truth, pred, train_mean):
    ok = np.isfinite(truth) & np.isfinite(pred)
    if ok.sum() < 10:
        return float("nan")
    sse = float(((truth[ok] - pred[ok]) ** 2).sum())
    sst = float(((truth[ok] - train_mean) ** 2).sum())
    return 1.0 - sse / sst if sst > 0 else float("nan")
