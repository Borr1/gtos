"""Max-T over the retention grid, day-block permutation. Null: the family's own trigger
variable carries no information about outcome -- permute trigger RANK within trading day,
recompute the whole retention curve, take the max statistic. Controls the 8-point grid."""
import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True)
fam,day,mon,st,e,usable,X=d["fam"],d["day"],d["mon"],d["st"],d["e"],d["usable"],d["X"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=np.nan_to_num(X[:,FI["cost_r"]]); g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)
days,didx=np.unique(day,return_inverse=True)
GRID=[0.75,0.50,0.30,0.20,0.10,0.05,0.02]; NPERM=4000
rng=np.random.default_rng(20260811)
CASES=[("cross_asset_lead_lag","trigger_bar_range_atr","upper"),
       ("displacement_continuation","trigger_bar_range_atr","upper"),
       ("displacement_continuation","trigger_bar_body_atr","upper"),
       ("liquidity_sweep_reclaim","sweep_depth_atr","upper"),
       ("structural_distance_extreme","close_position_in_lookback_range","extreme"),
       ("current_fvg_fill","poi_age_hours","upper")]
out={"protocol":"max-T over a 7-point retention grid; null permutes the trigger variable "
     "WITHIN trading day (preserves the day-level outcome distribution and the day clustering); "
     "statistic = mean GROSS R of the retained subset; 4000 permutations; seed 20260811. "
     "IN-SAMPLE: all five months were read before this test was designed.","cases":[]}
print(f"{'family':30s}{'feature':26s}{'best retain':>12s}{'obs gross':>11s}{'maxT p':>9s}{'net at cell':>12s}")
for f,k,direc in CASES:
    m0=(fam==f)&usable&~np.isnan(X[:,FI[k]])
    idx=np.where(m0)[0]; x=X[idx,FI[k]]
    score=np.abs(x-0.5) if direc=="extreme" else x
    gv=g[idx]; ev=e[idx]; dv=didx[idx]
    def curve(sc):
        r=[]
        for keep in GRID:
            thr=np.quantile(sc,1-keep); sel=sc>=thr
            r.append(gv[sel].mean() if sel.sum()>=300 else -np.inf)
        return np.array(r)
    obs=curve(score); bi=int(np.argmax(obs)); obs_max=float(obs[bi])
    # permute score within day
    order=np.argsort(dv,kind="stable"); bounds=np.searchsorted(dv[order],np.arange(len(days)+1))
    nulls=np.empty(NPERM)
    for p in range(NPERM):
        sh=score.copy()
        for a,b in zip(bounds[:-1],bounds[1:]):
            if b-a>1:
                seg=order[a:b]; sh[seg]=score[rng.permutation(seg)]
        nulls[p]=curve(sh).max()
    pval=float((nulls>=obs_max).mean())
    keep=GRID[bi]; thr=np.quantile(score,1-keep); sel=score>=thr
    rec={"family":f,"feature":k,"best_retain_frac":keep,"n_at_cell":int(sel.sum()),
         "gross_R_at_cell":round(obs_max,5),"net_R_at_cell":round(float(ev[sel].mean()),5),
         "cost_R_at_cell":round(float(cost[idx][sel][ (st[idx][sel]!='RESOLVED_NO_FILL') ].mean()),5),
         "maxT_p":round(pval,5),"grid_points":len(GRID),"n_permutations":NPERM}
    out["cases"].append(rec)
    print(f"{f:30s}{k:26s}{keep*100:11.0f}%{obs_max:11.4f}{pval:9.4f}{rec['net_R_at_cell']:12.4f}")
json.dump(out,open("LANEC_MAXT_V1.json","w"),indent=1,sort_keys=True)
print("\nwrote LANEC_MAXT_V1.json")
