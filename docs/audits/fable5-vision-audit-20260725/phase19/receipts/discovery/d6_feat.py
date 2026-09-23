"""d6_feat — can anything OBSERVABLE at T+k tell a confirming setup from a phantom?

The +0.209 R/trade earliness lever lives on the PAIRED subset — the setups that
also emit at the M15 close.  That membership is not knowable at T+k.  This module
builds every feature the forming bar itself can supply at the decision instant
(nothing after it is ever read) and asks two questions:

  (a) does any of them separate paired from phantom;
  (b) does any RULE over them produce a partial-bar book that is net-positive,
      fitted on January and tested on February + March.

    python3 d6_feat.py --months 202601,202602,202603 --out /tmp/d6/D6_FEAT_V1.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PBG))
sys.path.insert(0, str(HERE.parents[5]))

import d6_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402


def featurise(month, fams):
    rows = D.load(month, fams=fams)
    tape = E.Tape(L.SYMBOLS, [month])
    out = []
    for r in rows:
        P = r.get("P")
        if not P:
            continue
        i = tape.idx(r["t_part"])          # decision stamp
        j = tape.idx(r["b"])               # forming bar's open stamp
        if j < 0 or i <= j:
            continue
        o = tape.o[r["s"]][j:i]
        h = tape.h[r["s"]][j:i]
        lo = tape.l[r["s"]][j:i]
        ok = ~np.isnan(h)
        if not ok.any():
            continue
        bar_open = float(o[ok][0])
        hh = float(np.nanmax(h))
        ll = float(np.nanmin(lo))
        d = P["d"]
        e = P["e"]
        long = r["sd"] == "L"
        disp_r = ((e - bar_open) if long else (bar_open - e)) / d
        rng_r = (hh - ll) / d
        span = hh - ll
        pos = ((e - ll) / span) if span > 0 else 0.5
        if not long:
            pos = 1.0 - pos
        # adverse excursion already taken inside the forming bar, in R
        mae_r = ((bar_open - ll) if long else (hh - bar_open)) / d
        out.append({
            "m": month, "f": r["f"], "s": r["s"], "sd": r["sd"],
            "day": r["day_part"], "k": r["k"], "hr": P["hr"],
            "paired": 1 if r.get("C") else 0,
            "net": P["g2"] - P["cr"], "gross": P["g2"], "cost": P["cr"],
            "risk_bps": d / e * 1e4,
            "disp_r": disp_r, "rng_r": rng_r, "pos": pos, "mae_r": mae_r,
            "minutes_in": 15 - r["k"] if r["k"] else None,
        })
    return out


def auc(pos, neg):
    """Mann-Whitney AUC of `pos` over `neg`."""
    a = np.concatenate([pos, neg])
    order = a.argsort()
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1)
    # tie correction is immaterial at this n; report the plain statistic
    r1 = ranks[: len(pos)].sum()
    n1, n2 = len(pos), len(neg)
    return (r1 - n1 * (n1 + 1) / 2) / (n1 * n2)


def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return None
    sp = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else None


def bookstat(rows):
    if not rows:
        return {"n": 0}
    n = np.array([r["net"] for r in rows])
    by_day = defaultdict(lambda: [0.0, 0])
    for r in rows:
        by_day[r["m"] + "|" + r["day"]][0] += r["net"]
        by_day[r["m"] + "|" + r["day"]][1] += 1
    return {"n": int(len(n)), "net_r": float(n.mean()),
            "gross_r": float(np.mean([r["gross"] for r in rows])),
            "cost_r": float(np.mean([r["cost"] for r in rows])),
            "paired_frac": float(np.mean([r["paired"] for r in rows])),
            "days_positive": sum(1 for d in by_day if by_day[d][0] > 0),
            "n_days": len(by_day),
            "boot": D.bootstrap_days(by_day)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--train", default="202601")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()
    fams = set(D.EARLY5)

    data = []
    for m in months:
        data += featurise(m, fams)
    res = {"months": months, "n_rows": len(data),
           "generated_utc": datetime.now(timezone.utc).isoformat()}

    FEATS = ("k", "hr", "risk_bps", "disp_r", "rng_r", "pos", "mae_r")

    # --- (a) separability of paired vs phantom, pooled and per month
    sep = {}
    for m in ["ALL"] + months:
        sub = data if m == "ALL" else [r for r in data if r["m"] == m]
        P = [r for r in sub if r["paired"]]
        Q = [r for r in sub if not r["paired"]]
        cell = {"n_paired": len(P), "n_phantom": len(Q)}
        for f in FEATS:
            a = np.array([r[f] for r in P], float)
            b = np.array([r[f] for r in Q], float)
            a = a[np.isfinite(a)]
            b = b[np.isfinite(b)]
            if len(a) < 2 or len(b) < 2:
                continue
            cell[f] = {"mean_paired": float(a.mean()), "mean_phantom": float(b.mean()),
                       "cohens_d": cohens_d(a, b), "auc": float(auc(a, b))}
        sep[m] = cell
    res["separability"] = sep

    # --- (b) rule search.  Fit on train month(s), test on the rest.
    train = [r for r in data if r["m"] == args.train]
    test = [r for r in data if r["m"] != args.train]
    grid = []
    for f in FEATS:
        vals = np.array([r[f] for r in train if np.isfinite(r[f])], float)
        if not len(vals):
            continue
        qs = np.percentile(vals, [10, 20, 30, 40, 50, 60, 70, 80, 90])
        for q in np.unique(np.round(qs, 6)):
            for op in (">=", "<="):
                sel_tr = [r for r in train if (r[f] >= q if op == ">=" else r[f] <= q)]
                if len(sel_tr) < 200:
                    continue
                st = bookstat(sel_tr)
                se = bookstat([r for r in test if (r[f] >= q if op == ">=" else r[f] <= q)])
                grid.append({"feature": f, "op": op, "thr": float(q),
                             "train": st, "test": se})
    grid.sort(key=lambda g: -(g["train"]["net_r"] if g["train"]["n"] else -9))
    res["single_rule_grid_top20_by_train"] = grid[:20]
    res["single_rule_grid_best_test"] = sorted(
        grid, key=lambda g: -(g["test"]["net_r"] if g["test"].get("n") else -9))[:10]
    res["single_rule_n_cells"] = len(grid)
    res["single_rule_n_train_positive"] = sum(1 for g in grid if g["train"]["net_r"] > 0)
    res["single_rule_n_test_positive"] = sum(
        1 for g in grid if g["test"].get("n") and g["test"]["net_r"] > 0)

    # --- (c) the whole-population reference and the family cells
    res["reference"] = {
        "partial_book_all": bookstat(data),
        "paired_only_ORACLE": bookstat([r for r in data if r["paired"]]),
        "phantom_only": bookstat([r for r in data if not r["paired"]]),
    }
    res["by_family"] = {f: bookstat([r for r in data if r["f"] == f]) for f in D.EARLY5}

    # --- (d) two-feature conjunctions on the train month, tested out of sample
    best2 = []
    fq = {}
    for f in FEATS:
        v = np.array([r[f] for r in train if np.isfinite(r[f])], float)
        fq[f] = np.unique(np.round(np.percentile(v, [20, 40, 60, 80]), 6)) if len(v) else []
    for i, f1 in enumerate(FEATS):
        for f2 in FEATS[i + 1:]:
            for t1 in fq[f1]:
                for o1 in (">=", "<="):
                    for t2 in fq[f2]:
                        for o2 in (">=", "<="):
                            def ok(r):
                                a = r[f1] >= t1 if o1 == ">=" else r[f1] <= t1
                                b = r[f2] >= t2 if o2 == ">=" else r[f2] <= t2
                                return a and b
                            sel = [r for r in train if ok(r)]
                            if len(sel) < 200:
                                continue
                            st = bookstat(sel)
                            best2.append({"f1": f1, "op1": o1, "t1": float(t1),
                                          "f2": f2, "op2": o2, "t2": float(t2),
                                          "train": st,
                                          "test": bookstat([r for r in test if ok(r)])})
    best2.sort(key=lambda g: -g["train"]["net_r"])
    res["pair_rule_n_cells"] = len(best2)
    res["pair_rule_n_train_positive"] = sum(1 for g in best2 if g["train"]["net_r"] > 0)
    res["pair_rule_top10_by_train"] = best2[:10]
    res["pair_rule_best_test"] = sorted(
        best2, key=lambda g: -(g["test"]["net_r"] if g["test"].get("n") else -9))[:5]

    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out, len(data), "rows;", len(grid), "single cells;", len(best2), "pair cells")


if __name__ == "__main__":
    main()
