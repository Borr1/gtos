#!/usr/bin/env python3
"""CI on the deployable object: the selected book at each horizon."""
import gzip,pickle,json,datetime as dt
from collections import defaultdict,Counter
import numpy as np
RNG=np.random.default_rng(20260812); MIN_R=0.10
M=["feb","apr","may","jun","jul"]; HS=["h1","h2","h4","h8","hInf"]
W={}
for m in M:
    for r in pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb")): W[r["k"]]=r
rows=[]
for m in M:
    for c in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        if c.get("pred_month_boundary") is not None: rows.append(c)
EP=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
def mn(s): return int((dt.datetime.fromisoformat(str(s))-EP).total_seconds()//60)
byw=defaultdict(list)
for c in rows: byw[c["decision_window_id"]].append(c)
order=sorted(byw.values(),key=lambda v:(min(mn(x["label_span_start_utc"]) for x in v),v[0]["decision_window_id"]))
book={}
for h in HS:
    active={}; sel=[]
    for cands in order:
        at=min(mn(x["label_span_start_utc"]) for x in cands)
        active={s:e for s,e in active.items() if e>at}
        av=[c for c in cands if c["symbol"] not in active]
        if not av: continue
        top=max(av,key=lambda c:(float(c["pred_month_boundary"]),-float(c["cost_r"]),c["candidate_occurrence_key"]))
        if float(top["pred_month_boundary"])<MIN_R or top["proposed_order_type"]!="MARKET": continue
        w=W.get(top["candidate_occurrence_key"])
        if w is None or w.get("fi") is None or not w.get(h) or w[h]["gross"] is None:
            active[top["symbol"]]=mn(top["expiry_utc"]); continue
        sel.append((top["trading_day"],w[h]["gross"]-w["ded"],w[h]["end"]-w["fill_min"],w[h]["kind"]))
        active[top["symbol"]]=w[h]["end"]
    book[h]=sel
base={d:0.0 for d in {x[0] for s in book.values() for x in s}}
def daytot(sel):
    t=defaultdict(float)
    for d,r,_,_ in sel: t[d]+=r
    return t
days=sorted({x[0] for s in book.values() for x in s})
out={}
b0=daytot(book["h1"])
for h in HS:
    t=daytot(book[h])
    v=np.array([t.get(d,0.0) for d in days]); v0=np.array([b0.get(d,0.0) for d in days])
    bs=np.array([v[RNG.choice(len(days),len(days),True)].sum()*1.0 for _ in range(4000)])
    dd=v-v0
    bd=np.array([dd[RNG.choice(len(days),len(days),True)].mean()*len(days) for _ in range(4000)])
    out[h]={"n_trades":len(book[h]),"total_r":float(v.sum()),"r_per_day":float(v.mean()),
      "total_ci":[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
      "delta_total_vs_h1":float(dd.sum()),
      "delta_ci":[float(np.percentile(bd,2.5)),float(np.percentile(bd,97.5))],
      "p":float(2*min((bd<=0).mean(),(bd>=0).mean())),"active_days":int((v!=0).sum()),
      "mean_hold_min":float(np.mean([x[2] for x in book[h]])),
      "kinds":dict(Counter(x[3] for x in book[h]))}
    print(h,json.dumps(out[h]),flush=True)
json.dump({"days":len(days),"book":out},open("SELECTOR_BOOT.json","w"),indent=1)
