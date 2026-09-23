"""MAGNITUDE PROGRAM — diagnostic: is the negative BREAKOUT-BLIND delta real, or geometry?

Three barrier-free instruments, all in ATR14 units, breakout vs matched blind:
  1. signed forward return in the trade direction (pure direction)
  2. MFE / MAE beyond the entry (the "realised travel beyond the trigger" the thesis needs)
  3. the entry gap (trigger close -> executable next open), which is the one term a
     bar-close backtest silently gives away
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

OUT = Path("/tmp/mag_program/out")
BAR_HOURS = {"D1": 24.0, "H4": 4.0}


def main():
    rows = []
    for grid in ("D1", "H4"):
        ev = pd.read_parquet(OUT / f"events_{grid}.parquet")
        out = pd.read_parquet(OUT / f"out_{grid}.parquet")
        # MFE/MAE at the longest horizon are barrier-independent (path extremes), so take
        # one (s,k) slice: they are identical across s,k for a given H.
        H = 80 if grid == "D1" else 480
        o = out[(out.H == H) & (out.s == 1.0) & (out.k == 1.0)][["uid", "mfe_atr", "mae_atr"]]
        d = ev.merge(o, on="uid", how="inner")
        d["grid"] = grid
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    d["travel_net"] = d.mfe_atr - d.mae_atr
    g = d.groupby(["grid", "channel", "side", "arm"], observed=True).agg(
        n=("mfe_atr", "size"), mfe=("mfe_atr", "mean"), mae=("mae_atr", "mean"),
        travel_net=("travel_net", "mean"), entry_gap=("entry_gap_atr", "mean"),
        atr14=("atr14", "median")).reset_index()
    g["mfe_over_mae"] = g.mfe / g.mae
    piv = g.pivot_table(index=["grid", "channel", "side"], columns="arm",
                        values=["mfe", "mae", "mfe_over_mae", "entry_gap"])
    print("=== path extremes over the LONGEST horizon, ATR units ===")
    print(piv.round(4).to_string())
    piv.round(5).to_csv(OUT / "DIAG_PATH_EXTREMES.csv")

    # entry gap, the executable-entry tax
    eg = d.groupby(["grid", "arm"], observed=True)["entry_gap_atr"].agg(
        ["mean", "median", "std", "size"]).reset_index()
    print("\n=== entry gap (trigger close -> next open, signed AGAINST the trade), ATR ===")
    print(eg.round(5).to_string(index=False))
    eg.round(6).to_csv(OUT / "DIAG_ENTRY_GAP.csv", index=False)

    # by symbol, longest channel, does the reversion hold everywhere?
    s = d[(d.channel == 55)].groupby(["grid", "symbol", "arm"], observed=True).agg(
        n=("mfe_atr", "size"), mfe=("mfe_atr", "mean"), mae=("mae_atr", "mean")).reset_index()
    s["net"] = s.mfe - s.mae
    sp = s.pivot_table(index=["grid", "symbol"], columns="arm", values="net")
    sp["delta"] = sp["BREAKOUT"] - sp["BLIND"]
    print("\n=== per-symbol (MFE-MAE) breakout minus blind, channel 55, longest horizon ===")
    print(f"symbols with delta < 0: {int((sp.delta < 0).sum())} / {len(sp)}")
    print(sp.round(4).sort_values("delta").to_string())
    sp.round(5).to_csv(OUT / "DIAG_SYMBOL_TRAVEL.csv")


main()
