#!/usr/bin/env python3
"""l4 step B: adverse selection — does fill LATENCY predict outcome? Plus limit DISTANCE."""
import gzip, json, os
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_FILL_V1.jsonl.gz"),"rt") if l.strip()]
res={}
def agg(pop):
    rs=[r["fill_r"] for r in pop if r["fill_r"] is not None]
    if not rs: return {"n":0}
    ex={}
    for r in pop:
        if r["fill_r"] is not None: ex[r["fill_reason"]]=ex.get(r["fill_reason"],0)+1
    life=[r["fill_life"] for r in pop if r["fill_r"] is not None]
    return {"n":len(rs),"mean_r":round(sum(rs)/len(rs),6),"win":round(sum(1 for x in rs if x>0)/len(rs),5),
            "tgt":ex.get("target",0),"stop":ex.get("stop",0),"mark":ex.get("mark",0),
            "sum_r":round(sum(rs),2),"mean_life":round(sum(life)/len(life),1)}
BUCK=[(1,1),(2,2),(3,5),(6,10),(11,15),(16,30),(31,45),(46,60),(61,90),(91,120)]
for popname,pop in (("ALL",rows),("SANE",[r for r in rows if r["born"]!="past_stop"]),
                    ("RESTING",[r for r in rows if r["born"]=="resting"]),
                    ("AT_LIMIT",[r for r in rows if r["born"]=="at_limit"])):
    tab=[]
    for lo,hi in BUCK:
        sub=[r for r in pop if r["fill_bar0"] is not None and lo<=r["fill_bar0"]+1<=hi]
        a=agg(sub); a["bucket"]="%d-%d"%(lo,hi); tab.append(a)
    nf=[r for r in pop if r["fill_bar0"] is None]
    res["latency_"+popname]={"table":tab,"never_filled":len(nf)}
# resolved-only sensitivity (exclude trades marked at the 2h wall)
def agg_res(pop):
    rs=[r["fill_r"] for r in pop if r["fill_r"] is not None and r["fill_reason"]!="mark"]
    if not rs: return {"n":0}
    return {"n":len(rs),"mean_r":round(sum(rs)/len(rs),6),"win":round(sum(1 for x in rs if x>0)/len(rs),5)}
res["resolved_only"]={k:agg_res(v) for k,v in (("ALL",rows),("SANE",[r for r in rows if r["born"]!="past_stop"]),
                        ("RESTING",[r for r in rows if r["born"]=="resting"]))}
# limit DISTANCE from the market at decision (|mkt_r_prev_close| in R) vs fill rate & outcome
DB=[(0.0,0.0),(0.0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.5),(0.5,0.75),(0.75,1.0),(1.0,2.0),(2.0,99)]
dist=[]
rest=[r for r in rows if r["born"]=="resting"]
for lo,hi in DB:
    if lo==hi==0.0: continue
    sub=[r for r in rest if lo<r["mkt_r_prev_close"]<=hi]
    if not sub: continue
    f=[r for r in sub if r["fill_bar0"] is not None]
    fb=[r["fill_bar0"]+1 for r in f]
    a=agg(sub)
    dist.append({"dist_r":"%.2f-%.2f"%(lo,hi),"n":len(sub),"ever_fill":len(f),
                 "ever_fill_rate":round(len(f)/len(sub),5),
                 "fill_bar_median":sorted(fb)[len(fb)//2] if fb else None,
                 "fill_rate_15m":round(sum(1 for r in sub if r["fill_bar0"] is not None and r["fill_bar0"]+1<=15)/len(sub),5),
                 "fill_rate_60m":round(sum(1 for r in sub if r["fill_bar0"] is not None and r["fill_bar0"]+1<=60)/len(sub),5),
                 "mean_r_on_fill":a.get("mean_r"),"win":a.get("win"),
                 "declared_exec_fill_prob_mean":round(sum(r["execution_fill_probability"] or 0 for r in sub)/len(sub),5)})
res["distance_resting"]=dist
json.dump(res,open(os.path.join(HERE,"L4_LATENCY_V1.json"),"w"),indent=1)
for k in ("latency_SANE","latency_RESTING","latency_AT_LIMIT"):
    print("\n"+k+"  (never filled: %d)"%res[k]["never_filled"])
    print("  bucket      n   meanR    win%   tgt/stop/mark   life")
    for a in res[k]["table"]:
        if a["n"]==0: continue
        print("  %-8s %5d %8.4f %6.2f %5d/%5d/%5d %6.1f"%(a["bucket"],a["n"],a["mean_r"],100*a["win"],a["tgt"],a["stop"],a["mark"],a["mean_life"]))
print("\nRESOLVED-ONLY (drop 2h-wall marks):",json.dumps(res["resolved_only"]))
print("\nRESTING limit distance from market:")
print("  dist(R)      n  everfill%  med bar  fill15%  fill60%   meanR   win%  declared_p")
for d in dist:
    print("  %-10s %5d %8.2f %8s %8.2f %8.2f %8.4f %6.2f %8.4f"%(d["dist_r"],d["n"],100*d["ever_fill_rate"],d["fill_bar_median"],100*d["fill_rate_15m"],100*d["fill_rate_60m"],d["mean_r_on_fill"] or 0,100*(d["win"] or 0),d["declared_exec_fill_prob_mean"]))
