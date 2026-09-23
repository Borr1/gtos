#!/usr/bin/env python3
"""l4 step M: what the FILL-PROBABILITY FLOOR removes.
The declared execution_fill_probability is a monotone DECREASING function of the limit's
distance from the market (poi_execution_lifecycle.py:178-181), and distance is the one
monotone predictor of trade quality under the owner's contract. So a floor on it removes
the best cohort. Sweeps the configured floors."""
import gzip, json, os, math
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_FILL_V1.jsonl.gz"),"rt") if l.strip()]
def f(x,d=0.0): return d if x is None else float(x)
def cost_passive(r,k,reason):
    sp=f(r["spread_r"])/k
    return f(r["commission_r"])+(0.5*sp+f(r["expected_slippage_r"]) if reason in ("stop","mark") else 0.0)
sane=[r for r in rows if r["born"]!="past_stop" and r["fill_bar0"] is not None and r["fill_bar0"]+1<=120
      and r["execution_fill_probability"] is not None]
for r in sane: r["_net"]=r["fill_r"]-cost_passive(r,7.3,r["fill_reason"])
def blk(v):
    if not v: return None
    g=[x["fill_r"] for x in v]; n=[x["_net"] for x in v]
    mg=sum(g)/len(g); sd=math.sqrt(sum((x-mg)**2 for x in g)/max(1,len(g)-1))
    return {"n":len(v),"gross":round(mg,6),"net":round(sum(n)/len(n),6),"total_gross":round(sum(g),1),
            "win":round(sum(1 for x in g if x>0)/len(v),5),"t":round(mg/(sd/math.sqrt(len(v))),3) if sd>0 else None,
            "mean_declared_p":round(sum(f(x["execution_fill_probability"]) for x in v)/len(v),4),
            "measured_fill_within_120":1.0}
res={"n_sane_filled":len(sane),"floors":[]}
CONFIG_FLOORS=[("selector_v4_calibrated_min_fill_probability",0.45,"config/agent_config.yaml:811"),
    ("scheduler_v4_best_trade_allocator_dynamic_budget_min_fill_probability",0.80,"config/agent_config.yaml:1002"),
    ("scheduler_v4_..._selector_reduce_risk_new_entry_min_fill_probability",0.80,"config/agent_config.yaml:1016"),
    ("ultimate_candidate_package_..._off_session_min_fill_probability",0.70,"config/agent_config.yaml:794"),
    ("ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability",0.25,"config/agent_config.yaml:798"),
    ("ultimate_candidate_package_strong_fill_floor_bypass_min_execution_fill_probability",0.35,"config/agent_config.yaml:801")]
seen=set()
for name,thr,cite in CONFIG_FLOORS:
    if thr in seen: 
        res["floors"].append({"key":name,"threshold":thr,"cite":cite,"same_as_above":True}); continue
    seen.add(thr)
    keep=[r for r in sane if f(r["execution_fill_probability"])>=thr]
    drop=[r for r in sane if f(r["execution_fill_probability"])<thr]
    res["floors"].append({"key":name,"threshold":thr,"cite":cite,"kept":blk(keep),"dropped":blk(drop),
        "delta_gross_from_gating":round((blk(keep)["gross"]-blk(sane)["gross"]),6) if keep else None})
res["ungated"]=blk(sane)
print("UNGATED (SANE, filled, owner contract): n=%d gross %.4f net %.4f win %.2f%%"%(
    res["ungated"]["n"],res["ungated"]["gross"],res["ungated"]["net"],100*res["ungated"]["win"]))
print("\n  floor   n_kept    gross_kept  net_kept | n_dropped  gross_dropped  net_dropped |  effect of gating")
for d in res["floors"]:
    if d.get("same_as_above"): continue
    k=d["kept"]; dr=d["dropped"]
    print("  %5.2f %7d %11.4f %9.4f | %8d %13.4f %11.4f | %+.4f  (%s)"%(
        d["threshold"],k["n"],k["gross"],k["net"],dr["n"],dr["gross"],dr["net"],d["delta_gross_from_gating"],d["cite"].split("/")[-1]))
# decile view
sd=sorted(sane,key=lambda r:f(r["execution_fill_probability"]))
dec=[]
for i in range(10):
    v=sd[i*len(sd)//10:(i+1)*len(sd)//10]
    b=blk(v); b["decile"]=i+1
    b["p_range"]=[round(f(v[0]["execution_fill_probability"]),4),round(f(v[-1]["execution_fill_probability"]),4)]
    dec.append(b)
res["deciles_by_declared_p"]=dec
print("\n  DECILE OF DECLARED FILL PROBABILITY (1 = lowest declared p)")
print("  dec   p_range           n     gross      net     win%      t")
for b in dec:
    print("  %3d  %5.3f-%5.3f %6d %9.4f %8.4f %6.2f %7s"%(b["decile"],b["p_range"][0],b["p_range"][1],b["n"],b["gross"],b["net"],100*b["win"],b["t"]))
json.dump(res,open(os.path.join(HERE,"L4_GATE_V1.json"),"w"),indent=1)
print("\nwrote L4_GATE_V1.json")
