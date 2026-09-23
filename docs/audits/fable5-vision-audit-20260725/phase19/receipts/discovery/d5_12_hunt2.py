"""d5-12 — re-rank every observable against the SIDE-AWARE outcome labels.

Why this had to be redone: under the estate's fill convention a BUY whose entry sits ABOVE the
market is filled instantly at that entry, so 86.9 % of those rows label as `stop`.  Any feature
correlated with "entry on the wrong side of the market" therefore separates target-from-stop for
a reason that has nothing to do with the market.  Re-labelling with the broker-correct touch side
(a BUY above the market fills on high>=e) removes that circuit.

Populations, all on the reproduced sealed roster, 5 fully-rebuilt windows:
  RESOLVED            side-aware fill reached target or stop first
  PENDING_RESOLVED    ... and the order was still UNFILLED at T+1m, i.e. the confirm minute is
                      genuinely actionable (this is the only population a refusal rule can use)
"""
import json, os, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import cohens_d, auc, qcut, strat_d, within_rank

OUT = "/tmp/d5/out"
WINS = [w for w in ("2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
                    "2026-04", "2026-05")
        if os.path.isfile("%s/D9_%s.npz" % (OUT, w)) and os.path.isfile("%s/D5_%s.npz" % (OUT, w))
        and np.load("%s/D9_%s.npz" % (OUT, w))["c0"].size == np.load("%s/D5_%s.npz" % (OUT, w))["c0"].size]
ACC = []
for wi, w in enumerate(WINS):
    a = np.load("%s/D5_%s.npz" % (OUT, w)); b = np.load("%s/D9_%s.npz" % (OUT, w))
    D = {k: a[k] for k in ("geo", "barrng_r", "atr60_r", "risk_bps", "cost_r", "c0", "c0_fav",
                           "c0_adv", "c0_rng", "touch0", "vol0_ratio", "c1", "c4", "fav5",
                           "adv5", "mkt_r0", "hour", "sym", "fam", "dayi")}
    D["rs"] = b["rs"]; D["js"] = b["js"]; D["gs"] = b["gs"]; D["r0"] = b["r0"]; D["j0"] = b["j0"]
    D["win"] = np.full(D["c0"].size, wi)
    ACC.append(D)
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
A["disp0"] = A["c0"] - A["mkt_r0"]
A["mom5"] = A["c4"] - A["c0"]
A["abs_mkt_r0"] = np.abs(A["mkt_r0"])
N = A["c0"].size

FEATS = [("mkt_r0", "PRE"), ("abs_mkt_r0", "PRE"), ("geo", "PRE"), ("barrng_r", "PRE"),
         ("atr60_r", "PRE"), ("risk_bps", "PRE"), ("cost_r", "PRE"),
         ("c0", "CONFIRM"), ("disp0", "CONFIRM"), ("c0_fav", "CONFIRM"), ("c0_adv", "CONFIRM"),
         ("c0_rng", "CONFIRM"), ("touch0", "CONFIRM"), ("vol0_ratio", "CONFIRM"),
         ("c1", "CONFIRM+"), ("c4", "CONFIRM+"), ("fav5", "CONFIRM+"), ("adv5", "CONFIRM+"),
         ("mom5", "CONFIRM+")]
CTRLS = ["symbol", "hour", "family", "cost_decile", "risk_decile", "atr_decile", "geo_decile"]

res_s = np.isin(A["rs"], [0, 1]); ist_s = A["rs"] == 0
res_0 = np.isin(A["r0"], [0, 1]); ist_0 = A["r0"] == 0
POPS = {
    "ESTATE_CONVENTION_RESOLVED": (res_0, ist_0),
    "SIDE_AWARE_RESOLVED": (res_s, ist_s),
    "SIDE_AWARE_PENDING_RESOLVED (cancel is available)": (res_s & (A["js"] > 0), ist_s),
}
R = {"windows": WINS, "N": int(N), "ceiling": 0.152, "pops": {}}
for pname, (pm, ist) in POPS.items():
    idx = np.nonzero(pm)[0]
    sub = {k: A[k][idx] for k in A}
    lt = ist[idx]
    strata = {"symbol": sub["sym"], "hour": sub["hour"], "family": sub["fam"],
              "cost_decile": qcut(sub["cost_r"]), "risk_decile": qcut(sub["risk_bps"]),
              "atr_decile": qcut(sub["atr60_r"]), "geo_decile": qcut(sub["geo"])}
    rows = {}
    for f, cls in FEATS:
        x = sub[f].astype(float)
        d = cohens_d(x[lt], x[~lt]); a_ = auc(x[lt], x[~lt])
        ctl = {c: strat_d(x, lt, ~lt, strata[c]) for c in CTRLS}
        rk = {c: cohens_d(*(lambda r: (r[lt], r[~lt]))(within_rank(x, strata[c]))) for c in ("symbol", "family")}
        mn = float(np.nanmin([abs(v) for v in ctl.values()])) if np.isfinite(list(ctl.values())).any() else float("nan")
        rows[f] = {"class": cls, "d": d, "auc": a_, "beats_ceiling": bool(abs(d) > 0.152),
                   "within_stratum_d": ctl, "rank_normalised_d": rk, "min_abs_controlled_d": mn}
        print("%-12s %-42s %-8s d=%+.4f auc=%.4f  min|d| ctl %.4f"
              % (f, pname[:42], cls, d, a_, mn), flush=True)
    R["pops"][pname] = {"n": int(pm.sum()), "n_target": int((pm & ist).sum()), "feats": rows}

# per-window replication of c0 under both label sets
R["per_window_c0"] = {}
for i, w in enumerate(WINS):
    m = A["win"] == i
    out = {}
    for tag, (pm, ist) in POPS.items():
        mm = m & pm
        x = A["c0"][mm]; lt = ist[mm]
        out[tag] = {"n": int(mm.sum()), "d": cohens_d(x[lt], x[~lt]), "auc": auc(x[lt], x[~lt])}
    R["per_window_c0"][w] = out
json.dump(R, open("%s/D5_12_HUNT2.json" % OUT, "w"), indent=1, default=float)
print("saved")
