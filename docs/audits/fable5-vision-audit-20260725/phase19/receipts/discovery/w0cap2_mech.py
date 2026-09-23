"""Mechanism, precisely: how far through the market (in PRICE %, i.e. spread units) and how
STALE is the emitted level, per born state and per family."""
import sys,os,json,gzip
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
rows=w0_ws.load(); byk={w0_ws.key(r):r for r in rows}
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
stale=json.load(open(os.path.join(D,"W0CAP2_STALE_V1.json")))
def bornof(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],5)
res={}
byb={}
for r in rows:
    k=w0_ws.key(r); a=anch.get(k)
    if a is None or not r.get("entry_price"): continue
    bs=bornof(a["mkt_r_close"])
    off_bps=abs(a["mkt_r_close"])*r["risk_distance"]/r["entry_price"]*10000.0
    byb.setdefault(bs,[]).append((off_bps, (r.get("spread_r") or 0.0)*r["risk_distance"]/r["entry_price"]*10000.0, r.get("origin_family"), r["symbol"]))
for bs,v in byb.items():
    offs=[x[0] for x in v]; sps=[x[1] for x in v]
    ratio=[x[0]/x[1] for x in v if x[1]>1e-9]
    res.setdefault("through_market_distance",{})[bs]={"n":len(v),
      "offset_bps_p25":q(offs,.25),"offset_bps_median":q(offs,.5),"offset_bps_p75":q(offs,.75),"offset_bps_p95":q(offs,.95),
      "frozen_spread_bps_median":q(sps,.5),
      "offset_in_SPREAD_UNITS_median":q(ratio,.5),"offset_in_SPREAD_UNITS_p75":q(ratio,.75)}
# per-family staleness for born_past_stop / born_marketable, recomputed cheaply from the anchor+stale artifacts
import csv,bisect
BARS="/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601"
cache={}
def bars(s):
    if s in cache: return cache[s]
    ts=[];hi=[];lo=[]
    with open(os.path.join(BARS,f"{s}_M1.csv")) as f:
        rd=csv.reader(f); next(rd)
        for r_ in rd: ts.append(r_[0]);hi.append(float(r_[2]));lo.append(float(r_[3]))
    cache[s]=(ts,hi,lo); return cache[s]
fam={}
for r in rows:
    k=w0_ws.key(r); a=anch.get(k)
    if a is None: continue
    bs=bornof(a["mkt_r_close"])
    if bs!="born_past_stop": continue
    ts,hi,lo=bars(r["symbol"]); i=bisect.bisect_right(ts,r["decision_time_utc"])-1
    e=r["entry_price"]; lag=None; j=i
    while j>=max(0,i-1440):
        if lo[j]<=e<=hi[j]: lag=i-j; break
        j-=1
    fam.setdefault(r.get("origin_family"),[]).append(lag)
res["born_past_stop_staleness_by_family"]={f:{"n":len(v),
   "level_never_traded_in_prior_1440_bars_n":sum(1 for x in v if x is None),
   "level_never_traded_pct":round(100*sum(1 for x in v if x is None)/len(v),2),
   "lag_bars_median":q([x for x in v if x is not None],.5),
   "lag_bars_p75":q([x for x in v if x is not None],.75)} for f,v in sorted(fam.items(),key=lambda kv:-len(kv[1]))}
res["born_past_stop_staleness_overall"]=stale["born_past_stop"]
res["born_marketable_staleness_overall"]=stale["born_marketable"]
res["born_resting_staleness_overall"]=stale["born_resting"]
with open(os.path.join(D,"W0CAP2_MECH_V1.json"),"w") as f: json.dump(res,f,indent=1)
print(json.dumps(res["through_market_distance"],indent=1))
print("STALENESS by family (born_past_stop):")
for f,v in res["born_past_stop_staleness_by_family"].items():
    print(f'  {str(f)[:30]:32s} n{v["n"]:5d} never_traded_24h {v["level_never_traded_pct"]:5.1f}%  lag_median {v["lag_bars_median"]}')
