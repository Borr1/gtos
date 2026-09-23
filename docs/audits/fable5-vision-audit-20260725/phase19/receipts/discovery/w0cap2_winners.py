"""METHOD 4/5 re-done on the population that is actually tradeable.
What closes a winning trade at +1.04R, ON BORN-RESTING ROWS?  Does the clean pool realize 2:1?"""
import sys, os, json, gzip
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import w0_ws
rows=w0_ws.load(); byk={w0_ws.key(r):r for r in rows}
anch={}
with gzip.open(os.path.join(D,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as f:
    for ln in f:
        a=json.loads(ln); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bornof(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
def q(v,p):
    if not v: return None
    s=sorted(v); return round(s[min(len(s)-1,max(0,int(round(p*(len(s)-1)))))],4)
def mean(v):
    v=[x for x in v if x is not None]; return round(sum(v)/len(v),5) if v else None

WALK={}   # key -> dict
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    r=byk.get(k); a=anch.get(k)
    if r is None or a is None: continue
    fav,adv=rp["fav"],rp["adv"]; tgt=rp.get("policy_target_r") or 2.0
    fb=next((i for i in range(len(adv)) if adv[i]<=0.0),None)
    if fb is None:
        WALK[k]={"bs":bornof(a["mkt_r_close"]),"filled":False}; continue
    # walk from the fill bar
    exit_r=None; reason=None; xb=None; mfe=-9e9; mae=9e9
    for i in range(fb,len(fav)):
        mfe=max(mfe,fav[i]); mae=min(mae,adv[i])
        ht=fav[i]>=tgt; hs=adv[i]<=-1.0
        if ht and hs: exit_r,reason,xb=-1.0,"same_bar_conservative_stop",i; break
        if ht: exit_r,reason,xb=tgt,"target",i; break
        if hs: exit_r,reason,xb=-1.0,"stop",i; break
    if exit_r is None:
        exit_r=max(-1.0,min(rp["cls"][-1],tgt)); reason="mark_at_horizon"; xb=len(fav)-1
    WALK[k]={"bs":bornof(a["mkt_r_close"]),"filled":True,"r":round(exit_r,6),"reason":reason,
             "mfe":round(mfe,4),"mae":round(mae,4),"tgt":tgt,"fb":fb+1,"xb":xb+1,
             "eng":r.get("gross_r"),"fam":r.get("family"),"sym":r["symbol"],
             "cost":r.get("expected_cost_r"),"spread":r.get("spread_r"),"comm":r.get("commission_r")}

res={}
def book(sel,label):
    w=[x for x in sel if x.get("filled")]
    rs=[x["r"] for x in w]; win=[x for x in w if x["r"]>0]; los=[x for x in w if x["r"]<=0]
    mw=mean([x["r"] for x in win]); ml=mean([x["r"] for x in los])
    be=round(-ml/(mw-ml),4) if (mw is not None and ml is not None and mw!=ml) else None
    reasons={}
    for x in w: reasons.setdefault(x["reason"],[]).append(x["r"])
    wr={}
    for x in win: wr.setdefault(x["reason"],[]).append(x["r"])
    return {"label":label,"n_sel":len(sel),"n_filled":len(w),
        "gross_r_walked":mean(rs),"engine_gross_r":mean([x.get("eng") for x in sel]),
        "win_pct":round(100*len(win)/len(w),4) if w else None,
        "mean_winner":mw,"mean_loser":ml,"realized_payoff":round(mw/abs(ml),4) if (mw and ml) else None,
        "breakeven_win":be,
        "exit_reason_census":{k2:{"n":len(v),"share_pct":round(100*len(v)/len(w),3),"mean_r":mean(v)} for k2,v in sorted(reasons.items())},
        "WINNER_exit_census":{k2:{"n":len(v),"share_of_winners_pct":round(100*len(v)/len(win),3),"mean_r":mean(v),
                                  "R_contribution_per_filled_trade":round(sum(v)/len(w),5)} for k2,v in sorted(wr.items())}}
allw=list(WALK.values())
res["POOL_all"]=book(allw,"all rows")
res["BORN_RESTING"]=book([x for x in allw if x["bs"]=="born_resting"],"born_resting only")
res["BORN_MARKETABLE"]=book([x for x in allw if x["bs"]=="born_marketable"],"born_marketable only")
res["BORN_PAST_STOP"]=book([x for x in allw if x["bs"]=="born_past_stop"],"born_past_stop only")

# METHOD 5 on born_resting: stops, money on the table
st=[x for x in allw if x["bs"]=="born_resting" and x.get("filled") and x["reason"]=="stop"]
res["BORN_RESTING_STOPS_MFE"]={"n":len(st),"mfe_median":q([x["mfe"] for x in st],.5),
  "mfe_p75":q([x["mfe"] for x in st],.75),"mfe_p90":q([x["mfe"] for x in st],.90),
  "share_mfe_ge_0.5_pct":round(100*sum(1 for x in st if x["mfe"]>=0.5)/len(st),3) if st else None,
  "share_mfe_ge_1.0_pct":round(100*sum(1 for x in st if x["mfe"]>=1.0)/len(st),3) if st else None,
  "share_mfe_ge_2.0_pct":round(100*sum(1 for x in st if x["mfe"]>=2.0)/len(st),3) if st else None}
# METHOD 4 on born_resting: sub-target winners
sw=[x for x in allw if x["bs"]=="born_resting" and x.get("filled") and 0<x["r"]<x["tgt"]-1e-9]
res["BORN_RESTING_SUBTARGET_WINNERS"]={"n":len(sw),"mean_r":mean([x["r"] for x in sw]),
  "all_reason_mark_at_horizon_pct":round(100*sum(1 for x in sw if x["reason"]=="mark_at_horizon")/len(sw),3) if sw else None,
  "mfe_median":q([x["mfe"] for x in sw],.5),"mfe_mean":mean([x["mfe"] for x in sw]),
  "share_mfe_reached_target_pct":round(100*sum(1 for x in sw if x["mfe"]>=x["tgt"])/len(sw),3) if sw else None}
with open(os.path.join(D,"W0CAP2_WINNERS_V1.json"),"w") as f: json.dump(res,f,indent=1)
for k in ("POOL_all","BORN_RESTING"):
    b=res[k]; print("==",k,{kk:b[kk] for kk in ("n_filled","gross_r_walked","engine_gross_r","win_pct","mean_winner","mean_loser","realized_payoff","breakeven_win")})
    print("   exits:",{kk:(v["n"],v["mean_r"]) for kk,v in b["exit_reason_census"].items()})
    print("   winner exits:",{kk:(v["n"],v["mean_r"],v["R_contribution_per_filled_trade"]) for kk,v in b["WINNER_exit_census"].items()})
print("SUBTGT",res["BORN_RESTING_SUBTARGET_WINNERS"]); print("STOPS",res["BORN_RESTING_STOPS_MFE"])
print("MKTBL",{k:res["BORN_MARKETABLE"][k] for k in ("n_filled","gross_r_walked","engine_gross_r","win_pct","realized_payoff")})
