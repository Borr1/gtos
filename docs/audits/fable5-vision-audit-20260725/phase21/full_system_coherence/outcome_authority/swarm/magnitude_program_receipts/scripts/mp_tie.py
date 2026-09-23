"""MAGNITUDE PROGRAM — bound the intrabar-ambiguity rule.

A bar that reaches both barriers has an unknowable intrabar ordering at this resolution.
The main run scores it STOP (pessimistic, Lane I's rule). This bounds every headline
number under all three rules — STOP / TARGET / EXCLUDE — so no conclusion rests on the
choice. Reported for the BREAKOUT-BLIND delta, which is the kill test's instrument.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import mp_analyze as MA

OUT = Path("/tmp/mag_program/out")


def main():
    frames = []
    for grid in ("D1", "H4"):
        frames.append(MA.load_grid(grid))
    d = pd.concat(frames, ignore_index=True)
    del frames
    tie = d["tie"].to_numpy(bool)
    k = d["k"].to_numpy(float)
    # r under the three rules (gap-honest gross)
    d["r_stop"] = d["r_gap"].to_numpy(float)
    d["r_tgt"] = np.where(tie, k, d["r_gap"].to_numpy(float))
    d["net_stop"] = d["r_stop"] - d["cost_r"]
    d["net_tgt"] = d["r_tgt"] - d["cost_r"]

    rate = d.groupby(["grid", "arm", "s", "H"], observed=True)["tie"].mean().reset_index()
    rate.rename(columns={"tie": "ambiguous_rate"}, inplace=True)
    rate.to_csv(OUT / "TIE_RATE.csv", index=False)
    print("=== ambiguous-bar rate (both barriers reached in one bar) ===")
    print(rate.pivot_table(index=["grid", "s", "H"], columns="arm",
                           values="ambiguous_rate").round(4).to_string())

    dcell = ["grid", "channel", "side", "s", "k", "H"]
    res = {}
    for name, col in (("STOP", "net_stop"), ("TARGET", "net_tgt")):
        piv = d.pivot_table(index=[*dcell, "cluster"], columns="arm", values=col,
                            aggfunc="mean").dropna().reset_index()
        piv["delta"] = piv["BREAKOUT"] - piv["BLIND"]
        r = MA.cluster_ci(piv, dcell, "delta")
        r["rule"] = name
        res[name] = r
    ex = d[~tie]
    piv = ex.pivot_table(index=[*dcell, "cluster"], columns="arm", values="net_r",
                         aggfunc="mean").dropna().reset_index()
    piv["delta"] = piv["BREAKOUT"] - piv["BLIND"]
    r = MA.cluster_ci(piv, dcell, "delta"); r["rule"] = "EXCLUDE"
    res["EXCLUDE"] = r
    allr = pd.concat(res.values(), ignore_index=True)
    allr.to_csv(OUT / "TIE_BOUNDED_DELTA.csv", index=False)
    print("\n=== BREAKOUT - BLIND net delta, under all three ambiguity rules ===")
    print(allr.groupby(["rule", "grid"]).agg(
        cells=("delta_mean", "size"), mean=("delta_mean", "mean"),
        best=("delta_mean", "max"), cells_positive=("delta_mean", lambda s: (s > 0).sum()),
        cells_ci_lo_positive=("delta_lo", lambda s: (s > 0).sum())).round(5).to_string())

    # and the absolute breakout economics under the optimistic rule
    bo = d[d.arm == "BREAKOUT"]
    for name, col in (("STOP", "net_stop"), ("TARGET", "net_tgt")):
        t = MA.cluster_ci(bo, ["grid", "channel", "side", "s", "k", "H"], col)
        t["rule"] = name
        t.to_csv(OUT / f"BREAKOUT_NET_{name}.csv", index=False)
        print(f"\n=== BREAKOUT absolute net, rule={name}: "
              f"cells>0 {(t[col+'_mean']>0).sum()}/{len(t)}, "
              f"CI-lo>0 {(t[col+'_lo']>0).sum()}, best {t[col+'_mean'].max():.4f}")


main()
