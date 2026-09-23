#!/usr/bin/env python3
"""l4 step C: the implementable policy grid.

   PLACEMENT DELAY k0 : the signal fires at T; the limit is PLACED at T+k0 minutes.
                        A fill can only happen at a bar >= k0.  (Implementable: you
                        simply do not have an order working before then.)
   CANCEL WINDOW  W   : if unfilled by bar W it is cancelled and the trade never exists.

   Walks from the fill bar, target +2R, stop -1R, conservative same-bar tie -> stop,
   mark to market at the 2h wall.  Emits per-cell book stats and a per-candidate cell
   dump for the best cells so downstream lanes can re-slice without re-walking.
"""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws

K0=[0,1,2,3,5,10,15,20,30,45,60]
WW=[15,30,60,90,120]

meta={}
for r in w0_ws.iter_rows():
    meta[(r["candidate_id"],r["decision_time_utc"])]=(r["origin_family"],r["symbol"],r["session_bucket"])
anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")

def born(m):
    if m is None: return "unknown"
    if m<=-1+1e-12: return "past_stop"
    if m<-1e-12: return "marketable"
    if m<=1e-12: return "at_limit"
    return "resting"

cells={}   # (k0,W,pop) -> accumulators
POPS=("ALL","SANE","RESTING")
for k0 in K0:
    for W in WW:
        for p in POPS:
            cells[(k0,W,p)]={"n_off":0,"n_fill":0,"sum":0.0,"win":0,"tgt":0,"stop":0,"mark":0,"life":0}

per_cand_best={}
n=0
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]
    nb=len(fav)
    m=anch.get(k); b=born(m)
    pops=["ALL"]+(["SANE"] if b!="past_stop" else [])+(["RESTING"] if b=="resting" else [])
    for k0 in K0:
        fb=None
        for i in range(k0,nb):
            if adv[i]<=1e-12: fb=i; break
        if fb is None:
            for W in WW:
                for p in pops: cells[(k0,W,p)]["n_off"]+=1
            continue
        # walk once from fb
        r=None;reason=None
        for i in range(fb,nb):
            if adv[i]<=-1.0+1e-12: r=-1.0;reason="stop";break
            if fav[i]>=2.0-1e-12: r=2.0;reason="target";break
        if r is None: r=cls[nb-1];reason="mark"
        rk={"target":"tgt","stop":"stop","mark":"mark"}[reason]
        life=nb-fb
        for W in WW:
            ok=(fb+1)<=W
            for p in pops:
                c=cells[(k0,W,p)]; c["n_off"]+=1
                if ok:
                    c["n_fill"]+=1; c["sum"]+=r; c["life"]+=life
                    if r>0: c["win"]+=1
                    c[rk]+=1
        if k0 in (0,15,30) :
            per_cand_best.setdefault(k0,{})[ "%s|%s"%k ]=(fb+1,round(r,4),reason,b)
    n+=1

out={"K0":K0,"W":WW,"grid":[]}
for (k0,W,p),c in sorted(cells.items()):
    if c["n_fill"]==0: continue
    out["grid"].append({"k0":k0,"W":W,"pop":p,"n_offered":c["n_off"],"n_filled":c["n_fill"],
        "fill_rate":round(c["n_fill"]/c["n_off"],5),"r_per_trade":round(c["sum"]/c["n_fill"],6),
        "total_r":round(c["sum"],2),"win":round(c["win"]/c["n_fill"],5),
        "tgt":c["tgt"],"stop":c["stop"],"mark":c["mark"],"mean_life":round(c["life"]/c["n_fill"],2),
        "r_per_offered":round(c["sum"]/c["n_off"],6)})
json.dump(out,open(os.path.join(HERE,"L4_GRID_V1.json"),"w"),indent=1)
json.dump({str(k):v for k,v in per_cand_best.items()},gzip.open(os.path.join(HERE,"L4_GRID_PERCAND_V1.json.gz"),"wt"))
for p in POPS:
    print("\nPOP=%s   rows=r_per_trade (n_filled)"%p)
    print("  k0\\W   "+"".join("%18d"%W for W in WW))
    for k0 in K0:
        line="  %3d   "%k0
        for W in WW:
            g=[x for x in out["grid"] if x["k0"]==k0 and x["W"]==W and x["pop"]==p]
            line+= "%10.4f(%6d)"%(g[0]["r_per_trade"],g[0]["n_filled"]) if g else "%18s"%"-"
        print(line)
print("\nrows processed",n)
