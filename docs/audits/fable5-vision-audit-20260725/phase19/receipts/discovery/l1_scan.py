#!/usr/bin/env python3
"""l1 pass 9 — the exhaustive honest scan.

Objective = NET R per trade at the corrected cost model (spread/7.3 + commission +
slippage + swap).  Every filter used is observable AT THE DECISION INSTANT: born-state
(w0-capture's zero-look-ahead classification), pre-trade cost, family, symbol, side,
session.  Fit the (T,S) cell on Jan 01-15, report Jan 16-31.  Count the whole search so
the multiplicity is on the record.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_SCAN_V1.json")
N_ORIG = 27658
GRID = [(T, S) for T in FAV for S in ADV]
COSTF = [("none", 9e9), ("le0.20", 0.20), ("le0.15", 0.15), ("le0.10", 0.10), ("le0.05", 0.05)]


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def netmean(rows, T, S):
    if not rows:
        return None
    return sum(cell(r, T, S, "r")[0] - r["_c"] for r in rows) / len(rows)


def main():
    recs = pop(load(), "TAKEABLE")
    for r in recs:
        r["_c"] = corrected(r)
        r["_day"] = int(r["decision_time_utc"][8:10])
    TR = [r for r in recs if r["_day"] <= 15]
    TE = [r for r in recs if r["_day"] >= 16]
    dims = {
        "family": lambda r: r["family"],
        "born": lambda r: r["born"],
        "side": lambda r: r["side"],
        "symbol": lambda r: r["symbol"],
        "family_born": lambda r: "%s|%s" % (r["family"], r["born"]),
        "family_side": lambda r: "%s|%s" % (r["family"], r["side"]),
        "born_side": lambda r: "%s|%s" % (r["born"], r["side"]),
        "session": lambda r: r["session"],
        "ALL": lambda r: "ALL",
    }
    rows_out = []
    n_fits = 0
    for dname, kf in dims.items():
        gt, ge = {}, {}
        for r in TR:
            gt.setdefault(kf(r), []).append(r)
        for r in TE:
            ge.setdefault(kf(r), []).append(r)
        for k in sorted(set(gt) & set(ge), key=str):
            for cname, climit in COSTF:
                tr = [r for r in gt[k] if r["_c"] <= climit]
                te = [r for r in ge[k] if r["_c"] <= climit]
                if len(tr) < 100 or len(te) < 100:
                    continue
                n_fits += 1
                bT, bS = max(GRID, key=lambda ts: netmean(tr, *ts))
                trn = netmean(tr, bT, bS)
                ten = netmean(te, bT, bS)
                rows_out.append({
                    "dim": dname, "stratum": str(k), "cost_filter": cname,
                    "n_train": len(tr), "n_test": len(te), "fit_T": bT, "fit_S": bS,
                    "train_NET": round(trn, 5), "test_NET": round(ten, 5),
                    "shrinkage": round(ten - trn, 5),
                    "test_GROSS": round(mean(cell(r, bT, bS, "r")[0] for r in te), 5),
                    "test_meancost": round(mean(r["_c"] for r in te), 5),
                    "test_NET_at_declared_T2S1": round(netmean(te, 2.0, 1.0), 5),
                    "test_share_of_pool": round(len(te) / N_ORIG, 5),
                    "test_NET_per_ORIGINAL": round(ten * len(te) / N_ORIG, 6),
                })
    rows_out.sort(key=lambda d: -d["test_NET"])
    res = {"objective": "NET R per trade at corrected cost (spread/7.3 + commission + slippage + swap)",
           "n_fits_searched": n_fits, "n_grid_cells_per_fit": len(GRID),
           "total_cells_evaluated_on_train": n_fits * len(GRID),
           "n_train_rows": len(TR), "n_test_rows": len(TE),
           "n_positive_test_NET": sum(1 for d in rows_out if d["test_NET"] > 0),
           "n_positive_train_NET": sum(1 for d in rows_out if d["train_NET"] > 0),
           "ROWS": rows_out}
    # what does the pool-wide flat contract net?
    res["CONTROL_ALL_TEST_T2S1_NET"] = round(netmean(TE, 2.0, 1.0), 5)
    res["CONTROL_ALL_TEST_T075S025_NET"] = round(netmean(TE, 0.75, 0.25), 5)
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print("fits=%d cells_evaluated=%d | positive on TRAIN %d | positive on TEST %d"
          % (n_fits, n_fits * len(GRID), res["n_positive_train_NET"], res["n_positive_test_NET"]))
    print("control TEST net: T2/S1 %+.5f | T0.75/S0.25 %+.5f"
          % (res["CONTROL_ALL_TEST_T2S1_NET"], res["CONTROL_ALL_TEST_T075S025_NET"]))
    print("--- top 20 by TEST net ---")
    for d in rows_out[:20]:
        print("  %-13s %-34s %-7s ntr%5d nte%5d T%.2f/S%.2f tr %+.4f TE %+.4f (T2S1 %+.4f) shr %+.4f"
              % (d["dim"], d["stratum"][:34], d["cost_filter"], d["n_train"], d["n_test"],
                 d["fit_T"], d["fit_S"], d["train_NET"], d["test_NET"],
                 d["test_NET_at_declared_T2S1"], d["shrinkage"]))
    print("--- shrinkage distribution ---")
    sh = [d["shrinkage"] for d in rows_out]
    print("  n=%d mean %+.5f median %+.5f p10 %+.5f p90 %+.5f share_negative %.4f"
          % (len(sh), mean(sh), q(sh, .5), q(sh, .1), q(sh, .9),
             sum(1 for x in sh if x < 0) / len(sh)))


if __name__ == "__main__":
    main()
