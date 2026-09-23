"""What the SHIPPED entry-trigger constant would have earned had it been TIGHTER.

The cache can answer the tightening direction only: loosening a threshold emits rows that
do not exist in this population, and changing a lookback/timeframe is a different detector.
Reported as a curve over the family's own recorded trigger variable, with the shipped
constant marked, day-clustered CI on the retained subset, and an early/late split.
"""
import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True); hour=np.load("hour.npy")
fam,day,mon,st,e,usable,X=d["fam"],d["day"],d["mon"],d["st"],d["e"],d["usable"],d["X"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=np.nan_to_num(X[:,FI["cost_r"]]); g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811); B=3000; PICK=rng.integers(0,ND,(B,ND))
EARLY=np.isin(mon,["feb","apr","may"]); LATE=np.isin(mon,["jun","jul"])
def ci(m,v):
    s=np.bincount(didx[m],weights=v[m],minlength=ND); c=np.bincount(didx[m],minlength=ND).astype(float)
    S=s[PICK].sum(1); C=c[PICK].sum(1); ok=C>0; mm=S[ok]/C[ok]
    return round(float(v[m].mean()),5),round(float(np.percentile(mm,2.5)),5),round(float(np.percentile(mm,97.5)),5)

# family -> (feature, shipped constant as it appears in the recorded feature, direction)
SPEC={
 "structural_distance_extreme":("close_position_in_lookback_range",
    "pos50>=0.97 (SHORT) / <=0.03 (LONG); recorded feature is the RAW pos, so tighten = move toward the extremes",
    "extreme"),
 "displacement_continuation":("trigger_bar_range_atr","bar_range/atr14 >= 1.5 (:1591)","upper"),
 "displacement_continuation2":("trigger_bar_body_atr","body/atr14 >= 0.75 (:1591)","upper"),
 "liquidity_sweep_reclaim":("sweep_depth_atr","no depth threshold at all -- sweep is binary (:1555)","upper"),
 "volatility_compression_expansion":("compression_ratio_prior_bar","prior atr14/atr50 <= 0.75 (:1620)","lower"),
 "cross_asset_lead_lag":("trigger_bar_range_atr","leader_impulse >= 1.0 (:1899); lag bar range is the proxy","upper"),
 "session_open_range_break":("session_open_range_width_atr","no width threshold at all (:1791)","upper"),
 "current_fvg_fill":("poi_max_mitigation_fraction","no mitigation threshold at all","lower"),
}
out={"note":"TIGHTENING ONLY. Loosening a constant, changing a lookback, or changing the decision "
     "timeframe emits rows absent from this population and CANNOT be measured here. All five months "
     "read: IN-SAMPLE. No multiplicity correction applied to the retention grid.",
     "bootstrap":{"kind":"day-clustered","B":B,"seed":20260811},"families":{}}
GRID=[1.0,0.75,0.50,0.30,0.20,0.10,0.05,0.02]
for key,(feat,prov,direc) in SPEC.items():
    f=key.rstrip("2")
    base=(fam==f)&usable&~np.isnan(X[:,FI[feat]])
    if base.sum()<800: continue
    x=X[:,FI[feat]]
    if direc=="upper":  score=x
    elif direc=="lower": score=-x
    else: score=np.abs(x-0.5)     # distance from mid-range = "more extreme"
    sv=score[base]; rows=[]
    print(f"\n=== {f} / {feat}\n    shipped: {prov}")
    print(f"    {'retain':>7s}{'n':>8s}{'E[R]net':>10s}{'net ci95':>20s}{'E[R]gross':>11s}{'gross ci95':>20s}{'early':>9s}{'late':>9s}")
    for keep in GRID:
        thr=np.quantile(sv,1-keep)
        m=base&(score>=thr)
        if m.sum()<300: continue
        n_,nlo,nhi=ci(m,e); gm,glo,ghi=ci(m,g)
        ee=float(e[m&EARLY].mean()) if (m&EARLY).sum()>100 else float("nan")
        el=float(e[m&LATE].mean()) if (m&LATE).sum()>100 else float("nan")
        rows.append({"retain_frac":keep,"threshold":round(float(thr),5),"n":int(m.sum()),
                     "E_R_net":n_,"net_ci95":[nlo,nhi],"E_R_gross":gm,"gross_ci95":[glo,ghi],
                     "E_R_net_early":round(ee,5),"E_R_net_late":round(el,5)})
        print(f"    {keep*100:6.0f}%{m.sum():8d}{n_:10.4f}{'['+format(nlo,'+.4f')+','+format(nhi,'+.4f')+']':>20s}"
              f"{gm:11.4f}{'['+format(glo,'+.4f')+','+format(ghi,'+.4f')+']':>20s}{ee:9.4f}{el:9.4f}")
    out["families"][key]={"feature":feat,"shipped_constant":prov,"tighten_direction":direc,"curve":rows}
json.dump(out,open("LANEC_TIGHTENING_V1.json","w"),indent=1,sort_keys=True)
print("\nwrote LANEC_TIGHTENING_V1.json")
