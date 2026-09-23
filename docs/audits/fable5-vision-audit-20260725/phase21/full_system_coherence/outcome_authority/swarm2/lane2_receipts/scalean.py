#!/usr/bin/env python3
"""(E) the joint stop-width x horizon surface, priced."""
import gzip,pickle,json
from collections import Counter,defaultdict
import numpy as np
SCALES=["1.0","1.5","2.0","3.0","4.0"]; ARMS=["hA","hB","hC","hInf"]
ALAB={"hA":"120 min (sealed)","hB":"120*k min","hC":"120*k^2 min (d^2-matched)","hInf":"unbounded"}
SLIP=0.02
RNG=np.random.default_rng(20260812)
rows=[]
for m in ["feb","apr","may","jun","jul"]: rows.extend(pickle.load(gzip.open(f"scale_{m}.pkl.gz","rb")))
print("rows",len(rows))
def ok(r):
    return all((r["arms"][k].get(a) or {}).get("kind") not in (None,"CENSOR") for k in SCALES for a in ARMS)
C=[r for r in rows if ok(r)]
print("common across every (k,horizon) cell:",len(C),len(C)/len(rows))
def net(r,k,a):
    d=r["arms"][k][a]
    if not d or d["gross"] is None: return None
    kk=float(k)
    ded=SLIP+(r["ded"]-SLIP)/kk        # price-domain terms divide by the stop scale
    return d["gross"]-ded
def boot(rows,k,a,B=1500):
    by=defaultdict(list)
    for r in rows:
        x=net(r,k,a); y=net(r,"1.0","hA")
        if x is None or y is None: continue
        by[r["day"]].append((y,x))
    days=list(by); idx={d:np.array(by[d]) for d in days}
    A=np.concatenate([idx[d] for d in days]); ms=[];ds=[]
    for _ in range(B):
        p=RNG.choice(len(days),len(days),replace=True)
        s=np.concatenate([idx[days[i]] for i in p])
        ms.append(s[:,1].mean()); ds.append((s[:,1]-s[:,0]).mean())
    ds=np.array(ds)
    return {"n":len(A),"mean":float(A[:,1].mean()),"ci":[float(np.percentile(ms,2.5)),float(np.percentile(ms,97.5))],
            "delta":float((A[:,1]-A[:,0]).mean()),"delta_ci":[float(np.percentile(ds,2.5)),float(np.percentile(ds,97.5))],
            "p":float(2*min((ds<=0).mean(),(ds>=0).mean()))}
out={"n_common":len(C),"cells":{}}
print("\n%-6s %-24s %8s %8s %9s %9s %9s %10s %8s"%("k","horizon","TARGET","STOP","TIME_STOP","meanNet","medHold","delta_vs_base","p"))
for k in SCALES:
    for a in ARMS:
        sub=[r for r in C if r["arms"][k][a]]
        ks=Counter(r["arms"][k][a]["kind"] for r in sub)
        hold=[r["arms"][k][a]["end"]-r["fill_min"] for r in sub]
        b=boot(C,k,a)
        cell={"k":float(k),"arm":a,"TARGET":ks.get("TARGET",0),"STOP":ks.get("STOP",0),
              "TIME_STOP":ks.get("TIME_STOP",0),"RUNOUT":ks.get("RUNOUT",0),
              "median_hold_min":float(np.median(hold)),"mean_hold_min":float(np.mean(hold)),
              "mean_ded":float(np.mean([SLIP+(r["ded"]-SLIP)/float(k) for r in C])),**b}
        out["cells"][f"k{k}_{a}"]=cell
        print("%-6s %-24s %8d %8d %9d %+9.4f %9.0f %+10.4f [%+.4f,%+.4f] %6.3f"%(
          k,ALAB[a],cell["TARGET"],cell["STOP"],cell["TIME_STOP"],b["mean"],cell["median_hold_min"],b["delta"],b["delta_ci"][0],b["delta_ci"][1],b["p"]))
# family view at the best cell
json.dump(out,open("SCALE_SURFACE.json","w"),indent=1)
