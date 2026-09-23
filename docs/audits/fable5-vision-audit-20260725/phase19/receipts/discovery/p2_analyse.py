"""p2_analyse — apply the pre-declared sealed-test hypotheses.  One pass.

Every threshold here is copied from p2_PREDECLARATION.md §3 and is not tunable.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

import numpy as np

FAMS = [
    "displacement_continuation", "liquidity_sweep_reclaim",
    "structural_distance_extreme", "volatility_compression_expansion",
    "session_open_range_break", "regime_transition_break", "cross_asset_lead_lag",
    "current_fvg_fill", "current_ob_retest", "current_breaker_re_entry",
]
ATM = set(FAMS[:7])
EARLY5 = {"displacement_continuation", "liquidity_sweep_reclaim",
          "session_open_range_break", "regime_transition_break",
          "volatility_compression_expansion"}
JUNE_MIN = "2025-06-12"
NDRAW = 4000
SEED = 20260806
WIN = {"202506": "june_2025", "202508": "august_2025", "202509": "september_2025"}
import collections
WIN = collections.defaultdict(lambda: "OTHER", WIN)
for _m in ("202510","202511","202512","202601","202602","202603","202604","202605"):
    WIN[_m] = _m


def boot(vals, blocks, n=NDRAW, seed=SEED):
    """Day-block bootstrap of a mean.  blocks = integer block id per value."""
    vals = np.asarray(vals, float)
    ok = np.isfinite(vals)
    vals, blocks = vals[ok], np.asarray(blocks)[ok]
    if vals.size == 0:
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n": 0, "n_blocks": 0}
    ub, inv = np.unique(blocks, return_inverse=True)
    s = np.bincount(inv, weights=vals, minlength=ub.size)
    c = np.bincount(inv, minlength=ub.size).astype(float)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, ub.size, size=(n, ub.size))
    m = s[pick].sum(1) / np.maximum(c[pick].sum(1), 1e-12)
    return {
        "mean": float(vals.mean()), "ci_lo": float(np.percentile(m, 2.5)),
        "ci_hi": float(np.percentile(m, 97.5)),
        "p_le_0": float((m <= 0).mean()), "p_ge_0": float((m >= 0).mean()),
        "n": int(vals.size), "n_blocks": int(ub.size),
    }


def econ(g, c, filled):
    """gross/cost/net per FILL, win rate, payoff, breakeven."""
    g, c, filled = np.asarray(g), np.asarray(c), np.asarray(filled, bool)
    if filled.sum() == 0:
        return {}
    gg, cc = g[filled], c[filled]
    win = gg > 0
    a = float(gg[win].mean()) if win.any() else 0.0
    b = float(-gg[~win].mean()) if (~win).any() else 0.0
    C = float(cc.mean())
    return {
        "n_fills": int(filled.sum()), "gross": float(gg.mean()), "cost": C,
        "net": float((gg - cc).mean()), "win_rate": float(win.mean()),
        "winner_mean": a, "loser_mean": b,
        "payoff": (a / b) if b else None,
        "breakeven_gross": (b / (a + b)) if (a + b) else None,
        "breakeven_net": ((b + C) / (a + b)) if (a + b) else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    D = {}
    for path in args.npz.split(","):
        z = np.load(path, allow_pickle=False)
        meta = json.loads(str(z["meta"]))
        D[meta["month"]] = (z, meta)

    R = {"windows": {}, "pooled": {}, "declaration": "p2_PREDECLARATION.md"}
    months = sorted(D)

    # ---------------- assemble pooled roster arrays --------------------
    cols = ["day", "sym", "fam", "long", "e", "d", "gap_r", "bps", "lag", "cost_r",
            "g_c", "x_c", "g_l", "x_l", "g_s", "x_s", "g_a", "x_a", "g_e", "x_e", "g_m", "x_m"]
    P = defaultdict(list)
    blk, wlab, daylab = [], [], []
    bid = 0
    for m in months:
        z, meta = D[m]
        days = np.array(meta["days"])
        dnames = days[z["day"]]
        keep = np.ones(len(dnames), bool) if m != "202506" else (dnames >= JUNE_MIN)
        for c in cols:
            P[c].append(z[c][keep])
        dk = dnames[keep]
        ub = {d: bid + i for i, d in enumerate(sorted(set(dk)))}
        bid += len(ub)
        blk.append(np.array([ub[d] for d in dk]))
        wlab.append(np.array([m] * keep.sum()))
        daylab.append(dk)
        R["windows"].setdefault(WIN[m], {})["coverage"] = {
            "generated_days": len(days), "days_used": int(len(set(dk))),
            "days_dropped_incomplete_lookback": int(len(days) - len(set(dk))),
            "emissions_walked_all_days": int(len(dnames)),
            "emissions_used": int(keep.sum()),
            "raw_generator_rows_all_k": meta["n_raw_rows"],
            "close_only_emissions": meta["n_close_rows"],
        }
    A = {c: np.concatenate(P[c]) for c in cols}
    A["blk"] = np.concatenate(blk)
    A["win"] = np.concatenate(wlab)
    A["dayname"] = np.concatenate(daylab)

    famname = np.array(FAMS)[A["fam"]]
    clean = (famname != "current_breaker_re_entry") & (A["bps"] == 0)
    fill_c = A["x_c"] != 3
    fill_l = A["x_l"] != 3
    fill_a = A["x_a"] != 3
    net_c = A["g_c"] - A["cost_r"] * fill_c
    net_l = A["g_l"] - A["cost_r"] * fill_l
    net_a = A["g_a"] - A["cost_r"] * fill_a
    net_s = A["g_s"] - A["cost_r"] * (A["x_s"] != 3)
    fill_e = A["x_e"] != 3
    net_e = A["g_e"] - A["cost_r"] * fill_e

    def per_window(mask, arr):
        return {WIN[m]: (float(np.nanmean(arr[mask & (A["win"] == m)]))
                         if (mask & (A["win"] == m)).any() else None) for m in months}

    # ================= H1 ==============================================
    mc = clean & fill_c
    h1 = econ(A["g_c"], A["cost_r"], mc)
    h1["bootstrap_gross"] = boot(A["g_c"][mc], A["blk"][mc])
    h1["bootstrap_net"] = boot(net_c[mc], A["blk"][mc])
    h1["per_window_gross"] = per_window(mc, A["g_c"])
    h1["per_window_net"] = per_window(mc, net_c)
    h1["per_window_n"] = {WIN[m]: int((mc & (A["win"] == m)).sum()) for m in months}
    pos = sum(1 for v in h1["per_window_gross"].values() if v is not None and v > 0)
    g, n = h1["gross"], h1["net"]
    if n >= 0:
        verdict = "ECONOMIC_REFUTATION"
    elif g >= 0.05 and h1["bootstrap_gross"]["ci_lo"] > 0 and pos >= 2:
        verdict = "REFUTED_SIGNAL_REAL"
    elif g <= -0.05 and h1["bootstrap_gross"]["ci_hi"] < 0:
        verdict = "REFUTED_SIGNAL_NEGATIVE"
    elif abs(g) <= 0.05 and n <= -0.10:
        verdict = "CONFIRMED"
    else:
        verdict = "INDETERMINATE_vs_DECLARED_BANDS"
    h1["windows_gross_positive"] = pos
    h1["VERDICT"] = verdict
    # secondary: f1 contract, whole roster, per-emission
    ml = clean & fill_l
    h1["secondary_f1_contract_clean"] = econ(A["g_l"], A["cost_r"], ml)
    h1["secondary_whole_roster_corrected"] = econ(A["g_c"], A["cost_r"], fill_c)
    h1["secondary_per_emission_corrected_clean"] = {
        "n": int(clean.sum()), "gross": float(A["g_c"][clean].mean()),
        "net": float(net_c[clean].mean()),
    }
    R["H1_signal_is_zero"] = h1

    # ================= H2 ==============================================
    sde = clean & fill_c & (famname == "structural_distance_extreme")
    h2 = econ(A["g_c"], A["cost_r"], sde)
    h2["bootstrap_gross"] = boot(A["g_c"][sde], A["blk"][sde])
    h2["per_window_gross"] = per_window(sde, A["g_c"])
    h2["per_window_n"] = {WIN[m]: int((sde & (A["win"] == m)).sum()) for m in months}
    p2 = sum(1 for v in h2["per_window_gross"].values() if v is not None and v > 0)
    h2["windows_positive"] = p2
    h2["gross_over_toll"] = h2["gross"] / h2["cost"] if h2.get("cost") else None
    h2["VERDICT"] = ("REPLICATES" if (h2["gross"] >= 0.03 and p2 >= 2)
                     else "IN_SAMPLE_ARTIFACT")
    h2["in_sample_reference"] = {"gross": 0.06639, "windows_positive": "8/8"}
    # all families, for the record
    h2["all_families"] = {}
    for f in FAMS:
        mf = clean & fill_c & (famname == f)
        if mf.sum() < 30:
            continue
        e = econ(A["g_c"], A["cost_r"], mf)
        e["per_window_gross"] = per_window(mf, A["g_c"])
        h2["all_families"][f] = e
    R["H2_structural_distance_extreme"] = h2

    # ================= H3 ==============================================
    m3 = clean & fill_c
    dlt = (net_s - net_c)[m3]
    h3 = {"n": int(m3.sum()), "delta_net": float(dlt.mean()),
          "net_shipped_target_2R": float(net_c[m3].mean()),
          "net_stop_only_horizon": float(net_s[m3].mean()),
          "bootstrap": boot(dlt, A["blk"][m3]),
          "per_window": per_window(m3, net_s - net_c),
          "in_sample_reference": {"delta_net": 0.03500, "windows_positive": "8/8"}}
    p3 = sum(1 for v in h3["per_window"].values() if v is not None and v > 0)
    h3["windows_positive"] = p3
    h3["VERDICT"] = ("REPLICATES" if (h3["delta_net"] >= 0.02 and p3 >= 2)
                     else "DOES_NOT_REPLICATE")
    R["H3_exit_swap"] = h3

    # ================= H4 ==============================================
    dlt4 = net_a - net_l          # per OPPORTUNITY (no_fill books 0)
    allm = np.ones(len(dlt4), bool)
    h4 = {"n_opportunities": int(allm.sum()),
          "net_estate_all_limit": float(net_l.mean()),
          "net_side_aware": float(net_a.mean()),
          "gross_estate_per_fill": float(A["g_l"][fill_l].mean()),
          "gross_side_aware_per_fill": float(A["g_a"][fill_a].mean()),
          "delta_net": float(dlt4.mean()),
          "bootstrap": boot(dlt4, A["blk"]),
          "per_window": per_window(allm, dlt4),
          "share_gap_r_negative": float((A["gap_r"] < 0).mean()),
          "fill_rate_gap_neg_estate": float(fill_l[A["gap_r"] < 0].mean()),
          "fill_rate_gap_neg_side_aware": float(fill_a[A["gap_r"] < 0].mean()),
          "in_sample_reference": {"delta_net": 0.02995, "windows_positive": "8/8"}}
    d5b = net_a - net_e
    h4["variant_b_vs_d5_one_sided_estate_baseline"] = {
        "net_d5_estate_one_sided": float(net_e.mean()),
        "gross_d5_estate_per_fill": float(A["g_e"][fill_e].mean()),
        "fill_rate_gap_neg_d5_estate": float(fill_e[A["gap_r"] < 0].mean()),
        "delta_net": float(d5b.mean()), "bootstrap": boot(d5b, A["blk"]),
        "per_window": per_window(np.ones(len(d5b), bool), d5b)}
    _v = h4["variant_b_vs_d5_one_sided_estate_baseline"]
    _p = sum(1 for v in _v["per_window"].values() if v is not None and v > 0)
    _v["windows_positive"] = _p
    _v["VERDICT"] = ("REPLICATES" if (_v["delta_net"] >= 0.015 and _p >= 2)
                     else "DOES_NOT_REPLICATE")
    p4 = sum(1 for v in h4["per_window"].values() if v is not None and v > 0)
    h4["windows_positive"] = p4
    h4["VERDICT"] = ("REPLICATES" if (h4["delta_net"] >= 0.015 and p4 >= 2)
                     else "DOES_NOT_REPLICATE")
    R["H4_fill_contract_repair"] = h4

    # ================= H6 ==============================================
    m6 = (np.isin(famname, list(ATM))) & (A["lag"] == 0) & np.isfinite(A["g_m"])
    sig = (A["g_c"] - A["g_m"])[m6]
    h6 = {"n": int(m6.sum()), "real_gross": float(A["g_c"][m6].mean()),
          "mirror_gross": float(A["g_m"][m6].mean()),
          "signal": float(sig.mean()), "bootstrap": boot(sig, A["blk"][m6]),
          "per_window": per_window(m6, A["g_c"] - A["g_m"]),
          "toll_on_same_rows": float(A["cost_r"][m6].mean()),
          "in_sample_reference": {"f2_paired_signal": 0.02877, "d7_signal": -0.04230}}
    p6 = sum(1 for v in h6["per_window"].values() if v is not None and v > 0)
    h6["windows_positive"] = p6
    lo, hi = h6["bootstrap"]["ci_lo"], h6["bootstrap"]["ci_hi"]
    if h6["signal"] >= 0.02 and lo > 0:
        h6["VERDICT"] = "DIRECTION_POSITIVE"
    elif h6["signal"] <= -0.02 and hi < 0:
        h6["VERDICT"] = "DIRECTION_NEGATIVE"
    else:
        h6["VERDICT"] = "DIRECTION_ZERO"
    R["H6_direction_vs_mirror"] = h6

    # ================= H5 ==============================================
    h5 = {}
    pk = {}
    for m in months:
        z, meta = D[m]
        if "P_c_g" not in z:
            continue
        days = np.array(meta["days"])
        dn = days[z["P_day"]]
        keep = np.ones(len(dn), bool) if m != "202506" else (dn >= JUNE_MIN)
        pk[m] = {k[2:]: z[k][keep] for k in z.files if k.startswith("P_")}
        pk[m]["dayname"] = dn[keep]
    if pk:
        cg = np.concatenate([pk[m]["c_g"] for m in pk])
        cc = np.concatenate([pk[m]["c_c"] for m in pk])
        pg = np.concatenate([pk[m]["p_g"] for m in pk])
        pc = np.concatenate([pk[m]["p_c"] for m in pk])
        pki = np.concatenate([pk[m]["p_k"] for m in pk])
        ci_ = np.concatenate([pk[m]["c_i"] for m in pk])
        pi_ = np.concatenate([pk[m]["p_i"] for m in pk])
        fam5 = np.array(FAMS)[np.concatenate([pk[m]["fam"] for m in pk])]
        sy5 = np.concatenate([pk[m]["sym"] for m in pk])
        dn5 = np.concatenate([pk[m]["dayname"] for m in pk])
        w5 = np.concatenate([np.array([m] * len(pk[m]["c_g"])) for m in pk])
        ub5 = {d: i for i, d in enumerate(sorted(set(dn5)))}
        blk5 = np.array([ub5[d] for d in dn5])
        e5 = np.isin(fam5, list(EARLY5))
        cn, pn = cg - cc, pg - pc
        paired = e5 & np.isfinite(cn) & np.isfinite(pn)
        dl = (pn - cn)[paired]
        h5["a_paired"] = {
            "n_pairs": int(paired.sum()), "close_net": float(cn[paired].mean()),
            "partial_net": float(pn[paired].mean()), "delta_net": float(dl.mean()),
            "bootstrap": boot(dl, blk5[paired]),
            "mean_earliness_min": float((15 - pki[paired]).mean()),
            "per_window": {WIN[m]: (float((pn - cn)[paired & (w5 == m)].mean())
                                    if (paired & (w5 == m)).any() else None)
                           for m in months},
            "in_sample_reference": {"jan": 0.19562, "feb": 0.19302, "mar": 0.23656},
        }
        pw = h5["a_paired"]["per_window"]
        npos = sum(1 for v in pw.values() if v is not None and v > 0)
        h5["a_paired"]["windows_positive"] = npos
        h5["a_paired"]["VERDICT"] = (
            "REPLICATES" if (h5["a_paired"]["delta_net"] >= 0.10
                             and npos == len([v for v in pw.values() if v is not None]))
            else "DOES_NOT_REPLICATE")

        # implementable books, live PlacementLedger dedup
        def book(net, idx, present):
            m = e5 & present & np.isfinite(net)
            best = {}
            for j in np.nonzero(m)[0]:
                key = (fam5[j], sy5[j], dn5[j])
                if key not in best or idx[j] < idx[best[key]]:
                    best[key] = j
            sel = np.array(sorted(best.values()), int)
            return sel
        selc = book(cn, ci_, np.isfinite(cg))
        selp = book(pn, pi_, np.isfinite(pg))
        h5["b_implementable"] = {
            "close_book": {"n": int(selc.size), "net": float(cn[selc].mean()),
                           "gross": float(cg[selc].mean()),
                           "bootstrap": boot(cn[selc], blk5[selc])},
            "partial_book": {"n": int(selp.size), "net": float(pn[selp].mean()),
                             "gross": float(pg[selp].mean()),
                             "bootstrap": boot(pn[selp], blk5[selp])},
            "phantom_leg": {
                "n": int((e5 & np.isfinite(pg) & ~np.isfinite(cg)).sum()),
                "net": float(pn[e5 & np.isfinite(pg) & ~np.isfinite(cg)].mean())
                if (e5 & np.isfinite(pg) & ~np.isfinite(cg)).any() else None},
            "per_window": {WIN[m]: {
                "close": float(cn[selc][w5[selc] == m].mean())
                if (w5[selc] == m).any() else None,
                "partial": float(pn[selp][w5[selp] == m].mean())
                if (w5[selp] == m).any() else None} for m in months},
            "in_sample_reference": {"close_book": -0.15161, "partial_book": -0.17778},
        }
        bw = h5["b_implementable"]["per_window"]
        beat = sum(1 for v in bw.values()
                   if v["close"] is not None and v["partial"] is not None
                   and v["partial"] > v["close"])
        h5["b_implementable"]["windows_partial_beats_close"] = beat
        h5["b_implementable"]["CANDIDATE"] = (
            "PASSES" if (h5["b_implementable"]["partial_book"]["net"] > 0 and beat >= 2)
            else "FAILS")
    R["H5_forming_bar_candidate"] = h5

    with open(args.out, "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    for k in ("H1_signal_is_zero", "H2_structural_distance_extreme",
              "H3_exit_swap", "H4_fill_contract_repair", "H6_direction_vs_mirror"):
        v = R[k]
        print(k, v.get("VERDICT"),
              {a: round(v[a], 5) for a in ("gross", "net", "delta_net", "signal")
               if a in v and v[a] is not None})
    if h5:
        print("H5a", h5["a_paired"]["VERDICT"], round(h5["a_paired"]["delta_net"], 5))
        print("H5b", h5["b_implementable"]["CANDIDATE"],
              round(h5["b_implementable"]["partial_book"]["net"], 5),
              "vs close", round(h5["b_implementable"]["close_book"]["net"], 5))


if __name__ == "__main__":
    main()
