"""MAGNITUDE PROGRAM — the horizon optimum, and the survivors' holdout.

A. FINE HORIZON SWEEP. Lane I F4 says "cost drag falls as 1/sqrt(t)". That is true of the
   FIXED terms measured against forward DISPERSION. For a fixed-R barrier contract the
   relevant denominator is the STOP, not the dispersion, and carry is LINEAR in t. So
   total cost_R has a minimum, not a monotone fall. This measures where it is.
B. The two surviving cells and the six surviving symbol-sides, re-measured on the
   2022-2026 holdout alone.
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import mp_build as MB
import mp_cost as MC
import mp_analyze as MA

OUT = Path("/tmp/mag_program/out")
SWEEP = {"D1": (1, 2, 3, 5, 8, 12, 20, 40, 80, 160),
         "H4": (2, 3, 6, 12, 24, 48, 96, 180, 360, 720)}
CH, S, K = 20, 2.0, 3.0


def build_sweep(grid):
    syms = sorted({p.name.rsplit("_", 1)[0] for p in MB.SRC.glob(f"*_{grid}.csv")})
    rows = []
    for sym in syms:
        t, o, h, l, c = MB.load(sym, grid)
        n = len(c)
        a14 = MB.atr(h, l, c, 14)
        pri_hi = np.r_[[np.nan], MB.roll(h, CH, "max")[:-1]]
        pri_lo = np.r_[[np.nan], MB.roll(l, CH, "min")[:-1]]
        for side, sig in (("LONG", c > pri_hi), ("SHORT", c < pri_lo)):
            idx = np.flatnonzero(sig)
            idx = idx[(idx + 1) < n]
            idx = idx[np.isfinite(a14[idx]) & (a14[idx] > 0)]
            if not len(idx):
                continue
            base = pd.DataFrame({"symbol": sym, "grid": grid, "side": side,
                                 "entry_time": t.to_numpy()[idx + 1],
                                 "entry_px": o[idx + 1], "atr14": a14[idx],
                                 "channel": CH, "vol_regime": np.nan, "year": t.dt.year.to_numpy()[idx],
                                 "entry_hour": t.dt.hour.to_numpy()[idx + 1],
                                 "break_ext_atr": np.nan, "entry_gap_atr": np.nan})
            base["uid"] = sym + "|" + side + "|" + np.arange(len(idx)).astype(str)
            for H in SWEEP[grid]:
                r, rg, lab, mfe, mae, bars, tie = MB.first_touch_block(
                    o, h, l, c, idx + 1, o[idx + 1], a14[idx], side, S, K, H)
                rows.append(base.assign(H=H, r=r, r_gap=rg, label=lab, mfe_atr=mfe,
                                        mae_atr=mae, bars_held=bars, tie=tie, s=S, k=K))
    return pd.concat(rows, ignore_index=True)


def main():
    t0 = time.time()
    frames = []
    for grid in ("D1", "H4"):
        d = build_sweep(grid)
        ev = d.drop_duplicates("uid")[["uid", "symbol", "grid", "side", "entry_time",
                                       "entry_px", "atr14"]].copy()
        ev = MC.event_cost_inputs(ev)
        d = d.drop(columns=["entry_px", "atr14"]).merge(
            ev.drop(columns=["symbol", "grid", "side", "entry_time"]), on="uid", how="left")
        d["hold_h"] = d["bars_held"].to_numpy(float) * MC.BAR_HOURS[grid]
        nights = np.zeros(len(d))
        for rw, g in d.groupby("rollover_wd", observed=True):
            nights[g.index] = MC.rollover_nights_vec(
                g["entry_time"].to_numpy(), g["hold_h"].to_numpy(float), int(rw))
        sl = S * d["atr14"].to_numpy(float)
        d["cost_fixed_r"] = ((d["spread_price"] + d["comm_price"] + d["slip_price"]
                              ).to_numpy(float) / sl + d["slip_fixed_r"].to_numpy(float))
        d["cost_carry_r"] = nights * d["swap_night_price"].to_numpy(float) / sl
        d["cost_r"] = d["cost_fixed_r"] + d["cost_carry_r"]
        d["net_r"] = d["r_gap"].to_numpy(float) - d["cost_r"].to_numpy(float)
        q = pd.PeriodIndex(pd.to_datetime(d["entry_time"], utc=True), freq="Q")
        d["cluster"] = d["symbol"].astype(str) + "|" + q.astype(str)
        frames.append(d)
        print(json.dumps({"grid": grid, "rows": int(len(d)), "t": round(time.time() - t0, 1)}),
              flush=True)
    d = pd.concat(frames, ignore_index=True)
    tab = d.groupby(["grid", "side", "H"], observed=True).agg(
        n=("net_r", "size"), hold_h=("hold_h", "mean"), med_hold=("hold_h", "median"),
        cost_fixed=("cost_fixed_r", "mean"), cost_carry=("cost_carry_r", "mean"),
        cost_total=("cost_r", "mean"), gross=("r_gap", "mean"), net=("net_r", "mean"),
        target_rate=("label", lambda s: (s == 1).mean()),
        timeout_rate=("label", lambda s: (s == 2).mean())).reset_index()
    ci = MA.cluster_ci(d, ["grid", "side", "H"], "net_r")
    tab = tab.merge(ci.drop(columns=["n"]), on=["grid", "side", "H"])
    tab.to_csv(OUT / "HORIZON_SWEEP.csv", index=False)
    print("\n=== FINE HORIZON SWEEP: Donchian-20, stop 2.0 ATR14, target 3R, 24 symbols ===")
    for g in ("D1", "H4"):
        print(f"\n--- {g} ---")
        print(tab[tab.grid == g][["side", "H", "hold_h", "n", "cost_fixed", "cost_carry",
                                  "cost_total", "gross", "net", "net_r_lo", "net_r_hi",
                                  "target_rate", "timeout_rate"]].to_string(
            index=False, float_format=lambda x: f"{x:,.4f}"))
    best = tab.loc[tab.groupby(["grid", "side"])["net"].idxmax()]
    print("\n=== cost-minimising / net-maximising horizon per grid x side ===")
    print(best[["grid", "side", "H", "hold_h", "cost_total", "gross", "net",
                "net_r_lo", "net_r_hi"]].to_string(index=False,
                                                   float_format=lambda x: f"{x:,.4f}"))
    cm = tab.loc[tab.groupby(["grid", "side"])["cost_total"].idxmin()]
    print("\n=== the cost minimum itself ===")
    print(cm[["grid", "side", "H", "hold_h", "cost_fixed", "cost_carry",
              "cost_total"]].to_string(index=False, float_format=lambda x: f"{x:,.4f}"))


main()
