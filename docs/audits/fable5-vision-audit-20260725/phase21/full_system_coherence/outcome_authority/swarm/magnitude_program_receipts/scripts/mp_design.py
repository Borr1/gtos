"""MAGNITUDE PROGRAM — design measurements (Task 1 adversarial pass + Task 2 inputs).

1. PER-SYMBOL DRIFT-FREE DELTA. The per-symbol net positives are all LONG on assets that
   rose 2014-2026. Blind entry on the same symbol captures the same drift, so
   BREAKOUT - BLIND is the drift-free instrument. If the delta is ~0 where the level is
   large, the level is beta.
2. ENTRY HOUR. The rollover-hour spread blowout, priced.
3. STOP WIDTH / VOL-RATIO SCALING. Lane I F2 says travel per unit ATR14 is 1.42x higher
   when ATR14/ATR50 is compressed. For a fixed-R barrier that cannot move expectancy
   (a driftless barrier is scale-free) but it MOVES COST, because cost_R = cost_price /
   (s * ATR14). Measured as a cost-geometry lever, not an edge lever.
4. TRAIN 2014-2021 -> TEST 2022-2026 on the delta.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import mp_analyze as MA

OUT = Path("/tmp/mag_program/out")


def main():
    d = pd.concat([MA.load_grid(g) for g in ("D1", "H4")], ignore_index=True)

    # ---- 1. per-symbol, drift-free -------------------------------------------------
    ps = MA.paired_delta_ci(d, ["grid", "symbol", "side"], "r_gap")
    lv = d[d.arm == "BREAKOUT"].groupby(["grid", "symbol", "side"], observed=True).agg(
        level_gross=("r_gap", "mean"), level_net=("net_r", "mean")).reset_index()
    bl = d[d.arm == "BLIND"].groupby(["grid", "symbol", "side"], observed=True).agg(
        blind_gross=("r_gap", "mean")).reset_index()
    ps = ps.merge(lv, on=["grid", "symbol", "side"]).merge(bl, on=["grid", "symbol", "side"])
    ps.to_csv(OUT / "SYMBOL_DELTA.csv", index=False)
    print("=== per-symbol BREAKOUT-BLIND gross delta (drift-free) vs the LEVEL ===")
    print(f"symbols x sides: {len(ps)}; delta>0 {int((ps.r_gap_delta>0).sum())}; "
          f"CI-lo>0 {int((ps.r_gap_delta_lo>0).sum())}; CI-hi<0 {int((ps.r_gap_delta_hi<0).sum())}")
    top = ps.sort_values("level_gross", ascending=False).head(10)
    print(top[["grid", "symbol", "side", "n_hi", "level_gross", "blind_gross",
               "r_gap_delta", "r_gap_delta_lo", "r_gap_delta_hi"]].to_string(
        index=False, float_format=lambda x: f"{x:,.4f}"))
    c = ps[["level_gross", "r_gap_delta"]].corr().iloc[0, 1]
    print(f"corr(level, drift-free delta) = {c:.4f}")

    # ---- 2. entry hour, H4 anchors only, with CI -----------------------------------
    h4 = d[(d.grid == "H4") & (d.broker_hour.isin([0, 4, 8, 12, 16, 20]))].copy()
    hr = MA.cluster_ci(h4[h4.arm == "BREAKOUT"], ["broker_hour"], "net_r")
    hg = h4[h4.arm == "BREAKOUT"].groupby("broker_hour", observed=True).agg(
        gross=("r_gap", "mean"), cost_fixed=("cost_fixed_r", "mean"),
        cost_carry=("cost_carry_r", "mean"), spread_r=("spread_price", "mean")).reset_index()
    hr = hr.merge(hg, on="broker_hour")
    hr.to_csv(OUT / "ENTRY_HOUR.csv", index=False)
    print("\n=== entry hour (broker wall), H4 breakouts, all contracts pooled ===")
    print(hr.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    # ---- 3. stop width as a cost lever ---------------------------------------------
    bo = d[d.arm == "BREAKOUT"].copy()
    bo["vq"] = bo.groupby(["grid", "symbol"], observed=True)["vol_regime"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    sw = bo.groupby(["grid", "s", "vq"], observed=True).agg(
        n=("net_r", "size"), atr14=("atr14", "median"), vol_regime=("vol_regime", "median"),
        cost_fixed=("cost_fixed_r", "mean"), cost_carry=("cost_carry_r", "mean"),
        cost_total=("cost_r", "mean"), gross=("r_gap", "mean"), net=("net_r", "mean"),
        mfe=("mfe_atr", "mean")).reset_index()
    sw.to_csv(OUT / "STOP_WIDTH_LEVER.csv", index=False)
    print("\n=== cost vs stop width x vol-ratio quintile (the geometry lever) ===")
    print(sw.pivot_table(index=["grid", "vq"], columns="s",
                         values=["cost_total", "gross", "net"]).round(4).to_string())

    # ---- 4. train -> test on the delta ---------------------------------------------
    d["era"] = np.where(d.year <= MA.TRAIN_END, "train", "test")
    rows = []
    for era, g in d.groupby("era", observed=True):
        r = MA.paired_delta_ci(g, ["grid", "channel", "side", "s", "k", "H"], "r_gap")
        r["era"] = era
        rows.append(r)
    tt = pd.concat(rows, ignore_index=True)
    p = tt.pivot_table(index=["grid", "channel", "side", "s", "k", "H"], columns="era",
                       values="r_gap_delta").reset_index()
    p["sign_match"] = np.sign(p["train"]) == np.sign(p["test"])
    p.to_csv(OUT / "DELTA_TRAIN_TEST.csv", index=False)
    print("\n=== train 2014-2021 -> test 2022-2026, gross delta ===")
    print(f"cells {len(p)}; sign match {int(p.sign_match.sum())} ({p.sign_match.mean():.1%}); "
          f"corr {p['train'].corr(p['test']):.3f}")
    print(f"train mean {p['train'].mean():+.5f}  test mean {p['test'].mean():+.5f}")
    print(f"cells positive in BOTH: {int(((p['train']>0)&(p['test']>0)).sum())}")

    # ---- 5. the one honest per-cell survivor screen ---------------------------------
    ec = pd.read_csv(OUT / "BREAKOUT_ECONOMICS.csv")
    ec = ec[ec.arm == "BREAKOUT"]
    dl = pd.read_csv(OUT / "BREAKOUT_DELTA.csv")
    m = ec.merge(dl, on=["grid", "channel", "side", "s", "k", "H"], how="left")
    surv = m[(m.net_r_lo > 0)]
    print(f"\n=== cells with absolute net CI-lo > 0: {len(surv)} of {len(m)} ===")
    surv2 = m[(m.net_r > 0) & (m.r_gap_delta_lo > 0)]
    print(f"=== cells net-positive AND trigger-gross CI-lo > 0: {len(surv2)} ===")
    if len(surv2):
        print(surv2[["grid", "channel", "side", "s", "k", "H", "n", "gross_r", "cost_r",
                     "net_r", "net_r_lo", "net_r_hi", "r_gap_delta", "r_gap_delta_lo"]].to_string(
            index=False, float_format=lambda x: f"{x:,.4f}"))
    m.to_csv(OUT / "CELL_SCREEN.csv", index=False)


main()
