#!/usr/bin/env python3
"""l4 step L: honest search for a positive corner of the OWNER'S contract.
Fill-honest, T=+2R, S=-1R, cancel window 120 (the engine's own pending expiry),
SANE population (born_past_stop dropped), net of the passive cost model."""
import gzip, json, os, math
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_FILL_V1.jsonl.gz"),"rt") if l.strip()]
def f(x,d=0.0): return d if x is None else float(x)
def cost_passive(r,k,reason):
    sp=f(r["spread_r"])/k
    return f(r["commission_r"]) + (0.5*sp+f(r["expected_slippage_r"]) if reason in ("stop","mark") else 0.0)
sane=[r for r in rows if r["born"]!="past_stop" and r["fill_bar0"] is not None and r["fill_bar0"]+1<=120]
for r in sane:
    r["_hour"]=int(r["decision_time_utc"][11:13])
    r["_net"]=r["fill_r"]-cost_passive(r,7.3,r["fill_reason"])
    m=r["mkt_r_prev_close"]
    r["_dist"]=("at_or_through" if m is None or m<=1e-12 else
                "0-0.5R" if m<=0.5 else "0.5-1R" if m<=1.0 else "1-2R" if m<=2.0 else ">2R")
def cells(keyf,minn):
    g={}
    for r in sane: g.setdefault(keyf(r),[]).append(r)
    out=[]
    for k,v in g.items():
        if len(v)<minn: continue
        gr=[x["fill_r"] for x in v]; nt=[x["_net"] for x in v]
        mg=sum(gr)/len(gr); sd=math.sqrt(sum((x-mg)**2 for x in gr)/max(1,len(gr)-1))
        out.append({"key":str(k),"n":len(v),"gross":round(mg,6),"net":round(sum(nt)/len(nt),6),
                    "total_gross":round(sum(gr),1),"win":round(sum(1 for x in gr if x>0)/len(v),5),
                    "t_stat":round(mg/(sd/math.sqrt(len(v))),3) if sd>0 else None})
    return sorted(out,key=lambda d:-d["gross"])
res={"population":"SANE fill-honest T2 S-1 W120","n":len(sane),
     "pool_gross":round(sum(r["fill_r"] for r in sane)/len(sane),6),
     "pool_net_passive7p3":round(sum(r["_net"] for r in sane)/len(sane),6)}
cuts={"by_hour":(lambda r:r["_hour"],200),
      "by_distance":(lambda r:r["_dist"],200),
      "by_family_x_dist":(lambda r:(r["origin_family"],r["_dist"]),150),
      "by_symbol_x_hour":(lambda r:(r["symbol"],r["_hour"]),60),
      "by_family_x_hour":(lambda r:(r["origin_family"],r["_hour"]),100),
      "by_side":(lambda r:r["side"],200),
      "by_fillreason":(lambda r:r["fill_reason"],10),
      "by_dupe":(lambda r:"first_emission" if r["is_first_emission"] else "repeat",200)}
for name,(kf,mn) in cuts.items():
    res[name]=cells(kf,mn)
print("OWNER CONTRACT, SANE, n=%d  gross %.4f  net(passive 7.3x) %.4f"%(len(sane),res["pool_gross"],res["pool_net_passive7p3"]))
for name in ("by_distance","by_side","by_dupe","by_hour"):
    print("\n%s"%name)
    print("  key                 n      gross      net     win%    t")
    for d in res[name]:
        print("  %-16s %6d %9.4f %8.4f %6.2f %6s"%(d["key"][:16],d["n"],d["gross"],d["net"],100*d["win"],d["t_stat"]))
for name in ("by_family_x_dist","by_family_x_hour","by_symbol_x_hour"):
    pos=[d for d in res[name] if d["gross"]>0]
    tot=len(res[name]); npos_net=len([d for d in res[name] if d["net"]>0])
    res[name+"_summary"]={"cells":tot,"positive_gross":len(pos),"positive_net":npos_net,
        "n_in_positive":sum(d["n"] for d in pos)}
    print("\n%s: %d cells, %d gross-positive (%d net-positive). TOP 6:"%(name,tot,len(pos),npos_net))
    for d in res[name][:6]:
        print("   %-34s n=%5d gross %8.4f net %8.4f win %5.2f t=%s"%(d["key"][:34],d["n"],d["gross"],d["net"],100*d["win"],d["t_stat"]))
json.dump(res,open(os.path.join(HERE,"L4_SEARCH_V1.json"),"w"),indent=1)
print("\nwrote L4_SEARCH_V1.json")
