#!/usr/bin/env python3
"""l4 step D: four contracts side by side, net-of-cost under an explicit passive cost model,
and the per-family / per-symbol / per-session cut. Window = the engine's own pending expiry
(REPAIRED_PENDING_EXPIRY_MINUTES = 120, v4_timewarp_simulated_live_research_loop.py:378)."""
import gzip, json, os
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_FILL_V1.jsonl.gz"),"rt") if l.strip()]

def f(x,d=0.0):
    return d if x is None else float(x)

# ------- cost models -------------------------------------------------------
# frozen: cost_r as the engine charged it (spread_r + commission_r + slippage + swap)
# passive_k: a resting limit provides liquidity on ENTRY and (when it exits at its own
#   take-profit limit) on EXIT too.  It crosses only when the exit is a market order
#   (stop or the 2h mark).  spread_r is ONE FULL spread (broker_net_cost_engine.py:302
#   spread_r = spread_price / sl_distance), so one crossing = 0.5 * spread_r.
#   k divides spread_r by the measured over-charge factor (7.3 - 8.5x).
def cost_frozen(r): return f(r["cost_r"])
def cost_passive(r, k, reason):
    sp = f(r["spread_r"])/k
    crosses = 0.5*sp + f(r["expected_slippage_r"]) if reason in ("stop","mark") else 0.0
    return f(r["commission_r"]) + crosses          # swap = 0: every trade is <= 2 h
def cost_taker(r, k, reason):
    sp = f(r["spread_r"])/k
    return f(r["commission_r"]) + sp + f(r["expected_slippage_r"])   # cross both sides

W=120
def contract_rows(pop, which):
    """-> list of (r_gross, reason, row) for trades that EXIST under the contract."""
    out=[]
    for r in pop:
        if which=="a_blind":
            out.append((r["blind_r"], r["blind_reason"], r))
        elif which=="b_owner":
            if r["fill_bar0"] is not None and r["fill_bar0"]+1<=W:
                out.append((r["fill_r"], r["fill_reason"], r))
        elif which=="c_chase":
            if r["chase_r_samesize"] is not None:
                out.append((r["chase_r_samesize"], r["chase_reason"], r))
        elif which=="c_chase_rn":
            if r["chase_r_risknorm"] is not None:
                out.append((r["chase_r_risknorm"], r["chase_reason"], r))
        elif which=="d_frozen":
            out.append((r["gross_r"], "pool", r))
    return out

def book(pop, which, n_offered):
    tr=contract_rows(pop,which)
    if not tr: return {"n":0}
    g=[x for x,_,_ in tr]
    n=len(g); s=sum(g)
    ex={}
    for _,rs,_ in tr: ex[rs]=ex.get(rs,0)+1
    d={"n_offered":n_offered,"n_trades":n,"take_rate":round(n/n_offered,5),
       "gross_r_per_trade":round(s/n,6),"gross_total_r":round(s,2),
       "gross_r_per_offered":round(s/n_offered,6),
       "win":round(sum(1 for x in g if x>0)/n,5),
       "exits":{k:v for k,v in sorted(ex.items())}}
    for label,fn in (("net_frozen",lambda r,rs: cost_frozen(r)),
                     ("net_passive_1x",lambda r,rs: cost_passive(r,1.0,rs)),
                     ("net_passive_7p3x",lambda r,rs: cost_passive(r,7.3,rs)),
                     ("net_passive_8p5x",lambda r,rs: cost_passive(r,8.5,rs)),
                     ("net_taker_7p3x",lambda r,rs: cost_taker(r,7.3,rs))):
        tot=sum(x-fn(r,rs) for x,rs,r in tr)
        d[label+"_per_trade"]=round(tot/n,6); d[label+"_total"]=round(tot,2)
        d[label+"_per_offered"]=round(tot/n_offered,6)
    d["mean_cost_frozen"]=round(sum(cost_frozen(r) for _,_,r in tr)/n,6)
    d["mean_cost_passive_7p3x"]=round(sum(cost_passive(r,7.3,rs) for _,rs,r in tr)/n,6)
    return d

res={"window_bars":W,"window_source":"REPAIRED_PENDING_EXPIRY_MINUTES=120 (v4_timewarp_simulated_live_research_loop.py:378)"}
pops={"ALL":rows,"SANE":[r for r in rows if r["born"]!="past_stop"],
      "RESTING":[r for r in rows if r["born"]=="resting"]}
for pname,pop in pops.items():
    res["contracts_"+pname]={w:book(pop,w,len(pop)) for w in
        ("a_blind","b_owner","c_chase","c_chase_rn","d_frozen")}

# ------- per family / symbol / session, owner contract -----------------------
def cut(pop,keyf,minn=30):
    g={}
    for r in pop: g.setdefault(keyf(r),[]).append(r)
    out=[]
    for k,v in g.items():
        if len(v)<minn: continue
        fl=[r for r in v if r["fill_bar0"] is not None and r["fill_bar0"]+1<=W]
        f15=[r for r in v if r["fill_bar0"] is not None and r["fill_bar0"]+1<=15]
        f60=[r for r in v if r["fill_bar0"] is not None and r["fill_bar0"]+1<=60]
        if not fl: continue
        rs=[r["fill_r"] for r in fl]
        blind=[r["blind_r"] for r in v]
        netp=[r["fill_r"]-cost_passive(r,7.3,r["fill_reason"]) for r in fl]
        out.append({"key":k,"n_offered":len(v),"n_filled":len(fl),
            "fill_rate_120":round(len(fl)/len(v),5),"fill_rate_15":round(len(f15)/len(v),5),
            "fill_rate_60":round(len(f60)/len(v),5),
            "declared_p_mean":round(sum(f(r["execution_fill_probability"]) for r in v)/len(v),5),
            "owner_gross_r":round(sum(rs)/len(rs),6),"owner_total_r":round(sum(rs),1),
            "owner_net_passive_7p3x":round(sum(netp)/len(netp),6),
            "owner_win":round(sum(1 for x in rs if x>0)/len(rs),5),
            "blind_gross_r":round(sum(blind)/len(blind),6),
            "pool_gross_r":round(sum(r["gross_r"] for r in v)/len(v),6),
            "fill_bias_r":round(sum(rs)/len(rs)-sum(blind)/len(blind),6)})
    return sorted(out,key=lambda d:-d["owner_gross_r"])
sane=pops["SANE"]
res["by_family_SANE"]=cut(sane,lambda r:r["origin_family"])
res["by_symbol_SANE"]=cut(sane,lambda r:r["symbol"])
res["by_session_SANE"]=cut(sane,lambda r:r["session_bucket"] or "none")
res["by_family_ALL"]=cut(rows,lambda r:r["origin_family"])
json.dump(res,open(os.path.join(HERE,"L4_CONTRACTS_V1.json"),"w"),indent=1)

for pname in ("ALL","SANE","RESTING"):
    print("\n=== POP %s (offered %d) ==="%(pname,len(pops[pname])))
    print("  contract        n     take%   grossR/tr  netFROZEN  netPASS7.3  netTAKER7.3   win%")
    for w in ("a_blind","b_owner","c_chase","c_chase_rn","d_frozen"):
        d=res["contracts_"+pname][w]
        if not d.get("n_trades"): continue
        print("  %-12s %6d %7.2f %10.4f %10.4f %11.4f %12.4f %6.2f"%(w,d["n_trades"],100*d["take_rate"],
              d["gross_r_per_trade"],d["net_frozen_per_trade"],d["net_passive_7p3x_per_trade"],
              d["net_taker_7p3x_per_trade"],100*d["win"]))
print("\nBY FAMILY (SANE, owner contract W=120)")
print("  family                          off  fill%  declP  ownerGross  ownerNet7.3  blind   fillbias  win%")
for d in res["by_family_SANE"]:
    print("  %-28s %6d %6.1f %6.3f %10.4f %11.4f %8.4f %9.4f %5.1f"%(d["key"][:28],d["n_offered"],100*d["fill_rate_120"],
        d["declared_p_mean"],d["owner_gross_r"],d["owner_net_passive_7p3x"],d["blind_gross_r"],d["fill_bias_r"],100*d["owner_win"]))
