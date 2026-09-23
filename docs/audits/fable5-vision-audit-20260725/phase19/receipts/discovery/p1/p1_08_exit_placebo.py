"""p1 step 8 — IS THE PERSISTENT EXIT ORDERING AN EDGE, OR TAPE GEOMETRY?

The one axis whose ordering travels is the exit contract.  Test it against the exact
mirror (placebo-side) arm on the identical rows: widening the target from 1.5R to 2.0R
is a pure exit change, so if the coin flip gains the same amount the ordering is a
property of the tape's path distribution, available to any participant -- real money to
a book already taking these trades, but NOT evidence of signal.
"""
from __future__ import annotations
import numpy as np, json, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L
ws, _ = L.load_all()
OUT = {"target_ladder_1p5_to_2p0": {}, "note": ""}
rows = []
for w in ws:
    z = np.load(f"{L.ROWS}/D1_{w.w}.npz")
    m = (w.fil == 1) & (w.past == 0) & (w.fam != 1)          # clean roster, limit contract
    r15 = w.g15[m]; r20 = w.g[m]
    f15 = z["fg15"].astype(float)[m]; f20 = w.gm[m]
    a = (w.atm == 1) & (w.mfil == 1) & (w.past == 0) & (w.fam != 1)  # at-market, market fill
    m15 = z["mr15"].astype(float)[a]; m20 = z["mr20"].astype(float)[a]
    mf15 = z["mf15"].astype(float)[a]; mf20 = z["mf20"].astype(float)[a]
    d = dict(window=w.w, n=int(m.sum()),
             real_gain=float((r20 - r15).mean()), mirror_gain=float((f20 - f15).mean()),
             n_atm=int(a.sum()),
             real_gain_atm=float((m20 - m15).mean()), mirror_gain_atm=float((mf20 - mf15).mean()))
    d["signal_component"] = d["real_gain"] - d["mirror_gain"]
    d["signal_component_atm"] = d["real_gain_atm"] - d["mirror_gain_atm"]
    rows.append(d)
    print(f"{w.w} clean n={d['n']:6d} real +{d['real_gain']:.5f} mirror +{d['mirror_gain']:.5f} "
          f"signal {d['signal_component']:+.5f} | atm n={d['n_atm']:6d} real +{d['real_gain_atm']:.5f} "
          f"mirror +{d['mirror_gain_atm']:.5f} signal {d['signal_component_atm']:+.5f}", flush=True)
W = lambda f, k: float(np.average([r[f] for r in rows], weights=[r[k] for r in rows]))
agg = dict(real_gain=W("real_gain", "n"), mirror_gain=W("mirror_gain", "n"),
           signal=W("signal_component", "n"),
           real_gain_atm=W("real_gain_atm", "n_atm"), mirror_gain_atm=W("mirror_gain_atm", "n_atm"),
           signal_atm=W("signal_component_atm", "n_atm"),
           months_real_pos=sum(1 for r in rows if r["real_gain"] > 0),
           months_mirror_pos=sum(1 for r in rows if r["mirror_gain"] > 0),
           months_signal_pos=sum(1 for r in rows if r["signal_component"] > 0))
agg["coin_flip_share_of_gain"] = agg["mirror_gain"] / agg["real_gain"]
agg["coin_flip_share_of_gain_atm"] = agg["mirror_gain_atm"] / agg["real_gain_atm"]
OUT["target_ladder_1p5_to_2p0"] = dict(per_window=rows, pooled=agg)
print("\nPOOLED  real +%.5f  mirror(coin flip) +%.5f  -> coin flip reproduces %.1f%% "
      "| signal attributable %+.5f (%d/8 months)"
      % (agg["real_gain"], agg["mirror_gain"], 100 * agg["coin_flip_share_of_gain"],
         agg["signal"], agg["months_signal_pos"]))
print("AT-MKT  real +%.5f  mirror +%.5f  -> %.1f%% | signal %+.5f"
      % (agg["real_gain_atm"], agg["mirror_gain_atm"], 100 * agg["coin_flip_share_of_gain_atm"],
         agg["signal_atm"]))
json.dump(OUT, open("/tmp/p1/P1_EXITPLACEBO_V1.json", "w"))
