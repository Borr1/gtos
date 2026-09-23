#!/usr/bin/env python3
"""F4 — the pre-registered leak controls (C1, C5) plus the book-realism test.

C1  one-day lag: replace every feature with the same feature from the most recent
    PRIOR trading day, same symbol. Declared interpretation is in the prereg.
C5  random split vs time split on identical rows: the control that CAN see a leak
    permutation cannot -- sibling rows in one decision window sharing an outcome.
BOOK the top-decile MARKET result is only a book if it survives one-candidate-per-
    decision-window. Measured as realized net R per trade and per day.
"""
from __future__ import annotations
import gzip, pickle, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
sys.path.insert(0, str(Path(__file__).parent))
from f4_common import CATEGORICAL, EVAL_FOLDS, MONTHS, NUMERIC, enrich, jdump, load_month

HERE = Path(__file__).parent; OUT = HERE / "receipts"; SEED = 20260812

def build():
    rows = []
    for m in MONTHS: rows += enrich(load_month(m))
    with gzip.open(HERE/"f4_excursion_join.pkl.gz","rb") as f:
        exc = {r["candidate_occurrence_key"]: r["mfe"] for r in pickle.load(f)}
    with gzip.open(HERE/"f4_new_features.pkl.gz","rb") as f: new = pickle.load(f)
    out=[]
    for r in rows:
        k=r["candidate_occurrence_key"]
        if k in exc:
            r["mfe"]=exc[k]; r["_new"]=new.get(k,{}); out.append(r)
    return out, sorted({k for v in new.values() for k in v})

def enc(rows, newnames, src=None):
    src = src or rows
    n=len(rows); cols=len(CATEGORICAL)+len(NUMERIC)+len(newnames)
    X=np.full((n,cols),np.nan); cm=np.zeros(cols,dtype=bool)
    for j,k in enumerate(CATEGORICAL):
        cm[j]=True; v={}
        X[:,j]=[v.setdefault(str(r.get(k)),len(v)) for r in src]
    o=len(CATEGORICAL)
    for j,k in enumerate(NUMERIC):
        X[:,o+j]=[r.get(k,np.nan) if r.get(k) is not None else np.nan for r in src]
    o2=o+len(NUMERIC)
    for j,k in enumerate(newnames):
        X[:,o2+j]=[r["_new"].get(k,np.nan) for r in src]
    return X,cm

def lab(rows): 
    y=np.array([1 if r["mfe"]>=1.5 else (0 if r["mfe"]<0.3 else -1) for r in rows]); return y, y>=0

def fit(Xtr,ytr,Xte,cm):
    m=HistGradientBoostingClassifier(random_state=SEED,categorical_features=cm,
        early_stopping=False,max_iter=100,max_leaf_nodes=15,learning_rate=0.05)
    m.fit(Xtr,ytr); return m.predict_proba(Xte)[:,1]

def main():
    rows,newnames=build()
    mk=[r for r in rows if r["proposed_order_type"]=="MARKET"]
    res={"prereg_sha256":"bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054"}

    # ---- C1 one-day lag on MARKET -------------------------------------------
    bysd=defaultdict(list)
    for r in mk: bysd[r["symbol"]].append(r)
    donor={}
    for sym,rs in bysd.items():
        rs=sorted(rs,key=lambda r:r["label_span_start_utc"])
        byday=defaultdict(list)
        for r in rs: byday[r["trading_day"]].append(r)
        days=sorted(byday)
        for i,d in enumerate(days):
            if i==0: continue
            prev=byday[days[i-1]]
            for j,r in enumerate(byday[d]): donor[r["candidate_occurrence_key"]]=prev[j%len(prev)]
    for name,use_donor in (("real",False),("lagged_one_day",True)):
        R=[r for r in mk if not use_donor or r["candidate_occurrence_key"] in donor]
        y,keep=lab(R); R=[r for r,k in zip(R,keep) if k]; y=y[keep]
        src=[donor[r["candidate_occurrence_key"]] for r in R] if use_donor else R
        X,cm=enc(R,newnames,src); mon=np.array([r["month"] for r in R])
        S,Y=[],[]
        for f in EVAL_FOLDS:
            tr=np.isin(mon,MONTHS[:MONTHS.index(f)]); te=mon==f
            if tr.sum()<500 or te.sum()<200: continue
            S.append(fit(X[tr],y[tr],X[te],cm)); Y.append(y[te])
        S,Y=np.concatenate(S),np.concatenate(Y)
        res[f"C1_{name}"]={"auc":float(roc_auc_score(Y,S)),"n":int(len(S))}
        print(f"C1 {name}: AUC={res[f'C1_{name}']['auc']:.4f} n={len(S)}",flush=True)

    # ---- C5 random split vs time split, identical rows -----------------------
    y,keep=lab(mk); R=[r for r,k in zip(mk,keep) if k]; y=y[keep]
    X,cm=enc(R,newnames); mon=np.array([r["month"] for r in R])
    te_time=np.isin(mon,EVAL_FOLDS); tr_time=~te_time
    s=fit(X[tr_time],y[tr_time],X[te_time],cm)
    auc_time=float(roc_auc_score(y[te_time],s))
    rg=np.random.default_rng(SEED); perm=rg.permutation(len(R))
    ntr=int(tr_time.sum()); tr_r=np.zeros(len(R),bool); tr_r[perm[:ntr]]=True
    s2=fit(X[tr_r],y[tr_r],X[~tr_r],cm)
    auc_rand=float(roc_auc_score(y[~tr_r],s2))
    res["C5_leak_control"]={"auc_time_split":auc_time,"auc_random_split":auc_rand,
        "gap":auc_rand-auc_time,
        "verdict":"random-split advantage above 0.03 AUC indicates within-window information sharing"}
    print(f"C5 time={auc_time:.4f} random={auc_rand:.4f} gap={auc_rand-auc_time:+.4f}",flush=True)

    # ---- BOOK: one candidate per decision window, MARKET only ---------------
    y,keep=lab(mk); Rl=[r for r,k in zip(mk,keep) if k]
    Xa,cma=enc(mk,newnames); mona=np.array([r["month"] for r in mk])
    yl,keepl=lab(mk)
    books={}
    for thr_q in (0.90,0.95,0.99):
        rows_sel=[]
        for f in EVAL_FOLDS:
            trm=np.isin(mona,MONTHS[:MONTHS.index(f)]) & keepl
            tem=mona==f
            if trm.sum()<500 or tem.sum()<200: continue
            sc=fit(Xa[trm],yl[trm],Xa[tem],cma)
            te_rows=[r for r,m in zip(mk,tem) if m]
            cut=np.quantile(sc,thr_q)
            best={}
            for r,v in zip(te_rows,sc):
                if v<cut: continue
                w=r["decision_window_id"]
                if w not in best or v>best[w][1]: best[w]=(r,v)
            rows_sel+= [v[0] for v in best.values()]
        nr=np.array([r["terminal_net_r"] for r in rows_sel])
        days=defaultdict(float)
        for r in rows_sel: days[r["trading_day"]]+=r["terminal_net_r"]
        dv=np.array(list(days.values()))
        rg2=np.random.default_rng(SEED)
        bs=np.array([dv[rg2.integers(0,len(dv),len(dv))].sum() for _ in range(2000)])
        books[f"top_{int((1-thr_q)*100)}pct_one_per_window"]={
            "n_trades":len(rows_sel),"trades_per_day":len(rows_sel)/len(days),
            "net_r_per_trade":float(nr.mean()),"net_r_total":float(nr.sum()),
            "usd_per_trade_at_500_per_R":round(float(nr.mean())*500,1),
            "n_days":len(days),"pos_days":int((dv>0).sum()),"neg_days":int((dv<0).sum()),
            "total_r_ci95":[float(np.quantile(bs,.025)),float(np.quantile(bs,.975))],
            "p_total_gt_0":float((bs>0).mean()),
            "target_hit_rate":float(np.mean([r["lifecycle_label_status"]=="RESOLVED_FILLED_TARGET" for r in rows_sel]))}
        b=books[f"top_{int((1-thr_q)*100)}pct_one_per_window"]
        print(f"BOOK top{int((1-thr_q)*100)}%: n={b['n_trades']} {b['trades_per_day']:.1f}/day "
              f"netR/trade={b['net_r_per_trade']:+.4f} total={b['net_r_total']:+.1f} "
              f"CI[{b['total_r_ci95'][0]:+.1f},{b['total_r_ci95'][1]:+.1f}] p={b['p_total_gt_0']:.3f} "
              f"hit={b['target_hit_rate']:.4f} days {b['pos_days']}/{b['neg_days']}",flush=True)
    res["book_one_per_window_market_only"]=books
    jdump(res,OUT/"F4_CONTROLS_V1.json"); print("wrote F4_CONTROLS_V1.json")

if __name__=="__main__": main()
