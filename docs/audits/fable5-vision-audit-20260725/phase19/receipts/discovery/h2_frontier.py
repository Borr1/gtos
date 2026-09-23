"""h2_frontier — decompose the winning cells into CHEAP vs HIGH-EDGE, and calibrate against
a permutation null in which the edge is exactly flat.

Two hypotheses generate a cell with edge/cost > 1:
  (A) FLAT-EDGE / CHEAP CELL   the cell carries the pooled edge and its cost is below it.
  (B) EDGE CONCENTRATION       the cell's gross edge is genuinely above pooled.
(A) needs no edge estimation and cannot be overfit; (B) can be.  This script measures both
and reports how many trades sit in each.

Also: the identity that governs the whole hunt --
      net_r = (gross_bps - cost_bps) / (rdp * 1e4)
so the money-per-trade metric wants a POSITIVE price-space margin AND a TIGHT stop.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h2_lib as H  # noqa: E402
import h2_scan  # noqa: E402

B = 2000  # permutation draws


def cellsets(rows):
    """(name, key-list) for every cell definition used in the hunt."""
    out = []
    for name, fn in h2_scan.AXES:
        out.append((name, [fn(r) for r in rows]))
    for name, fn in h2_scan.PAIRS:
        out.append((name, [fn(r) for r in rows]))
    for name, fn in h2_scan.TRIPLES:
        out.append((name, [fn(r) for r in rows]))
    return out


def main():
    rows = h2_scan.build()
    n = len(rows)
    g = np.array([r["g"] for r in rows])
    c = np.array([r["c"] for r in rows])
    gb = np.array([r["g_bps"] for r in rows])
    cb = np.array([r["c_bps"] for r in rows])
    rdp = np.array([float(r["rdp"]) for r in rows])
    month = np.array([r["month"] for r in rows])
    pooled_g = float(g.mean())
    pooled_c = float(c.mean())
    out = {"pooled_gross_r": pooled_g, "pooled_cost_r": pooled_c,
           "pooled_gross_bps": float(gb.mean()), "pooled_cost_bps": float(cb.mean()), "n": n}

    # ---------------------------------------------------------------- 1. trade-level census
    aff_r = c < pooled_g
    aff_bps = cb < float(gb.mean())
    def blk(mask, label):
        if mask.sum() == 0:
            return None
        gg, cc = g[mask], c[mask]
        return {"label": label, "n": int(mask.sum()), "share": round(float(mask.mean()), 5),
                "gross_r": round(float(gg.mean()), 6), "cost_r": round(float(cc.mean()), 6),
                "net_r": round(float((gg - cc).mean()), 6),
                "t_net": round(float((gg - cc).mean() / ((gg - cc).std(ddof=1) / math.sqrt(mask.sum()))), 3),
                "gross_bps": round(float(gb[mask].mean()), 5),
                "cost_bps": round(float(cb[mask].mean()), 5),
                "edge_cost_r": round(float(gg.mean() / cc.mean()), 4),
                "mean_rdp_bps": round(float(rdp[mask].mean() * 1e4), 3)}
    out["trade_level_affordability"] = {
        "cost_r_below_pooled_edge": blk(aff_r, "cost_true < %.6f R" % pooled_g),
        "cost_bps_below_pooled_edge_bps": blk(aff_bps, "cost_bps < %.5f" % gb.mean()),
        "complement_cost_r": blk(~aff_r, "cost_true >= pooled edge"),
    }
    # cost_r deciles and cost_bps deciles, trade level
    for tag, arr in (("cost_r", c), ("cost_bps", cb)):
        qs = np.quantile(arr, np.linspace(0, 1, 11))
        dec = []
        for i in range(10):
            lo, hi = qs[i], qs[i + 1]
            m = (arr >= lo) & (arr <= hi) if i == 9 else (arr >= lo) & (arr < hi)
            d = blk(m, "%s d%d [%.5f,%.5f]" % (tag, i + 1, lo, hi))
            dec.append(d)
        out["deciles_" + tag] = dec

    # ---------------------------------------------------------------- 2. cell tables
    sets = cellsets(rows)
    daykey = np.array([r["day"] for r in rows])
    cells = []
    for name, keys in sets:
        uniq = sorted(set(keys))
        idx = {k: i for i, k in enumerate(uniq)}
        code = np.array([idx[k] for k in keys])
        cnt = np.bincount(code, minlength=len(uniq))
        sg = np.bincount(code, weights=g, minlength=len(uniq))
        sc = np.bincount(code, weights=c, minlength=len(uniq))
        sgb = np.bincount(code, weights=gb, minlength=len(uniq))
        scb = np.bincount(code, weights=cb, minlength=len(uniq))
        srd = np.bincount(code, weights=rdp, minlength=len(uniq))
        for i, k in enumerate(uniq):
            if cnt[i] < 20:
                continue
            m = code == i
            gg, cc = g[m], c[m]
            nt = gg - cc
            sd = nt.std(ddof=1) if cnt[i] > 1 else float("nan")
            # day-clustered SE of net
            dd = daykey[m]
            dm = nt - nt.mean()
            agg = {}
            for x, dk in zip(dm, dd):
                agg[dk] = agg.get(dk, 0.0) + x
            G = len(agg)
            cse = (math.sqrt(sum(a * a for a in agg.values()) * G / (G - 1)) / cnt[i]) if G > 1 else float("nan")
            cells.append({
                "axis": name, "cell": k, "n": int(cnt[i]),
                "gross_r": round(sg[i] / cnt[i], 6), "cost_r": round(sc[i] / cnt[i], 6),
                "net_r": round((sg[i] - sc[i]) / cnt[i], 6),
                "gross_bps": round(sgb[i] / cnt[i], 5), "cost_bps": round(scb[i] / cnt[i], 5),
                "margin_bps": round((sgb[i] - scb[i]) / cnt[i], 5),
                "edge_cost_r": round(sg[i] / sc[i], 4) if sc[i] > 0 else None,
                "rdp_bps": round(srd[i] / cnt[i] * 1e4, 3),
                "t_net": round(float(nt.mean() / (sd / math.sqrt(cnt[i]))), 3) if sd > 0 else None,
                "t_net_clu": round(float(nt.mean() / cse), 3) if cse == cse and cse > 0 else None,
                "t_edge_vs_pooled": round(float((gg.mean() - pooled_g) /
                                                (gg.std(ddof=1) / math.sqrt(cnt[i]))), 3)
                if cnt[i] > 1 and gg.std(ddof=1) > 0 else None,
                "expected_net_flat_edge": round(pooled_g - sc[i] / cnt[i], 6),
                "excess_over_flat": round((sg[i] / cnt[i]) - pooled_g, 6),
            })
    out["cells"] = cells

    # ---------------------------------------------------------------- 3. flat vs concentration
    win = [x for x in cells if x["net_r"] > 0 and x["n"] >= 100]
    out["winner_decomposition"] = {
        "n_cells_scanned_ge20": len(cells),
        "n_cells_ge100": sum(1 for x in cells if x["n"] >= 100),
        "n_winners_ge100": len(win),
        "winners_that_are_cheap_enough_under_flat_edge":
            sum(1 for x in win if x["expected_net_flat_edge"] > 0),
        "winners_needing_above_pooled_edge":
            sum(1 for x in win if x["expected_net_flat_edge"] <= 0),
        "winners_with_both": sum(1 for x in win if x["expected_net_flat_edge"] > 0
                                 and x["excess_over_flat"] > 0),
    }
    # correlation of realized net vs the flat-edge prediction across cells
    ks = [x for x in cells if x["n"] >= 100]
    out["flat_edge_predictive_power"] = {
        "cells": len(ks),
        "pearson_net_vs_flatpred": H.pearson([x["net_r"] for x in ks],
                                             [x["expected_net_flat_edge"] for x in ks]),
        "spearman_net_vs_flatpred": H.spearman([x["net_r"] for x in ks],
                                               [x["expected_net_flat_edge"] for x in ks]),
        "pearson_net_vs_excess": H.pearson([x["net_r"] for x in ks],
                                           [x["excess_over_flat"] for x in ks]),
        "var_share_cost": None,
    }
    nv = np.array([x["net_r"] for x in ks])
    fv = np.array([x["expected_net_flat_edge"] for x in ks])
    ev = np.array([x["excess_over_flat"] for x in ks])
    out["flat_edge_predictive_power"]["var_share_cost"] = round(
        float(np.var(fv) / np.var(nv)), 4)
    out["flat_edge_predictive_power"]["var_share_edge"] = round(
        float(np.var(ev) / np.var(nv)), 4)
    out["flat_edge_predictive_power"]["cov_share"] = round(
        float(2 * np.cov(fv, ev)[0, 1] / np.var(nv)), 4)

    # ---------------------------------------------------------------- 4. permutation null
    # H0: the gross edge is FLAT -- every trade's g is exchangeable within its month.
    # Cost stays attached to the row.  Count how many cells still clear net>0 and how far
    # the best cell's EXCESS over pooled goes.
    rng = np.random.default_rng(20260806)
    mon_idx = {m: np.where(month == m)[0] for m in np.unique(month)}
    prepared = []
    for name, keys in sets:
        uniq = sorted(set(keys))
        idx = {k: i for i, k in enumerate(uniq)}
        code = np.array([idx[k] for k in keys])
        cnt = np.bincount(code, minlength=len(uniq)).astype(float)
        sc = np.bincount(code, weights=c, minlength=len(uniq))
        keep = cnt >= 100
        prepared.append((name, code, cnt, sc, keep, len(uniq)))
    obs_win = len(win)
    obs_max_excess = max((x["excess_over_flat"] for x in ks), default=0.0)
    obs_max_t = max((x["t_edge_vs_pooled"] or -99 for x in ks), default=0.0)
    null_win, null_max_excess, null_max_t = [], [], []
    for _b in range(B):
        gp = g.copy()
        for m, ii in mon_idx.items():
            gp[ii] = g[rng.permutation(ii)]
        w = 0
        mx = -9e9
        mt = -9e9
        for name, code, cnt, sc, keep, nu in prepared:
            sgp = np.bincount(code, weights=gp, minlength=nu)
            mg = np.divide(sgp, cnt, out=np.zeros_like(sgp), where=cnt > 0)
            mc = np.divide(sc, cnt, out=np.zeros_like(sc), where=cnt > 0)
            w += int(np.sum(keep & (mg - mc > 0)))
            ex = mg - pooled_g
            if keep.any():
                mx = max(mx, float(ex[keep].max()))
                # z of excess using pooled sd as an approximation
                z = ex[keep] / (g.std(ddof=1) / np.sqrt(cnt[keep]))
                mt = max(mt, float(z.max()))
        null_win.append(w)
        null_max_excess.append(mx)
        null_max_t.append(mt)
    null_win = np.array(null_win)
    out["permutation_null"] = {
        "draws": B,
        "observed_winner_cells_ge100": obs_win,
        "null_winner_cells_mean": round(float(null_win.mean()), 2),
        "null_winner_cells_p05": float(np.quantile(null_win, 0.05)),
        "null_winner_cells_p50": float(np.quantile(null_win, 0.50)),
        "null_winner_cells_p95": float(np.quantile(null_win, 0.95)),
        "null_winner_cells_max": int(null_win.max()),
        "p_value_winner_count": round(float((null_win >= obs_win).mean()), 5),
        "observed_max_excess_over_pooled": round(float(obs_max_excess), 6),
        "null_max_excess_p95": round(float(np.quantile(null_max_excess, 0.95)), 6),
        "p_value_max_excess": round(float((np.array(null_max_excess) >= obs_max_excess).mean()), 5),
        "observed_max_t_edge_vs_pooled": round(float(obs_max_t), 3),
        "null_max_t_p95": round(float(np.quantile(null_max_t, 0.95)), 3),
        "p_value_max_t": round(float((np.array(null_max_t) >= obs_max_t).mean()), 5),
        "note": ("H0 is FLAT EDGE, not zero edge: every trade keeps the pooled +%.6f R and its "
                 "own real cost.  A high null winner count therefore CONFIRMS the hypothesis "
                 "that cheap cells pay at the pooled edge -- it is not a false-positive rate."
                 % pooled_g),
    }

    with open(os.path.join(D, "H2_FRONTIER_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    # ------------------------------------------------------------------ bounded print
    print("pooled gross %.6f R (%.5f bps)  cost %.6f R (%.5f bps)  n=%d"
          % (pooled_g, gb.mean(), pooled_c, cb.mean(), n))
    a = out["trade_level_affordability"]
    for k in ("cost_r_below_pooled_edge", "cost_bps_below_pooled_edge_bps", "complement_cost_r"):
        v = a[k]
        if v is None:
            print("  %-32s EMPTY -- NOT ONE TRADE of %d qualifies" % (k, n))
            continue
        print("  %-32s n=%-6d %5.1f%%  g=%+.5f c=%.5f net=%+.5f t=%+.2f ratio=%.3f rdp=%.1fbps"
              % (k, v["n"], 100 * v["share"], v["gross_r"], v["cost_r"], v["net_r"],
                 v["t_net"], v["edge_cost_r"], v["mean_rdp_bps"]))
    print("cost_r deciles (trade level):")
    for d in out["deciles_cost_r"]:
        print("   %-34s n=%-5d g=%+.5f c=%.5f net=%+.5f t=%+6.2f ratio=%6.3f rdp=%.1f"
              % (d["label"], d["n"], d["gross_r"], d["cost_r"], d["net_r"], d["t_net"],
                 d["edge_cost_r"], d["mean_rdp_bps"]))
    print("cost_bps deciles (trade level):")
    for d in out["deciles_cost_bps"]:
        print("   %-34s n=%-5d g=%+.5f c=%.5f net=%+.5f t=%+6.2f ratio=%6.3f rdp=%.1f"
              % (d["label"], d["n"], d["gross_r"], d["cost_r"], d["net_r"], d["t_net"],
                 d["edge_cost_r"], d["mean_rdp_bps"]))
    w = out["winner_decomposition"]
    print("winners: %d cells n>=100 of %d scanned; cheap-enough-under-flat-edge %d; need-above-pooled %d; both %d"
          % (w["n_winners_ge100"], w["n_cells_ge100"],
             w["winners_that_are_cheap_enough_under_flat_edge"],
             w["winners_needing_above_pooled_edge"], w["winners_with_both"]))
    f = out["flat_edge_predictive_power"]
    print("flat-edge prediction vs realized net across %d cells: pearson %.4f spearman %.4f | var share cost %.3f edge %.3f cov %.3f"
          % (f["cells"], f["pearson_net_vs_flatpred"], f["spearman_net_vs_flatpred"],
             f["var_share_cost"], f["var_share_edge"], f["cov_share"]))
    pn = out["permutation_null"]
    print("PERM NULL (flat edge, %d draws): observed winners %d vs null mean %.1f [p05 %.0f p50 %.0f p95 %.0f max %d] p=%.4f"
          % (pn["draws"], pn["observed_winner_cells_ge100"], pn["null_winner_cells_mean"],
             pn["null_winner_cells_p05"], pn["null_winner_cells_p50"],
             pn["null_winner_cells_p95"], pn["null_winner_cells_max"], pn["p_value_winner_count"]))
    print("   max excess over pooled: obs %+.6f vs null p95 %+.6f  p=%.4f | max t: obs %+.2f null p95 %+.2f p=%.4f"
          % (pn["observed_max_excess_over_pooled"], pn["null_max_excess_p95"],
             pn["p_value_max_excess"], pn["observed_max_t_edge_vs_pooled"],
             pn["null_max_t_p95"], pn["p_value_max_t"]))


if __name__ == "__main__":
    main()
