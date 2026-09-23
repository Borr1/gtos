"""Decision-time-only filters: born_resting x cost/geometry sanity.  Everything used here is
knowable BEFORE the trade (market price at decision, emitted geometry, frozen cost estimate)."""
import sys,os,json,gzip
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
rows=w0_ws.load(); byk={w0_ws.key(r):r for r in rows}
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bornof(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
recs=[]
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"]); r=byk.get(k); a=anch.get(k)
    if r is None or a is None: continue
    fav,adv=rp["fav"],rp["adv"]; tgt=rp.get("policy_target_r") or 2.0
    fb=next((i for i in range(len(adv)) if adv[i]<=0.0),None)
    if fb is None: continue
    xr=None
    for i in range(fb,len(fav)):
        ht=fav[i]>=tgt; hs=adv[i]<=-1.0
        if ht and hs: xr=-1.0;break
        if ht: xr=tgt;break
        if hs: xr=-1.0;break
    if xr is None: xr=max(-1.0,min(rp["cls"][-1],tgt))
    recs.append({"bs":bornof(a["mkt_r_close"]),"r":xr,"eng":r.get("gross_r"),
        "cost":r.get("expected_cost_r") or 0.0,"sp":r.get("spread_r") or 0.0,
        "rd":(r["risk_distance"]/r["entry_price"]*100.0) if r.get("entry_price") else None,
        "m":a["mkt_r_close"],"fam":r.get("origin_family"),"sym":r["symbol"],
        "cid":rp["candidate_id"],"dt":rp["decision_time_utc"]})
def bk(sel,div=7.3):
    if not sel: return None
    g=sum(x["r"] for x in sel)/len(sel)
    net=sum(x["r"]-(x["cost"]-x["sp"]+x["sp"]/div) for x in sel)/len(sel)
    netf=sum(x["r"]-x["cost"] for x in sel)/len(sel)
    w=[x for x in sel if x["r"]>0]
    return {"n":len(sel),"gross":round(g,5),"net_frozen":round(netf,5),"net_div7.3":round(net,5),
            "win_pct":round(100*len(w)/len(sel),3),"total_R_gross":round(sum(x['r'] for x in sel),1)}
res={"universe_filled_n":len(recs),"ALL_FILLED":bk(recs)}
BR=[x for x in recs if x["bs"]=="born_resting"]
res["BORN_RESTING"]=bk(BR)
# 1D sweeps on born_resting
res["sweep_cost_r_max"]={str(t):bk([x for x in BR if x["cost"]<=t]) for t in (5,2,1,0.6,0.4,0.3,0.25,0.2,0.15,0.1,0.05)}
res["sweep_spread_r_max"]={str(t):bk([x for x in BR if x["sp"]<=t]) for t in (5,1,0.5,0.3,0.2,0.15,0.1,0.05,0.03)}
res["sweep_risk_distance_pct_min"]={str(t):bk([x for x in BR if x["rd"] is not None and x["rd"]>=t]) for t in (0,0.02,0.05,0.08,0.1,0.15,0.2,0.3)}
# same sweeps on the WHOLE filled pool, to show born_resting is not redundant with cost
res["sweep_cost_r_max_ALL"]={str(t):bk([x for x in recs if x["cost"]<=t]) for t in (1,0.4,0.25,0.15,0.1)}
# 2D: born_resting x cost
res["joint_born_resting_x_cost"]={str(t):bk([x for x in BR if x["cost"]<=t]) for t in (0.4,0.25,0.15)}
# how far into the money does 'marketable' have to be before it hurts?
bands=[(-99,-3),(-3,-1),(-1,-0.5),(-0.5,-0.25),(-0.25,-0.1),(-0.1,-0.001),(-0.001,0.001),
       (0.001,0.1),(0.1,0.25),(0.25,0.5),(0.5,1),(1,2),(2,99)]
res["book_by_mkt_r_band_at_decision"]={f"{a}..{b}":bk([x for x in recs if a<x["m"]<=b]) for a,b in bands}
with open(os.path.join(D,"W0CAP2_SWEEP_V1.json"),"w") as f: json.dump(res,f,indent=1)
print("ALL_FILLED",res["ALL_FILLED"]); print("BORN_RESTING",res["BORN_RESTING"])
print("-- cost sweep on born_resting --")
for t,v in res["sweep_cost_r_max"].items():
    if v: print(f'  cost<={t:>5s} n{v["n"]:6d} gross{v["gross"]:+8.4f} netfz{v["net_frozen"]:+8.4f} net7.3{v["net_div7.3"]:+8.4f} win{v["win_pct"]:5.1f}%')
print("-- cost sweep on ALL filled (no born filter) --")
for t,v in res["sweep_cost_r_max_ALL"].items():
    if v: print(f'  cost<={t:>5s} n{v["n"]:6d} gross{v["gross"]:+8.4f} netfz{v["net_frozen"]:+8.4f} net7.3{v["net_div7.3"]:+8.4f} win{v["win_pct"]:5.1f}%')
print("-- book by mkt_r band at decision --")
for t,v in res["book_by_mkt_r_band_at_decision"].items():
    if v: print(f'  {t:>14s} n{v["n"]:6d} gross{v["gross"]:+8.4f} win{v["win_pct"]:5.1f}%')
