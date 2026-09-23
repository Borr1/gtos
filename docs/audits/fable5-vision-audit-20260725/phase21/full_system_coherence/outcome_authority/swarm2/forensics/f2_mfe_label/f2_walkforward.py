#!/usr/bin/env python3
"""F2 walk-forward: every target, every scored day, strictly prior training.

Protocol is B3's, unchanged: unit = trading day; 100 scored days in the frozen
chain order; training on day D = the frozen bootstrap (Oct/Nov 2025 dev +
January 2026) plus every strictly prior day; sample weights are the frozen
1/(candidates in the row's decision window) computed within each target's own
training population; no hyperparameter is searched.

The implementation exploits the fact that an EXPANDING training window makes
the Ridge sufficient statistics additive: X'WX, X'Wy, X'W1, X'1 and X'X are
sums over rows, so each day adds its own rows to an accumulator instead of
re-reading the corpus.  The estimator is unchanged (f2_selftest.py).

Variants (-v):
  base    the declared primary
  lag1    T1 -- every feature vector replaced by the same symbol's most recent
          STRICTLY PRIOR scored-day vector; rows without one are dropped
  emb1    T5 -- a row may enter training only once its label span has closed
          strictly before the scored day begins
  shuf    T3 -- labels shuffled WITHIN each decision window (leak control)
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L

OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


class Accum:
    """Additive Ridge sufficient statistics for one training population."""

    def __init__(self, p, K):
        self.p, self.K = p, K
        self.A = np.zeros((p, p))       # X'WX
        self.s = np.zeros(p)            # X'W1
        self.cs = np.zeros(p)           # X'1        (for the unweighted scaler)
        self.css = np.zeros(p)          # (X*X)'1
        self.B = np.zeros((p, K))       # X'Wy
        self.wy = np.zeros(K)           # 1'Wy
        self.sw = 0.0
        self.n = 0

    def add(self, X, Y, w):
        if X.shape[0] == 0:
            return
        Xw = X.multiply(w[:, None]).tocsr()
        self.A += np.asarray((X.T @ Xw).todense())
        self.s += np.asarray(Xw.sum(axis=0)).ravel()
        self.cs += np.asarray(X.sum(axis=0)).ravel()
        self.css += np.asarray(X.multiply(X).sum(axis=0)).ravel()
        Yf = np.nan_to_num(Y, nan=0.0)
        self.B += np.asarray(X.T @ (Yf * w[:, None]))
        self.wy += (Yf * w[:, None]).sum(axis=0)
        self.sw += float(w.sum())
        self.n += X.shape[0]

    def solve(self, alpha, scale_cols=None):
        """Returns (coef p x K, intercept K, ybar K).

        The design matrix has already been standardised on the frozen bootstrap
        (see `standardise_on_bootstrap`), so this only has to apply Ridge's own
        weighted centering: (Zc'W Zc + alpha I) b = Zc'W yc.  Identical to
        MultiRidge with scale_cols=None, which f2_selftest.py asserts against
        sklearn.
        """
        if self.n < 50:
            return None
        sw = self.sw
        zbar = self.s / sw
        G = self.A - sw * np.outer(zbar, zbar)
        G = 0.5 * (G + G.T)
        G[np.diag_indices_from(G)] += alpha
        Lc = np.linalg.cholesky(G)
        ybar = self.wy / sw
        Bc = self.B - np.outer(self.s, ybar)
        Bc -= np.outer(zbar, (self.wy - sw * ybar))
        coef = np.linalg.solve(Lc.T, np.linalg.solve(Lc, Bc))
        icpt = ybar - (zbar @ coef)
        return coef, icpt, ybar


def build_targets(meta, tgt, filled):
    """Target matrix and the three training populations.

    R  resolved rows -- where the SHIPPED label terminal_net_r exists
    F  walker-filled rows -- where an excursion exists.  F is NOT a subset of R:
       the walker fills 19,865 rows the sealed labeller censors outright.
    B  R and F -- the EXACTLY MATCHED population.  Stage L's head-to-head runs
       here so that `terminal_net_r` and `mfe` see identical rows, identical
       weights, identical folds and identical estimator; the F-vs-B gap is
       reported separately as the censoring gain.
    """
    res = np.asarray([m["res"] for m in meta], dtype=bool)
    both = res & filled
    names, cols, pops = [], [], []
    for nm in L.ALL_TARGETS:
        names.append(nm); cols.append(tgt[nm]); pops.append("F")
    names.append("tnr"); cols.append(tgt["tnr"]); pops[names.index("tnr")] = "R"
    # de-duplicate: tnr was already in ALL_TARGETS
    names, cols, pops = [], [], []
    for nm in L.ALL_TARGETS:
        if nm in ("tnr", "mfe_collapse"):
            names.append(nm); cols.append(tgt[nm]); pops.append("R")
        else:
            names.append(nm); cols.append(tgt[nm]); pops.append("F")
    names.append("fill"); cols.append(np.where(res, filled.astype(float), np.nan)); pops.append("R")
    # the matched-population pair
    for nm in ("tnr", "mfe", "mae", "ratio", "tmfe", "mfe_capped"):
        names.append(nm + "_B"); cols.append(tgt[nm]); pops.append("B")
    Y = np.column_stack(cols)
    return names, Y, np.asarray(pops, dtype=object), res, both


def pop_weights(meta, member):
    """1/(candidates in the row's decision window) inside the given population."""
    cnt = defaultdict(int)
    for i, ok in enumerate(member):
        if ok:
            cnt[meta[i]["win"]] += 1
    w = np.zeros(len(meta))
    for i, ok in enumerate(member):
        if ok:
            w[i] = 1.0 / cnt[meta[i]["win"]]
    return w


def apply_lag1(meta, X, scored_rows_by_day, cdays):
    """T1: replace each row's feature vector with the most recent STRICTLY PRIOR
    scored-day vector for the same symbol.  Rows with no predecessor are dropped."""
    last = {}
    src = np.full(len(meta), -1, dtype=np.int64)
    for d in cdays:
        rows = scored_rows_by_day.get(d, [])
        for i in rows:
            s = last.get(meta[i]["sym"])
            if s is not None:
                src[i] = s
        seen = {}
        for i in rows:
            seen[meta[i]["sym"]] = i
        last.update(seen)
    ok = src >= 0
    Xl = X[np.where(ok, src, 0)]
    return Xl, ok


def standardise_on_bootstrap(meta, X, names_col):
    """Standardise the numeric + indicator block using the FROZEN BOOTSTRAP only.

    B3 refits sklearn's StandardScaler on the expanding window each day.  F2
    fixes the scaler on the bootstrap instead, for two reasons, both declared:
    (1) the raw numeric columns span ~6 orders of magnitude (`poi_age_hours`
    against `risk_fraction_of_entry`), and forming the centred Gram by expansion
    at that spread is not positive definite in float64; (2) a bootstrap-only
    scaler is STRICTLY PRIOR to every scored day, so it cannot see the window it
    is scoring.  B6 measured the expanding-window scaler leak at exactly 0.0000
    (`B6_REGIME_OVERLAY_BOOK_V1.md` L1), so nothing is given up.
    """
    isnum = np.asarray([not any(c.startswith(f"{cc}=") for cc in L.CAT0)
                        for c in names_col])
    boot = np.asarray([not m["cday"].startswith("0002-") for m in meta])
    Xb = X[boot]
    nb = Xb.shape[0]
    mu = np.asarray(Xb.sum(axis=0)).ravel() / nb
    var = np.asarray(Xb.multiply(Xb).sum(axis=0)).ravel() / nb - mu ** 2
    sd = np.sqrt(np.maximum(var, 0.0))
    # Only the numeric + indicator block is shifted, so only that block becomes
    # dense.  The one-hot block stays sparse and is left untouched, exactly as
    # b3_lib's ColumnTransformer leaves it.
    Xc = X.tocsc()
    cat = Xc[:, ~isnum].tocsr()
    num = np.asarray(Xc[:, isnum].todense())
    num = (num - mu[isnum]) / np.where(sd[isnum] > 1e-12, sd[isnum], 1.0)
    Xs = sp.hstack([cat, sp.csr_matrix(num)], format="csr")
    order = [c for c, k in zip(names_col, isnum) if not k] + \
            [c for c, k in zip(names_col, isnum) if k]
    return Xs, order, {"n_bootstrap_rows": int(nb), "n_scaled_cols": int(isnum.sum()),
                       "n_onehot_cols": int((~isnum).sum())}


def main(variant="base", months=None):
    meta, X, names_col, tgt, filled, ded, info = L.build_dataset()
    log(stage="dataset", **info, p=X.shape[1])
    names, Y, pop, res, both = build_targets(meta, tgt, filled)
    K = len(names)
    X, names_col, sinfo = standardise_on_bootstrap(meta, X, names_col)
    scale_cols = None
    # fidelity: the walker's own fill disposition against the sealed label
    sealed_fill = np.asarray([m["fil"] for m in meta], dtype=bool)
    sinfo["sealed_filled"] = int(sealed_fill.sum())
    sinfo["walker_filled"] = int(filled.sum())
    sinfo["agree"] = int((sealed_fill == filled).sum())
    sinfo["sealed_only"] = int((sealed_fill & ~filled).sum())
    sinfo["walker_only"] = int((~sealed_fill & filled).sum())
    log(stage="targets", K=K, **sinfo,
        n_resolved=int(res.sum()), n_filled=int(filled.sum()))

    cdays, scored = L.day_chain(meta)
    rows_by_day = defaultdict(list)
    for i, m in enumerate(meta):
        rows_by_day[m["cday"]].append(i)

    members = {"R": res.copy(), "F": filled.copy(), "B": both.copy()}
    weights = {k: pop_weights(meta, v) for k, v in members.items()}

    if variant == "lag1":
        Xf, okl = apply_lag1(meta, X, rows_by_day, cdays)
        log(stage="lag1", kept=int(okl.sum()), dropped=int((~okl).sum()))
    else:
        Xf, okl = X, np.ones(len(meta), dtype=bool)

    if variant == "shuf":
        rng = np.random.default_rng(L.SEED)
        bywin = defaultdict(list)
        for i in range(len(meta)):
            bywin[meta[i]["win"]].append(i)
        Y = Y.copy()
        for win, idx in bywin.items():
            idx = np.asarray(idx)
            perm = rng.permutation(len(idx))
            Y[idx] = Y[idx[perm]]
        log(stage="shuffled_within_window", windows=len(bywin))

    # label-span end, for the embargo variant
    if variant == "emb1":
        t1 = np.asarray([str(m["t1"] or "")[:10] for m in meta])

    kidx = {g: [k for k in range(K) if pop[k] == g] for g in ("R", "F", "B")}
    accs = {g: Accum(X.shape[1], len(kidx[g])) for g in kidx}
    preds = np.full((len(meta), K), np.nan)
    pending = []
    ybar_hist = {}
    ntr_hist = {}
    done = []

    for d in cdays:
        rows = np.asarray(rows_by_day[d], dtype=np.int64)
        if d.startswith("0002-"):
            sc = rows[okl[rows]]
            for g in ("R", "F", "B"):
                acc, ks = accs[g], kidx[g]
                out = acc.solve(L.RIDGE_ALPHA, scale_cols)
                if out is None or len(sc) == 0:
                    continue
                coef, icpt, ybar = out
                P = np.asarray(Xf[sc] @ coef) + icpt
                preds[np.ix_(sc, ks)] = P
                for c, k in enumerate(ks):
                    ybar_hist.setdefault(names[k], {})[d] = float(ybar[c])
                    ntr_hist.setdefault(names[k], {})[d] = int(acc.n)
            done.append(d)
            if len(done) % 20 == 0:
                log(stage="day", variant=variant, day=d, done=len(done),
                    **{f"n{g}": accs[g].n for g in accs})
        # ---- absorb the day into training ----------------------------------
        # T5 embargo: hold each day's rows back one scored day, so a row may
        # enter training only once its label span has closed strictly before the
        # scored day begins. B3 measured every late label is exactly +1 day
        # (23,790/481,098 = 4.9449 %), so one day removes 100 % of it.
        add = rows[okl[rows]]
        if variant == "emb1":
            pending.append(add)
            if len(pending) <= 1:
                continue
            add = pending.pop(0)
        for g in ("R", "F", "B"):
            sel = add[members[g][add]]
            if len(sel) == 0:
                continue
            accs[g].add(Xf[sel], Y[np.ix_(sel, kidx[g])], weights[g][sel])

    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / f"preds_{variant}.npz", preds=preds.astype(np.float32),
                        names=np.asarray(names), scored=np.asarray(done))
    with (OUT / f"meta_{variant}.json").open("w") as fh:
        json.dump({"variant": variant, "days_done": done, "K": K, "names": names,
                   "n_rows": len(meta), "n_resolved": int(res.sum()),
                   "n_filled": int(filled.sum()), "n_both": int(both.sum()),
                   "p": int(X.shape[1]), "populations": {g: int(members[g].sum()) for g in members},
                   "census_joined": info["census_joined"],
                   "ybar_last": {k: v[done[-1]] for k, v in ybar_hist.items() if done[-1] in v},
                   "ntrain_last": {k: v[done[-1]] for k, v in ntr_hist.items() if done[-1] in v},
                   "prereg_sha256": L.PREREG_SHA}, fh, indent=1)
    log(stage="DONE", variant=variant, days=len(done))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
