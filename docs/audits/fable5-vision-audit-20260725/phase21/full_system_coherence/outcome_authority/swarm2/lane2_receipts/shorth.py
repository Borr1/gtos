#!/usr/bin/env python3
"""Short-horizon arm: does cutting EARLIER help, given the pool's negative gross drift?"""
import gzip,pickle,json
from collections import Counter,defaultdict
import numpy as np
HS=["h0.125","h0.25","h0.5","h1.0","h2.0"]
LAB={"h0.125":"15 min","h0.25":"30 min","h0.5":"60 min","h1.0":"120 min (sealed)","h2.0":"240 min"}
RNG=np.random.default_rng(20260812)
recs=[]
for m in ["feb","apr","may","jun","jul"]:
    recs.extend(pickle.load(gzip.open(f"walk2_{m}.pkl.gz","rb")))
F=[r for r in recs if r.get("fi") is not None and r["H1"]>0 and not r.get("err")]
C=[r for r in F if all((r.get(h) or {}).get("kind") not in (None,"CENSOR") for h in HS)]
print("filled",len(F),"common",len(C))
def net(r,h):
    d=r.get(h)
    if not d or d["gross"] is None: return None
    return d["gross"]-r["ded"]
def boot(rows,h,ref="h1.0",B=2000):
    by=defaultdict(list)
    for r in rows:
        a,b=net(r,ref),net(r,h)
        if a is None or b is None: continue
        by[r["day"]].append((a,b))
    days=list(by); idx={d:np.array(by[d]) for d in days}
    A=np.concatenate([idx[d] for d in days])
    ms=[];ds=[];hs=[]
    for _ in range(B):
        p=RNG.choice(len(days),len(days),replace=True)
        s=np.concatenate([idx[days[i]] for i in p])
        ms.append(s[:,1].mean()); ds.append((s[:,1]-s[:,0]).mean())
    ds=np.array(ds)
    return {"n":len(A),"mean":float(A[:,1].mean()),"ci":[float(np.percentile(ms,2.5)),float(np.percentile(ms,97.5))],
            "delta":float((A[:,1]-A[:,0]).mean()),"delta_ci":[float(np.percentile(ds,2.5)),float(np.percentile(ds,97.5))],
            "p":float(2*min((ds<=0).mean(),(ds>=0).mean())),"days":len(days)}
out={"n_common":len(C),"all":{},"by_family":{},"by_month":{},"by_order_type":{}}
def block(rows,B=2000):
    o={}
    for h in HS:
        ks=Counter((r.get(h) or {}).get("kind") for r in rows)
        hold=[r[h]["end"]-r["fill_min"] for r in rows if r.get(h)]
        b=boot(rows,h,B=B)
        o[h]={"TARGET":ks.get("TARGET",0),"STOP":ks.get("STOP",0),"TIME_STOP":ks.get("TIME_STOP",0),
              "mean_hold_min":float(np.mean(hold)),"median_hold_min":float(np.median(hold)),
              "r_per_hour_exposure":float(b["mean"]/(np.mean(hold)/60.0)),**b}
    return o
out["all"]=block(C)
for ot in ("MARKET","LIMIT"): out["by_order_type"][ot]=block([r for r in C if r["ot"]==ot],B=1000)
for fam in sorted({r["fam"] for r in C}): out["by_family"][fam]=block([r for r in C if r["fam"]==fam],B=800)
for m in ["feb","apr","may","jun","jul"]: out["by_month"][m]=block([r for r in C if r["month"]==m],B=800)
json.dump(out,open("SHORT_HORIZON.json","w"),indent=1)
print("\n%-20s %8s %8s %10s %9s %9s %10s %8s %9s"%("horizon","TARGET","STOP","TIME_STOP","meanNet","medHold","delta_vs_1x","p","R/hr"))
for h in HS:
    v=out["all"][h]
    print("%-20s %8d %8d %10d %+9.4f %9.0f %+10.4f [%+.4f,%+.4f] %6.3f %+9.4f"%(LAB[h],v["TARGET"],v["STOP"],v["TIME_STOP"],v["mean"],v["median_hold_min"],v["delta"],v["delta_ci"][0],v["delta_ci"][1],v["p"],v["r_per_hour_exposure"]))
