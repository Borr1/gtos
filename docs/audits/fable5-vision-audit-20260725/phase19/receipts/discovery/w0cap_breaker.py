"""w0-capture STEP 4: the breaker family + METHOD 4/5 close-out."""
import sys,json,math
from collections import Counter,defaultdict
D="docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,D); import w0_ws
rows={w0_ws.key(r):r for r in w0_ws.load()}
fat,tb={},{}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    if k not in rows: continue
    t=next((i for i,a in enumerate(rp["adv"]) if a<=1e-12),None); tb[k]=t
    if t is not None: fat[k]=rp["fav"][t]
def cls(k):
    t=tb.get(k); return "never" if t is None else ("gap" if fat[k]<0 else "clean")
def stat(v):
    v=sorted(x for x in v if x is not None and math.isfinite(x))
    if not v: return None
    n=len(v);q=lambda p:v[min(n-1,int(p*n))]
    return {"n":n,"mean":sum(v)/n,"p05":q(.05),"p25":q(.25),"median":q(.5),"p75":q(.75),"p95":q(.95),"max":v[-1]}
out={}
br=[k for k,r in rows.items() if (r.get("origin_family") or r.get("route_family"))=="current_breaker_re_entry"]
bu=[k for k in br if cls(k)=="gap" and fat[k]<=-1.0]
bo=[k for k in br if k not in set(bu)]
G=lambda ks:[rows[k]["gross_r"] for k in ks if rows[k].get("gross_r") is not None]
out["breaker"]={
 "n":len(br),
 "n_untakeable":len(bu),"share_untakeable":len(bu)/len(br),
 "untakeable_engine_gross_mean_R":sum(G(bu))/len(G(bu)),
 "untakeable_engine_win_rate":sum(1 for x in G(bu) if x>1e-3)/len(G(bu)),
 "untakeable_outcome_bands":dict(Counter(rows[k].get("outcome_band") for k in bu)),
 "untakeable_policy_target_r":stat([rows[k].get("policy_target_r") for k in bu]),
 "untakeable_fav_at_touch":stat([fat[k] for k in bu]),
 "untakeable_touch_bar_is_1_share":sum(1 for k in bu if tb[k]==0)/len(bu),
 "remainder_n":len(bo),"remainder_engine_gross_mean_R":sum(G(bo))/len(G(bo)),
 "remainder_win_rate":sum(1 for x in G(bo) if x>1e-3)/len(G(bo)),
 "INVERSE_of_untakeable_R_per_family_trade":-sum(G(bu))/len(br),
 "INVERSE_at_declared_policy_target_R_per_untakeable_row":
    sum(float(rows[k].get("policy_target_r") or 2.0) for k in bu)/len(bu),
 "family_share_of_pool":len(br)/len(rows),
 "untakeable_share_of_pool":len(bu)/len(rows)}
# what fraction of the pool's whole untakeable population is this one family
allunt=[k for k in rows if cls(k)=="gap" and fat[k]<=-1.0]
out["breaker"]["share_of_all_untakeable_rows"]=len(bu)/len(allunt)
out["all_untakeable_policy_target_r"]=stat([rows[k].get("policy_target_r") for k in allunt])
# METHOD 4/5 reprint from mechanism artifact
m=json.load(open(D+"/W0CAP_MECHANISM_V1.json"))
out["method4_sub_target_winners"]=m["sub_target_winners"]
out["method5_full_stops"]=m["full_stops"]
json.dump(out,open(D+"/W0CAP_BREAKER_V1.json","w"),indent=1,default=str)
print("BREAKER:"); [print("  ",a,"=",str(b)[:190]) for a,b in out["breaker"].items()]
print("ALL-UNTAKEABLE policy_target_r:",out["all_untakeable_policy_target_r"])
print("METHOD4:"); [print("  ",a,"=",str(b)[:190]) for a,b in m["sub_target_winners"].items()]
print("METHOD5:"); [print("  ",a,"=",str(b)[:190]) for a,b in m["full_stops"].items()]
