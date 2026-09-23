"""Cost by born state, per-family/symbol tables, and the TRUE horizon lift measured past the
2-hour wall in the raw M1 series, on the tradeable population only."""
import sys,os,json,gzip,bisect,csv
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
BARS="/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601"
rows=w0_ws.load(); byk={w0_ws.key(r):r for r in rows}
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bornof(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],5)
cache={}
def bars(s):
    if s in cache: return cache[s]
    ts=[];hi=[];lo=[];cl=[]
    with open(os.path.join(BARS,f"{s}_M1.csv")) as f:
        rd=csv.reader(f); next(rd)
        for r in rd: ts.append(r[0]);hi.append(float(r[2]));lo.append(float(r[3]));cl.append(float(r[4]))
    cache[s]=(ts,hi,lo,cl); return cache[s]

recs=[]
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"]); r=byk.get(k); a=anch.get(k)
    if r is None or a is None: continue
    fav,adv=rp["fav"],rp["adv"]; tgt=rp.get("policy_target_r") or 2.0
    fb=next((i for i in range(len(adv)) if adv[i]<=0.0),None)
    e={"bs":bornof(a["mkt_r_close"]),"fam":r.get("origin_family"),"sym":r["symbol"],"eng":r.get("gross_r"),
       "cost":r.get("expected_cost_r"),"sp":r.get("spread_r"),"cm":r.get("commission_r"),
       "sw":r.get("swap_cost_r"),"sl":r.get("expected_slippage_r"),
       "rd_frac":(r["risk_distance"]/r["entry_price"]) if r.get("entry_price") else None,
       "filled":fb is not None,"tgt":tgt,"lastoff":rp["off"][-1],"cid":rp["candidate_id"],"dt":rp["decision_time_utc"]}
    if fb is not None:
        xr=None;rs=None
        for i in range(fb,len(fav)):
            ht=fav[i]>=tgt; hs=adv[i]<=-1.0
            if ht and hs: xr,rs=-1.0,"same_bar";break
            if ht: xr,rs=tgt,"target";break
            if hs: xr,rs=-1.0,"stop";break
        if xr is None: xr,rs=max(-1.0,min(rp["cls"][-1],tgt)),"mark_at_horizon"
        e["r"]=xr; e["reason"]=rs
    recs.append(e)

res={}
# 1. cost by born state
for bs in ("born_resting","born_at_limit","born_marketable","born_past_stop"):
    s=[x for x in recs if x["bs"]==bs]
    res.setdefault("cost_by_born_state",{})[bs]={"n":len(s),
      "mean_cost_r":mean([x["cost"] for x in s]),"median_cost_r":q([x["cost"] for x in s],.5),
      "mean_spread_r":mean([x["sp"] for x in s]),"median_spread_r":q([x["sp"] for x in s],.5),
      "mean_commission_r":mean([x["cm"] for x in s]),"mean_swap_r":mean([x["sw"] for x in s]),
      "median_risk_distance_pct_of_price":q([100*x["rd_frac"] for x in s if x["rd_frac"]],.5)}
# 2. net books at de-inflated spread
def net(sel,div):
    return mean([ (x["eng"] or 0) - ((x["cost"] or 0) - (x["sp"] or 0) + (x["sp"] or 0)/div) for x in sel])
for lbl,sel in (("POOL",recs),("BORN_RESTING",[x for x in recs if x["bs"]=="born_resting"]),
                ("BORN_RESTING_FILLED",[x for x in recs if x["bs"]=="born_resting" and x["filled"]])):
    res.setdefault("net_books",{})[lbl]={"n":len(sel),"gross":mean([x["eng"] for x in sel]),
      "net_frozen":net(sel,1.0),"net_spread_div7.3":net(sel,7.3),"net_spread_div8.5":net(sel,8.5)}
# 3. per family
fam={}
for x in recs: fam.setdefault(x["fam"],[]).append(x)
for f,s in fam.items():
    br=[x for x in s if x["bs"]=="born_resting"]
    fam_row={"pool_n":len(s),"engine_gross":mean([x["eng"] for x in s]),
      "born_resting_n":len(br),"born_resting_pct":round(100*len(br)/len(s),2),
      "born_resting_engine_gross":mean([x["eng"] for x in br]),
      "born_past_stop_n":sum(1 for x in s if x["bs"]=="born_past_stop"),
      "born_past_stop_pct":round(100*sum(1 for x in s if x["bs"]=="born_past_stop")/len(s),2),
      "born_marketable_pct":round(100*sum(1 for x in s if x["bs"]=="born_marketable")/len(s),2)}
    brf=[x for x in br if x["filled"]]
    w=[x for x in brf if x.get("r",0)>0]
    fam_row["born_resting_filled_n"]=len(brf); fam_row["born_resting_walked_gross"]=mean([x.get("r") for x in brf])
    fam_row["born_resting_win_pct"]=round(100*len(w)/len(brf),2) if brf else None
    res.setdefault("per_family",{})[f]=fam_row
# 4. per symbol
sym={}
for x in recs: sym.setdefault(x["sym"],[]).append(x)
for sname,s in sym.items():
    br=[x for x in s if x["bs"]=="born_resting"]
    res.setdefault("per_symbol",{})[sname]={"pool_n":len(s),"engine_gross":mean([x["eng"] for x in s]),
      "born_past_stop_pct":round(100*sum(1 for x in s if x["bs"]=="born_past_stop")/len(s),2),
      "born_resting_pct":round(100*len(br)/len(s),2),"born_resting_engine_gross":mean([x["eng"] for x in br])}
# 5. TRUE horizon lift on born_resting, past the wall, raw M1
mk=[x for x in recs if x["bs"]=="born_resting" and x["filled"] and x.get("reason")=="mark_at_horizon"]
resolved={"target":0,"stop":0,"still_open_24h":0}
newr=[]
for x in mk:
    r=byk[(x["cid"],x["dt"])]
    ts,hi,lo,cl=bars(x["sym"]); i=bisect.bisect_right(ts,x["dt"])-1
    start=i+x["lastoff"]+1
    entry=r["entry_price"]; d=r["risk_distance"]; sgn=1.0 if r["side"]=="LONG" else -1.0
    got=None
    for j in range(start,min(len(ts),start+1440)):
        f=sgn*((hi[j] if sgn>0 else lo[j])-entry)/d
        av=sgn*((lo[j] if sgn>0 else hi[j])-entry)/d
        if sgn<0: f=(entry-lo[j])/d; av=(entry-hi[j])/d
        if f>=x["tgt"] and av<=-1.0: got=("stop",-1.0);break
        if f>=x["tgt"]: got=("target",x["tgt"]);break
        if av<=-1.0: got=("stop",-1.0);break
    if got is None: resolved["still_open_24h"]+=1; newr.append(x["r"])
    else: resolved[got[0]]+=1; newr.append(got[1])
brf=[x for x in recs if x["bs"]=="born_resting" and x["filled"]]
base=mean([x["r"] for x in brf])
mkset={(x["cid"],x["dt"]) for x in mk}
lift_sum=sum(newr)-sum(x["r"] for x in mk)
res["HORIZON_LIFT_ON_BORN_RESTING"]={"n_marked":len(mk),"share_of_filled_pct":round(100*len(mk)/len(brf),3),
  "resolution_when_wall_lifted_24h":resolved,
  "mark_mean_r_at_wall":mean([x["r"] for x in mk]),"resolved_mean_r":mean(newr),
  "walked_gross_at_wall":base,"walked_gross_wall_lifted":round(base+lift_sum/len(brf),5),
  "lift_r_per_filled_trade":round(lift_sum/len(brf),5)}
with open(os.path.join(D,"W0CAP2_FINAL_V1.json"),"w") as f: json.dump(res,f,indent=1)
print(json.dumps({k:res[k] for k in ("cost_by_born_state","net_books","HORIZON_LIFT_ON_BORN_RESTING")},indent=1))
