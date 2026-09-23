#!/usr/bin/env python3
"""(D) the fill-anchored optimal-horizon surface, with carry priced."""
import gzip,pickle,json,datetime as dt
from collections import Counter,defaultdict
import numpy as np
LAD=["15","30","60","120","240","480","960","1920","inf"]
RNG=np.random.default_rng(20260812)
EP=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
rows=[]
for m in ["feb","apr","may","jun","jul"]: rows.extend(pickle.load(gzip.open(f"hz_{m}.pkl.gz","rb")))
cache={}
for m in ["feb","apr","may","jun","jul"]:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        cache[c["candidate_occurrence_key"]]=c
print("hz rows",len(rows))
C=[r for r in rows if all((r["arms"].get(a) or {}).get("kind") not in (None,"CENSOR") for a in LAD)]
print("common",len(C),len(C)/len(rows))
# per-night swap rate, estimated from rows the sealed 120-min clock already charged
sw=np.array([float(cache[r["k"]].get("swap_cost_r") or 0.0) for r in C])
pernight=float(np.median(sw[sw>0])) if (sw>0).any() else 0.0
def nights(a,b):
    """broker rollover = 00:00 broker = 21:00/22:00 UTC (New York + 7h). Count crossings."""
    n=0; t=a
    while True:
        d0=(EP+dt.timedelta(minutes=int(t)))
        nxt=d0.replace(hour=21,minute=0,second=0,microsecond=0)
        if nxt<=d0: nxt+=dt.timedelta(days=1)
        m=int((nxt-EP).total_seconds()//60)
        if m>=b: return n
        n+=1; t=m+1
        if n>40: return n
def net(r,a,extra=0.0): 
    d=r["arms"][a]
    return None if (not d or d["gross"] is None) else d["gross"]-r["ded"]-extra
def boot(rows,a,vals,B=1500):
    by=defaultdict(list)
    for r,v in zip(rows,vals): by[r["day"]].append(v)
    dl=list(by); idx={d:np.array(by[d]) for d in dl}
    bs=[np.concatenate([idx[dl[i]] for i in RNG.choice(len(dl),len(dl),replace=True)]).mean() for _ in range(B)]
    return [float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))]
base=np.array([net(r,"120") for r in C])
out={"n_common":len(C),"per_night_swap_r_median":pernight,"ladder":{}}
print("\n%-8s %8s %8s %10s %9s %9s %9s %10s %10s"%("Hmin","TARGET","STOP","TIME_STOP","meanNet","medHold","R/hr","extraCarry","netAfterCarry"))
for a in LAD:
    ks=Counter(r["arms"][a]["kind"] for r in C)
    hold=np.array([r["arms"][a]["end"]-r["arms"]["15"]["end"]+15 for r in C],dtype=float)
    hold=np.array([r["arms"][a]["end"] for r in C],dtype=float)-np.array([r["arms"]["15"]["end"]-15 for r in C],dtype=float)
    v=np.array([net(r,a) for r in C])
    nn=np.array([nights(r["arms"]["15"]["end"]-15, r["arms"][a]["end"]) for r in C],dtype=float)
    nn0=np.array([nights(r["arms"]["15"]["end"]-15, r["arms"]["120"]["end"]) for r in C],dtype=float)
    carry=np.maximum(0.0,(nn-nn0))*pernight
    d=v-base
    cell={"H":a,"TARGET":ks.get("TARGET",0),"STOP":ks.get("STOP",0),"TIME_STOP":ks.get("TIME_STOP",0),
          "RUNOUT":ks.get("RUNOUT",0),"mean_net":float(v.mean()),"ci":boot(C,a,v),
          "delta_vs_120":float(d.mean()),"delta_ci":boot(C,a,d),
          "median_hold_min":float(np.median(hold)),"mean_hold_min":float(hold.mean()),
          "r_per_hour":float(v.mean()/(hold.mean()/60.0)),
          "mean_extra_nights":float((nn-nn0).mean()),"mean_extra_carry_r":float(carry.mean()),
          "net_after_carry":float((v-carry).mean())}
    out["ladder"][a]=cell
    print("%-8s %8d %8d %10d %+9.4f %9.0f %+9.4f %10.4f %+10.4f"%(a,cell["TARGET"],cell["STOP"],cell["TIME_STOP"],cell["mean_net"],cell["median_hold_min"],cell["r_per_hour"],cell["mean_extra_carry_r"],cell["net_after_carry"]))
byfam={}
for fam in sorted({r["fam"] for r in C}):
    sub=[r for r in C if r["fam"]==fam]
    b=np.array([net(r,"120") for r in sub])
    best=None
    fr={}
    for a in LAD:
        v=np.array([net(r,a) for r in sub]); d=v-b
        fr[a]={"mean":float(v.mean()),"delta":float(d.mean()),"delta_ci":boot(sub,a,d,B=600),"n":len(sub)}
        if best is None or fr[a]["mean"]>fr[best]["mean"]: best=a
    byfam[fam]={"n":len(sub),"best_H":best,"cells":fr}
out["by_family"]=byfam
json.dump(out,open("HZ_LADDER.json","w"),indent=1)
print("\n%-34s %6s %8s %10s %10s %s"%("family","n","best_H","net@best","net@120","delta [CI95]"))
for f,v in byfam.items():
    b=v["cells"][v["best_H"]]
    print("%-34s %6d %8s %+10.4f %+10.4f %+.4f [%+.4f,%+.4f]"%(f,v["n"],v["best_H"],b["mean"],v["cells"]["120"]["mean"],b["delta"],b["delta_ci"][0],b["delta_ci"][1]))
