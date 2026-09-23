#!/usr/bin/env python3
"""l4 step N: the stacked owner contract — every filter is decidable AT THE DECISION INSTANT,
no look-ahead — plus the cost decomposition of the surviving book."""
import gzip, json, os, math
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_FILL_V1.jsonl.gz"),"rt") if l.strip()]
def f(x,d=0.0): return d if x is None else float(x)
def cost_passive(r,k,reason):
    sp=f(r["spread_r"])/k
    return f(r["commission_r"])+(0.5*sp+f(r["expected_slippage_r"]) if reason in ("stop","mark") else 0.0)
def blk(v,label):
    fl=[r for r in v if r["fill_bar0"] is not None and r["fill_bar0"]+1<=120]
    if not fl: return {"label":label,"n_offered":len(v),"n_trades":0}
    g=[r["fill_r"] for r in fl]; mg=sum(g)/len(g)
    sd=math.sqrt(sum((x-mg)**2 for x in g)/max(1,len(g)-1))
    nt=[r["fill_r"]-cost_passive(r,7.3,r["fill_reason"]) for r in fl]
    ntk=[r["fill_r"]-cost_passive(r,1.0,r["fill_reason"]) for r in fl]
    nf=[r["fill_r"]-f(r["cost_r"]) for r in fl]
    return {"label":label,"n_offered":len(v),"n_trades":len(fl),
        "fill_rate":round(len(fl)/len(v),5),"gross":round(mg,6),"total_gross_r":round(sum(g),1),
        "win":round(sum(1 for x in g if x>0)/len(fl),5),"t":round(mg/(sd/math.sqrt(len(fl))),3),
        "net_passive_7p3":round(sum(nt)/len(nt),6),"total_net_passive_r":round(sum(nt),1),
        "net_passive_1x":round(sum(ntk)/len(ntk),6),"net_frozen":round(sum(nf)/len(nf),6),
        "mean_commission_r":round(sum(f(r["commission_r"]) for r in fl)/len(fl),6),
        "mean_spread_r_frozen":round(sum(f(r["spread_r"]) for r in fl)/len(fl),6),
        "mean_cost_frozen":round(sum(f(r["cost_r"]) for r in fl)/len(fl),6),
        "exit_tgt":sum(1 for r in fl if r["fill_reason"]=="target"),
        "exit_stop":sum(1 for r in fl if r["fill_reason"]=="stop"),
        "exit_mark":sum(1 for r in fl if r["fill_reason"]=="mark")}
S=[]
S.append(blk(rows,"0. every candidate, owner contract"))
a=[r for r in rows if r["born"]!="past_stop"]
S.append(blk(a,"1. + drop stop-already-breached (born_past_stop)"))
b=[r for r in a if r["mkt_r_prev_close"] is not None and r["mkt_r_prev_close"]>1.0]
S.append(blk(b,"2. + only limits resting >1R from the market"))
c=[r for r in a if r["mkt_r_prev_close"] is not None and r["mkt_r_prev_close"]>2.0]
S.append(blk(c,"2b. + only limits resting >2R from the market"))
d=[r for r in c if f(r["execution_fill_probability"],1)<0.80]
S.append(blk(d,"3. + INVERT the p_fill floor (keep declared p<0.80)"))
e=[r for r in a if f(r["execution_fill_probability"],1)<0.578]
S.append(blk(e,"3b. keep declared p<0.578 (deciles 1-2) only"))
g=[r for r in a if int(r["decision_time_utc"][11:13]) in (8,10,11,16,19,21,23)]
S.append(blk(g,"4. + best-7-hours only (in-sample selected, NOT a claim)"))
h=[r for r in c if int(r["decision_time_utc"][11:13]) in (8,10,11,16,19,21,23)]
S.append(blk(h,"5. >2R AND best-7-hours (in-sample, NOT a claim)"))
print("  contract stack                                          offered  trades   gross      t   netPASS  netFROZ   totalNET")
for s in S:
    if not s.get("n_trades"): continue
    print("  %-54s %7d %7d %8.4f %6.2f %8.4f %8.4f %10.1f"%(s["label"][:54],s["n_offered"],s["n_trades"],
        s["gross"],s["t"],s["net_passive_7p3"],s["net_frozen"],s["total_net_passive_r"]))
print("\n  cost decomposition of each stage (R/trade)")
print("  stage                                                   commission  spread_froz  cost_froz")
for s in S:
    if not s.get("n_trades"): continue
    print("  %-54s %10.4f %12.4f %10.4f"%(s["label"][:54],s["mean_commission_r"],s["mean_spread_r_frozen"],s["mean_cost_frozen"]))
json.dump({"stack":S},open(os.path.join(HERE,"L4_STACK_V1.json"),"w"),indent=1)
print("\nwrote L4_STACK_V1.json")
