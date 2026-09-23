#!/usr/bin/env python3
"""Does the pool's edge scale with the stop, or only its cost? The ceiling of the
stop-widening lever."""
import gzip,pickle,json
from collections import defaultdict
import numpy as np
SCALES=["1.0","1.5","2.0","3.0","4.0"]; SLIP=0.02
RNG=np.random.default_rng(20260812)
rows=[]
for m in ["feb","apr","may","jun","jul"]: rows.extend(pickle.load(gzip.open(f"scale_{m}.pkl.gz","rb")))
cache={}
for m in ["feb","apr","may","jun","jul"]:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        cache[c["candidate_occurrence_key"]]=c
C=[r for r in rows if all((r["arms"][k].get(a) or {}).get("kind") not in (None,"CENSOR")
   for k in SCALES for a in ("hA","hInf"))]
print("common",len(C))
out={}
for k in SCALES:
    kk=float(k)
    g=np.array([r["arms"][k]["hInf"]["gross"] for r in C])
    s=np.array([float(cache[r["k"]].get("spread_r") or 0.0)/kk for r in C])   # spread_r is price/stop
    ded=np.array([SLIP+(r["ded"]-SLIP)/kk for r in C])
    drift=g+s                                    # fair game EV is exactly -s
    days=np.array([r["day"] for r in C])
    by=defaultdict(list)
    for d,x in zip(days,drift): by[d].append(x)
    dl=list(by); idx={d:np.array(by[d]) for d in dl}
    bs=[np.concatenate([idx[dl[i]] for i in RNG.choice(len(dl),len(dl),replace=True)]).mean() for _ in range(2000)]
    out[k]={"k":kk,"mean_spread_r":float(s.mean()),"mean_ded":float(ded.mean()),
            "gross":float(g.mean()),"fair_gross":float(-s.mean()),"drift":float(drift.mean()),
            "drift_ci":[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
            "net":float((g-ded).mean()),"cost_total":float(s.mean()+ded.mean())}
    print(json.dumps(out[k]),flush=True)
ks=np.array([out[k]["k"] for k in SCALES]); dr=np.array([out[k]["drift"] for k in SCALES])
co=np.polyfit(np.log(ks),np.log(np.maximum(dr,1e-6)),1)
out["drift_scaling_exponent_loglog"]=float(co[0])
out["cost_floor_flat_slippage_r"]=SLIP
out["limiting_net_as_k_to_inf"]=-SLIP
json.dump(out,open("DRIFT_SCALING.json","w"),indent=1)
print("\ndrift ~ k^%.3f   (a value >= +1 would eventually turn the pool positive; <1 cannot)"%co[0])
print("cost floor = flat slippage 0.02 R; limiting net as k->inf = %.4f + drift(inf)"%(-SLIP))
