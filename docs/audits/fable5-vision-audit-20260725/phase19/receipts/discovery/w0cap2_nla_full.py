"""FULL RECOMPUTE on the strictly no-look-ahead anchor.
Bars are OPEN-STAMPED (proved: M15@T aggregates M1@T..T+14, 89-98% OHLC match vs 0.05-0.2%
for close-stamping).  So the M1 bar stamped at the decision minute is ENTIRELY POST-DECISION.
The last price observable at the decision instant is the close of the bar stamped decision-1min
= `mkt_r_prev_close`.  Everything here uses that and only that."""
import sys,os,json,gzip,bisect,csv
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
BARS="/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601"
rows=w0_ws.load(); byk={w0_ws.key(r):r for r in rows}
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],5)
cache={}
def bars(s):
    if s in cache: return cache[s]
    ts=[];hi=[];lo=[]
    with open(os.path.join(BARS,f"{s}_M1.csv")) as f:
        rd=csv.reader(f); next(rd)
        for r_ in rd: ts.append(r_[0]);hi.append(float(r_[2]));lo.append(float(r_[3]))
    cache[s]=(ts,hi,lo); return cache[s]

recs=[]
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"]); r=byk.get(k); a=anch.get(k)
    if r is None or a is None: continue
    m=a["mkt_r_prev_close"]; fav,adv=rp["fav"],rp["adv"]; tgt=rp.get("policy_target_r") or 2.0
    fb=next((i for i in range(len(adv)) if adv[i]<=0.0),None)
    e={"bs":bo(m),"m":m,"fam":r.get("origin_family"),"sym":r["symbol"],"eng":r.get("gross_r"),
       "cost":r.get("expected_cost_r") or 0.0,"sp":r.get("spread_r") or 0.0,"filled":fb is not None,
       "tgt":tgt,"cid":rp["candidate_id"],"dt":rp["decision_time_utc"],
       "rd":(r["risk_distance"]/r["entry_price"]*100.0) if r.get("entry_price") else None}
    if fb is not None:
        xr=None;rs=None;mfe=-9e9
        for i in range(fb,len(fav)):
            mfe=max(mfe,fav[i]); ht=fav[i]>=tgt; hs=adv[i]<=-1.0
            if ht and hs: xr,rs=-1.0,"same_bar";break
            if ht: xr,rs=tgt,"target";break
            if hs: xr,rs=-1.0,"stop";break
        if xr is None: xr,rs=max(-1.0,min(rp["cls"][-1],tgt)),"mark_at_horizon"
        e["r"],e["reason"],e["mfe"]=xr,rs,round(mfe,4)
    recs.append(e)
N=len(recs)
res={"anchor":"mkt_r_prev_close (close of M1 bar stamped decision-1min; bars OPEN-stamped => this bar closes AT the decision instant)","n":N}
res["bar_convention_proof"]={"test":"M15 bar stamped T vs M1 bars stamped T..T+14 (open) or T-14..T (close), high+low exact match",
  "EURUSD":{"n":2016,"open_stamped":1921,"close_stamped":4},"GER40":{"n":1903,"open_stamped":1704,"close_stamped":2},
  "BTCUSD":{"n":2908,"open_stamped":2806,"close_stamped":1},"XAUUSD":{"n":1922,"open_stamped":1881,"close_stamped":0}}
# born census
g={}
for x in recs: g.setdefault(x["bs"],[]).append(x)
res["BORN_CENSUS"]={bs:{"n":len(v),"share_pct":round(100*len(v)/N,3),"engine_gross_r":mean([x["eng"] for x in v]),
    "win_pct":round(100*sum(1 for x in v if (x["eng"] or 0)>0)/len(v),3),
    "contribution_to_pool_r":round(sum((x["eng"] or 0) for x in v)/N,5),
    "median_risk_distance_pct_of_price":q([x["rd"] for x in v if x["rd"]],.5),
    "mean_cost_r":mean([x["cost"] for x in v])} for bs,v in sorted(g.items())}
# drop past_stop
keep=[x for x in recs if x["bs"]!="born_past_stop"]
res["DROP_BORN_PAST_STOP"]={"n_dropped":N-len(keep),"n_kept":len(keep),
  "pool_gross_before":mean([x["eng"] for x in recs]),"pool_gross_after":mean([x["eng"] for x in keep]),
  "recoverable_r_per_pool_trade":round(mean([x["eng"] for x in keep])-mean([x["eng"] for x in recs]),5),
  "win_pct_after":round(100*sum(1 for x in keep if (x["eng"] or 0)>0)/len(keep),3)}
# dose response
bands=[(-1e9,-3),(-3,-1),(-1,-0.5),(-0.5,-0.25),(-0.25,-0.1),(-0.1,-1e-9),(-1e-9,1e-9),(1e-9,0.1),(0.1,0.25),(0.25,0.5),(0.5,1),(1,2),(2,1e9)]
res["DOSE_RESPONSE"]={f"{a}..{b}":{"n":len([x for x in recs if a<x["m"]<=b]),
   "engine_gross":mean([x["eng"] for x in recs if a<x["m"]<=b]),
   "win_pct":round(100*sum(1 for x in recs if a<x["m"]<=b and (x["eng"] or 0)>0)/max(1,len([x for x in recs if a<x["m"]<=b])),2)} for a,b in bands}
# staleness for born_past_stop
fam={}
lag_all=[]
for x in recs:
    if x["bs"]!="born_past_stop": continue
    r=byk[(x["cid"],x["dt"])]; ts,hi,lo=bars(x["sym"]); i=bisect.bisect_right(ts,x["dt"])-1
    e=r["entry_price"]; lag=None; j=i
    while j>=max(0,i-1440):
        if lo[j]<=e<=hi[j]: lag=i-j; break
        j-=1
    lag_all.append(lag); fam.setdefault(x["fam"],[]).append(lag)
ok=[l for l in lag_all if l is not None]
res["BORN_PAST_STOP_STALENESS"]={"n":len(lag_all),"level_found_pct":round(100*len(ok)/len(lag_all),2),
  "never_traded_prior_1440_bars_pct":round(100*(len(lag_all)-len(ok))/len(lag_all),2),
  "lag_bars_median":q(ok,.5),"lag_bars_p25":q(ok,.25),"lag_bars_p75":q(ok,.75),"lag_bars_mean":round(sum(ok)/len(ok),2),
  "by_family":{str(f):{"n":len(v),"never_traded_pct":round(100*sum(1 for x in v if x is None)/len(v),2),
      "lag_median":q([x for x in v if x is not None],.5)} for f,v in sorted(fam.items(),key=lambda kv:-len(kv[1]))}}
res["BORN_PAST_STOP_mkt_r"]={"mean":mean([x["m"] for x in recs if x["bs"]=="born_past_stop"]),
  "median":q([x["m"] for x in recs if x["bs"]=="born_past_stop"],.5),
  "p05":q([x["m"] for x in recs if x["bs"]=="born_past_stop"],.05),
  "p95":q([x["m"] for x in recs if x["bs"]=="born_past_stop"],.95)}
# per family / symbol
for key,fld in (("per_family","fam"),("per_symbol","sym")):
    d={}
    for x in recs: d.setdefault(x[fld],[]).append(x)
    res[key]={str(k2):{"pool_n":len(v),"engine_gross":mean([x["eng"] for x in v]),
        "past_stop_n":sum(1 for x in v if x["bs"]=="born_past_stop"),
        "past_stop_pct":round(100*sum(1 for x in v if x["bs"]=="born_past_stop")/len(v),2),
        "gross_ex_past_stop":mean([x["eng"] for x in v if x["bs"]!="born_past_stop"]),
        "n_ex_past_stop":sum(1 for x in v if x["bs"]!="born_past_stop"),
        "walked_gross_ex_past_stop":mean([x.get("r") for x in v if x["bs"]!="born_past_stop" and x["filled"]]),
        "win_pct_ex_past_stop":round(100*sum(1 for x in v if x["bs"]!="born_past_stop" and x["filled"] and x.get("r",0)>0)/max(1,sum(1 for x in v if x["bs"]!="born_past_stop" and x["filled"])),2)}
        for k2,v in sorted(d.items(),key=lambda kv:-len(kv[1]))}
# METHOD 4/5 on the honest tradeable set (everything except born_past_stop)
tf=[x for x in keep if x["filled"]]
w=[x for x in tf if x["r"]>0]; l=[x for x in tf if x["r"]<=0]
rc={}; wc={}
for x in tf: rc.setdefault(x["reason"],[]).append(x["r"])
for x in w: wc.setdefault(x["reason"],[]).append(x["r"])
mw=mean([x["r"] for x in w]); ml=mean([x["r"] for x in l])
res["METHOD4_tradeable_set"]={"n_filled":len(tf),"walked_gross":mean([x["r"] for x in tf]),
  "win_pct":round(100*len(w)/len(tf),3),"mean_winner":mw,"mean_loser":ml,
  "realized_payoff":round(mw/abs(ml),4),"breakeven_win":round(-ml/(mw-ml),4),
  "exit_census":{k2:{"n":len(v),"share_pct":round(100*len(v)/len(tf),3),"mean_r":mean(v)} for k2,v in sorted(rc.items())},
  "WINNER_exit_census":{k2:{"n":len(v),"share_of_winners_pct":round(100*len(v)/len(w),3),"mean_r":mean(v),
     "R_contribution_per_filled":round(sum(v)/len(tf),5)} for k2,v in sorted(wc.items())}}
st=[x for x in tf if x["reason"]=="stop"]
res["METHOD5_tradeable_stops"]={"n":len(st),"mfe_median":q([x["mfe"] for x in st],.5),
  "mfe_p75":q([x["mfe"] for x in st],.75),"mfe_p90":q([x["mfe"] for x in st],.90),
  "share_mfe_ge_0.5_pct":round(100*sum(1 for x in st if x["mfe"]>=0.5)/len(st),2),
  "share_mfe_ge_1.0_pct":round(100*sum(1 for x in st if x["mfe"]>=1.0)/len(st),2)}
json.dump(res,open(os.path.join(D,"W0CAP2_NOLOOKAHEAD_FULL_V1.json"),"w"),indent=1)
print(json.dumps({k:res[k] for k in ("BORN_CENSUS","DROP_BORN_PAST_STOP","BORN_PAST_STOP_STALENESS","METHOD4_tradeable_set")},indent=1)[:3000])
