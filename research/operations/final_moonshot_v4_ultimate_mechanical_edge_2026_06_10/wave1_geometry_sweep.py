"""WAVE 1b — geometry sweep + gate-on-best-geometry.

Wave1 found: (a) the regime classifier had ~0 AUC, and (b) the continuation
baseline itself bled -0.45R/trade in EVERY year. Gating a broken strategy proves
nothing. This script:
  1. Sweeps continuation geometry (stop mult, fixed-R targets AND trail arm/gap)
     on UNGATED Donchian breakouts, to find any config that is not structurally broken.
  2. Independently measures whether the classifier's predicted-trend selection actually
     picks forward windows with higher realized forward efficiency ratio (true skill test,
     decoupled from any one geometry).
  3. Applies the gate to the BEST ungated geometry and reports per-year R for
     gated / ungated / anti / random.
Honest bar unchanged: forward-positive AND positive in majority of years.
"""
from __future__ import annotations
import sys, os, math, json
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR = os.path.join(REPO, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, REPO); sys.path.insert(0, OPDIR)
import numpy as np
from geometry_lib import Bar, atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
# reuse loaders/features from wave1
from wave1_forward_regime_classifier import (
    load_symbol, year_of, build_features, FEATURE_NAMES, FULL_HISTORY_SYMS,
    donchian_signals, fit_logistic, predict_proba, auc, cost_for,
)

def main():
    print("Loading...")
    data={}
    for sym in FULL_HISTORY_SYMS:
        t,b=load_symbol(sym)
        if len(b)>=500: data[sym]=(t,b)
    feats={}
    train_fwd=[]
    for sym,(t,b) in data.items():
        F=build_features(b,t); feats[sym]=(t,b,F)
        for i in range(len(b)):
            if not math.isnan(F["_fwd_er"][i]) and year_of(t[i])<=2024:
                train_fwd.append(F["_fwd_er"][i])
    thr=float(np.quantile(np.array(train_fwd),0.66))
    for sym,(t,b,F) in feats.items():
        for i in range(len(b)):
            if not math.isnan(F["_fwd_er"][i]):
                F["_label"][i]=1.0 if F["_fwd_er"][i]>=thr else 0.0

    def row_ok(F,i):
        if math.isnan(F["_label"][i]): return False
        return all(not math.isnan(F[fn][i]) for fn in FEATURE_NAMES)

    # ---------- 1. GEOMETRY SWEEP on ungated Donchian-20 breakouts ----------
    print("\n=== GEOMETRY SWEEP (ungated Donchian-20 breakout) ===")
    # entry filter variations: breakout lookback; stop mult; exit (fixed R target OR trail).
    sweep_configs=[]
    for lb in (20,40,55):
        for stop_mult in (0.5,1.0,1.5,2.0):
            # fixed-R targets
            for tR in (1.0,1.5,2.0,3.0):
                sweep_configs.append(("fixedR",lb,stop_mult,tR,None,None))
            # trails (arm/gap as multiples of stop_dist)
            for arm in (1.0,2.0):
                for gap in (1.0,1.5,2.0):
                    sweep_configs.append(("trail",lb,stop_mult,None,arm,gap))

    # precompute signals per lookback
    sig_cache={lb:{} for lb in (20,40,55)}
    for sym,(t,b,F) in feats.items():
        for lb in (20,40,55):
            sig_cache[lb][sym]=donchian_signals(b,lookback=lb)

    def run(cfg, gate=None, mu=None,sd=None,w=None,p_gate=None, antimode=False, randmode=False, rng=None):
        mode,lb,sm,tR,arm,gap=cfg
        py=defaultdict(list)
        for sym,(t,b,F) in feats.items():
            atr=F["_atr"]; cost=cost_for(sym)
            for (i,direction) in sig_cache[lb][sym]:
                if i>=len(b)-2: continue
                if math.isnan(atr[i]) or atr[i]<=0: continue
                if gate is not None:
                    if not row_ok(F,i): continue
                    x=(np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd
                    p=predict_proba(w,x.reshape(1,-1))[0]
                    if gate=="gated" and not (p>=p_gate): continue
                    if gate=="anti" and not (p<p_gate): continue
                    if gate=="random" and rng.random()>0.40: continue
                stop=sm*atr[i]
                if mode=="fixedR":
                    r=simulate(b,i,direction,stop_dist=stop,target_dist=tR*stop,maxbars=60,cost=cost)
                else:
                    r=simulate(b,i,direction,stop_dist=stop,trail_arm=arm*stop,trail_gap=gap*stop,maxbars=60,cost=cost)
                py[year_of(t[i])].append(r)
        return py

    def score(py):
        years=[y for y in py if py[y]]
        means={y:float(np.mean(py[y])) for y in years}
        allr=[r for y in years for r in py[y]]
        fwd=[r for y in years if y>=2025 for r in py[y]]
        pos=sum(1 for y in years if means[y]>0)
        return {"pos":pos,"ny":len(years),"fwd_mean":float(np.mean(fwd)) if fwd else float('nan'),
                "fwd_n":len(fwd),"all_mean":float(np.mean(allr)) if allr else float('nan'),
                "all_n":len(allr),"means":means}

    rows=[]
    for cfg in sweep_configs:
        s=score(run(cfg))
        rows.append((cfg,s))
    # rank by all_mean (closest to / above 0), require decent sample
    rows=[r for r in rows if r[1]["all_n"]>=2000]
    rows.sort(key=lambda r:-(r[1]["all_mean"]))
    print(f"{'config':40s} {'all_mean':>9s} {'all_n':>7s} {'fwd_mean':>9s} {'pos/ny':>7s}")
    for cfg,s in rows[:15]:
        print(f"{str(cfg):40s} {s['all_mean']:+9.4f} {s['all_n']:7d} {s['fwd_mean']:+9.4f} {s['pos']:3d}/{s['ny']:<3d}")
    best_cfg,best_s=rows[0]
    print(f"\nBEST ungated geometry: {best_cfg}")
    print(f"  per-year means: "+", ".join(f"{y}:{best_s['means'][y]:+.3f}" for y in sorted(best_s['means'])))

    # ---------- 2. classifier skill, decoupled ----------
    Xtr,ytr=[],[]
    for sym,(t,b,F) in feats.items():
        for i in range(len(b)):
            if year_of(t[i])<=2024 and row_ok(F,i):
                Xtr.append([F[fn][i] for fn in FEATURE_NAMES]); ytr.append(F["_label"][i])
    Xtr=np.array(Xtr); ytr=np.array(ytr)
    mu=Xtr.mean(0); sd=Xtr.std(0); sd[sd==0]=1.0
    w=fit_logistic((Xtr-mu)/sd,ytr,l2=2.0,iters=600,lr=0.4)
    # forward-window selection test: among predicted-trend bars, is realized fwd_er higher?
    print("\n=== TRUE SKILL: does predicted-trend pick higher realized fwd efficiency? (FWD 2025-26) ===")
    tr_probs=[]
    for sym,(t,b,F) in feats.items():
        for i in range(len(b)):
            if year_of(t[i])<=2024 and row_ok(F,i):
                tr_probs.append(predict_proba(w,((np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd).reshape(1,-1))[0])
    p_gate=float(np.quantile(np.array(tr_probs),0.60))
    for yrset,lab in [([y for y in range(2015,2025)],"TRAIN"),([2025,2026],"FWD")]:
        sel_er=[]; rej_er=[]
        for sym,(t,b,F) in feats.items():
            for i in range(len(b)):
                if year_of(t[i]) in yrset and row_ok(F,i):
                    p=predict_proba(w,((np.array([F[fn][i] for fn in FEATURE_NAMES])-mu)/sd).reshape(1,-1))[0]
                    (sel_er if p>=p_gate else rej_er).append(F["_fwd_er"][i])
        sm_=np.mean(sel_er) if sel_er else float('nan'); rm_=np.mean(rej_er) if rej_er else float('nan')
        print(f"  {lab}: predicted-trend fwd_er={sm_:.4f} (n={len(sel_er)})  vs predicted-chop fwd_er={rm_:.4f} (n={len(rej_er)})  delta={sm_-rm_:+.4f}")

    # ---------- 3. gate on BEST geometry ----------
    print(f"\n=== GATE APPLIED TO BEST GEOMETRY {best_cfg} ===")
    rng=np.random.default_rng(11)
    outmodes={}
    for gate in ["ungated_feat","gated","anti","random"]:
        g = None if gate=="ungated_feat" else gate
        # ungated_feat = ungated but restricted to feature-defined bars for fair compare
        if gate=="ungated_feat":
            py=defaultdict(list)
            mode,lb,sm,tR,arm,gap=best_cfg
            for sym,(t,b,F) in feats.items():
                atr=F["_atr"]; cost=cost_for(sym)
                for (i,direction) in sig_cache[lb][sym]:
                    if i>=len(b)-2 or math.isnan(atr[i]) or atr[i]<=0: continue
                    if not row_ok(F,i): continue
                    stop=sm*atr[i]
                    if mode=="fixedR": r=simulate(b,i,direction,stop_dist=stop,target_dist=tR*stop,maxbars=60,cost=cost)
                    else: r=simulate(b,i,direction,stop_dist=stop,trail_arm=arm*stop,trail_gap=gap*stop,maxbars=60,cost=cost)
                    py[year_of(t[i])].append(r)
        else:
            py=run(best_cfg,gate=gate,mu=mu,sd=sd,w=w,p_gate=p_gate,rng=rng)
        outmodes[gate]=score(py)

    years=sorted(set().union(*[set(outmodes[m]["means"].keys()) for m in outmodes]))
    print(f"{'year':6s} | {'ungated_feat':>16s} | {'gated':>16s} | {'anti':>10s} | {'random':>10s}")
    for y in years:
        line=f"{y:6d} | "
        for m in ["ungated_feat","gated"]:
            mn=outmodes[m]["means"].get(y)
            line+=(f"{mn:+.4f}" if mn is not None else "  --   ").rjust(16)+" | "
        for m in ["anti","random"]:
            mn=outmodes[m]["means"].get(y)
            line+=(f"{mn:+.3f}" if mn is not None else " -- ").rjust(10)+" | "
        print(line)
    print("\nSummary:")
    for m in ["ungated_feat","gated","anti","random"]:
        s=outmodes[m]
        print(f"  {m:14s} pos={s['pos']}/{s['ny']}  fwd_meanR={s['fwd_mean']:+.4f}(n={s['fwd_n']})  all_meanR={s['all_mean']:+.4f}(n={s['all_n']})")
    g=outmodes["gated"]
    robust=(g['fwd_mean']>0) and (g['pos']>g['ny']/2)
    print(f"\n>>> GATED regime-robust: {robust}  (fwd+={g['fwd_mean']>0}, majority-yrs+={g['pos']>g['ny']/2})")

    res={"best_geometry":list(best_cfg),"best_geometry_score":{k:(v if not isinstance(v,dict) else {int(a):b for a,b in v.items()}) for k,v in best_s.items()},
         "gate_prob":p_gate,
         "gate_on_best":{m:{**{k:(v if not isinstance(v,dict) else {int(a):float(b) for a,b in v.items()}) for k,v in outmodes[m].items()}} for m in outmodes},
         "robust":bool(robust)}
    with open(os.path.join(OPDIR,"wave1_geometry_sweep_RESULT.json"),"w") as f:
        json.dump(res,f,indent=2,default=float)
    print("\nWrote wave1_geometry_sweep_RESULT.json")

if __name__=="__main__":
    main()
