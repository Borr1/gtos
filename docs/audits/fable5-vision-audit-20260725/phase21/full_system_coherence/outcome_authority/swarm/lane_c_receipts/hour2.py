import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True); hour=np.load("hour.npy")
fam,day,st,e,usable,X=d["fam"],d["day"],d["st"],d["e"],d["usable"],d["X"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=np.nan_to_num(X[:,FI["cost_r"]]); g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811); B=4000; PICK=rng.integers(0,ND,(B,ND))
def tmb(mhi,mlo,v):
    def sc(m): return np.bincount(didx[m],weights=v[m],minlength=ND),np.bincount(didx[m],minlength=ND).astype(float)
    sh,ch=sc(mhi); sl,cl=sc(mlo); Sh,Ch=sh[PICK].sum(1),ch[PICK].sum(1); Sl,Cl=sl[PICK].sum(1),cl[PICK].sum(1)
    ok=(Ch>0)&(Cl>0); dd=Sh[ok]/Ch[ok]-Sl[ok]/Cl[ok]
    return round(float(v[mhi].mean()-v[mlo].mean()),5),round(float(np.percentile(dd,2.5)),5),round(float(np.percentile(dd,97.5)),5)
out={"note":"Hour-of-day is UNFILTERED in every funnel family: no generator gates on hour or session "
     "(the only session logic is session_open_range_break's range construction). Argmax over 24 hours, "
     "IN-SAMPLE, NO multiplicity correction -- a hypothesis, not a result.","families":{}}
print(f"{'family':32s}{'hrs':>4s}{'best h':>7s}{'E[R]net':>9s}{'worst h':>8s}{'E[R]net':>9s}{'net b-w':>9s}{'gross b-w (ci95)':>28s}")
for f in sorted(set(fam.tolist())):
    m=(fam==f)&usable
    hs=[(h,float(e[m&(hour==h)].mean()),float(g[m&(hour==h)].mean()),int((m&(hour==h)).sum()))
        for h in range(24) if (m&(hour==h)).sum()>=200]
    if len(hs)<6: continue
    hs.sort(key=lambda t:t[1]); w,b=hs[0],hs[-1]
    gb=tmb(m&(hour==b[0]),m&(hour==w[0]),g)
    out["families"][f]={"hours_evaluated":len(hs),
      "best":{"hour":b[0],"E_R_net":round(b[1],5),"E_R_gross":round(b[2],5),"n":b[3]},
      "worst":{"hour":w[0],"E_R_net":round(w[1],5),"E_R_gross":round(w[2],5),"n":w[3]},
      "net_best_minus_worst":round(b[1]-w[1],5),"gross_best_minus_worst":{"pt":gb[0],"lo":gb[1],"hi":gb[2]},
      "gross_excludes_zero":bool(gb[1]>0 or gb[2]<0),
      "per_hour":[{"hour":h,"n":n,"E_R_net":round(en,5),"E_R_gross":round(eg,5)} for h,en,eg,n in sorted(hs)]}
    print(f"{f:32s}{len(hs):4d}{b[0]:7d}{b[1]:9.4f}{w[0]:8d}{w[1]:9.4f}{b[1]-w[1]:9.4f}"
          f"{f'{gb[0]:+.4f} [{gb[1]:+.3f},{gb[2]:+.3f}]':>28s}")
json.dump(out,open("LANEC_HOUR_V1.json","w"),indent=1,sort_keys=True)
print("\nwrote LANEC_HOUR_V1.json")
