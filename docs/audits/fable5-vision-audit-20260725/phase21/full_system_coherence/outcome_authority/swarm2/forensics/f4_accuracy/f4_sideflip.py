#!/usr/bin/env python3
"""F4 — the side-flip control. The test that decides what the AUC 0.84 means.

MFE is denominated in stop-distance units, so a model can score well on
"will this reach +1.5R" purely by knowing MAGNITUDE — how far this instrument
typically travels in two hours relative to this trade's stop — with no opinion
whatever about DIRECTION. Such a model is arithmetic, not edge, and cannot make
money, because a trade needs the move to go the right way.

The test: for every filled trade, recompute the excursion it would have had on
the OPPOSITE side over the identical window, from the identical fill instant.
Everything -- symbol, instant, horizon, risk, volatility state, every feature
except the sign of `side` -- is held exactly constant.

  * If P(MFE >= k) is the same for the real side and the flipped side, the
    generator has no directional edge at all.
  * If a model predicts FLIPPED MFE as well as it predicts REAL MFE, then its
    apparent separability is magnitude arithmetic and carries no direction.

Read-only.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import (CATEGORICAL, EVAL_FOLDS, MONTHS, NUMERIC, enrich,  # noqa: E402
                       jdump, load_month)

HERE = Path(__file__).parent
OUT = HERE / "receipts"
WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
MONTH_SRC = {"feb": "202602", "apr": "202604", "may": "202605",
             "jun": "202606", "jul": "202607"}
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
KS = [0.5, 1.0, 1.5, 2.0]
SEED = 20260812


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_m1(month):
    out = {}
    for p in sorted((BARS / f"bridge_ftmo_m1_{MONTH_SRC[month]}").glob("*_M1.csv")):
        sym = p.name[:-7]
        rows = []
        with p.open(newline="") as fh:
            for row in csv.DictReader(fh):
                rows.append((row["time"], row["high"], row["low"]))
        rows = sorted(set(rows), key=lambda r: r[0])
        t = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(t) > 0])
        t = t[keep]
        rows = [r for r, k in zip(rows, keep) if k]
        out[sym] = dict(t=t,
                        h=np.array([float(r[1]) for r in rows]),
                        l=np.array([float(r[2]) for r in rows]))
    return out


def build():
    rows = []
    for m in MONTHS:
        rows += enrich(load_month(m))
    with gzip.open(HERE / "f4_excursion_join.pkl.gz", "rb") as f:
        exc = {r["candidate_occurrence_key"]: r["mfe"] for r in pickle.load(f)}
    with gzip.open(HERE / "f4_new_features.pkl.gz", "rb") as f:
        new = pickle.load(f)
    fil = []
    for r in rows:
        k = r["candidate_occurrence_key"]
        if k in exc:
            r["mfe"] = exc[k]
            r["_new"] = new.get(k, {})
            fil.append(r)

    # flipped excursion, from the SAME fill price and the SAME window
    for m in MONTHS:
        S = load_m1(m)
        wk = {}
        with gzip.open(WALK / f"walk_{m}.pkl.gz", "rb") as f:
            for r in pickle.load(f):
                wk[r["k"]] = r
        for r in [x for x in fil if x["month"] == m]:
            w = wk.get(r["candidate_occurrence_key"])
            s = S.get(r["symbol"])
            if w is None or s is None or not w.get("risk") or w.get("fp") is None:
                continue
            risk = float(w["risk"])
            fp = float(w["fp"])
            fm = int(w["fill_min"])
            span = mins(at(r["label_span_end_utc"])) - mins(at(r["label_span_start_utc"]))
            i0 = int(np.searchsorted(s["t"], fm, side="left"))
            i1 = int(np.searchsorted(s["t"], fm + span, side="right"))
            if i1 <= i0 or risk <= 0:
                continue
            d = 1.0 if r["side"] == "LONG" else -1.0
            # the excursion the OPPOSITE side would have seen, same fill, same window
            opp = ((fp - s["l"][i0:i1].min()) if d > 0 else (s["h"][i0:i1].max() - fp))
            r["mfe_flipped"] = float(opp / risk)
        print(f"flip {m} done", flush=True)
    return [r for r in fil if "mfe_flipped" in r]


def encode(rows, cols_num, cols_cat, cols_new):
    n = len(rows)
    X = np.full((n, len(cols_cat) + len(cols_num) + len(cols_new)), np.nan)
    cm = np.zeros(X.shape[1], dtype=bool)
    for j, k in enumerate(cols_cat):
        cm[j] = True
        vocab = {}
        X[:, j] = [vocab.setdefault(str(r.get(k)), len(vocab)) for r in rows]
    o = len(cols_cat)
    for j, k in enumerate(cols_num):
        X[:, o + j] = [r.get(k, np.nan) if r.get(k) is not None else np.nan for r in rows]
    o2 = o + len(cols_num)
    for j, k in enumerate(cols_new):
        X[:, o2 + j] = [r["_new"].get(k, np.nan) for r in rows]
    return X, cm


def walk_auc(rows, cols_num, cols_cat, cols_new, label_key, thr=1.5, lo=0.3):
    y = np.array([1 if r[label_key] >= thr else (0 if r[label_key] < lo else -1) for r in rows])
    keep = y >= 0
    R = [r for r, k in zip(rows, keep) if k]
    y = y[keep]
    X, cm = encode(R, cols_num, cols_cat, cols_new)
    mon = np.array([r["month"] for r in R])
    S, Y = [], []
    for f in EVAL_FOLDS:
        tr = np.isin(mon, MONTHS[:MONTHS.index(f)])
        te = mon == f
        if tr.sum() < 500 or te.sum() < 200:
            continue
        m = HistGradientBoostingClassifier(random_state=SEED, categorical_features=cm,
                                           early_stopping=False, max_iter=100,
                                           max_leaf_nodes=15, learning_rate=0.05)
        m.fit(X[tr], y[tr])
        S.append(m.predict_proba(X[te])[:, 1])
        Y.append(y[te])
    S, Y = np.concatenate(S), np.concatenate(Y)
    return {"auc": float(roc_auc_score(Y, S)), "n": int(len(S)), "base_rate": float(Y.mean())}


def main():
    rows = build()
    print(f"rows with both real and flipped excursion: {len(rows)}")
    newnames = sorted({k for r in rows for k in r["_new"]})
    N2 = [n for n in newnames if n.startswith(("feas_", "vol_term_"))]

    def dist(vals):
        a = np.array(vals)
        return {"mean": float(a.mean()), "median": float(np.median(a)),
                "frac_ge": {str(k): float((a >= k).mean()) for k in KS}}

    res = {"prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
           "n": len(rows), "seed": SEED,
           "note": ("The flipped arm uses the SAME fill price and the SAME window; it is the "
                    "excursion available to a trade identical in every respect except the sign "
                    "of side. It is measured from the real side's quote-adjusted fill, which "
                    "handicaps the flipped arm by one spread and therefore makes any positive "
                    "real-vs-flipped gap an UPPER bound on the generator's directional edge.")}

    for name, sub in (("ALL_FILLED", rows),
                      ("MARKET", [r for r in rows if r["proposed_order_type"] == "MARKET"]),
                      ("LIMIT", [r for r in rows if r["proposed_order_type"] == "LIMIT"])):
        real = dist([r["mfe"] for r in sub])
        flip = dist([r["mfe_flipped"] for r in sub])
        # paired bootstrap by trading day on P(MFE>=2R)
        days = defaultdict(list)
        for r in sub:
            days[r["trading_day"]].append(r)
        dk = list(days)
        rg = np.random.default_rng(SEED)
        bs = []
        for _ in range(2000):
            pick = rg.choice(len(dk), size=len(dk), replace=True)
            a = [x["mfe"] >= 2.0 for i in pick for x in days[dk[i]]]
            b = [x["mfe_flipped"] >= 2.0 for i in pick for x in days[dk[i]]]
            bs.append(np.mean(a) - np.mean(b))
        bs = np.array(bs)
        res[f"excursion_{name}"] = {
            "n": len(sub), "real": real, "flipped": flip,
            "directional_lift": {k: real["frac_ge"][k] - flip["frac_ge"][k] for k in real["frac_ge"]},
            "lift_at_2R_bootstrap": {"point": real["frac_ge"]["2.0"] - flip["frac_ge"]["2.0"],
                                     "ci95_lo": float(np.quantile(bs, .025)),
                                     "ci95_hi": float(np.quantile(bs, .975)),
                                     "p_gt_0": float((bs > 0).mean()), "n_days": len(dk)},
        }
        print(f"\n{name} n={len(sub)}")
        print(f"  real    P(MFE>=k): {real['frac_ge']}")
        print(f"  flipped P(MFE>=k): {flip['frac_ge']}")
        print(f"  lift            : {res[f'excursion_{name}']['directional_lift']}")
        print(f"  lift@2R boot    : {res[f'excursion_{name}']['lift_at_2R_bootstrap']}")

    # --- can the model predict the FLIPPED label just as well? --------------
    arms = {
        "frozen43_real": (NUMERIC, CATEGORICAL, [], "mfe"),
        "frozen43_flipped": (NUMERIC, CATEGORICAL, [], "mfe_flipped"),
        "frozen43_plus_new_real": (NUMERIC, CATEGORICAL, newnames, "mfe"),
        "frozen43_plus_new_flipped": (NUMERIC, CATEGORICAL, newnames, "mfe_flipped"),
        "N2_only_real": ([], [], N2, "mfe"),
        "N2_only_flipped": ([], [], N2, "mfe_flipped"),
        "geometry_only_real": (["risk_over_atr", "cost_r", "spread_r"], [], [], "mfe"),
        "geometry_only_flipped": (["risk_over_atr", "cost_r", "spread_r"], [], [], "mfe_flipped"),
        "risk_over_atr_only_real": (["risk_over_atr"], [], [], "mfe"),
    }
    res["model_on_flipped_label"] = {}
    for k, (cn, cc, cnew, lab) in arms.items():
        r = walk_auc(rows, cn, cc, cnew, lab)
        res["model_on_flipped_label"][k] = r
        print(f"  {k:30s} AUC={r['auc']:.4f}  base={r['base_rate']:.4f}  n={r['n']}", flush=True)

    jdump(res, OUT / "F4_SIDEFLIP_V1.json")
    print("\nwrote F4_SIDEFLIP_V1.json")


if __name__ == "__main__":
    main()
