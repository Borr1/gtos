"""CQ inverted-breaker candidate, split by the STRICTLY NO-LOOK-AHEAD born state."""
import gzip,json,sys,os,statistics as st
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch.setdefault(a["candidate_id"],a)
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
rs=[json.loads(l) for l in gzip.open(os.path.join(os.path.dirname(D),'..','..','phase18','receipts','pools','CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz'),'rt')]
g={}; nm=0
for t in rs:
    a=anch.get(t.get("source_candidate_id"))
    if not a: nm+=1; continue
    g.setdefault(bo(a["mkt_r_prev_close"]),[]).append((t,a))
out={"trades":len(rs),"unmatched":nm,"anchor":"mkt_r_prev_close (no look-ahead)",
     "overall_r_gross":mean([t.get("r_gross") for t in rs]),
     "overall_grid_net_r":mean([t.get("grid_net_r") for t in rs])}
for bs,v in sorted(g.items()):
    ts=[t for t,_ in v]
    out[bs]={"n":len(v),"share_pct":round(100*len(v)/len(rs),2),
      "r_gross":mean([t.get("r_gross") for t in ts]),"grid_net_r":mean([t.get("grid_net_r") for t in ts]),
      "R_contribution_per_family_trade":round(sum((t.get("grid_net_r") or 0) for t in ts)/len(rs),4),
      "outcome_mix":{o:sum(1 for t in ts if t.get("outcome")==o) for o in sorted({t.get("outcome") for t in ts})}}
    om=out[bs]["outcome_mix"]; out[bs]["win_pct"]=round(100*om.get("TARGET",0)/len(v),2)
ps=g.get("born_past_stop",[])
X=[-a["mkt_r_prev_close"] for _,a in ps]; Y=[t.get("r_gross") for t,_ in ps]
n=len(X); mx=sum(X)/n; my=sum(Y)/n
cov=sum((X[i]-mx)*(Y[i]-my) for i in range(n))/n
out["staleness_regression"]={"n":n,"mean_staleness_R":round(mx,4),"mean_r_gross":round(my,4),
  "pearson_r":round(cov/(st.pstdev(X)*st.pstdev(Y)),5),"r_squared":round((cov/(st.pstdev(X)*st.pstdev(Y)))**2,5),
  "ols_slope":round(cov/st.pvariance(X),5)}
out["artifact_share_of_headline_pct"]=round(100*out["born_past_stop"]["R_contribution_per_family_trade"]/out["overall_grid_net_r"],2)
json.dump(out,open(os.path.join(D,"W0CAP2_CQ_NOLOOKAHEAD_V1.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
