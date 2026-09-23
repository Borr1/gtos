"""d3 — pool the eight windows, compute the paired REAL-minus-PLACEBO signal and its
day-block bootstrap CI, and print the transplant tables."""
from __future__ import annotations
import json, sys
from collections import defaultdict
import numpy as np

WINS=["2025-10","2025-11","2025-12","2026-01","2026-02","2026-03","2026-04","2026-05"]
def load(prefix):
    P={}
    for w in WINS:
        P[w]=json.load(open(f"/tmp/d3/{prefix}_{w}.json"))
    return P

def pool(P):
    tot=defaultdict(lambda: defaultdict(float))
    dayg=defaultdict(dict); dayn=defaultdict(dict); dayN=defaultdict(dict)
    perwin=defaultdict(dict)
    for w in WINS:
        for k,v in P[w]["cells"].items():
            for f,x in v.items():
                if f in ("day_net","day_gross","day_n"): continue
                tot[k][f]+=x
            for d,x in (v.get("day_gross") or {}).items(): dayg[k][w+"|"+d]=x
            for d,x in (v.get("day_net") or {}).items():   dayn[k][w+"|"+d]=x
            for d,x in (v.get("day_n") or {}).items():     dayN[k][w+"|"+d]=x
            n=v["n"]
            if n: perwin[k][w]=dict(n=n,gross=v["sum_gross"]/n,cost=v["sum_cost"]/n,net=v["sum_net"]/n)
    return tot,dayg,dayn,dayN,perwin

def paired_signal(dayg,dayN,kr,kp,nboot=4000,seed=20260806):
    days=sorted(set(dayg[kr])&set(dayg[kp]))
    if not days: return None
    diff=np.array([dayg[kr][d]-dayg[kp][d] for d in days])
    cnt =np.array([dayN[kr][d] for d in days],dtype=float)
    rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(days),size=(nboot,len(days)))
    num=diff[ix].sum(axis=1); den=cnt[ix].sum(axis=1); den[den==0]=np.nan
    m=num/den; m=m[np.isfinite(m)]
    return dict(mean=float(diff.sum()/cnt.sum()),
                lo=float(np.percentile(m,2.5)),hi=float(np.percentile(m,97.5)),
                p_le0=float((m<=0).mean()),n_days=len(days))

def row(tot,k):
    v=tot[k]; n=v["n"]
    if not n: return None
    return dict(n=int(n),gross=v["sum_gross"]/n,cost=v["sum_cost"]/n,net=v["sum_net"]/n,
                wr=v["n_win_gross"]/n,wr_net=v["n_win_net"]/n,
                hold_h=v["sum_hold_min"]/n/60,nights=v["sum_nights"]/n,
                p_stop=v["n_stop"]/n,p_tgt=v["n_target"]/n,p_hor=v["n_horizon"]/n,
                win_mean=(v["sum_win_r"]/v["n_pos"]) if v["n_pos"] else 0.0,
                loss_mean=(v["sum_loss_r"]/v["n_neg"]) if v["n_neg"] else 0.0)
