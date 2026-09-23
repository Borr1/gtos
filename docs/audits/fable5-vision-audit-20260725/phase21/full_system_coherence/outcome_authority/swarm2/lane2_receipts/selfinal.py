#!/usr/bin/env python3
"""The deployable object under (a) short horizons and (b) wider stops."""
import gzip,pickle,json,datetime as dt
from collections import defaultdict,Counter
import numpy as np
RNG=np.random.default_rng(20260812); MIN_R=0.10; SLIP=0.02
M=["feb","apr","may","jun","jul"]
W2={}; SC={}
for m in M:
    for r in pickle.load(gzip.open(f"walk2_{m}.pkl.gz","rb")): W2[r["k"]]=r
    for r in pickle.load(gzip.open(f"scale_{m}.pkl.gz","rb")): SC[r["k"]]=r
rows=[]
for m in M:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        if c.get("pred_month_boundary") is not None: rows.append(c)
EP=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
def mn(s): return int((dt.datetime.fromisoformat(str(s))-EP).total_seconds()//60)
byw=defaultdict(list)
for c in rows: byw[c["decision_window_id"]].append(c)
order=sorted(byw.values(),key=lambda v:(min(mn(x["label_span_start_utc"]) for x in v),v[0]["decision_window_id"]))
def replay(getter):
    active={}; sel=[]
    for cands in order:
        at=min(mn(x["label_span_start_utc"]) for x in cands)
        active={s:e for s,e in active.items() if e>at}
        av=[c for c in cands if c["symbol"] not in active]
        if not av: continue
        top=max(av,key=lambda c:(float(c["pred_month_boundary"]),-float(c["cost_r"]),c["candidate_occurrence_key"]))
        if float(top["pred_month_boundary"])<MIN_R or top["proposed_order_type"]!="MARKET": continue
        g=getter(top["candidate_occurrence_key"])
        if g is None: active[top["symbol"]]=mn(top["expiry_utc"]); continue
        r,end,kind,hold=g
        sel.append((top["trading_day"],r,hold,kind)); active[top["symbol"]]=end
    return sel
def short_get(h):
    def f(k):
        w=W2.get(k)
        if w is None or w.get("fi") is None or not w.get(h) or w[h]["gross"] is None: return None
        return (w[h]["gross"]-w["ded"], w[h]["end"], w[h]["kind"], w[h]["end"]-w["fill_min"])
    return f
def scale_get(kk,arm):
    def f(k):
        s=SC.get(k)
        if s is None: return None
        d=s["arms"][kk].get(arm)
        if not d or d["gross"] is None: return None
        ded=SLIP+(s["ded"]-SLIP)/float(kk)
        return (d["gross"]-ded, d["end"], d["kind"], d["end"]-s["fill_min"])
    return f
def stat(sel,ref=None):
    t=defaultdict(float)
    for d,r,_,_ in sel: t[d]+=r
    days=sorted(set(list(t)+ (list(ref) if ref else [])))
    v=np.array([t.get(d,0.0) for d in days])
    bs=np.array([v[RNG.choice(len(days),len(days),True)].sum() for _ in range(3000)])
    return {"n":len(sel),"total_r":float(v.sum()),"r_per_day":float(v.mean()),
            "ci":[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
            "mean_hold_min":float(np.mean([x[2] for x in sel])),
            "kinds":dict(Counter(x[3] for x in sel))},t
out={"short":{},"scale":{}}
base=None; bt=None
for h in ["h0.125","h0.25","h0.5","h1.0","h2.0"]:
    s,t=stat(replay(short_get(h)))
    if h=="h1.0": bt=t
    out["short"][h]=s
for h in ["h0.125","h0.25","h0.5","h1.0","h2.0"]:
    pass
# deltas vs the sealed 120-min arm, paired by day
def delta(t,t0):
    days=sorted(set(list(t)+list(t0)))
    d=np.array([t.get(x,0.0)-t0.get(x,0.0) for x in days])
    bs=np.array([d[RNG.choice(len(days),len(days),True)].sum() for _ in range(3000)])
    return {"delta_total":float(d.sum()),"ci":[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
            "p":float(2*min((bs<=0).mean(),(bs>=0).mean()))}
for h in ["h0.125","h0.25","h0.5","h1.0","h2.0"]:
    s,t=stat(replay(short_get(h))); out["short"][h]={**s,**delta(t,bt)}
    print("SHORT",h,json.dumps(out["short"][h]),flush=True)
for kk in ["1.0","1.5","2.0","3.0","4.0"]:
    for arm in ["hA","hC"]:
        s,t=stat(replay(scale_get(kk,arm))); out["scale"][f"k{kk}_{arm}"]={**s,**delta(t,bt)}
        print("SCALE",kk,arm,json.dumps(out["scale"][f"k{kk}_{arm}"]),flush=True)
json.dump(out,open("SELECTED_BOOK_LEVERS.json","w"),indent=1)
