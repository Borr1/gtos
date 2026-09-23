#!/usr/bin/env python3
"""l1 pass 7 — the definitive statement.

(a) The POLICY LADDER: every step expressed per ORIGINAL candidate (denominator 27,658, a
    candidate you decline books exactly 0.0 R), so the steps are additive and directly
    comparable with the pool's published -0.2175 R/trade gross.
(b) Per-family excursion percentiles and time-to-outcome.
(c) Net economics at the frozen cost model and at the spread/7.3 and /8.5 corrections.
(d) The re-sizing caveat priced: a tighter stop multiplies R-denominated cost by 1/S.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_FINAL_V1.json")
N_ORIG = 27658


def costs(r):
    sp = r["spread_r"] or 0.0
    return {"frozen": (r["cost_r"] or 0.0),
            "sp73": sp / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0),
            "sp85": sp / 8.5 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)}


def step(recs, taken, valf, label, note=""):
    """valf(r)->R for a taken candidate. Declined candidates book 0.0."""
    tot = sum(valf(r) for r in taken)
    cf = sum(costs(r)["frozen"] for r in taken)
    c73 = sum(costs(r)["sp73"] for r in taken)
    c85 = sum(costs(r)["sp85"] for r in taken)
    n = len(taken)
    return {"label": label, "note": note, "n_taken": n,
            "share_of_pool_taken": round(n / N_ORIG, 5),
            "gross_per_ORIGINAL_candidate": round(tot / N_ORIG, 5),
            "gross_per_TAKEN_trade": round(tot / n, 5) if n else None,
            "net_frozen_per_ORIGINAL": round((tot - cf) / N_ORIG, 5),
            "net_sp73_per_ORIGINAL": round((tot - c73) / N_ORIG, 5),
            "net_sp85_per_ORIGINAL": round((tot - c85) / N_ORIG, 5),
            "net_sp73_per_TAKEN": round((tot - c73) / n, 5) if n else None,
            "mean_cost_frozen_r": round(cf / n, 5) if n else None,
            "mean_cost_sp73_r": round(c73 / n, 5) if n else None}


def main():
    recs = load()
    res = {"N_ORIGINAL": N_ORIG,
           "denominator_note": "gross_per_ORIGINAL_candidate divides by all 27,658 pool rows; a "
                               "candidate the policy declines books exactly 0.0 R. This makes every "
                               "rung directly comparable with the published -0.2175 R/trade."}
    ladder = []
    ladder.append({"label": "P0 as-shipped engine (fill-blind, engine exit, whole pool)",
                   "n_taken": len(recs), "share_of_pool_taken": 1.0,
                   "gross_per_ORIGINAL_candidate": round(mean(r["gross_r"] or 0.0 for r in recs), 5),
                   "note": "the published -0.2175 baseline, reproduced from the working set"})
    allr = recs
    tak = pop(recs, "TAKEABLE")
    ladder.append(step(recs, allr, lambda r: cell(r, 2.0, 1.0, "b")[0], "P0b BLIND fill, declared T2/S1",
                       "the pool's own fill convention; W0-F2's fiction"))
    ladder.append(step(recs, allr, lambda r: cell(r, 2.0, 1.0, "r")[0], "P1 REAL fill, declared T2/S1, whole pool"))
    ladder.append(step(recs, tak, lambda r: cell(r, 2.0, 1.0, "r")[0], "P2 + decline born_past_stop",
                       "decision-time observable, zero look-ahead (w0-capture)"))
    tak_nm = [r for r in tak if r["born"] != "born_marketable"]
    ladder.append(step(recs, tak_nm, lambda r: cell(r, 2.0, 1.0, "r")[0], "P3 + decline born_marketable",
                       "also decision-time observable"))
    ladder.append(step(recs, tak, lambda r: cell(r, 0.75, 0.25, "r")[0], "P4 P2 + pool best TESTED cell T0.75/S0.25",
                       "cell fitted on Jan 01-15, this is the whole-month value"))
    ladder.append(step(recs, tak_nm, lambda r: cell(r, 0.75, 0.25, "r")[0], "P5 P3 + pool best TESTED cell"))
    # per-family tested cells, fitted on TRAIN half
    for r in recs:
        r["_day"] = int(r["decision_time_utc"][8:10])
    TR = [r for r in tak if r["_day"] <= 15]
    TE = [r for r in tak if r["_day"] >= 16]
    GRID = [(T, S) for T in FAV for S in ADV]
    famfit = {}
    g = {}
    for r in TR:
        g.setdefault(r["family"], []).append(r)
    for f, rows in g.items():
        famfit[f] = max(GRID, key=lambda ts: mean(cell(x, *ts, "r")[0] for x in rows))
    res["family_fitted_cells_train_01_15"] = {f: {"T": c[0], "S": c[1]} for f, c in famfit.items()}
    ladder.append(step(recs, TE, lambda r: cell(r, *famfit[r["family"]], "r")[0],
                       "P6 TEST HALF ONLY: per-family TRAIN-fitted cells", "n is the test half only"))
    ladder.append(step(recs, TE, lambda r: cell(r, 2.0, 1.0, "r")[0],
                       "P6c TEST HALF ONLY control: flat T2/S1"))
    ladder.append(step(recs, TE, lambda r: cell(r, 0.75, 0.25, "r")[0],
                       "P6d TEST HALF ONLY: pool TRAIN-fitted cell T0.75/S0.25"))
    # the standout family
    sde = [r for r in tak if r["family"] == "structural_distance_extreme"]
    sde_te = [r for r in TE if r["family"] == "structural_distance_extreme"]
    ladder.append(step(recs, sde, lambda r: cell(r, 3.0, 0.25, "r")[0],
                       "P7 structural_distance_extreme ONLY @ T3.00/S0.25 (whole month)"))
    ladder.append(step(recs, sde_te, lambda r: cell(r, 3.0, 0.25, "r")[0],
                       "P7t structural_distance_extreme ONLY @ T3.00/S0.25 (TEST half)"))
    ladder.append(step(recs, sde, lambda r: cell(r, 2.0, 1.0, "r")[0],
                       "P7c structural_distance_extreme ONLY @ declared T2/S1 (whole month)"))
    res["POLICY_LADDER"] = ladder

    # ---------- per-family excursion + time to outcome
    fam = {}
    for r in tak:
        fam.setdefault(r["family"], []).append(r)
    famblk = {}
    for f, rows in sorted(fam.items()):
        fill = [r for r in rows if r.get("tf_r") is not None]
        tt, ts_, pe = [], [], []
        for r in rows:
            v, why, ib = cell(r, 2.0, 1.0, "r")
            if why == "target":
                tt.append(ib + 1)
            elif why == "stop":
                ts_.append(ib + 1)
            elif why == "path_end":
                pe.append(r["cls_end"])
        famblk[f] = {
            "n": len(rows), "filled": len(fill),
            "mfe": stats([r["mfe_r"] for r in fill]),
            "mae": stats([r["mae_r"] for r in fill]),
            "mfe_ladder": {("ge_%.2f" % L): round(sum(1 for r in fill if r["tf_r"][FI[L]] is not None) / len(fill), 5)
                           for L in FAV},
            "mae_ladder": {("le_-%.2f" % L): round(sum(1 for r in fill if r["ta_r"][AI[L]] is not None) / len(fill), 5)
                           for L in ADV},
            "bars_to_target_T2": stats(tt), "bars_to_stop_S1": stats(ts_),
            "open_at_2h_n": len(pe), "open_at_2h_share": round(len(pe) / len(rows), 5),
            "open_at_2h_unrealized": stats(pe),
            "mean_cost_frozen_r": round(mean(costs(r)["frozen"] for r in rows), 5),
            "mean_cost_sp73_r": round(mean(costs(r)["sp73"] for r in rows), 5),
        }
    res["PER_FAMILY"] = famblk

    # ---------- the re-sizing caveat, priced
    rs = {}
    for f, c in list(famfit.items()) + [("POOL", (0.75, 0.25))]:
        rows = fam.get(f, tak)
        S = c[1]
        gr = mean(cell(r, *c, "r")[0] for r in rows)
        cf = mean(costs(r)["sp73"] for r in rows)
        rs[f] = {"T": c[0], "S": S, "gross_same_size": round(gr, 5),
                 "cost_sp73_same_size": round(cf, 5),
                 "net_same_size": round(gr - cf, 5),
                 "scale_if_resized": round(1.0 / S, 3),
                 "gross_resized": round(gr / S, 5), "cost_resized": round(cf / S, 5),
                 "net_resized": round((gr - cf) / S, 5),
                 "note": "re-sizing so the new stop is one unit of account risk scales BOTH "
                         "the return and the R-denominated cost by 1/S, so the sign is invariant"}
    res["RESIZING_CAVEAT"] = rs
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    print("POLICY LADDER (R per ORIGINAL candidate, n_taken, net@sp73/ORIG)")
    for L in ladder:
        print("  %-58s n%6d  gross %+.5f  net73 %s"
              % (L["label"][:58], L["n_taken"], L["gross_per_ORIGINAL_candidate"],
                 ("%+.5f" % L["net_sp73_per_ORIGINAL"]) if "net_sp73_per_ORIGINAL" in L else "   n/a"))
    print("--- RESIZING (same-size net at corrected cost) ---")
    for f, d in sorted(rs.items(), key=lambda kv: -kv[1]["net_same_size"]):
        print("  %-34s T%.2f/S%.2f gross %+.4f cost %+.4f NET %+.4f" %
              (f[:34], d["T"], d["S"], d["gross_same_size"], d["cost_sp73_same_size"], d["net_same_size"]))


if __name__ == "__main__":
    main()
