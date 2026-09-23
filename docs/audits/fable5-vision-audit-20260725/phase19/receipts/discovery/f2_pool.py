"""f2_pool — pool the per-month f2 ladders into the lane's answer table."""

from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "f2"


def w(d, key):
    return d.get(key)


def pool_rows(recs):
    """n-weighted pooling of agg() dicts."""
    n = sum(r["n"] for r in recs if r.get("n"))
    if not n:
        return None
    g = sum(r["total_gross_r"] for r in recs if r.get("n"))
    net = sum(r["total_net_r"] for r in recs if r.get("n"))
    wr = sum(r["win_rate_gross"] * r["n"] for r in recs if r.get("n"))
    days = sum(r["n_days"] for r in recs if r.get("n"))
    dpos = sum(r["days_net_positive"] for r in recs if r.get("n"))
    return {
        "n": n, "gross_r_per_trade": g / n, "net_r_per_trade": net / n,
        "cost_r_per_trade": (g - net) / n, "win_rate_gross": wr / n,
        "total_net_r": net, "n_days": days, "days_net_positive": dpos,
    }


def main():
    files = sorted(glob.glob(str(OUT / "F2_LADDER_*_V1.json")))
    months = []
    D = {}
    for f in files:
        d = json.load(open(f))
        D[d["month"]] = d
        months.append(d["month"])
    res = {"lane": "f2", "months": months, "n_months": len(months)}

    # ---------------- TRACK A ladder, per month and pooled
    A = {}
    for arm in ("REAL", "PLACEBO_SIDE", "PLACEBO_TIME"):
        A[arm] = {}
        for rung in ("R0", "R1", "R2", "R3", "R4", "R5"):
            A[arm][rung] = {
                "per_month": {m: D[m][arm]["TRACK_A_capacity_matched"][rung]["net_r_per_trade"]
                              for m in months},
                "pooled": pool_rows([D[m][arm]["TRACK_A_capacity_matched"][rung] for m in months]),
            }
    res["TRACK_A"] = A

    B = {}
    keys = list(D[months[0]]["REAL"]["TRACK_B_full_population"].keys())
    for arm in ("REAL", "PLACEBO_SIDE", "PLACEBO_TIME"):
        B[arm] = {}
        for k in keys:
            B[arm][k] = {
                "per_month": {m: D[m][arm]["TRACK_B_full_population"][k]["net_r_per_trade"]
                              for m in months},
                "pooled": pool_rows([D[m][arm]["TRACK_B_full_population"][k] for m in months]),
            }
    res["TRACK_B"] = B

    # ---------------- the deltas, real and placebo, and the signal per rung
    lad = []
    order = ("R0", "R1", "R2", "R3", "R4", "R5")
    prev_r = prev_p = None
    for rung in order:
        r = A["REAL"][rung]["pooled"]
        p = A["PLACEBO_SIDE"][rung]["pooled"]
        row = {
            "rung": rung, "n": r["n"], "win_rate": r["win_rate_gross"],
            "gross": r["gross_r_per_trade"], "cost": r["cost_r_per_trade"],
            "net": r["net_r_per_trade"], "placebo_net": p["net_r_per_trade"],
            "signal_net": r["net_r_per_trade"] - p["net_r_per_trade"],
            "delta_net_vs_rung_below": None if prev_r is None else r["net_r_per_trade"] - prev_r,
            "placebo_delta_vs_rung_below": None if prev_p is None else p["net_r_per_trade"] - prev_p,
        }
        if row["delta_net_vs_rung_below"] is not None:
            row["share_of_delta_a_coin_flip_also_gets"] = (
                row["placebo_delta_vs_rung_below"] / row["delta_net_vs_rung_below"]
                if abs(row["delta_net_vs_rung_below"]) > 1e-9 else None)
        lad.append(row)
        prev_r, prev_p = r["net_r_per_trade"], p["net_r_per_trade"]
    res["LADDER_TABLE_TRACK_A"] = lad

    ladB = []
    prev_r = prev_p = None
    for k in keys:
        r = B["REAL"][k]["pooled"]
        p = B["PLACEBO_SIDE"][k]["pooled"]
        row = {"rung": k, "n": r["n"], "win_rate": r["win_rate_gross"],
               "gross": r["gross_r_per_trade"], "cost": r["cost_r_per_trade"],
               "net": r["net_r_per_trade"], "placebo_net": p["net_r_per_trade"],
               "signal_net": r["net_r_per_trade"] - p["net_r_per_trade"],
               "placebo_share_of_level": (p["net_r_per_trade"] / r["net_r_per_trade"]
                                          if abs(r["net_r_per_trade"]) > 1e-9 else None)}
        ladB.append(row)
    res["LADDER_TABLE_TRACK_B"] = ladB

    # ---------------- paired signal, pooled across months by day-count weighting
    pk = list(D[months[0]]["PAIRED_SIGNAL_VS_RANDOM_SIDE"].keys())
    ps = {}
    for k in pk:
        recs = [D[m]["PAIRED_SIGNAL_VS_RANDOM_SIDE"][k] for m in months]
        n = sum(r["n_paired"] for r in recs)
        mean = sum(r["mean"] * r["n_paired"] for r in recs) / n
        # combine the per-month bootstrap half-widths as independent months
        hw = [np.mean([r["ci95_hi"] - r["mean"], r["mean"] - r["ci95_lo"]]) for r in recs]
        wts = np.array([r["n_paired"] for r in recs], dtype=float) / n
        comb = float(np.sqrt(np.sum((wts * np.array(hw)) ** 2)))
        ps[k] = {
            "n_paired": n, "pooled_mean": mean,
            "pooled_ci95_halfwidth_independent_months": comb,
            "pooled_ci95": [mean - comb, mean + comb],
            "per_month": {m: D[m]["PAIRED_SIGNAL_VS_RANDOM_SIDE"][k]["mean"] for m in months},
            "months_positive": sum(1 for r in recs if r["mean"] > 0),
        }
    res["PAIRED_SIGNAL_POOLED"] = ps

    # ---------------- toll
    tolls = [D[m]["TOLL_DECOMPOSITION"] for m in months]
    res["TOLL"] = {
        "per_month_toll_r": {m: D[m]["TOLL_DECOMPOSITION"]["toll_r_per_trade"] for m in months},
        "per_month_toll_bps": {m: D[m]["TOLL_DECOMPOSITION"]["toll_bps_mean"] for m in months},
        "pooled_toll_r": float(np.mean([t["toll_r_per_trade"] for t in tolls])),
        "pooled_toll_bps": float(np.mean([t["toll_bps_mean"] for t in tolls])),
        "per_month_R1_gross_r": {m: D[m]["TOLL_DECOMPOSITION"]["gross_r_per_trade_R1"] for m in months},
        "per_month_one_R_bps": {m: D[m]["TOLL_DECOMPOSITION"]["one_R_in_price_bps_mean"] for m in months},
    }

    # ---------------- cost-cap sweep, pooled
    if "COST_CAP_SWEEP" in D[months[0]]:
        caps = list(D[months[0]]["COST_CAP_SWEEP"].keys())
        cs = {}
        for c in caps:
            recs = [D[m]["COST_CAP_SWEEP"][c] for m in months if c in D[m]["COST_CAP_SWEEP"]]
            n = sum(r["n"] for r in recs)
            if not n:
                continue
            cs[c] = {
                "n": n,
                "share_of_population": float(np.mean([r["share_of_population"] for r in recs])),
                "gross_r_per_trade": sum(r["gross_r_per_trade"] * r["n"] for r in recs) / n,
                "cost_r_per_trade": sum(r["cost_r_per_trade"] * r["n"] for r in recs) / n,
                "net_r_per_trade": sum(r["net_r_per_trade"] * r["n"] for r in recs) / n,
                "placebo_net_r_per_trade": sum(r["placebo_net_r_per_trade"] * r["n"] for r in recs) / n,
                "signal_net": sum(r["signal_net"] * r["n"] for r in recs) / n,
                "months_net_positive": sum(1 for r in recs if r["net_r_per_trade"] > 0),
                "n_months": len(recs),
                "days_net_positive": sum(r["days_net_positive"] for r in recs),
                "n_days": sum(r["n_days"] for r in recs),
            }
        res["COST_CAP_SWEEP_POOLED"] = cs

    # ---------------- per family / instrument, pooled + cross-month sign stability
    for axis in ("family", "instrument"):
        tab = {}
        keysets = set()
        for m in months:
            keysets |= set(D[m]["by_axis"][axis].keys())
        for kk in sorted(keysets):
            recs = [D[m]["by_axis"][axis][kk] for m in months if kk in D[m]["by_axis"][axis]]
            if not recs:
                continue
            sigs = [r.get("signal_R1") for r in recs if r.get("signal_R1") is not None]
            sig4 = [r.get("signal_R4_path") for r in recs if r.get("signal_R4_path") is not None]
            tab[kk] = {
                "n_months": len(recs),
                "R1": pool_rows([r["R1"] for r in recs]),
                "R4_path": pool_rows([r["R4_path"] for r in recs]),
                "PLACEBO_SIDE_R1": pool_rows([r["PLACEBO_SIDE_R1"] for r in recs]),
                "PLACEBO_SIDE_R4_path": pool_rows([r["PLACEBO_SIDE_R4_path"] for r in recs]),
                "signal_R1_per_month": sigs,
                "signal_R1_months_positive": sum(1 for x in sigs if x > 0),
                "signal_R4_path_per_month": sig4,
                "signal_R4_path_months_positive": sum(1 for x in sig4 if x > 0),
            }
            a, b = tab[kk]["R1"], tab[kk]["PLACEBO_SIDE_R1"]
            tab[kk]["signal_R1_pooled"] = a["net_r_per_trade"] - b["net_r_per_trade"]
            a4, b4 = tab[kk]["R4_path"], tab[kk]["PLACEBO_SIDE_R4_path"]
            tab[kk]["signal_R4_path_pooled"] = a4["net_r_per_trade"] - b4["net_r_per_trade"]
            tab[kk]["toll_r_per_trade"] = a["cost_r_per_trade"]
            tab[kk]["signal_over_toll_R1"] = tab[kk]["signal_R1_pooled"] / max(a["cost_r_per_trade"], 1e-9)
        res["BY_" + axis.upper()] = tab

    (OUT / "F2_POOLED_V1.json").write_text(json.dumps(res, indent=1, default=str))

    # ------------------------------------------------------------------ print
    print("months:", months)
    print("\n=== TRACK A LADDER (pooled, capacity-matched) ===")
    print("%-4s %8s %7s %9s %8s %9s %10s %10s %11s" %
          ("rung", "n", "win", "gross", "cost", "net", "placebo", "SIGNAL", "delta"))
    for r in res["LADDER_TABLE_TRACK_A"]:
        print("%-4s %8d %7.4f %+9.5f %8.5f %+9.5f %+10.5f %+10.5f %11s" %
              (r["rung"], r["n"], r["win_rate"], r["gross"], r["cost"], r["net"],
               r["placebo_net"], r["signal_net"],
               "" if r["delta_net_vs_rung_below"] is None
               else "%+.5f" % r["delta_net_vs_rung_below"]))
    print("\n=== TRACK B LADDER (pooled, full population) ===")
    print("%-42s %8s %+9s %9s %10s %10s %8s" %
          ("rung", "n", "gross", "net", "placebo", "SIGNAL", "pl/real"))
    for r in res["LADDER_TABLE_TRACK_B"]:
        print("%-42s %8d %+9.5f %+9.5f %+10.5f %+10.5f %8s" %
              (r["rung"], r["n"], r["gross"], r["net"], r["placebo_net"], r["signal_net"],
               "" if r["placebo_share_of_level"] is None else "%.4f" % r["placebo_share_of_level"]))
    print("\n=== PAIRED SIGNAL (pooled) ===")
    for k, v in res["PAIRED_SIGNAL_POOLED"].items():
        print("%-34s n=%-7d %+.5f +/- %.5f  months_pos %d/%d" %
              (k, v["n_paired"], v["pooled_mean"],
               v["pooled_ci95_halfwidth_independent_months"], v["months_positive"],
               len(v["per_month"])))
    print("\nTOLL pooled: %.5f R/trade, %.4f bps;  one R = %.3f bps" %
          (res["TOLL"]["pooled_toll_r"], res["TOLL"]["pooled_toll_bps"],
           float(np.mean(list(res["TOLL"]["per_month_one_R_bps"].values())))))
    if "COST_CAP_SWEEP_POOLED" in res:
        print("\n=== COST-CAP SWEEP (pooled) ===")
        print("%-10s %8s %7s %9s %8s %9s %10s %10s %7s" %
              ("cap", "n", "share", "gross", "cost", "net", "placebo", "SIGNAL", "mo+"))
        for k, v in res["COST_CAP_SWEEP_POOLED"].items():
            print("%-10s %8d %7.4f %+9.5f %8.5f %+9.5f %+10.5f %+10.5f %3d/%d" %
                  (k, v["n"], v["share_of_population"], v["gross_r_per_trade"],
                   v["cost_r_per_trade"], v["net_r_per_trade"],
                   v["placebo_net_r_per_trade"], v["signal_net"],
                   v["months_net_positive"], v["n_months"]))


if __name__ == "__main__":
    main()
