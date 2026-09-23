"""LANE C final trigger-sensitivity measurement.

Three arms per (family, trigger feature), all day-clustered bootstrap, all IN-SAMPLE
(five months read before this ran):
  NET   per-candidate economic R  (no-fill = 0.0R)   -- the estate's own basis
  GROSS NET + cost_r                                  -- removes cost dilution
  FILLED conditional on a fill, net                   -- removes the fill-rate confound
A gradient that is significant in NET but not in GROSS+FILLED is not evidence about the
setup; it is evidence about cost or about not trading.
"""
import numpy as np, json
d=np.load("arrays.npz",allow_pickle=True)
fam,day,mon,st,e,usable,X=d["fam"],d["day"],d["mon"],d["st"],d["e"],d["usable"],d["X"]
FEATS=list(d["feats"]); FI={k:i for i,k in enumerate(FEATS)}
cost=np.nan_to_num(X[:,FI["cost_r"]]); g=np.where(st=="RESOLVED_NO_FILL",0.0,e+cost)
filledm=usable&(st!="RESOLVED_NO_FILL")
days,didx=np.unique(day,return_inverse=True); ND=len(days)
rng=np.random.default_rng(20260811); BOOT=4000; PICK=rng.integers(0,ND,(BOOT,ND))

def tmb(mhi,mlo,vals):
    def sc(m):
        return np.bincount(didx[m],weights=vals[m],minlength=ND),np.bincount(didx[m],minlength=ND).astype(float)
    sh,ch=sc(mhi); sl,cl=sc(mlo)
    Sh,Ch=sh[PICK].sum(1),ch[PICK].sum(1); Sl,Cl=sl[PICK].sum(1),cl[PICK].sum(1)
    ok=(Ch>0)&(Cl>0)
    if ok.sum()<200: return None
    dd=Sh[ok]/Ch[ok]-Sl[ok]/Cl[ok]
    return dict(pt=round(float(vals[mhi].mean()-vals[mlo].mean()),5),
                lo=round(float(np.percentile(dd,2.5)),5),hi=round(float(np.percentile(dd,97.5)),5))
def sig(a): return a is not None and (a["lo"]>0 or a["hi"]<0)

TRIG={
 "structural_distance_extreme":[("close_position_in_lookback_range","pos50>=0.97 / <=0.03 (:1702,:1720)"),
   ("dist_to_prior_high20_atr","lookback 20 (:1463)"),("risk_over_atr","stop = extreme +/- 0.25*ATR14 (:1706,:1724)")],
 "liquidity_sweep_reclaim":[("sweep_depth_atr","sweep of prior-20 extreme, depth unconstrained (:1555)"),
   ("dist_to_prior_high20_atr","lookback 20"),("risk_over_atr","stop = swept extreme +/- 0.25*ATR14 (:1565)")],
 "displacement_continuation":[("trigger_bar_range_atr","range/atr14 >= 1.5 (:1591)"),
   ("trigger_bar_body_atr","body/atr14 >= 0.75 (:1591)"),("risk_over_atr","stop = bar extreme +/- 0.25*ATR14 (:1593)")],
 "volatility_compression_expansion":[("compression_ratio_prior_bar","prior atr14/atr50 <= 0.75 (:1620)"),
   ("trigger_bar_range_atr","range/atr14 >= 1.25 (:1620)"),("risk_over_atr","stop = min(low,p_low20) - 0.20*ATR14 (:1629)")],
 "session_open_range_break":[("session_open_range_width_atr","NO width filter (:1791-1811)"),
   ("bars_since_session_open","NO bar-count filter"),("risk_over_atr","stop = opposite range edge -/+ 0.10*ATR14 (:1798)")],
 "regime_transition_break":[("close_position_in_lookback_range","trend flip + close beyond prior-20 (:1665)"),
   ("risk_over_atr","stop = prior-20 opposite extreme -/+ 0.10*ATR14 (:1673)")],
 "cross_asset_lead_lag":[("trigger_bar_range_atr","leader_impulse>=1.0 and lag_response<=0.5 (:1899)"),
   ("risk_over_atr","stop = lag bar extreme +/- 0.25*lag_ATR14 (:1904)")],
 "current_fvg_fill":[("poi_distance_to_zone_atr","poi_proximity_tolerance_pct default 0.01 (:2641-2656)"),
   ("poi_age_hours","NO age filter"),("poi_max_mitigation_fraction","NO mitigation filter"),
   ("poi_touch_count","NO touch filter"),("distance_to_limit_atr","limit distance at decision"),
   ("risk_over_atr","stop = zone edge -/+ sl_buffer_atr_multiplier (:2658-2672)")],
 "current_ob_retest":[("distance_to_limit_atr","ONLY recorded trigger proxy; poi_* are not_applicable"),
   ("risk_over_atr","stop = zone edge -/+ ob_retest_sl_min_buffer_atr")],
 "current_breaker_re_entry":[("distance_to_limit_atr","ONLY recorded trigger proxy; poi_* are not_applicable"),
   ("risk_over_atr","stop = zone edge -/+ sl_buffer_breaker_atr_multiplier")],
}
out={"basis":"per-candidate economic R; no-fill=0.0R; censored excluded; ALL FIVE MONTHS READ (in-sample, post-outcome)",
     "bootstrap":{"kind":"day-clustered","B":BOOT,"seed":20260811,"n_days":int(ND)},
     "arms":{"NET":"per-candidate net R","GROSS":"net + cost_r","FILLED":"net R | fill"},
     "rows":[]}
print(f"{'family':30s}{'trigger feature':28s}{'NET TmB':>22s}{'GROSS TmB':>22s}{'FILLED-GROSS TmB':>22s}  verdict")
print("-"*140)
for f in sorted(TRIG):
    base=(fam==f)&usable
    for k,prov in TRIG[f]:
        x=X[:,FI[k]]; m=base&~np.isnan(x)
        if m.sum()<500:
            out["rows"].append({"family":f,"feature":k,"provenance":prov,"status":"NOT_RECORDED_FOR_THIS_FAMILY"})
            print(f"{f:30s}{k:30s}{'--- not recorded for this family ---':>50s}"); continue
        xv=x[m]; qs=np.unique(np.quantile(xv,np.linspace(0,1,6)))
        if len(qs)<3:
            out["rows"].append({"family":f,"feature":k,"provenance":prov,"status":"DEGENERATE"}); continue
        bi=np.clip(np.digitize(xv,qs[1:-1]),0,len(qs)-2); nb=len(qs)-1; idx=np.where(m)[0]
        mhi=np.zeros(len(fam),bool); mhi[idx[bi==nb-1]]=True
        mlo=np.zeros(len(fam),bool); mlo[idx[bi==0]]=True
        a_net=tmb(mhi,mlo,e); a_gr=tmb(mhi,mlo,g)
        okf=(mhi&filledm).sum()>200 and (mlo&filledm).sum()>200
        a_fl=tmb(mhi&filledm,mlo&filledm,e) if okf else None
        a_fg=tmb(mhi&filledm,mlo&filledm,g) if okf else None
        # For 100%-fill (MARKET) families FILLED == NET and carries no extra information;
        # the discriminating arm is then GROSS alone.
        allfill=float((st[idx]!="RESOLVED_NO_FILL").mean())>0.999
        sn,sg,sfg=sig(a_net),sig(a_gr),sig(a_fg)
        same=lambda a,b: a is not None and b is not None and np.sign(a["pt"])==np.sign(b["pt"])
        if allfill:
            v="SIGNAL" if (sn and sg and same(a_net,a_gr)) else ("COST ARTIFACT" if sn else ("weak (net-flat)" if sg else "FLAT"))
        else:
            if sn and sfg and same(a_net,a_fg): v="SIGNAL"
            elif sfg: v="SIGNAL_IN_FILLS_ONLY" if not sn else "SIGNAL"
            elif sn: v="COST/FILL ARTIFACT"
            elif sg: v="weak (net-flat)"
            else: v="FLAT"
        cells=[{"bin":b,"lo":round(float(qs[b]),5),"hi":round(float(qs[b+1]),5),
                "n":int((bi==b).sum()),
                "E_R_net":round(float(e[idx[bi==b]].mean()),5),
                "E_R_gross":round(float(g[idx[bi==b]].mean()),5),
                "fill_rate":round(float((st[idx[bi==b]]!="RESOLVED_NO_FILL").mean()),4)} for b in range(nb)]
        out["rows"].append({"family":f,"feature":k,"provenance":prov,"n":int(m.sum()),
            "TmB_net":a_net,"TmB_gross":a_gr,"TmB_filled":a_fl,"TmB_filled_gross":a_fg,"all_fill":bool(allfill),"verdict":v,"cells":cells})
        fm=lambda a: (f"{a['pt']:+.4f}[{a['lo']:+.3f},{a['hi']:+.3f}]" if a else "n/a")
        print(f"{f:30s}{k:28s}{fm(a_net):>22s}{fm(a_gr):>22s}{fm(a_fg):>22s}  {v}")
json.dump(out,open("LANEC_TRIGGER_SENSITIVITY_V1.json","w"),indent=1,sort_keys=True)
print("\nwrote LANEC_TRIGGER_SENSITIVITY_V1.json")
