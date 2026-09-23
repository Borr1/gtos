"""MAGNITUDE PROGRAM — survivor holdout, and the power inputs for the forward lane."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import mp_analyze as MA

OUT = Path("/tmp/mag_program/out")


def main():
    d = pd.concat([MA.load_grid(g) for g in ("D1", "H4")], ignore_index=True)
    d["era"] = np.where(d.year <= MA.TRAIN_END, "train_2014_2021", "test_2022_2026")

    # ---- A. the two surviving cells, on the holdout alone --------------------------
    surv = [("H4", 40, "LONG", 2.0, 5.0, 30), ("H4", 55, "LONG", 2.0, 5.0, 30)]
    m = pd.DataFrame(surv, columns=["grid", "channel", "side", "s", "k", "H"])
    sd = d.merge(m, on=["grid", "channel", "side", "s", "k", "H"])
    print("=== the 2 scan survivors, split by era ===")
    for era, g in sd.groupby("era", observed=True):
        ci = MA.cluster_ci(g[g.arm == "BREAKOUT"], ["grid", "channel"], "net_r")
        dl = MA.paired_delta_ci(g, ["grid", "channel"], "r_gap")
        t = ci.merge(dl[["grid", "channel", "r_gap_delta", "r_gap_delta_lo",
                         "r_gap_delta_hi"]], on=["grid", "channel"])
        t["era"] = era
        print(t.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    # ---- B. the 6 symbol-side survivors, on the holdout alone ----------------------
    ps = pd.read_csv(OUT / "SYMBOL_DELTA.csv")
    six = ps[ps.r_gap_delta_lo > 0][["grid", "symbol", "side"]]
    print(f"\n=== the {len(six)} symbol-side survivors (full-sample CI-lo > 0) ===")
    print(six.to_string(index=False))
    sub = d.merge(six, on=["grid", "symbol", "side"])
    rows = []
    for era, g in sub.groupby("era", observed=True):
        r = MA.paired_delta_ci(g, ["grid", "symbol", "side"], "r_gap")
        lv = g[g.arm == "BREAKOUT"].groupby(["grid", "symbol", "side"], observed=True).agg(
            level_net=("net_r", "mean")).reset_index()
        r = r.merge(lv, on=["grid", "symbol", "side"]); r["era"] = era
        rows.append(r)
    tt = pd.concat(rows, ignore_index=True)
    print(tt[["era", "grid", "symbol", "side", "n_hi", "r_gap_delta", "r_gap_delta_lo",
              "r_gap_delta_hi", "level_net"]].sort_values(
        ["grid", "symbol", "side", "era"]).to_string(index=False,
                                                     float_format=lambda x: f"{x:,.4f}"))
    tt.to_csv(OUT / "SURVIVOR_HOLDOUT.csv", index=False)

    # ---- C. power inputs: per-trade SD and trade rate -------------------------------
    bo = d[d.arm == "BREAKOUT"]
    ref = bo[(bo.channel == 20) & (bo.s == 2.0) & (bo.k == 3.0)
             & (((bo.grid == "D1") & (bo.H == 20)) | ((bo.grid == "H4") & (bo.H == 120)))]
    pw = ref.groupby(["grid", "side"], observed=True).agg(
        n=("net_r", "size"), sd=("net_r", "std"), mean=("net_r", "mean"),
        span_days=("entry_time", lambda s: (pd.to_datetime(s, utc=True).max()
                                            - pd.to_datetime(s, utc=True).min()).days)
    ).reset_index()
    pw["trades_per_symbol_year"] = pw.n / 24 / (pw.span_days / 365.25)
    pw["trades_per_year_24sym"] = pw.n / (pw.span_days / 365.25)
    print("\n=== power inputs: per-trade net SD and trade rate (Donchian-20, 2 ATR stop, 3R) ===")
    print(pw.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    pw.to_csv(OUT / "POWER_INPUTS.csv", index=False)

    # per-trade SD by grid pooled over the whole scan, for the general statement
    allsd = bo.groupby("grid", observed=True)["net_r"].agg(["std", "size", "mean"])
    print("\n=== per-trade net R dispersion, whole breakout scan ===")
    print(allsd.to_string(float_format=lambda x: f"{x:,.4f}"))

    # effective independence: how much does clustering inflate the SE?
    for g in ("D1", "H4"):
        x = ref[ref.grid == g]
        if not len(x):
            continue
        naive = x.net_r.std() / np.sqrt(len(x))
        ci = MA.cluster_ci(x, ["grid"], "net_r")
        clus = float(ci["net_r_boot_sd"].iloc[0])
        print(f"{g}: naive SE {naive:.5f}  cluster-bootstrap SE {clus:.5f}  "
              f"inflation {clus/naive:.2f}x  -> design effect {(clus/naive)**2:.2f}")


main()
