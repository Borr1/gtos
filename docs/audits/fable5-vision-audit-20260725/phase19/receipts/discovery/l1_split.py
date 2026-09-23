#!/usr/bin/env python3
"""l1 pass 6 — is the best exit cell a FIT or a FINDING?

Splits January by decision date (TRAIN = days 01-15, TEST = days 16-31), fits the argmax
(T,S) cell on TRAIN for each stratum, and reports what that fitted cell earns on TEST.
A best cell picked over a 180-cell grid is an in-sample statistic; this converts it into a
tested one.  Also measures the 2-hour drift on the born x side x family intersections with
t-statistics, which is the instrument that says whether any drift exists to harvest at all.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_SPLIT_V1.json")
GRID = [(T, S) for T in FAV for S in ADV]


def cellmean(rows, T, S):
    return mean(cell(r, T, S, "r")[0] for r in rows)


def tstat(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n < 3:
        return None, None, None
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = (v / n) ** 0.5
    return round(m, 6), round(se, 6), (round(m / se, 3) if se > 0 else None)


def fit_eval(tr, te, label):
    if len(tr) < 40 or len(te) < 40:
        return None
    best = max(GRID, key=lambda ts: cellmean(tr, *ts))
    return {"stratum": label, "n_train": len(tr), "n_test": len(te),
            "fit_T": best[0], "fit_S": best[1],
            "train_R": round(cellmean(tr, *best), 5),
            "test_R": round(cellmean(te, *best), 5),
            "train_T2S1": round(cellmean(tr, 2.0, 1.0), 5),
            "test_T2S1": round(cellmean(te, 2.0, 1.0), 5),
            "test_delta_vs_T2S1": round(cellmean(te, *best) - cellmean(te, 2.0, 1.0), 5),
            "shrinkage": round(cellmean(te, *best) - cellmean(tr, *best), 5)}


def main():
    recs = pop(load(), "TAKEABLE")
    for r in recs:
        r["_day"] = int(r["decision_time_utc"][8:10])
    TR = [r for r in recs if r["_day"] <= 15]
    TE = [r for r in recs if r["_day"] >= 16]
    res = {"population": "TAKEABLE, fill REAL", "n": len(recs),
           "train_days": "01-15", "n_train": len(TR), "test_days": "16-31", "n_test": len(TE),
           "grid_cells": len(GRID)}
    res["POOL"] = fit_eval(TR, TE, "POOL")

    def by(keyf, name, min_n=40):
        gt, ge = {}, {}
        for r in TR:
            gt.setdefault(keyf(r), []).append(r)
        for r in TE:
            ge.setdefault(keyf(r), []).append(r)
        out = {}
        for k in sorted(set(gt) & set(ge), key=str):
            fe = fit_eval(gt[k], ge[k], str(k))
            if fe and fe["n_train"] >= min_n and fe["n_test"] >= min_n:
                out[str(k)] = fe
        res[name] = out
        # portfolio: apply each stratum's TRAIN-fitted cell to its own TEST rows
        num = 0.0
        den = 0
        for k, fe in out.items():
            rows = ge[k] if k in ge else [r for r in TE if str(keyf(r)) == k]
            num += sum(cell(r, fe["fit_T"], fe["fit_S"], "r")[0] for r in rows)
            den += len(rows)
        base = mean(cell(r, 2.0, 1.0, "r")[0] for r in TE)
        res[name + "_PORTFOLIO"] = {"n_test_covered": den,
                                    "test_R_fitted_policy": round(num / den, 5) if den else None,
                                    "test_R_flat_T2S1_all_TEST": round(base, 5),
                                    "delta": round((num / den) - base, 5) if den else None}

    by(lambda r: r["family"], "by_family")
    by(lambda r: r["symbol"], "by_symbol")
    by(lambda r: r["side"], "by_side")
    by(lambda r: r["born"], "by_born")
    by(lambda r: "%s|%s" % (r["family"], r["side"]), "by_family_side")
    by(lambda r: r["session"], "by_session")

    # ---- 2h drift on intersections (mark-to-market at the wall, no exit logic)
    drift = {}
    for name, keyf in (("born", lambda r: r["born"]),
                       ("born_side", lambda r: "%s|%s" % (r["born"], r["side"])),
                       ("born_family", lambda r: "%s|%s" % (r["born"], r["family"])),
                       ("family_side", lambda r: "%s|%s" % (r["family"], r["side"])),
                       ("symbol_side", lambda r: "%s|%s" % (r["symbol"], r["side"])),
                       ("born_side_family", lambda r: "%s|%s|%s" % (r["born"], r["side"], r["family"]))):
        g = {}
        for r in recs:
            if r.get("tf_r") is None:
                continue
            g.setdefault(keyf(r), []).append(r["cls_end"])
        blk = {}
        for k, xs in g.items():
            if len(xs) < 40:
                continue
            m, se_, t = tstat(xs)
            blk[str(k)] = {"n": len(xs), "mean_R_at_wall": m, "se": se_, "t": t,
                           "share_pos": round(sum(1 for x in xs if x > 0) / len(xs), 5)}
        drift[name] = dict(sorted(blk.items(), key=lambda kv: -(kv[1]["mean_R_at_wall"] or -9)))
    res["DRIFT_AT_2H"] = drift
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    p = res["POOL"]
    print("SPLIT n_train=%d n_test=%d | POOL fit T%.2f/S%.2f train %+.5f -> TEST %+.5f (flat T2S1 test %+.5f, delta %+.5f)"
          % (res["n_train"], res["n_test"], p["fit_T"], p["fit_S"], p["train_R"], p["test_R"],
             p["test_T2S1"], p["test_delta_vs_T2S1"]))
    for nm in ("by_family", "by_side", "by_born", "by_family_side", "by_symbol"):
        pf = res[nm + "_PORTFOLIO"]
        print("%-16s PORTFOLIO n=%s fitted %+.5f vs flat %+.5f delta %+.5f"
              % (nm, pf["n_test_covered"], pf["test_R_fitted_policy"] or 0,
                 pf["test_R_flat_T2S1_all_TEST"], pf["delta"] or 0))
    print("--- by_family fit->test ---")
    for k, fe in sorted(res["by_family"].items(), key=lambda kv: -kv[1]["test_R"]):
        print("  %-32s ntr%5d nte%5d T%.2f/S%.2f tr %+.4f te %+.4f (T2S1 te %+.4f) shrink %+.4f"
              % (k[:32], fe["n_train"], fe["n_test"], fe["fit_T"], fe["fit_S"],
                 fe["train_R"], fe["test_R"], fe["test_T2S1"], fe["shrinkage"]))
    print("--- DRIFT@2h born_side ---")
    for k, d in res["DRIFT_AT_2H"]["born_side"].items():
        print("  %-28s n%6d mean %+.4f t %s pos %.3f" % (k, d["n"], d["mean_R_at_wall"], d["t"], d["share_pos"]))
    print("--- DRIFT@2h top-8 born_side_family ---")
    for k, d in list(res["DRIFT_AT_2H"]["born_side_family"].items())[:8]:
        print("  %-52s n%5d mean %+.4f t %s" % (k[:52], d["n"], d["mean_R_at_wall"], d["t"]))


if __name__ == "__main__":
    main()
