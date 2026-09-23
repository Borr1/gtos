#!/usr/bin/env python3
"""F2 addendum, commissioned mid-flight after F1 landed.

Three questions:

  R1  Does F1's cell-level structure -- corr(mean MFE, mean |MAE|) = +0.963,
      corr(mean MFE, mean net R) = -0.613, corr(ratio, mean net R) = +0.459
      across 164 (family x symbol) cells -- reproduce, and does it TRANSFER to
      the trade level and to the within-decision-window level where a selector
      actually operates?  An ecological correlation across aggregates and a
      within-group correlation are different quantities and can differ in sign.

  R2  Rank on MFE/|MAE| rather than on MFE.  Two constructions, because they are
      not the same estimator: predict the ratio directly (declared in PREREG_V1
      as L-RATIO), and predict MFE and |MAE| separately and rank on the ratio of
      the predictions (new, added by the mid-flight commission).

  R3  Price every arm in R/trade net of cost, against F1's measured pool edge of
      +0.0301 R/trade and all-in cost of 0.2868 R.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L
from f2_stageL import ww_rho, paired_ww

WF = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
OUTD = Path(__file__).resolve().parent / "receipts"
F1P = (Path(__file__).resolve().parents[1] / "f1_excursion"
       / "F1_TRADE_EXCURSION_CENSUS_V1.parquet")
RATIO_EPS = L.RATIO_EPS


def cell_and_trade_correlations():
    """R1 -- the same three correlations at three levels of aggregation."""
    import pandas as pd
    d = pd.read_parquet(F1P, columns=["symbol", "family", "mfe_r", "mae_r",
                                      "net_r", "trading_day", "month"])
    d["abs_mae"] = d["mae_r"].abs()
    d["ratio"] = d["mfe_r"] / (d["abs_mae"] + RATIO_EPS)
    out = {"source": "F1_TRADE_EXCURSION_CENSUS_V1.parquet", "n_trades": int(len(d))}

    g = d.groupby(["family", "symbol"], observed=True).agg(
        n=("net_r", "size"), mfe=("mfe_r", "mean"), mae=("abs_mae", "mean"),
        net=("net_r", "mean"))
    g = g[g["n"] >= 150]
    g["ratio"] = g["mfe"] / g["mae"]
    out["CELL_LEVEL"] = {
        "n_cells": int(len(g)),
        "corr_meanMFE_meanAbsMAE": float(np.corrcoef(g["mfe"], g["mae"])[0, 1]),
        "corr_meanMFE_meanNetR": float(np.corrcoef(g["mfe"], g["net"])[0, 1]),
        "corr_ratio_meanNetR": float(np.corrcoef(g["ratio"], g["net"])[0, 1]),
        "pooled_ratio": float(d["mfe_r"].sum() / d["abs_mae"].sum()),
        "share_cells_ratio_gt_1": float((g["ratio"] > 1.0).mean()),
    }
    out["TRADE_LEVEL"] = {
        "n": int(len(d)),
        "corr_MFE_absMAE_pearson": float(np.corrcoef(d["mfe_r"], d["abs_mae"])[0, 1]),
        "corr_MFE_absMAE_spearman": L.spearman(d["mfe_r"].to_numpy(float),
                                               d["abs_mae"].to_numpy(float)),
        "corr_MFE_netR_spearman": L.spearman(d["mfe_r"].to_numpy(float),
                                             d["net_r"].to_numpy(float)),
        "corr_ratio_netR_spearman": L.spearman(d["ratio"].to_numpy(float),
                                               d["net_r"].to_numpy(float)),
    }
    # within-cell (the variation a selector inside one family x symbol sees)
    ws = []
    for _key, sub in d.groupby(["family", "symbol"], observed=True):
        if len(sub) < 150:
            continue
        ws.append((L.spearman(sub["mfe_r"].to_numpy(float), sub["net_r"].to_numpy(float)),
                   L.spearman(sub["ratio"].to_numpy(float), sub["net_r"].to_numpy(float)),
                   L.spearman(sub["mfe_r"].to_numpy(float), sub["abs_mae"].to_numpy(float))))
    ws = np.asarray([w for w in ws if all(np.isfinite(w))])
    out["WITHIN_CELL_mean_spearman"] = {
        "n_cells": int(len(ws)),
        "MFE_vs_netR": float(ws[:, 0].mean()),
        "ratio_vs_netR": float(ws[:, 1].mean()),
        "MFE_vs_absMAE": float(ws[:, 2].mean()),
    }
    return out


def ratio_arms(variant="base"):
    """R2 + R3 -- the ratio rankers on F2's own walk-forward folds."""
    meta, X, nc, tgt, filled, ded, info = L.build_dataset()
    Z = np.load(WF / f"preds_{variant}.npz", allow_pickle=True)
    P = Z["preds"].astype(np.float64)
    idx = {n: k for k, n in enumerate(list(Z["names"]))}
    sd = set(str(x) for x in Z["scored"])
    res = np.asarray([m["res"] for m in meta], dtype=bool)
    both = res & filled
    rows = np.asarray([i for i, m in enumerate(meta) if m["cday"] in sd and both[i]],
                      dtype=np.int64)
    tnr = tgt["tnr"]

    stats = {
        "shipped (Ehat[net R])": P[:, idx["tnr_B"]],
        "L-MFE  (Ehat[MFE])": P[:, idx["mfe_B"]],
        "L-RATIO (Ehat[MFE/|MAE|], declared)": P[:, idx["ratio_B"]],
        "JOINT-RATIO (Ehat[MFE]/|Ehat[MAE]|, new)":
            P[:, idx["mfe_B"]] / (np.abs(P[:, idx["mae_B"]]) + RATIO_EPS),
        "L-MAE  (Ehat[MAE])": P[:, idx["mae_B"]],
    }
    out = {"variant": variant, "n_rows": int(len(rows)), "arms": {}, "paired": {}}
    for tag, st in stats.items():
        r, dd, _ = ww_rho(meta, rows, st, tnr)
        b = L.boot_day(r, dd)
        out["arms"][tag] = {k: b[k] for k in ("point", "ci95_lo", "ci95_hi",
                                              "p_two_sided_sign", "n")}
    for tag in ("JOINT-RATIO (Ehat[MFE]/|Ehat[MAE]|, new)",
                "L-RATIO (Ehat[MFE/|MAE|], declared)"):
        for ref in ("shipped (Ehat[net R])", "L-MFE  (Ehat[MFE])"):
            dfs, dys = paired_ww(meta, rows, stats[tag], stats[ref], tnr)
            out["paired"][f"{tag}  MINUS  {ref}"] = L.boot_day(dfs, dys)

    # ---- R3: realized expectancy of the top decile of each ranker ----------
    # A within-window rank statistic must be converted to R/trade before it can
    # be called a candidate. Top-decile-per-window realized net R, net of cost.
    from collections import defaultdict
    out["R3_top_decile_realized_net_r_per_trade"] = {}
    bywin = defaultdict(list)
    for i in rows:
        bywin[meta[i]["win"]].append(i)
    for tag, st in stats.items():
        vals, days = [], []
        for win, ii in bywin.items():
            ii = [i for i in ii if np.isfinite(st[i]) and np.isfinite(tnr[i])]
            if len(ii) < 10:
                continue
            ii.sort(key=lambda z: -st[z])
            for i in ii[:max(1, len(ii) // 10)]:
                vals.append(tnr[i]); days.append(meta[i]["day"])
        b = L.boot_day(vals, days)
        out["R3_top_decile_realized_net_r_per_trade"][tag] = {
            "net_r_per_trade": b["point"], "ci95_lo": b["ci95_lo"],
            "ci95_hi": b["ci95_hi"], "n_trades": b["n"],
            "gap_to_breakeven_r": -b["point"]}
    out["R3_reference"] = {
        "F1_pool_barrier_free_edge_r_per_trade": 0.0301,
        "F1_all_in_cost_r": 0.2868,
        "cost_over_edge": 0.2868 / 0.0301,
        "note": "F2's realized figures are ALREADY net of deductible_cost_r; "
                "the gap column is what a positive book still needs."}
    return out


def main():
    rep = {"prereg_sha256": L.PREREG_SHA,
           "commission": "mid-flight coordinator correction after F1 landed"}
    rep["R1_aggregation_levels"] = cell_and_trade_correlations()
    rep["R2_R3_ratio_arms"] = ratio_arms("base")
    rep["R2_R3_ratio_arms_emb1"] = ratio_arms("emb1")
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / "R1_F1_RECONCILIATION_AND_RATIO_ARM.json").write_text(json.dumps(rep, indent=1))

    a = rep["R1_aggregation_levels"]
    print("R1 -- THE SAME THREE CORRELATIONS AT THREE LEVELS (F1's own parquet)")
    print(f"  CELL   (n={a['CELL_LEVEL']['n_cells']}):  MFE~|MAE| {a['CELL_LEVEL']['corr_meanMFE_meanAbsMAE']:+.4f}"
          f"   MFE~netR {a['CELL_LEVEL']['corr_meanMFE_meanNetR']:+.4f}"
          f"   ratio~netR {a['CELL_LEVEL']['corr_ratio_meanNetR']:+.4f}")
    t = a["TRADE_LEVEL"]
    print(f"  TRADE  (n={t['n']:,}):  MFE~|MAE| {t['corr_MFE_absMAE_spearman']:+.4f}"
          f"   MFE~netR {t['corr_MFE_netR_spearman']:+.4f}"
          f"   ratio~netR {t['corr_ratio_netR_spearman']:+.4f}")
    w = a["WITHIN_CELL_mean_spearman"]
    print(f"  WITHIN-CELL (n={w['n_cells']}): MFE~|MAE| {w['MFE_vs_absMAE']:+.4f}"
          f"   MFE~netR {w['MFE_vs_netR']:+.4f}   ratio~netR {w['ratio_vs_netR']:+.4f}")

    for key in ("R2_R3_ratio_arms", "R2_R3_ratio_arms_emb1"):
        r = rep[key]
        print(f"\nR2 -- WITHIN-WINDOW TRANSFER TO REALIZED NET R  [{r['variant']}]")
        for k, v in r["arms"].items():
            print(f"  {k:<42}{v['point']:+.4f} [{v['ci95_lo']:+.4f},{v['ci95_hi']:+.4f}] p={v['p_two_sided_sign']:.3f}")
        print("  paired:")
        for k, v in r["paired"].items():
            print(f"    {k:<62}{v['point']:+.4f} [{v['ci95_lo']:+.4f},{v['ci95_hi']:+.4f}] p={v['p_two_sided_sign']:.3f}")
        print(f"R3 -- TOP-DECILE REALIZED R/TRADE (net of cost)  [{r['variant']}]")
        for k, v in r["R3_top_decile_realized_net_r_per_trade"].items():
            print(f"  {k:<42}{v['net_r_per_trade']:+.4f} [{v['ci95_lo']:+.4f},{v['ci95_hi']:+.4f}]"
                  f"  n={v['n_trades']:,}  needs {v['gap_to_breakeven_r']:+.4f} more")


if __name__ == "__main__":
    main()
