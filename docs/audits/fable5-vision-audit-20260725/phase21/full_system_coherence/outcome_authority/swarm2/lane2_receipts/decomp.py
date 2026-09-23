#!/usr/bin/env python3
"""Why the pool loses: barrier geometry, the spread handicap, and residual drift.

Fair game: a driftless process started at the executable entry quote hits the target
before the stop with probability a/(a+b), a and b the two barrier distances measured
from that quote. Crossing the spread at entry moves the START, not the barriers:
a -> a - s, b -> b + s, with s = spread/stop_distance = the corpus `spread_r`
(src/costs/model.py:1334 -- "price / stop, one crossing").
"""
import gzip, json, pickle
from collections import defaultdict
import numpy as np

MONTHS=["feb","apr","may","jun","jul"]
recs=[]; 
for m in MONTHS: recs.extend(pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb")))
geom={}
for m in MONTHS:
    with gzip.open(f"geom_{m}.jsonl.gz","rt") as fh:
        for line in fh:
            r=json.loads(line); geom[r["k"]]=r
cache={}
for m in MONTHS:
    for row in pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb")):
        cache[row["candidate_occurrence_key"]]=row

rows=[]
for r in recs:
    if r.get("fi") is None or r["H1"]<=0 or r.get("err"): continue
    if any((r.get(h) or {}).get("kind") in (None,"CENSOR") for h in ["h1","h2","h4","h8","hInf"]): continue
    g=geom[r["k"]]; c=cache[r["k"]]
    d=1 if str(g["side"]).upper()=="LONG" else -1
    entry=float(g["entry_price"]); stop=float(g["stop_loss"]); target=float(g["take_profit_1"])
    risk=abs(entry-stop); fp=r["fp"]
    s=float(c.get("spread_r") or 0.0)
    a=d*(fp-stop)/risk          # adverse distance from the FILL (entry-side) quote, in R
    b=d*(target-fp)/risk        # favourable distance from the same quote, in R
    rows.append(dict(k=r["k"],fam=r["fam"],ot=r["ot"],month=r["month"],day=r["day"],
        a=a,b=b,s=s,tR=d*(target-entry)/risk,ded=r["ded"],
        g1=r["h1"]["gross"],gI=r["hInf"]["gross"],
        k1=r["h1"]["kind"],kI=r["hInf"]["kind"]))
print("n",len(rows),flush=True)
A=np.array([x["a"] for x in rows]); B=np.array([x["b"] for x in rows]); S=np.array([x["s"] for x in rows])
TR=np.array([x["tR"] for x in rows]); DED=np.array([x["ded"] for x in rows])
G1=np.array([x["g1"] for x in rows]); GI=np.array([x["gI"] for x in rows])
hitI=np.array([x["kI"]=="TARGET" for x in rows]); res=np.array([x["kI"] in ("TARGET","STOP") for x in rows])

p_nospread=A/(A+B)                       # fair game measured from the fill quote
p_spread=(A-S)/(A+B)                     # same barriers, start moved by one crossing
# fair-game gross EV in R (payoffs +b at target, -a at stop, from the fill quote)
ev_nospread=p_nospread*B-(1-p_nospread)*A
ev_spread=p_spread*(B+S)-(1-p_spread)*(A-S)
out={"n":len(rows),
 "geometry":{"mean_a":float(A.mean()),"mean_b":float(B.mean()),"mean_target_R":float(TR.mean()),
   "median_target_R":float(np.median(TR)),"mean_spread_r":float(S.mean()),"median_spread_r":float(np.median(S)),
   "mean_deductible_r":float(DED.mean())},
 "hit_rate":{"realized_unbounded":float(hitI[res].mean()),"n_resolved":int(res.sum()),
   "fair_no_spread":float(p_nospread.mean()),"fair_with_spread":float(p_spread.mean()),
   "shortfall_vs_fair_with_spread_pp":float(100*(hitI[res].mean()-p_spread[res].mean()))},
 "gross_ev":{"realized_1x":float(G1.mean()),"realized_unbounded":float(GI.mean()),
   "fair_no_spread":float(ev_nospread.mean()),"fair_with_spread":float(ev_spread.mean())},
 "net_ev":{"realized_1x":float((G1-DED).mean()),"realized_unbounded":float((GI-DED).mean())},
 "attribution_r_per_trade":{
   "fair_game_zero":0.0,
   "spread_crossing":float(ev_spread.mean()-ev_nospread.mean()),
   "residual_adverse_drift":float(GI.mean()-ev_spread.mean()),
   "other_deductibles_slippage_swap_commission":float(-DED.mean()),
   "total_net_unbounded":float((GI-DED).mean())}}
byfam={}
for fam in sorted({x["fam"] for x in rows}):
    idx=np.array([x["fam"]==fam for x in rows])
    r2=res&idx
    byfam[fam]={"n":int(idx.sum()),"mean_target_R":float(TR[idx].mean()),"mean_spread_r":float(S[idx].mean()),
      "realized_hit":float(hitI[r2].mean()),"fair_with_spread":float(p_spread[r2].mean()),
      "shortfall_pp":float(100*(hitI[r2].mean()-p_spread[r2].mean())),
      "gross_unbounded":float(GI[idx].mean()),"fair_gross":float(ev_spread[idx].mean()),
      "net_unbounded":float((GI-DED)[idx].mean()),"ded":float(DED[idx].mean())}
out["by_family"]=byfam
json.dump(out,open("DECOMP.json","w"),indent=1)
print(json.dumps({k:v for k,v in out.items() if k!="by_family"},indent=1))
print("\n%-34s %6s %7s %8s %8s %8s %8s %8s %8s"%("family","n","tgtR","spr_r","hit","fair","shortpp","grossInf","netInf"))
for f,v in sorted(byfam.items(),key=lambda kv:-kv[1]["shortfall_pp"]):
    print("%-34s %6d %7.3f %8.4f %8.4f %8.4f %+8.2f %+8.4f %+8.4f"%(f,v["n"],v["mean_target_R"],v["mean_spread_r"],v["realized_hit"],v["fair_with_spread"],v["shortfall_pp"],v["gross_unbounded"],v["net_unbounded"]))
