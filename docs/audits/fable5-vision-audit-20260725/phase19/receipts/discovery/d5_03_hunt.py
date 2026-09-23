"""d5-03 — is it a genuine separator or a proxy, and is there anything else in the same place?

Item 4: control c0 for cost, hour, instrument, family, volatility, geometry AND for its own
        PRE-decision predecessor mkt_r0 (the decision anchor, knowable AT T).
Item 5: rank EVERY post-decision-instant observable that can be built from the M1 tape, with its
        legality class, on the correct population.  The estate's standing ceiling is |d| = 0.152.
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

FEATS = [
    # name, class, legal-from
    ("mkt_r0", "PRE", "T"),
    ("abs_mkt_r0", "PRE", "T"),
    ("geo", "PRE", "T"),
    ("barrng_r", "PRE", "T"),
    ("atr60_r", "PRE", "T"),
    ("risk_bps", "PRE", "T"),
    ("cost_r", "PRE", "T"),
    ("c0", "CONFIRM", "T+1m"),
    ("disp0", "CONFIRM", "T+1m"),
    ("c0_fav", "CONFIRM", "T+1m"),
    ("c0_adv", "CONFIRM", "T+1m"),
    ("c0_rng", "CONFIRM", "T+1m"),
    ("touch0", "CONFIRM", "T+1m"),
    ("vol0_ratio", "CONFIRM", "T+1m"),
    ("c1", "CONFIRM+", "T+2m"),
    ("c4", "CONFIRM+", "T+5m"),
    ("fav5", "CONFIRM+", "T+5m"),
    ("adv5", "CONFIRM+", "T+5m"),
    ("mom5", "CONFIRM+", "T+5m"),
    ("disp5", "CONFIRM+", "T+5m"),
]

ACC = []
for wi, w in enumerate(WINDOWS):
    D = load(w)
    D["abs_mkt_r0"] = np.abs(D["mkt_r0"])
    D["mom5"] = D["c4"] - D["c0"]
    D["disp5"] = D["c4"] - D["mkt_r0"]
    keep = [f[0] for f in FEATS] + ["g", "net", "reason", "sym", "fam", "hour", "j"]
    ACC.append({k: D[k] for k in keep} | {"day": D["dayi"] + 1000 * wi, "win": np.full(D["g"].size, wi)})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
resolved = np.isin(A["reason"], [0, 1])
is_t = A["reason"] == 0
honest = A["mkt_r0"] >= 0.0
prefilled = A["j"] == 0

POPS = {
    "ALL_RESOLVED": resolved,
    "HONEST_RESOLVED": resolved & honest,                       # marketable-limit rows removed
    "HONEST_PREFILLED_RESOLVED": resolved & honest & prefilled,  # the exit-decision population
}
CTRLS = ["symbol", "hour", "family", "cost_decile", "risk_decile", "atr_decile",
         "geo_decile", "mkt_r0_decile"]

R = {"ceiling_quoted_by_estate": 0.152, "n_total_rows": int(N),
     "population_sizes": {k: int(v.sum()) for k, v in POPS.items()}, "rank": {}}

for pname, pmask in POPS.items():
    idx = np.nonzero(pmask)[0]
    sub = {k: A[k][idx] for k in A}
    lab_t = is_t[idx]; lab_s = ~lab_t
    strata = {
        "symbol": sub["sym"], "hour": sub["hour"], "family": sub["fam"],
        "cost_decile": qcut(sub["cost_r"]), "risk_decile": qcut(sub["risk_bps"]),
        "atr_decile": qcut(sub["atr60_r"]), "geo_decile": qcut(sub["geo"]),
        "mkt_r0_decile": qcut(sub["mkt_r0"]),
    }
    rows = {}
    for fname, cls, legal in FEATS:
        x = sub[fname].astype(float)
        d_raw = cohens_d(x[lab_t], x[lab_s])
        a_raw = auc(x[lab_t], x[lab_s])
        rec = {"class": cls, "legal_from": legal, "cohens_d": d_raw, "auc": a_raw,
               "beats_ceiling": bool(abs(d_raw) > 0.152) if np.isfinite(d_raw) else False,
               "n_target": int(lab_t.sum()), "n_stop": int(lab_s.sum()), "controls": {}}
        for cname in CTRLS:
            st = strata[cname]
            rec["controls"][cname] = {
                "within_stratum_d": strat_d(x, lab_t, lab_s, st),
                "rank_normalised_d": cohens_d(*(lambda r: (r[lab_t], r[lab_s]))(within_rank(x, st))),
            }
        rec["min_abs_controlled_d"] = float(np.nanmin(
            [abs(v["within_stratum_d"]) for v in rec["controls"].values()]))
        rows[fname] = rec
        print("%-22s %-9s %-6s d=%+.4f auc=%.4f  min|d| after control %.4f"
              % (fname, pname[:9], cls, d_raw, a_raw, rec["min_abs_controlled_d"]), flush=True)
    R["rank"][pname] = rows

# per-window replication of the headline feature set
R["per_window"] = {}
for wi, w in enumerate(WINDOWS):
    m = A["win"] == wi
    sub = {}
    for fname in ("c0", "disp0", "mkt_r0", "geo", "c4", "adv5"):
        for pname, pmask in POPS.items():
            mm = m & pmask
            x = A[fname][mm].astype(float)
            lt = is_t[mm]
            sub["%s|%s" % (fname, pname)] = {"d": cohens_d(x[lt], x[~lt]),
                                             "auc": auc(x[lt], x[~lt]), "n": int(mm.sum())}
    R["per_window"][w] = sub

json.dump(R, open("/tmp/d5/out/D5_03_HUNT.json", "w"), indent=1, default=float)
print("saved")
