"""Does the artifact arithmetically explain CQ's inverted-breaker +11.9 R/trade?"""
import sys,os,json,gzip
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
rows=w0_ws.load(); anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bornof(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],4)
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
br=[r for r in rows if r.get("origin_family")=="current_breaker_re_entry" and w0_ws.key(r) in anch]
res={"family_n":len(br)}
grp={}
for r in br: grp.setdefault(bornof(anch[w0_ws.key(r)]["mkt_r_close"]),[]).append(r)
for bs,v in grp.items():
    tr=[x.get("policy_target_r") for x in v]
    res.setdefault("by_born_state",{})[bs]={"n":len(v),"engine_gross":mean([x.get("gross_r") for x in v]),
      "win_pct":round(100*sum(1 for x in v if (x.get("gross_r") or 0)>0)/len(v),3),
      "policy_target_r_mean":mean(tr),"policy_target_r_median":q(tr,.5),"policy_target_r_max":round(max(t for t in tr if t is not None),3),
      "policy_target_r_p95":q(tr,.95),
      "share_target_gt_2_pct":round(100*sum(1 for t in tr if t and t>2.0001)/len(v),3)}
ps=grp.get("born_past_stop",[])
res["ARTIFACT_INVERSION_ARITHMETIC"]={
 "born_past_stop_n":len(ps),
 "share_of_family_pct":round(100*len(ps)/len(br),3),
 "engine_gross_on_these":mean([x.get("gross_r") for x in ps]),
 "inverted_at_flat_1R_per_trade":1.0,
 "inverted_at_declared_policy_target_mean_R":mean([x.get("policy_target_r") for x in ps]),
 "family_mean_if_inverted_rows_book_declared_target":round(
    sum((x.get("policy_target_r") or 0) for x in ps)/len(br),4),
 "clean_remainder_n":len(grp.get("born_resting",[])),
 "clean_remainder_engine_gross":mean([x.get("gross_r") for x in grp.get("born_resting",[])]),
}
with open(os.path.join(D,"W0CAP2_CQ_V1.json"),"w") as f: json.dump(res,f,indent=1)
print(json.dumps(res,indent=1))
