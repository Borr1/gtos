"""d5-06 — agree with x4 on x4's OWN population before disagreeing with it.

Two things are established here, both on the 27,658-row January counterfactual pool:
  1. this lane's c0 reproduces x4's c0_close_fav_r and x4's published cohort economics;
  2. on that same pool, the share of the refused cohort that is ALREADY FILLED when c0 becomes
     readable — i.e. the share of x4's headline that cannot be acted on.
"""
import gzip, json, math, os, sys
import numpy as np

DISC = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
        "fable5-vision-audit-20260725/phase19/receipts/discovery")
sys.path.insert(0, DISC)
sys.path.insert(0, "/tmp/d5")
from d5_lib import cohens_d, auc

ib = {}
with gzip.open(os.path.join(DISC, "x4_INTRABAR_V1.jsonl.gz"), "rt") as fh:
    for line in fh:
        r = json.loads(line)
        ib[r["candidate_id"]] = r
print("x4 intrabar rows", len(ib))

rows = []
with gzip.open(os.path.join(DISC, "w0_WORKING_SET.jsonl.gz"), "rt") as fh:
    for line in fh:
        rows.append(json.loads(line))
print("pool rows", len(rows))
k0 = rows[0]
cands = [k for k in k0 if "touch" in k or "which" in k or "fill" in k or "mkt" in k]
print("relevant pool keys:", cands[:25])

R = {"n_pool": len(rows), "n_x4": len(ib)}
c0 = []; hon = []; band = []; bte = []; mkt = []
for r in rows:
    x = ib.get(r["candidate_id"])
    if x is None or x.get("c0_close_fav_r") is None:
        continue
    c0.append(x["c0_close_fav_r"])
    hon.append(r.get("fill_honest_walk_r"))
    band.append(r.get("outcome_band"))
    bte.append(r.get("bars_to_entry_touch"))
    mkt.append(r.get("mkt_r_prev_close", r.get("mkt_r_close")))
c0 = np.array(c0, float)
hon = np.array([np.nan if v is None else v for v in hon], float)
bte = np.array([-1 if v is None else v for v in bte], float)
band = np.array(band, dtype=object)
n = c0.size
R["n_joined"] = int(n)

takeable = np.isfinite(hon)
ad = c0 <= -0.15
R["x4_repro"] = {
    "n_refused_c0<=-0.15": int((ad & takeable).sum()),
    "refused_set_honest_R": float(np.nanmean(hon[ad & takeable])),
    "kept_set_honest_R": float(np.nanmean(hon[~ad & takeable])),
    "pool_R_per_opportunity_after_refusal": float(np.nansum(hon[~ad & takeable]) / takeable.sum()),
    "baseline_pool_R": float(np.nanmean(hon[takeable])),
}
# x4's headline cohort: takeable AND bars_to_entry_touch == 1
b1 = takeable & (bte == 1)
for tag, m in (("all", b1), ("c0>-0.15", b1 & ~ad), ("c0<=-0.15", b1 & ad),
               ("c0>-0.05", b1 & (c0 > -0.05)), ("c0<=-0.05", b1 & (c0 <= -0.05))):
    R.setdefault("x4_bar1_cohort", {})[tag] = {"n": int(m.sum()),
                                               "honest_R": float(np.nanmean(hon[m])) if m.sum() else None}
# the separation itself, on the pool, x4's own definition
lt = takeable & (band == "ge_target")
ls = takeable & (band == "full_stop")
R["x4_separation_repro"] = {
    "n_target": int(lt.sum()), "n_stop": int(ls.sum()),
    "cohens_d": cohens_d(c0[lt], c0[ls]), "auc": auc(c0[lt], c0[ls])}
lt1 = b1 & (band == "ge_target"); ls1 = b1 & (band == "full_stop")
R["x4_separation_bar1"] = {"n_target": int(lt1.sum()), "n_stop": int(ls1.sum()),
                           "cohens_d": cohens_d(c0[lt1], c0[ls1]), "auc": auc(c0[lt1], c0[ls1])}

# ---- the achievability question ON THE POOL ITSELF
# a resting order live from T is already filled at T+1m iff the entry traded inside [T, T+1m).
# x4 measured that flag directly: c0_touch_entry.
tt = np.array([1 if (ib.get(r["candidate_id"]) or {}).get("c0_touch_entry") else 0
               for r in rows if ib.get(r["candidate_id"]) is not None
               and ib[r["candidate_id"]].get("c0_close_fav_r") is not None], float)
R["achievability_on_the_pool"] = {
    "n_refused": int((ad).sum()),
    "share_of_refused_rows_whose_entry_traded_inside_[T,T+1m)": float(tt[ad].mean()),
    "share_of_all_rows_whose_entry_traded_inside_[T,T+1m)": float(tt.mean()),
    "note": "x4 S2 measured the same quantity pool-wide at 70.53 %",
}
json.dump(R, open("/tmp/d5/out/D5_06_POOL_REPRO.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=float))
