#!/usr/bin/env python3
"""F4 task 2 — ex-ante separability on the EXCURSION target.

The question every prior experiment failed at was "rank terminal net R". This
poses a different and much less censored one:

    among trades that actually happened, can information available BEFORE entry
    separate the ones that went to +1.5R from the ones that never cleared +0.3R?

Arms, targets, controls and decision rules are frozen in F4_PREREG_V1.json
(sha256 bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054).

Read-only. Writes receipts.
"""
from __future__ import annotations

import gzip
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import (CATEGORICAL, EVAL_FOLDS, MONTHS, NUMERIC, assert_no_leak,  # noqa: E402
                       enrich, jdump, load_month)

HERE = Path(__file__).parent
OUT = HERE / "receipts"
SEED = 20260812

ARMS = {
    "A2a": dict(max_iter=100, max_leaf_nodes=15, learning_rate=0.05),
    "A2b": dict(max_iter=400, max_leaf_nodes=15, learning_rate=0.05),
    "A2c": dict(max_iter=400, max_leaf_nodes=63, learning_rate=0.05),
    "A2d": dict(max_iter=1200, max_leaf_nodes=63, learning_rate=0.05),
}


def build_rows():
    rows = []
    for m in MONTHS:
        rows += enrich(load_month(m))
    with gzip.open(HERE / "f4_excursion_join.pkl.gz", "rb") as f:
        exc = {r["candidate_occurrence_key"]: r for r in pickle.load(f)}
    with gzip.open(HERE / "f4_new_features.pkl.gz", "rb") as f:
        new = pickle.load(f)
    out = []
    for r in rows:
        e = exc.get(r["candidate_occurrence_key"])
        if e is None:
            continue
        r["mfe"] = e["mfe"]
        r["mae"] = e["mae"]
        r["_new"] = new.get(r["candidate_occurrence_key"], {})
        out.append(r)
    newnames = sorted({k for v in new.values() for k in v})
    return out, newnames


def encode(rows, newnames, use_new: bool, lag_map=None):
    """Ordinal-encode categoricals, stack numerics. Returns X, names, cat_mask.

    lag_map: optional {key -> donor row} used by control C1.
    """
    names = list(CATEGORICAL) + list(NUMERIC) + (list(newnames) if use_new else [])
    assert_no_leak(names)                                   # control C3
    n = len(rows)
    X = np.full((n, len(names)), np.nan)
    cat_mask = np.zeros(len(names), dtype=bool)
    src = [lag_map.get(r["candidate_occurrence_key"], r) if lag_map else r for r in rows]
    for j, k in enumerate(CATEGORICAL):
        cat_mask[j] = True
        vocab = {}
        col = np.empty(n)
        for i, r in enumerate(src):
            v = str(r.get(k))
            col[i] = vocab.setdefault(v, len(vocab))
        X[:, j] = col
    off = len(CATEGORICAL)
    for j, k in enumerate(NUMERIC):
        X[:, off + j] = [r.get(k, np.nan) if r.get(k) is not None else np.nan for r in src]
    if use_new:
        off2 = off + len(NUMERIC)
        for j, k in enumerate(newnames):
            X[:, off2 + j] = [r["_new"].get(k, np.nan) for r in src]
    return X, names, cat_mask


def labels(rows, target: str):
    """Returns y (0/1) and a keep mask."""
    if target == "S2_EXCURSION":
        y = np.array([1 if r["mfe"] >= 1.5 else (0 if r["mfe"] < 0.3 else -1) for r in rows])
    elif target == "S1_STATUS":
        y = np.array([1 if r["lifecycle_label_status"] == "RESOLVED_FILLED_TARGET"
                      else (0 if r["lifecycle_label_status"] == "RESOLVED_FILLED_STOP" else -1)
                      for r in rows])
    else:
        raise ValueError(target)
    return y, y >= 0


def fit_score(Xtr, ytr, Xte, kind: str, cat_mask=None, **kw):
    if kind == "logit":
        med = np.nanmedian(Xtr, axis=0)
        med = np.where(np.isnan(med), 0.0, med)
        A = np.where(np.isnan(Xtr), med, Xtr)
        B = np.where(np.isnan(Xte), med, Xte)
        mu, sd = A.mean(0), A.std(0) + 1e-9
        m = LogisticRegression(C=1.0, max_iter=2000)
        m.fit((A - mu) / sd, ytr)
        return m.predict_proba((B - mu) / sd)[:, 1]
    m = HistGradientBoostingClassifier(
        random_state=SEED, categorical_features=cat_mask, early_stopping=False, **kw)
    m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]


def walk(rows, newnames, target, arm, use_new, lag_map=None, subset=None):
    """Expanding-window walk forward. Returns per-fold and pooled results."""
    R = [r for r in rows if (subset is None or subset(r))]
    y, keep = labels(R, target)
    R = [r for r, k in zip(R, keep) if k]
    y = y[keep]
    X, names, cm = encode(R, newnames, use_new, lag_map)
    mon = np.array([r["month"] for r in R])
    folds, pooled_s, pooled_y, pooled_r = {}, [], [], []
    for f in EVAL_FOLDS:
        prior = MONTHS[:MONTHS.index(f)]
        tr = np.isin(mon, prior)
        te = mon == f
        if tr.sum() < 500 or te.sum() < 200:
            continue
        # control C6 — group disjointness
        assert not (set(r["decision_window_id"] for r, m in zip(R, tr) if m)
                    & set(r["decision_window_id"] for r, m in zip(R, te) if m))
        if arm == "A1":
            s = fit_score(X[tr], y[tr], X[te], "logit")
        elif arm == "A0":
            raw = [r.get("pred_month_boundary") for r, m in zip(R, te) if m]
            s = np.array([np.nan if v is None else float(v) for v in raw], dtype=float)
            if np.isnan(s).all():
                continue
            s = np.where(np.isnan(s), np.nanmedian(s), s)
        else:
            s = fit_score(X[tr], y[tr], X[te], "hgb", cat_mask=cm, **ARMS[arm])
        yt = y[te]
        auc = float(roc_auc_score(yt, s)) if len(set(yt)) > 1 else float("nan")
        k = max(1, int(0.10 * len(s)))
        top = np.argsort(-s)[:k]
        te_rows = [r for r, m in zip(R, te) if m]
        netr = np.array([r["terminal_net_r"] for r in te_rows])
        folds[f] = {
            "n_train": int(tr.sum()), "n_test": int(te.sum()), "auc": auc,
            "base_rate": float(yt.mean()),
            "top_decile_precision": float(yt[top].mean()),
            "top_decile_net_r_mean": float(netr[top].mean()),
            "all_net_r_mean": float(netr.mean()),
        }
        pooled_s.append(s); pooled_y.append(yt); pooled_r.append(netr)
    if not folds:
        return {"folds": {}, "pooled": {}}
    S = np.concatenate(pooled_s); Y = np.concatenate(pooled_y); NR = np.concatenate(pooled_r)
    k = max(1, int(0.10 * len(S)))
    top = np.argsort(-S)[:k]
    return {"folds": folds, "pooled": {
        "n": int(len(S)), "auc": float(roc_auc_score(Y, S)),
        "base_rate": float(Y.mean()),
        "top_decile_precision": float(Y[top].mean()),
        "top_decile_net_r_mean": float(NR[top].mean()),
        "top_decile_net_r_sum": float(NR[top].sum()),
        "all_net_r_mean": float(NR.mean()),
        "folds_auc_ge_055": int(sum(1 for v in folds.values() if v["auc"] >= 0.55)),
    }}


def main() -> None:
    rows, newnames = build_rows()
    print(f"rows with excursion+features: {len(rows)}; new features: {len(newnames)}")
    res = {"prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
           "n_rows": len(rows), "new_feature_names": newnames, "seed": SEED}

    for target in ("S2_EXCURSION", "S1_STATUS"):
        y, keep = labels(rows, target)
        res[f"{target}_population"] = {
            "n_positive": int((y == 1).sum()), "n_negative": int((y == 0).sum()),
            "n_excluded_middle": int((y == -1).sum()),
            "base_rate": float((y[keep] == 1).mean()),
        }
        block = {}
        for arm in ["A0", "A1", "A2a", "A2b", "A2c", "A2d"]:
            block[arm] = walk(rows, newnames, target, arm, use_new=False)
            p = block[arm]["pooled"]
            print(f"  {target} {arm:4s} frozen43  AUC={p.get('auc', float('nan')):.4f} "
                  f"topdec_prec={p.get('top_decile_precision', float('nan')):.4f} "
                  f"topdec_netR={p.get('top_decile_net_r_mean', float('nan')):+.4f}", flush=True)
        best = max([a for a in block if a.startswith("A2")],
                   key=lambda a: block[a]["pooled"].get("auc", 0))
        block["A3"] = walk(rows, newnames, target, best, use_new=True)
        block["A3_capacity_from"] = best
        p = block["A3"]["pooled"]
        print(f"  {target} A3   +NEW({best}) AUC={p.get('auc', float('nan')):.4f} "
              f"topdec_prec={p.get('top_decile_precision', float('nan')):.4f} "
              f"topdec_netR={p.get('top_decile_net_r_mean', float('nan')):+.4f}", flush=True)
        # ablation: each new family alone on top of the frozen 43
        fams = {"N1_htf": [n for n in newnames if n.startswith("htf_")],
                "N2_feas": [n for n in newnames if n.startswith(("feas_", "vol_term_"))],
                "N3_pool": [n for n in newnames if n.startswith("pool_")],
                "N1b_regime": [n for n in newnames if n.startswith("regime_")]}
        abl = {}
        for fname, cols in fams.items():
            if not cols:
                continue
            abl[fname] = walk(rows, cols, target, best, use_new=True)["pooled"]
            print(f"    ablation {fname:12s} AUC={abl[fname].get('auc', float('nan')):.4f}", flush=True)
        block["ablation_single_family"] = abl
        # ---- the decisive control: is the AUC just trade GEOMETRY? ----------
        # MFE is denominated in stop-distance units, so a wide stop relative to
        # volatility mechanically fails to reach +1.5R. If a model given ONLY the
        # geometry reaches the same AUC, the "separability" is unit arithmetic and
        # says nothing about setup quality.
        import f4_common as _c
        _keep = list(_c.NUMERIC); _keepcat = list(_c.CATEGORICAL)
        for geo_name, geo_cols in (
                ("GEOM3", ["risk_over_atr", "cost_r", "spread_r"]),
                ("GEOM1", ["risk_over_atr"]),
                ("NO_GEOM", [c for c in _keep if c not in
                             ("risk_over_atr", "cost_r", "spread_r", "commission_r",
                              "swap_cost_r", "expected_slippage_r", "risk_fraction_of_entry",
                              "stop_distance_atr", "target_distance_atr")])):
            _c.NUMERIC = geo_cols
            _c.CATEGORICAL = [] if geo_name.startswith("GEOM") else _keepcat
            try:
                block[f"control_{geo_name}"] = walk(rows, [], target, best, use_new=False)["pooled"]
                print(f"    control {geo_name:8s} ({len(geo_cols)} feats) "
                      f"AUC={block[f'control_{geo_name}'].get('auc', float('nan')):.4f} "
                      f"topdec_netR={block[f'control_{geo_name}'].get('top_decile_net_r_mean', float('nan')):+.4f}",
                      flush=True)
            finally:
                _c.NUMERIC = _keep; _c.CATEGORICAL = _keepcat
        # MARKET-only replication (no fill-selection conditioning)
        block["A3_market_only"] = walk(rows, newnames, target, best, use_new=True,
                                       subset=lambda r: r["proposed_order_type"] == "MARKET")
        block["A2_market_only"] = walk(rows, newnames, target, best, use_new=False,
                                       subset=lambda r: r["proposed_order_type"] == "MARKET")
        print(f"    MARKET-only  frozen43 AUC="
              f"{block['A2_market_only']['pooled'].get('auc', float('nan')):.4f}  "
              f"+NEW AUC={block['A3_market_only']['pooled'].get('auc', float('nan')):.4f}", flush=True)
        res[target] = block

    jdump(res, OUT / "F4_SEPARABILITY_V1.json")
    print("\nwrote F4_SEPARABILITY_V1.json")


if __name__ == "__main__":
    main()
