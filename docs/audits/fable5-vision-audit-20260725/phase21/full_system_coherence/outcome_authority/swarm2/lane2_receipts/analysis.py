#!/usr/bin/env python3
"""Lane 2 core analysis: A (census), B (horizon counterfactual), C (MFE/MAE anatomy)."""
import gzip, pickle, json, math
from collections import Counter, defaultdict
import numpy as np

MONTHS=["feb","apr","may","jun","jul"]
HS=["h1","h2","h4","h8","hInf"]
HLAB={"h1":"1x (sealed, 120 min)","h2":"2x (240 min)","h4":"4x (480 min)","h8":"8x (960 min)","hInf":"unbounded"}
RNG=np.random.default_rng(20260812)

recs=[]
for m in MONTHS:
    recs.extend(pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb")))
print("all recs", len(recs), flush=True)
F=[r for r in recs if r.get("fi") is not None and r["H1"]>0 and not r.get("err")]
print("filled", len(F), flush=True)

def kinds(r):
    return {h: (r.get(h) or {}).get("kind") for h in HS}
common=[r for r in F if all((r.get(h) or {}).get("kind") not in (None,"CENSOR") for h in HS)]
print("common (resolvable at every horizon)", len(common), len(common)/len(F), flush=True)

def net(r,h):
    d=r.get(h)
    if not d or d["gross"] is None: return None
    return d["gross"]-r["ded"]

def summ(rows,h):
    ns=[net(r,h) for r in rows]; ns=[x for x in ns if x is not None]
    ks=Counter((r.get(h) or {}).get("kind") for r in rows)
    hold=[ (r[h]["end"]-r["fill_min"]) for r in rows if r.get(h)]
    return {"n":len(rows),"n_net":len(ns),"mean_net":float(np.mean(ns)) if ns else None,
            "total_net":float(np.sum(ns)) if ns else None,
            "sd":float(np.std(ns,ddof=1)) if len(ns)>1 else None,
            "TARGET":ks.get("TARGET",0),"STOP":ks.get("STOP",0),"TIME_STOP":ks.get("TIME_STOP",0),
            "CENSOR":ks.get("CENSOR",0),"RUNOUT":ks.get("RUNOUT",0),
            "median_hold_min":float(np.median(hold)) if hold else None,
            "mean_hold_min":float(np.mean(hold)) if hold else None}

def boot(rows,h,href="h1",B=2000):
    """Cluster bootstrap by trading day on the per-trade mean and on the delta vs href."""
    by=defaultdict(list)
    for r in rows:
        a,b=net(r,href),net(r,h)
        if a is None or b is None: continue
        by[r["day"]].append((a,b))
    days=list(by); 
    if not days: return None
    A=np.array([x for d in days for x,_ in by[d]]); Bv=np.array([y for d in days for _,y in by[d]])
    ms,ds=[],[]
    idx={d:np.array(by[d]) for d in days}
    for _ in range(B):
        pick=RNG.choice(len(days),len(days),replace=True)
        s=np.concatenate([idx[days[i]] for i in pick])
        ms.append(s[:,1].mean()); ds.append((s[:,1]-s[:,0]).mean())
    return {"n":len(A),"mean":float(Bv.mean()),"ci":[float(np.percentile(ms,2.5)),float(np.percentile(ms,97.5))],
            "delta":float((Bv-A).mean()),"delta_ci":[float(np.percentile(ds,2.5)),float(np.percentile(ds,97.5))],
            "delta_p_two_sided":float(2*min((np.array(ds)<=0).mean(),(np.array(ds)>=0).mean())),
            "days":len(days)}

out={}
out["population"]={"all_rows":len(recs),"filled":len(F),"common_all_horizons":len(common),
                   "common_frac_of_filled":len(common)/len(F)}
out["by_horizon_all"]={h:summ(common,h) for h in HS}
out["by_horizon_boot"]={h:boot(common,h) for h in HS}
out["by_horizon_order_type"]={}
for ot in ("MARKET","LIMIT"):
    sub=[r for r in common if r["ot"]==ot]
    out["by_horizon_order_type"][ot]={h:{**summ(sub,h),"boot":boot(sub,h)} for h in HS}
out["by_family"]={}
for fam in sorted({r["fam"] for r in common}):
    sub=[r for r in common if r["fam"]==fam]
    out["by_family"][fam]={h:{**summ(sub,h),"boot":boot(sub,h,B=800)} for h in HS}
out["by_month"]={}
for m in MONTHS:
    sub=[r for r in common if r["month"]==m]
    out["by_month"][m]={h:{**summ(sub,h),"boot":boot(sub,h,B=800)} for h in HS}

# ---- C: anatomy of the 1x TIME_STOPs -------------------------------------
ts=[r for r in common if r["h1"]["kind"]=="TIME_STOP"]
def anat(rows,tag):
    g=np.array([r["h1"]["gross"] for r in rows]); n=g-np.array([r["ded"] for r in rows])
    mfe=np.array([r["h1"]["mfe"] for r in rows]); mae=np.array([r["h1"]["mae"] for r in rows])
    later={h:np.array([ (net(r,h) if net(r,h) is not None else np.nan) for r in rows]) for h in HS}
    kk={h:Counter((r.get(h) or {}).get("kind") for r in rows) for h in HS}
    return {"tag":tag,"n":len(rows),
      "gross_mean":float(g.mean()),"net_mean":float(n.mean()),"net_total":float(n.sum()),
      "frac_gross_pos":float((g>0).mean()),"frac_net_pos":float((n>0).mean()),
      "mfe_mean":float(mfe.mean()),"mfe_median":float(np.median(mfe)),
      "mae_mean":float(mae.mean()),"mae_median":float(np.median(mae)),
      "frac_mfe_ge_half_target":float(np.mean(mfe>=0.5*np.array([r.get("tR",1.5) or 1.5 for r in rows]))),
      "later_mean_net":{h:float(np.nanmean(later[h])) for h in HS},
      "later_kinds":{h:dict(kk[h]) for h in HS}}
out["C_time_stop_anatomy"]={"all":anat(ts,"all")}
for fam in sorted({r["fam"] for r in ts}):
    sub=[r for r in ts if r["fam"]==fam]
    if len(sub)>=100: out["C_time_stop_anatomy"][fam]=anat(sub,fam)
out["C_time_stop_boot_delta"]={h:boot(ts,h) for h in HS}

# ---- A: time-to-hit distributions at the unbounded horizon ---------------
def tt(rows,kind):
    v=[(r["hInf"]["end"]-r["fill_min"]) for r in rows if r["hInf"]["kind"]==kind]
    if not v: return None
    v=np.array(v,dtype=float)
    return {"n":int(len(v)),"median":float(np.median(v)),"mean":float(v.mean()),
            "p25":float(np.percentile(v,25)),"p75":float(np.percentile(v,75)),
            "p90":float(np.percentile(v,90))}
out["A_time_to_hit_unbounded"]={"TARGET":tt(common,"TARGET"),"STOP":tt(common,"STOP"),
    "by_family":{fam:{k:tt([r for r in common if r["fam"]==fam],k) for k in ("TARGET","STOP")}
                 for fam in sorted({r["fam"] for r in common})}}
json.dump(out,open("B_horizon.json","w"),indent=1)
print(json.dumps({"population":out["population"],
  "by_horizon_all":out["by_horizon_all"],"boot":out["by_horizon_boot"]},indent=1), flush=True)
