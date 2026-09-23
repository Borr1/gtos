#!/usr/bin/env python3
"""e-coherence step 12 — is the composed book's +0.0178 R/trade SIGNAL or January's DRIFT?

Every *_r column is signed for the trade's own side, so a common market drift enters LONG
rows with a + and SHORT rows with a -.  Therefore
    SIGNAL    = (mean_LONG + mean_SHORT) / 2     (direction-neutral: what the rule knows)
    DIRECTION = (mean_LONG - mean_SHORT) / 2     (what the market did)
L1-F4 ran this on the raw pool and found the only significant term was DIRECTION.  Run it
on the composed book, which is the only gross-positive contract in the lane.
"""
import json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["B"] = df["plain_walk_r"].astype(float)
live = df["born"] == "at_limit"
sub = df.loc[live].copy()
gT = (sub["true_spread_r"] <= 0.10) & (sub["cost_r_TRUE"] <= 0.15)
s2 = sub.loc[gT].copy()
keys = set(zip(s2["candidate_id"], s2["decision_time_utc"]))
res = {}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    if n <= 5:
        continue
    base = cls[4]
    peak, r = 0.0, None
    for i in range(5, n):
        f, a = fav[i] - base, adv[i] - base
        lvl = max(peak - 0.25, -1.0) if peak > 0 else -1.0
        if a <= lvl:
            r = lvl
            break
        peak = max(peak, f)
    res[kk] = cls[n - 1] - base if r is None else r
s2["_k"] = list(zip(s2["candidate_id"], s2["decision_time_utc"]))
s2["R"] = [res.get(k, np.nan) for k in s2["_k"]]
q = s2.loc[s2["R"].notna()].copy()
OUT = {}


def sd(frame, col, label):
    L = frame.loc[frame["side"].str.upper().str.startswith("L"), col]
    S = frame.loc[~frame["side"].str.upper().str.startswith("L"), col]
    if len(L) < 5 or len(S) < 5:
        return None
    sig = (L.mean() + S.mean()) / 2
    dirn = (L.mean() - S.mean()) / 2
    se_sig = 0.5 * np.sqrt(L.var(ddof=1) / len(L) + S.var(ddof=1) / len(S))
    return {"label": label, "n": len(frame), "n_long": int(len(L)), "n_short": int(len(S)),
            "mean_LONG": round(float(L.mean()), 6), "mean_SHORT": round(float(S.mean()), 6),
            "SIGNAL": round(float(sig), 6), "SIGNAL_se": round(float(se_sig), 6),
            "SIGNAL_t": round(float(sig / se_sig), 3),
            "DIRECTION": round(float(dirn), 6), "DIRECTION_t": round(float(dirn / se_sig), 3),
            "overall_mean": round(float(frame[col].mean()), 6)}


OUT["composed_book"] = sd(q, "R", "gated live cohort, delay5 + trail0.25")
OUT["live_cohort_baseline"] = sd(sub, "B", "all placeable, incumbent T2/S1")
OUT["whole_pool_engine"] = sd(df, "gross_r", "whole pool, engine gross (L1-F4 comparator)")

# per-symbol stability of the composed book
per = []
for s, g in q.groupby("symbol"):
    if len(g) < 60:
        continue
    per.append({"symbol": s, "n": int(len(g)), "mean": round(float(g["R"].mean()), 6),
                "t": round(float(g["R"].mean() / (g["R"].std(ddof=1) / np.sqrt(len(g)))), 2),
                "net_TRUE": round(float((g["R"] - g["cost_r_TRUE"]).mean()), 6)})
per.sort(key=lambda r: -r["mean"])
OUT["composed_book_by_symbol"] = per
OUT["concentration"] = {
    "n_symbols": len(per),
    "top_symbol_share_of_total_R": round(float(max(g["R"].sum() for _, g in q.groupby("symbol")) / q["R"].sum()), 4)
    if q["R"].sum() != 0 else None,
    "n_symbols_positive": int(sum(1 for p in per if p["mean"] > 0)),
    "n_symbols_net_positive": int(sum(1 for p in per if p["net_TRUE"] > 0)),
}
json.dump(OUT, open(f"{D}/E_SIGNALTEST_V1.json", "w"), indent=1)
for k in ("composed_book", "live_cohort_baseline", "whole_pool_engine"):
    v = OUT[k]
    print(f"{v['label']:44s} n={v['n']:6d} L={v['mean_LONG']:+.5f} S={v['mean_SHORT']:+.5f} SIGNAL={v['SIGNAL']:+.5f}(t{v['SIGNAL_t']:+.2f}) DIRECTION={v['DIRECTION']:+.5f}(t{v['DIRECTION_t']:+.2f})")
print("--- composed book by symbol ---")
for p in per:
    print(f"  {p['symbol']:12s} n={p['n']:5d} R={p['mean']:+.5f} t={p['t']:+5.2f} net={p['net_TRUE']:+.5f}")
print(json.dumps(OUT["concentration"]))
