"""Control: is the trigger gradient a real outcome gradient, or cost dilution?
gross R = net R + cost_r  (identity verified: cost_r == spread+commission+swap+slippage)."""
import gzip,pickle,numpy as np,json
d=np.load("arrays.npz",allow_pickle=True)
fam,day,mon,st,e,usable,X=d["fam"],d["day"],d["mon"],d["st"],d["e"],d["usable"],d["X"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=X[:,FI["cost_r"]].copy(); cost[np.isnan(cost)]=0.0
g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)     # gross per-candidate R
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811); BOOT=4000; PICK=rng.integers(0,ND,(BOOT,ND))
EARLY=np.isin(mon,["feb","apr","may"]); LATE=np.isin(mon,["jun","jul"])

def spread_ci(mhi,mlo,vals):
    def sc(m):
        v=vals[m]; di=didx[m]
        return np.bincount(di,weights=v,minlength=ND),np.bincount(di,minlength=ND).astype(float)
    sh,ch=sc(mhi); sl,cl=sc(mlo)
    Sh,Ch=sh[PICK].sum(1),ch[PICK].sum(1); Sl,Cl=sl[PICK].sum(1),cl[PICK].sum(1)
    ok=(Ch>0)&(Cl>0); dd=Sh[ok]/Ch[ok]-Sl[ok]/Cl[ok]
    return float(dd.mean()),float(np.percentile(dd,2.5)),float(np.percentile(dd,97.5))

TRIG={
 "structural_distance_extreme":["close_position_in_lookback_range","dist_to_prior_high20_atr","risk_over_atr"],
 "liquidity_sweep_reclaim":["sweep_depth_atr","dist_to_prior_high20_atr","risk_over_atr"],
 "displacement_continuation":["trigger_bar_range_atr","trigger_bar_body_atr","risk_over_atr"],
 "volatility_compression_expansion":["compression_ratio_prior_bar","trigger_bar_range_atr","risk_over_atr"],
 "session_open_range_break":["session_open_range_width_atr","bars_since_session_open","risk_over_atr"],
 "regime_transition_break":["close_position_in_lookback_range","risk_over_atr"],
 "cross_asset_lead_lag":["trigger_bar_range_atr","risk_over_atr"],
 "current_fvg_fill":["poi_distance_to_zone_atr","poi_age_hours","poi_max_mitigation_fraction","poi_touch_count","risk_over_atr"],
 "current_ob_retest":["poi_distance_to_zone_atr","poi_age_hours","risk_over_atr"],
 "current_breaker_re_entry":["poi_distance_to_zone_atr","poi_age_hours","risk_over_atr"],
}
out={"note":"TmB = top quintile minus bottom quintile of the family's own trigger feature. "
     "NET = per-candidate economic R. GROSS = NET + cost_r (cost dilution removed). "
     "A gradient present in NET but absent in GROSS is a COST artifact, not a signal.",
     "bootstrap":{"kind":"day-clustered","B":BOOT,"seed":20260811},"rows":[]}
print(f"{'family':32s}{'feature':30s}{'TmB net':>10s}{'net ci95':>20s}{'TmB gross':>11s}{'gross ci95':>20s}  verdict")
print("-"*130)
for f in sorted(TRIG):
    base=(fam==f)&usable
    for k in TRIG[f]:
        x=X[:,FI[k]]; m=base&~np.isnan(x); xv=x[m]
        if xv.size<500: 
            print(f"{f:32s}{k:30s}  SKIP n={xv.size}"); continue
        qs=np.unique(np.quantile(xv,np.linspace(0,1,6)))
        if len(qs)<3: 
            print(f"{f:32s}{k:30s}  SKIP degenerate"); continue
        bi=np.clip(np.digitize(xv,qs[1:-1]),0,len(qs)-2); nb=len(qs)-1
        idx=np.where(m)[0]
        mhi=np.zeros(len(fam),bool); mhi[idx[bi==nb-1]]=True
        mlo=np.zeros(len(fam),bool); mlo[idx[bi==0]]=True
        n_,nlo,nhi=spread_ci(mhi,mlo,e); gm,glo,ghi=spread_ci(mhi,mlo,g)
        net_sig=(nlo>0 or nhi<0); grs_sig=(glo>0 or ghi<0)
        if net_sig and grs_sig: v="SIGNAL (survives cost removal)"
        elif net_sig and not grs_sig: v="COST ARTIFACT"
        elif not net_sig and grs_sig: v="gross-only"
        else: v="flat"
        out["rows"].append({"family":f,"feature":k,"TmB_net":round(n_,5),"net_ci95":[round(nlo,5),round(nhi,5)],
            "TmB_gross":round(gm,5),"gross_ci95":[round(glo,5),round(ghi,5)],"verdict":v,
            "n_top":int(mhi.sum()),"n_bottom":int(mlo.sum())})
        print(f"{f:32s}{k:30s}{n_:+10.4f}{'['+format(nlo,'+.4f')+','+format(nhi,'+.4f')+']':>20s}"
              f"{gm:+11.4f}{'['+format(glo,'+.4f')+','+format(ghi,'+.4f')+']':>20s}  {v}")
json.dump(out,open("LANEC_GROSS_CONTROL.json","w"),indent=1,sort_keys=True)
