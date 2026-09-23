"""Harden the born-state split: coherence, the engine guard's miss rate, phantom-winner
contribution, fill rates, per-family / per-symbol.  All decision-time information only."""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws
rows = w0_ws.load()
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a
fillcls = {}
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"]); fav, adv = rp["fav"], rp["adv"]
    t = next((i for i in range(len(adv)) if adv[i] <= 0.0), None)
    fillcls[k] = ("never", None, None) if t is None else (
        ("untakeable" if fav[t] <= -1.0 else ("gap" if fav[t] < 0.0 else "clean")), fav[t], t + 1)

def born(m): return "born_past_stop" if m <= -1.0 else ("born_marketable" if m < 0.0 else ("born_at_limit" if m == 0.0 else "born_resting"))
def pct(a,b): return round(100.0*a/b,4) if b else None
def mean(v): 
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],4)

REC=[]
for r in rows:
    k=w0_ws.key(r); a=anch.get(k)
    if a is None: continue
    fc,fat,bt = fillcls.get(k,("?",None,None))
    REC.append({"r":r,"m":a["mkt_r_close"],"bs":born(a["mkt_r_close"]),"fc":fc,"bt":bt,
                "g":r.get("gross_r"),"c":r.get("expected_cost_r") if r.get("expected_cost_r") is not None else r.get("cost_r")})
res={"n":len(REC)}

# 1. the engine's own guard vs the measured truth
g={}
for e in REC:
    g.setdefault(str(e["r"].get("limit_marketable_at_decision")),{}).setdefault(e["bs"],0)
    g[str(e["r"].get("limit_marketable_at_decision"))][e["bs"]]+=1
res["engine_flag_vs_measured_born_state"]=g
truly=[e for e in REC if e["m"]<0.0]
flagT=[e for e in truly if e["r"].get("limit_marketable_at_decision") is True]
res["GUARD_MISS"]={"truly_marketable_at_decision_n":len(truly),
                   "share_of_pool_pct":pct(len(truly),len(REC)),
                   "flag_True_n":len(flagT),
                   "guard_recall_pct":pct(len(flagT),len(truly)),
                   "guard_miss_n":len(truly)-len(flagT),
                   "guard_miss_pct":pct(len(truly)-len(flagT),len(truly))}

# 2. coherence: how quickly does the entry get touched, by born state
for bs in ("born_resting","born_at_limit","born_marketable","born_past_stop"):
    sub=[e for e in REC if e["bs"]==bs]
    bts=[e["bt"] for e in sub if e["bt"] is not None]
    res.setdefault("coherence",{})[bs]={"n":len(sub),
        "touch_at_bar1_pct":pct(sum(1 for b in bts if b==1),len(bts)),
        "never_touched_n":sum(1 for e in sub if e["bt"] is None),
        "median_bars_to_touch":q(bts,.5),
        "mkt_r_median":q([e["m"] for e in sub],.5),
        "mkt_r_p25":q([e["m"] for e in sub],.25),
        "fill_class_mix":{fc:sum(1 for e in sub if e["fc"]==fc) for fc in ("clean","gap","untakeable","never")}}

# 3. born_resting book, with and without phantom winners; and cost
BR=[e for e in REC if e["bs"]=="born_resting"]
ph=[e for e in BR if e["fc"]=="never"]
filled=[e for e in BR if e["fc"]!="never"]
res["BORN_RESTING_BOOK"]={
 "n":len(BR),"engine_gross_r":mean([e["g"] for e in BR]),
 "win_pct":pct(sum(1 for e in BR if e["g"] and e["g"]>0),len(BR)),
 "phantom_never_touched_n":len(ph),"phantom_gross_r":mean([e["g"] for e in ph]),
 "phantom_contribution_r_per_pool_trade":round(sum(e["g"] for e in ph if e["g"] is not None)/len(BR),5),
 "filled_only_n":len(filled),"filled_only_gross_r":mean([e["g"] for e in filled]),
 "filled_only_win_pct":pct(sum(1 for e in filled if e["g"] and e["g"]>0),len(filled)),
 "strict_unfilled_as_zero_gross_r":round(sum(e["g"] for e in filled if e["g"] is not None)/len(BR),5),
 "mean_frozen_cost_r":mean([e["c"] for e in BR]),
 "fill_rate_pct":pct(len(filled),len(BR)),
}
# 4. pool decomposition: contribution of each born state to the -0.2175
res["POOL_DECOMPOSITION_R_PER_POOL_TRADE"]={
  bs: round(sum(e["g"] for e in REC if e["bs"]==bs and e["g"] is not None)/len(REC),5)
  for bs in ("born_resting","born_at_limit","born_marketable","born_past_stop")}
res["POOL_DECOMPOSITION_R_PER_POOL_TRADE"]["TOTAL"]=round(sum(e["g"] for e in REC if e["g"] is not None)/len(REC),5)
with open(os.path.join(D,"W0CAP2_BORN_V1.json"),"w") as f: json.dump(res,f,indent=1)
print(json.dumps({k:res[k] for k in ("GUARD_MISS","BORN_RESTING_BOOK","POOL_DECOMPOSITION_R_PER_POOL_TRADE")},indent=1))
print("COHERENCE:",json.dumps(res["coherence"],indent=1)[:1400])
