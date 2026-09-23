"""WAVE 1c — falsify the no-skill verdict with a nonlinear model + single-feature probes.

Wave1/1b: logistic gate had ~0 AUC and the gate hurt forward returns. Before
concluding 'forward regime is unpredictable at H4 from these features', test
whether a NONLINEAR model (gradient-boosted shallow trees, hand-rolled) or any
SINGLE feature's monotone tercile sort can predict forward efficiency ratio
out-of-sample (FWD 2025-26). If both find nothing, the negative result is firm.
Also: regression on continuous fwd_er (not just the tercile label) to catch any
weak-but-real monotone signal.
"""
from __future__ import annotations
import sys, os, math, json
from collections import defaultdict
REPO="/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR=os.path.join(REPO,"research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0,REPO); sys.path.insert(0,OPDIR)
import numpy as np
from wave1_forward_regime_classifier import (load_symbol,year_of,build_features,FEATURE_NAMES,FULL_HISTORY_SYMS,auc)

def spearman(a,b):
    ar=np.argsort(np.argsort(a)).astype(float); br=np.argsort(np.argsort(b)).astype(float)
    ar-=ar.mean(); br-=br.mean()
    d=math.sqrt((ar*ar).sum()*(br*br).sum())
    return float((ar*br).sum()/d) if d>0 else 0.0

# tiny gradient boosting for binary classification (depth-1 stumps), numpy only
def fit_gbm(X,y,n_trees=80,lr=0.1,depth=2):
    n,d=X.shape
    Fpred=np.zeros(n); base=math.log((y.mean()+1e-9)/(1-y.mean()+1e-9)); Fpred+=base
    trees=[]
    for _ in range(n_trees):
        p=1/(1+np.exp(-np.clip(Fpred,-30,30))); grad=y-p
        tree=build_tree(X,grad,depth); trees.append(tree)
        Fpred+=lr*predict_tree(tree,X)
    return base,lr,trees

def build_tree(X,g,depth):
    if depth==0 or len(g)<50: return {"leaf":float(g.mean())}
    best=None
    n,d=X.shape
    for f in range(d):
        xs=X[:,f]; thr=np.quantile(xs,[0.25,0.5,0.75])
        for t in thr:
            m=xs<=t
            if m.sum()<25 or (~m).sum()<25: continue
            gl=g[m].mean(); gr=g[~m].mean()
            # variance reduction proxy
            sse=((g[m]-gl)**2).sum()+((g[~m]-gr)**2).sum()
            if best is None or sse<best[0]: best=(sse,f,t)
    if best is None: return {"leaf":float(g.mean())}
    _,f,t=best; m=X[:,f]<=t
    return {"f":f,"t":t,"l":build_tree(X[m],g[m],depth-1),"r":build_tree(X[~m],g[~m],depth-1)}

def predict_tree(tree,X):
    if "leaf" in tree: return np.full(len(X),tree["leaf"])
    m=X[:,tree["f"]]<=tree["t"]; out=np.zeros(len(X))
    out[m]=predict_tree(tree["l"],X[m]); out[~m]=predict_tree(tree["r"],X[~m]); return out

def gbm_proba(model,X):
    base,lr,trees=model; F=np.full(len(X),base)
    for tr in trees: F+=lr*predict_tree(tr,X)
    return 1/(1+np.exp(-np.clip(F,-30,30)))

def main():
    data={}
    for sym in FULL_HISTORY_SYMS:
        t,b=load_symbol(sym)
        if len(b)>=500: data[sym]=(t,b)
    feats={}
    train_fwd=[]
    for sym,(t,b) in data.items():
        F=build_features(b,t); feats[sym]=(t,b,F)
        for i in range(len(b)):
            if not math.isnan(F["_fwd_er"][i]) and year_of(t[i])<=2024: train_fwd.append(F["_fwd_er"][i])
    thr=float(np.quantile(np.array(train_fwd),0.66))
    for sym,(t,b,F) in feats.items():
        for i in range(len(b)):
            if not math.isnan(F["_fwd_er"][i]): F["_label"][i]=1.0 if F["_fwd_er"][i]>=thr else 0.0
    def ok(F,i):
        return (not math.isnan(F["_label"][i])) and all(not math.isnan(F[fn][i]) for fn in FEATURE_NAMES)

    Xtr=[];ytr=[];ertr=[];Xf=[];yf=[];erf=[]
    for sym,(t,b,F) in feats.items():
        for i in range(len(b)):
            if not ok(F,i): continue
            row=[F[fn][i] for fn in FEATURE_NAMES]
            if year_of(t[i])<=2024: Xtr.append(row);ytr.append(F["_label"][i]);ertr.append(F["_fwd_er"][i])
            elif year_of(t[i])>=2025: Xf.append(row);yf.append(F["_label"][i]);erf.append(F["_fwd_er"][i])
    Xtr=np.array(Xtr);ytr=np.array(ytr);ertr=np.array(ertr)
    Xf=np.array(Xf);yf=np.array(yf);erf=np.array(erf)
    mu=Xtr.mean(0);sd=Xtr.std(0);sd[sd==0]=1
    Xtr_s=(Xtr-mu)/sd; Xf_s=(Xf-mu)/sd

    print("=== SINGLE-FEATURE forward predictive power (out-of-sample 2025-26) ===")
    print(f"{'feature':22s} {'spearman_FWD(feat,fwd_er)':>26s} {'top-tercile fwd_er lift':>24s}")
    base_er=erf.mean()
    for k,fn in enumerate(FEATURE_NAMES):
        sp=spearman(Xf[:,k],erf)
        cut=np.quantile(Xf[:,k],0.66); lift=erf[Xf[:,k]>=cut].mean()/base_er
        print(f"{fn:22s} {sp:+26.4f} {lift:24.3f}x")

    print("\n=== GBM (nonlinear) classifier — trees find interactions logistic missed? ===")
    model=fit_gbm(Xtr_s,ytr,n_trees=80,lr=0.1,depth=2)
    ptr=gbm_proba(model,Xtr_s); pf=gbm_proba(model,Xf_s)
    print(f"  GBM AUC TRAIN={auc(ytr,ptr):.3f}   GBM AUC FWD={auc(yf,pf):.3f}")
    # does GBM top-quintile predicted-trend have higher realized fwd_er OOS?
    cut=np.quantile(ptr,0.80)
    sel=erf[pf>=cut]; rej=erf[pf<cut]
    print(f"  FWD: GBM predicted-trend(top20%) fwd_er={sel.mean():.4f}(n={len(sel)}) vs rest={rej.mean():.4f}(n={len(rej)}) delta={sel.mean()-rej.mean():+.4f}")

    print("\n=== continuous regression check (spearman of GBM-prob vs realized fwd_er, OOS) ===")
    print(f"  spearman(GBM_prob_FWD, fwd_er_FWD) = {spearman(pf,erf):+.4f}")

    res={"single_feature_spearman_fwd":{fn:spearman(Xf[:,k],erf) for k,fn in enumerate(FEATURE_NAMES)},
         "gbm_auc_train":auc(ytr,ptr),"gbm_auc_fwd":auc(yf,pf),
         "gbm_fwd_selected_er":float(sel.mean()),"gbm_fwd_rest_er":float(rej.mean()),
         "gbm_prob_vs_fwder_spearman":spearman(pf,erf)}
    with open(os.path.join(OPDIR,"wave1_skill_falsification_RESULT.json"),"w") as f: json.dump(res,f,indent=2,default=float)
    print("\nVERDICT: if all AUC~0.50, all spearman~0, all lift~1.0x -> forward regime is NOT predictable at H4 from these features.")
    print("Wrote wave1_skill_falsification_RESULT.json")

if __name__=="__main__": main()
