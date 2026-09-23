import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True)
fam,day,st,e,usable=d["fam"],d["day"],d["st"],d["e"],d["usable"]
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811)
BOOT=4000
PICK=rng.integers(0,ND,(BOOT,ND))

def day_ci(mask,vals=None):
    """Day-clustered bootstrap 95% CI of mean(vals[mask]) (vals defaults to e)."""
    v=(e if vals is None else vals)[mask]; di=didx[mask]
    if v.size<20: return (float("nan"),float("nan"),float("nan"))
    s=np.bincount(di,weights=v,minlength=ND); c=np.bincount(di,minlength=ND).astype(float)
    S=s[PICK].sum(1); C=c[PICK].sum(1)
    ok=C>0; m=S[ok]/C[ok]
    return (float(v.mean()),float(np.percentile(m,2.5)),float(np.percentile(m,97.5)))

out={"n_emitted":int(len(fam)),"n_usable":int(usable.sum()),"n_days":int(ND),
     "bootstrap":{"kind":"day-clustered","B":BOOT,"seed":20260811},
     "basis":"per-candidate economic R; RESOLVED_NO_FILL=0.0R; censored rows excluded",
     "families":{}}
hdr=f"{'family':34s}{'emitted':>8s}{'cens%':>7s}{'fill%':>7s}{'E[R]/cand':>11s}{'ci95':>22s}{'E[R]|fill':>10s}{'tgt%':>6s}{'stp%':>6s}{'tstop%':>7s}"
print(hdr); print("-"*len(hdr))
for f in sorted(set(fam.tolist())):
    m=(fam==f)&usable; me=(fam==f)
    fill=m&(st!="RESOLVED_NO_FILL")
    nf=int(fill.sum())
    mu,lo,hi=day_ci(m)
    rec={"emitted":int(me.sum()),"usable":int(m.sum()),
         "censored_frac":round(1-m.sum()/me.sum(),4),
         "fill_rate":round(nf/m.sum(),4),
         "E_R_per_candidate":round(mu,5),"ci95":[round(lo,5),round(hi,5)],
         "E_R_per_fill":round(float(e[fill].mean()),5),
         "target_frac":round(float(((fam==f)&(st=="RESOLVED_FILLED_TARGET")).sum())/nf,4),
         "stop_frac":round(float(((fam==f)&(st=="RESOLVED_FILLED_STOP")).sum())/nf,4),
         "timestop_frac":round(float(((fam==f)&(st=="RESOLVED_FILLED_TIME_STOP")).sum())/nf,4)}
    out["families"][f]=rec
    print(f"{f:34s}{rec['emitted']:8d}{rec['censored_frac']*100:7.1f}{rec['fill_rate']*100:7.1f}"
          f"{rec['E_R_per_candidate']:11.4f}{'['+format(lo,'.4f')+','+format(hi,'.4f')+']':>22s}"
          f"{rec['E_R_per_fill']:10.4f}{rec['target_frac']*100:6.1f}{rec['stop_frac']*100:6.1f}{rec['timestop_frac']*100:7.1f}")
mu,lo,hi=day_ci(usable)
out["ALL"]={"E_R_per_candidate":round(mu,5),"ci95":[round(lo,5),round(hi,5)]}
print(f"\nALL FAMILIES pooled: E[R]/cand {mu:.5f}  ci95 [{lo:.5f},{hi:.5f}]  n={int(usable.sum())}")
json.dump(out,open("LANEC_FAMILY_BASELINE.json","w"),indent=1,sort_keys=True)
