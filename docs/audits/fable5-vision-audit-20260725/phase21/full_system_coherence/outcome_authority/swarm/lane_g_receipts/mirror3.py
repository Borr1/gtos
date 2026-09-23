"""Assumption-free version + the economics.

(iii) GEOMETRY-MATCHED two-sample test. The labeler gives a LONG tape-barriers
(R, 2R) and a SHORT (R-s, 2R+s). So compare only LIKE with LIKE:
   LONG pool  = {orig arm of signal-LONG rows} vs {mirror arm of signal-SHORT rows}
   SHORT pool = {orig arm of signal-SHORT rows} vs {mirror arm of signal-LONG rows}
Both members of each pool are the same order side with the same geometry on the same
symbols/instants; the only difference is whether the signal endorsed that direction.
No driftless model, no horizon model, no volatility model."""
import gzip, pickle, math, json
import numpy as np
from collections import defaultdict
from scipy.stats import norm

MONTHS=["feb","apr","may","jun","jul"]
recs=[]
for mo in MONTHS:
    with gzip.open(f"/private/tmp/laneG-walk/lg_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh): r["month"]=mo; recs.append(r)

def two_prop(k1,n1,k2,n2):
    if n1==0 or n2==0: return None,None
    p1,p2=k1/n1,k2/n2; p=(k1+k2)/(n1+n2)
    se=math.sqrt(p*(1-p)*(1/n1+1/n2))
    z=(p1-p2)/se if se>0 else None
    return z, (2*(1-norm.cdf(abs(z))) if z is not None else None)

def welch(x,y):
    x,y=np.asarray(x),np.asarray(y)
    if len(x)<2 or len(y)<2: return None,None,None
    se=math.sqrt(x.var(ddof=1)/len(x)+y.var(ddof=1)/len(y))
    t=(x.mean()-y.mean())/se if se>0 else None
    return x.mean()-y.mean(), t, (2*(1-norm.cdf(abs(t))) if t is not None else None)

byfam=defaultdict(list)
for r in recs: byfam[r["family"]].append(r)

def analyse(rows):
    o=dict(endorse_k=0,endorse_n=0,oppose_k=0,oppose_n=0)   # realised-LONG pool
    s=dict(endorse_k=0,endorse_n=0,oppose_k=0,oppose_n=0)   # realised-SHORT pool
    net_o, net_m = [], []
    for r in rows:
        is_long = r["side"]=="LONG"
        so, sm = r["orig"]["state"], r["mirror"]["state"]
        # realised-LONG pool
        pool = o if is_long else s
        if so in ("TARGET","STOP"):
            pool["endorse_n"]+=1; pool["endorse_k"]+= (so=="TARGET")
        pool2 = s if is_long else o   # the MIRROR of this row is the opposite side
        if sm in ("TARGET","STOP"):
            pool2["oppose_n"]+=1; pool2["oppose_k"]+= (sm=="TARGET")
        if r["orig"]["net"] is not None: net_o.append(r["orig"]["net"])
        if r["mirror"]["net"] is not None: net_m.append(r["mirror"]["net"])
    out={}
    for name,pool in (("LONGpool",o),("SHORTpool",s)):
        z,p = two_prop(pool["endorse_k"],pool["endorse_n"],pool["oppose_k"],pool["oppose_n"])
        out[name]=dict(endorsed_hit=pool["endorse_k"]/pool["endorse_n"] if pool["endorse_n"] else None,
                       endorsed_n=pool["endorse_n"],
                       opposed_hit=pool["oppose_k"]/pool["oppose_n"] if pool["oppose_n"] else None,
                       opposed_n=pool["oppose_n"], z=z, p=p)
    # combined (Mantel-Haenszel-ish: sum the two strata)
    K1=o["endorse_k"]+s["endorse_k"]; N1=o["endorse_n"]+s["endorse_n"]
    K2=o["oppose_k"]+s["oppose_k"];  N2=o["oppose_n"]+s["oppose_n"]
    z,p=two_prop(K1,N1,K2,N2)
    out["combined"]=dict(endorsed_hit=K1/N1, endorsed_n=N1, opposed_hit=K2/N2, opposed_n=N2, z=z, p=p)
    d,t,pp = welch(net_o, net_m)
    out["economics"]=dict(orig_net_mean=float(np.mean(net_o)), orig_n=len(net_o),
                          mirror_net_mean=float(np.mean(net_m)), mirror_n=len(net_m),
                          diff=d, t=t, p=pp)
    return out

print("GEOMETRY-MATCHED: signal-ENDORSED direction vs signal-OPPOSED direction, like-for-like\n")
print(f"{'family':34s} {'endors.n':>8s} {'hit':>7s} {'oppos.n':>8s} {'hit':>7s} {'z':>7s} {'p':>9s} | "
      f"{'orig net':>9s} {'mirr net':>9s} {'diff':>8s} {'t':>6s}")
res={}
for fam,rows in sorted(byfam.items(), key=lambda kv:-len(kv[1])):
    a=analyse(rows); res[fam]=a; c=a["combined"]; e=a["economics"]
    print(f"{fam:34s} {c['endorsed_n']:8d} {c['endorsed_hit']:7.4f} {c['opposed_n']:8d} {c['opposed_hit']:7.4f} "
          f"{c['z']:7.2f} {c['p']:9.2e} | {e['orig_net_mean']:+9.4f} {e['mirror_net_mean']:+9.4f} "
          f"{e['diff']:+8.4f} {e['t']:6.2f}")
a=analyse(recs); res["_POOLED"]=a; c=a["combined"]; e=a["economics"]
print(f"{'POOLED':34s} {c['endorsed_n']:8d} {c['endorsed_hit']:7.4f} {c['opposed_n']:8d} {c['opposed_hit']:7.4f} "
      f"{c['z']:7.2f} {c['p']:9.2e} | {e['orig_net_mean']:+9.4f} {e['mirror_net_mean']:+9.4f} {e['diff']:+8.4f} {e['t']:6.2f}")
print("\nper-stratum for the pooled set:")
for k in ("LONGpool","SHORTpool"):
    d=res["_POOLED"][k]
    print(f"  {k:10s} endorsed {d['endorsed_hit']:.4f} (n={d['endorsed_n']}) vs opposed {d['opposed_hit']:.4f} "
          f"(n={d['opposed_n']}) z={d['z']:+.2f} p={d['p']:.3e}")
json.dump(res, open("/tmp/laneG/mirror_geometry_matched.json","w"), indent=1)
