import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True)
fam,day,mon,st,e,usable,X,ses=d["fam"],d["day"],d["mon"],d["st"],d["e"],d["usable"],d["X"],d["ses"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=np.nan_to_num(X[:,FI["cost_r"]]); g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)
hour=X[:,FI["utc_hour"]]
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811); B=4000; PICK=rng.integers(0,ND,(B,ND))
def ci(m,v=None):
    v=e if v is None else v
    s=np.bincount(didx[m],weights=v[m],minlength=ND); c=np.bincount(didx[m],minlength=ND).astype(float)
    S=s[PICK].sum(1); C=c[PICK].sum(1); ok=C>0; mm=S[ok]/C[ok]
    return round(float(v[m].mean()),5),round(float(np.percentile(mm,2.5)),5),round(float(np.percentile(mm,97.5)),5)

out={"cost_burden":{},"horizon_binding":{},"hour":{},"session":{}}
print("A. COST BURDEN — what the 2h/1.5R contract charges, per family")
print(f"{'family':32s}{'E[R]net':>9s}{'E[R]gross':>10s}{'cost R/fill':>12s}{'cost as % of |gross|':>21s}{'spread/cost':>12s}")
for f in sorted(set(fam.tolist())):
    m=(fam==f)&usable; fl=m&(st!="RESOLVED_NO_FILL")
    cr=float(cost[fl].mean()); gr=float(g[fl].mean()); nr=float(e[fl].mean())
    spr=float(np.nan_to_num(X[fl,FI["spread_r"]]).mean())
    out["cost_burden"][f]={"E_R_net_per_fill":round(nr,5),"E_R_gross_per_fill":round(gr,5),
        "cost_R_per_fill":round(cr,5),"spread_R_per_fill":round(spr,5),
        "cost_pct_of_abs_gross":round(100*cr/abs(gr),1) if gr else None}
    print(f"{f:32s}{nr:9.4f}{gr:10.4f}{cr:12.4f}{100*cr/abs(gr) if gr else float('nan'):21.1f}{spr/cr if cr else 0:12.2f}")

print("\nB. HORIZON BINDING — the 120-min funnel lifecycle (w21_generate_day_r2.py:116)")
print(f"{'family':32s}{'target%':>9s}{'stop%':>8s}{'timestop%':>11s}{'E[R]|timestop':>15s}{'E[R]|nontimestop':>18s}")
for f in sorted(set(fam.tolist())):
    m=(fam==f)&usable; fl=m&(st!="RESOLVED_NO_FILL")
    tsm=m&(st=="RESOLVED_FILLED_TIME_STOP"); ntm=fl&~tsm
    n=int(fl.sum())
    r={"timestop_frac":round(float(tsm.sum())/n,4),
       "target_frac":round(float((m&(st=="RESOLVED_FILLED_TARGET")).sum())/n,4),
       "stop_frac":round(float((m&(st=="RESOLVED_FILLED_STOP")).sum())/n,4),
       "E_R_timestop":ci(tsm) if tsm.sum()>200 else None,
       "E_R_non_timestop":ci(ntm) if ntm.sum()>200 else None}
    out["horizon_binding"][f]=r
    ts=r["E_R_timestop"][0] if r["E_R_timestop"] else float('nan')
    nt=r["E_R_non_timestop"][0] if r["E_R_non_timestop"] else float('nan')
    print(f"{f:32s}{r['target_frac']*100:9.1f}{r['stop_frac']*100:8.1f}{r['timestop_frac']*100:11.1f}{ts:15.4f}{nt:18.4f}")

print("\nC. HOUR-OF-DAY — never filtered in any funnel family (no session/hour gate in the generator)")
print(f"{'family':32s}{'best hour':>10s}{'E[R] best':>11s}{'worst hour':>11s}{'E[R] worst':>12s}{'gross best-worst':>18s}")
for f in sorted(set(fam.tolist())):
    m=(fam==f)&usable
    if m.sum()<1500: continue
    hs=[]
    for h in range(24):
        mh=m&(hour==h)
        if mh.sum()>=250: hs.append((h,float(e[mh].mean()),float(g[mh].mean()),int(mh.sum())))
    if len(hs)<6: continue
    hs.sort(key=lambda t:t[1])
    w,b=hs[0],hs[-1]
    out["hour"][f]={"n_hours_evaluated":len(hs),"best":{"hour":b[0],"E_R_net":round(b[1],5),"E_R_gross":round(b[2],5),"n":b[3]},
                    "worst":{"hour":w[0],"E_R_net":round(w[1],5),"E_R_gross":round(w[2],5),"n":w[3]},
                    "net_spread":round(b[1]-w[1],5),"gross_spread":round(b[2]-w[2],5),
                    "note":"argmax over up to 24 hours, IN-SAMPLE, no multiplicity correction"}
    print(f"{f:32s}{b[0]:10d}{b[1]:11.4f}{w[0]:11d}{w[1]:12.4f}{b[2]-w[2]:18.4f}")
json.dump(out,open("LANEC_HORIZON_COST_HOUR.json","w"),indent=1,sort_keys=True)
print("\nwrote LANEC_HORIZON_COST_HOUR.json")
