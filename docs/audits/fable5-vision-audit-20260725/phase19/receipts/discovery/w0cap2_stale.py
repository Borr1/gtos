"""MECHANISM: is entry_price a STALE level?  For every row, walk BACKWARD from the decision
minute and find the most recent M1 bar whose [low,high] contains entry_price.  The lag in
minutes is the age of the level the candidate is quoting."""
import sys, os, json, gzip, bisect, csv
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws
BARS="/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601"
rows=w0_ws.load()
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
cache={}
def bars(s):
    if s in cache: return cache[s]
    p=os.path.join(BARS,f"{s}_M1.csv"); ts=[];hi=[];lo=[]
    with open(p) as f:
        rd=csv.reader(f); next(rd)
        for r in rd: ts.append(r[0]); hi.append(float(r[2])); lo.append(float(r[3]))
    cache[s]=(ts,hi,lo); return cache[s]
LOOK=1440   # search back up to 24h of BARS (not minutes; the series has gaps)
out={}
recs=[]
for r in rows:
    k=w0_ws.key(r); a=anch.get(k)
    if a is None: continue
    m=a["mkt_r_close"]
    bs="born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
    ts,hi,lo=bars(r["symbol"])
    i=bisect.bisect_right(ts,r["decision_time_utc"])-1
    e=r["entry_price"]; lagbars=None
    j=i; lim=max(0,i-LOOK)
    while j>=lim:
        if lo[j]<=e<=hi[j]: lagbars=i-j; break
        j-=1
    recs.append({"bs":bs,"lagbars":lagbars,"g":r.get("gross_r"),"fam":r.get("family"),"sym":r["symbol"],
                 "cid":r["candidate_id"],"dt":r["decision_time_utc"],"m":m})
def q(v,p):
    if not v: return None
    s=sorted(v); return s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))]
res={}
for bs in ("born_resting","born_at_limit","born_marketable","born_past_stop"):
    sub=[x for x in recs if x["bs"]==bs]
    lag=[x["lagbars"] for x in sub if x["lagbars"] is not None]
    res[bs]={"n":len(sub),"level_found_within_24h_n":len(lag),
             "level_found_pct":round(100*len(lag)/len(sub),3) if sub else None,
             "lag_bars_p05":q(lag,.05),"lag_bars_p25":q(lag,.25),"lag_bars_median":q(lag,.5),
             "lag_bars_p75":q(lag,.75),"lag_bars_p95":q(lag,.95),
             "lag_bars_mean":round(sum(lag)/len(lag),2) if lag else None,
             "lag_le_1_pct":round(100*sum(1 for x in lag if x<=1)/len(lag),3) if lag else None,
             "lag_le_15_pct":round(100*sum(1 for x in lag if x<=15)/len(lag),3) if lag else None,
             "lag_ge_60_pct":round(100*sum(1 for x in lag if x>=60)/len(lag),3) if lag else None,
             "never_traded_in_24h_pct":round(100*(len(sub)-len(lag))/len(sub),3) if sub else None}
# worst offenders for citation
ps=[x for x in recs if x["bs"]=="born_past_stop"]
ps_sorted=sorted(ps,key=lambda x:x["m"])[:8]
res["_cited_born_past_stop_examples"]=[{"candidate_id":x["cid"],"decision_time_utc":x["dt"],
    "symbol":x["sym"],"family":x["fam"],"mkt_r_at_decision":x["m"],"entry_level_age_bars":x["lagbars"],
    "engine_gross_r":x["g"]} for x in ps_sorted]
with open(os.path.join(D,"W0CAP2_STALE_V1.json"),"w") as f: json.dump(res,f,indent=1)
print(json.dumps({k:v for k,v in res.items() if not k.startswith("_")},indent=1))
