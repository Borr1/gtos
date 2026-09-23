#!/usr/bin/env python3
"""e-coherence step 9 — THE QUESTION NO LANE ASKED, ANSWERED.

12,747 rows (46.088% of the pool) are POI limit orders the live engine cannot place
(L10-X3: entry == executable quote on 296/296 live captures, TRADE_ACTION_DEAL only).
Every lane either dropped them, or walked them at a price the market had already left.
Nobody asked the obvious thing: CONVERT them.  Take the same setup, enter at MARKET at
the decision instant, keep the same stop price.  That is a one-line generator change and
it makes 46% of the book placeable.

Exact algebra.  Let d = |entry - stop| (the pool's risk distance) and m = mkt_r (the market's
position at the decision, signed for the trade, in units of d).  Entering at market:
    new risk distance   d' = (1 + m) * d          [stop price unchanged]
    path R rebased      R' = (path_r - m) / (1 + m)
    the stop is still exactly -1 R' and a k-R' target is k*(1+m) - m in old units.
Rows with 1 + m <= 0 (past_stop) have no positive risk distance and are un-convertible.
"""
import json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
born = df["born"]
conv = born.isin(["resting", "marketable"])          # 9,214 convertible POI limits
sub = df.loc[conv]
keys = set(zip(sub["candidate_id"], sub["decision_time_utc"]))
mmap = dict(zip(zip(sub["candidate_id"], sub["decision_time_utc"]), sub["mkt_r"]))
OUT = {"population": {"convertible_n": int(conv.sum()),
                      "resting": int((born == "resting").sum()),
                      "marketable": int((born == "marketable").sum()),
                      "past_stop_unconvertible": int((born == "past_stop").sum())}}

res = {}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    m = float(mmap[kk])
    scale = 1.0 + m
    if scale <= 1e-9:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    out = {}
    for tgt in (2.0, 1.5, 3.0):
        r = None
        for i in range(n):
            f = (fav[i] - m) / scale
            a = (adv[i] - m) / scale
            if a <= -1.0:
                r = -1.0
                break
            if f >= tgt:
                r = tgt
                break
        if r is None:
            r = (cls[n - 1] - m) / scale
        out[f"T{tgt}"] = r
    out["hold"] = (cls[n - 1] - m) / scale
    out["scale"] = scale
    res[kk] = out

sub = sub.copy()
sub["_k"] = list(zip(sub["candidate_id"], sub["decision_time_utc"]))
for c in ["T2.0", "T1.5", "T3.0", "hold", "scale"]:
    sub[c] = [res.get(k, {}).get(c, np.nan) for k in sub["_k"]]
ok = sub["scale"].notna()
s = sub.loc[ok].copy()
# cost re-denominated onto the NEW risk distance: cost_price is unchanged, d' = scale*d
s["cost_TRUE_conv"] = s["cost_r_TRUE"] / s["scale"]
s["cost_frozen_conv"] = s["cost_r"] / s["scale"]
s["rd_bps_conv"] = (s["risk_distance"] * s["scale"] / s["entry_price"]) * 1e4
s["signal_bps_conv"] = s["T2.0"] * s["rd_bps_conv"]
s["toll_bps"] = s["cost_r_TRUE"] * (s["risk_distance"] / s["entry_price"]) * 1e4

def blk(q, label):
    n = len(q)
    return {"label": label, "n": n,
            "R_gross_T2": round(float(q["T2.0"].mean()), 6),
            "se": round(float(q["T2.0"].std(ddof=1) / np.sqrt(n)), 6),
            "t": round(float(q["T2.0"].mean() / (q["T2.0"].std(ddof=1) / np.sqrt(n))), 3),
            "R_gross_hold": round(float(q["hold"].mean()), 6),
            "cost_TRUE_conv": round(float(q["cost_TRUE_conv"].mean()), 6),
            "R_net_TRUE": round(float((q["T2.0"] - q["cost_TRUE_conv"]).mean()), 6),
            "signal_bps": round(float(q["signal_bps_conv"].mean()), 4),
            "toll_bps": round(float(q["toll_bps"].mean()), 4),
            "edge_bps": round(float((q["signal_bps_conv"] - q["toll_bps"]).mean()), 4),
            "median_scale": round(float(q["scale"].median()), 4),
            "win": round(float((q["T2.0"] > 0).mean()), 5)}

OUT["headline"] = [
    blk(s, "ALL convertible POI limits, entered at MARKET"),
    blk(s.loc[s["born"] == "resting"], "resting only"),
    blk(s.loc[s["born"] == "marketable"], "marketable only"),
]
OUT["as_emitted_comparison"] = {
    "same_rows_fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 6),
    "same_rows_plain_blind_walk_r": round(float(s["plain_walk_r"].mean()), 6),
    "same_rows_engine_gross_r": round(float(s["gross_r"].mean()), 6),
    "converted_to_market_T2": round(float(s["T2.0"].mean()), 6),
    "converted_net_at_TRUE": round(float((s["T2.0"] - s["cost_TRUE_conv"]).mean()), 6),
}
per = []
for f, g in s.groupby("origin_family"):
    if len(g) < 30:
        continue
    per.append({"family": f, "n": int(len(g)),
                "R_gross_T2": round(float(g["T2.0"].mean()), 6),
                "t": round(float(g["T2.0"].mean() / (g["T2.0"].std(ddof=1) / np.sqrt(len(g)))), 3),
                "R_net_TRUE": round(float((g["T2.0"] - g["cost_TRUE_conv"]).mean()), 6),
                "edge_bps": round(float((g["signal_bps_conv"] - g["toll_bps"]).mean()), 4),
                "as_emitted_honest": round(float(g["fill_honest_walk_r"].mean()), 6)})
per.sort(key=lambda r: -r["R_net_TRUE"])
OUT["per_family"] = per
# split-half by date
s["half"] = np.where(s["day"] <= "2026-01-15", "H1", "H2")
OUT["split_half"] = [{"half": h, "n": int(len(g)),
                      "R_gross_T2": round(float(g["T2.0"].mean()), 6),
                      "R_net_TRUE": round(float((g["T2.0"] - g["cost_TRUE_conv"]).mean()), 6)}
                     for h, g in s.groupby("half")]
# dedup control
fe = s.loc[s["is_first_emission"].astype(bool)]
OUT["first_emission_only"] = {"n": int(len(fe)),
                              "R_gross_T2": round(float(fe["T2.0"].mean()), 6),
                              "R_net_TRUE": round(float((fe["T2.0"] - fe["cost_TRUE_conv"]).mean()), 6)}
json.dump(OUT, open(f"{D}/E_CONVERT_V1.json", "w"), indent=1)
print(json.dumps(OUT["population"]))
for h in OUT["headline"]:
    print(f"{h['label']:44s} n={h['n']:5d} R_T2={h['R_gross_T2']:+.5f}(t{h['t']:+.2f}) hold={h['R_gross_hold']:+.5f} cost={h['cost_TRUE_conv']:.4f} NET={h['R_net_TRUE']:+.5f} sig={h['signal_bps']:+.3f}bps toll={h['toll_bps']:.3f} edge={h['edge_bps']:+.3f} scale={h['median_scale']:.3f}")
print(json.dumps(OUT["as_emitted_comparison"], indent=0))
print("--- per family (converted) ---")
for p in per:
    print(f"  {p['family']:28s} n={p['n']:5d} R_T2={p['R_gross_T2']:+.5f}(t{p['t']:+.2f}) NET={p['R_net_TRUE']:+.5f} edge={p['edge_bps']:+7.3f}bps  as-emitted={p['as_emitted_honest']:+.5f}")
print(json.dumps(OUT["split_half"]), json.dumps(OUT["first_emission_only"]))
