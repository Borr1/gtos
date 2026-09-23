#!/usr/bin/env python3
"""(A) The measured exponent alpha in median T(d) ~ d^alpha, from one-sided first passage."""
import gzip,pickle,json
import numpy as np
LAD=[0.25,0.5,0.75,1.0,1.25,1.5,2.0,2.5,3.0]
rows=[]
for m in ["feb","apr","may","jun","jul"]:
    rows.extend(pickle.load(gzip.open(f"fpt_{m}.pkl.gz","rb")))
print("fpt rows",len(rows))
def fit(sub,tag):
    o={"tag":tag,"n":len(sub),"ladder":{}}
    xs,ys,ws=[],[],[]
    for x in LAD:
        up=[r[f"fu{x}"] for r in sub if r.get(f"fu{x}")]
        dn=[r[f"fd{x}"] for r in sub if r.get(f"fd{x}")]
        rec={"d":x,"n_up":len(up),"n_dn":len(dn),"reach_up":len(up)/len(sub),"reach_dn":len(dn)/len(sub)}
        if up:
            a=np.array([v[0] for v in up],dtype=float); b=np.array([v[1] for v in up],dtype=float)
            rec.update(med_up_min=float(np.median(a)),mean_up_min=float(a.mean()),med_up_bars=float(np.median(b)))
        if dn:
            a=np.array([v[0] for v in dn],dtype=float)
            rec.update(med_dn_min=float(np.median(a)),mean_dn_min=float(a.mean()))
        # pooled both sides: censoring-free estimator would need survival; median of the
        # reached subset is downward-biased at large d and that bias is reported, not hidden.
        if up and dn:
            m=max(0.5,0.5*(rec["med_up_min"]+rec["med_dn_min"]))
            rec["med_pooled_min"]=m; xs.append(np.log(x)); ys.append(np.log(m)); ws.append(min(len(up),len(dn)))
        o["ladder"][str(x)]=rec
    if len(xs)>=3:
        X=np.array(xs);Y=np.array(ys);W=np.array(ws,dtype=float)
        A=np.vstack([X,np.ones_like(X)]).T
        coef,*_=np.linalg.lstsq(A*W[:,None]**0.5,Y*W**0.5,rcond=None)
        o["alpha_weighted"]=float(coef[0]); o["intercept"]=float(coef[1])
        coef2,*_=np.linalg.lstsq(A,Y,rcond=None)
        o["alpha_unweighted"]=float(coef2[0])
        # restricted to d<=1.0 where >70% of trades reach the level (censoring is mild)
        sel=[i for i,x in enumerate(LAD[:len(xs)]) if x<=1.0]
        if len(sel)>=3:
            c3,*_=np.linalg.lstsq(np.vstack([X[sel],np.ones(len(sel))]).T,Y[sel],rcond=None)
            o["alpha_d_le_1"]=float(c3[0])
    return o
out={"all":fit(rows,"all")}
for fam in sorted({r["fam"] for r in rows}):
    sub=[r for r in rows if r["fam"]==fam]
    if len(sub)>=500: out[fam]=fit(sub,fam)
json.dump(out,open("FPT_EXPONENT.json","w"),indent=1)
a=out["all"]
print("\n=== one-sided first passage, all %d fills ==="%a["n"])
print("%6s %8s %8s %10s %10s %10s"%("d(R)","reach_up","reach_dn","med_up_min","med_dn_min","med_pooled"))
for x in LAD:
    r=a["ladder"][str(x)]
    print("%6.2f %8.4f %8.4f %10.1f %10.1f %10.1f"%(x,r["reach_up"],r["reach_dn"],r.get("med_up_min",float('nan')),r.get("med_dn_min",float('nan')),r.get("med_pooled_min",float('nan'))))
print("\nalpha (weighted) = %.3f   unweighted = %.3f   d<=1 only = %.3f   [theory: 2.000]"%(a["alpha_weighted"],a["alpha_unweighted"],a.get("alpha_d_le_1",float('nan'))))
print("\n%-34s %8s %8s %8s"%("family","alpha_w","alpha_u","alpha_d<=1"))
for f,v in out.items():
    if f=="all": continue
    print("%-34s %8.3f %8.3f %8.3f"%(f,v["alpha_weighted"],v["alpha_unweighted"],v.get("alpha_d_le_1",float('nan'))))
