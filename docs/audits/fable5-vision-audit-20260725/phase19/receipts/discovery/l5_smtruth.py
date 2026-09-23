"""V2 truth source: src/costs/spread_model.py at each candidate's OWN decision instant
(era-ratio + intraweek), instead of the pooled 37-day tick p50. Adds sm_* columns and
re-measures the gate stack. Writes l5_MONEY_TABLE_SM.jsonl.gz."""
import sys,gzip,json,os,collections,math
sys.path.insert(0,"/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
from datetime import datetime
from src.costs.spread_model import spread_price
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
cache={}
def sm(sym,ts,band):
    k=(sym,ts.weekday(),ts.hour,band)
    if k in cache: return cache[k]
    try:
        e=spread_price(sym,"FTMO",ts,band=band)
        v=(e.spread_price,str(e.coverage),e.era_class,bool(e.decidable))
    except Exception as ex:
        v=(None,"ERROR:"+type(ex).__name__,None,None)
    cache[k]=v; return v
w=gzip.open(os.path.join(DISC,"l5_MONEY_TABLE_SM.jsonl.gz"),"wt")
errs=collections.Counter()
for r in rows:
    ts=datetime.fromisoformat(r["decision_time_utc"])
    bs=r["broker_symbol"]
    mid,cov,era,dec=sm(bs,ts,"mid"); lo,_,_,_=sm(bs,ts,"low"); hi,_,_,_=sm(bs,ts,"high")
    if mid is None: errs[cov]+=1
    rd=r["risk_distance"]; risk=r["risk_usd"]
    r["sm_spread_price"]=mid; r["sm_spread_price_low"]=lo; r["sm_spread_price_high"]=hi
    r["sm_coverage"]=cov; r["sm_era_class"]=era; r["sm_decidable"]=dec
    r["sm_spread_r"]=(mid/rd) if mid is not None else None
    r["sm_spread_r_low"]=(lo/rd) if lo is not None else None
    r["sm_spread_r_high"]=(hi/rd) if hi is not None else None
    r["sm_overcharge_x"]=(r["frozen_spread_price"]/mid) if (mid and r["frozen_spread_price"]) else None
    ct=r.get("commission_r_true") or 0.0; sw=r.get("swap_cost_r") or 0.0; sl=r.get("slippage_true_r") or 0.0
    for suf,key in (("","sm_spread_r"),("_low","sm_spread_r_low"),("_high","sm_spread_r_high")):
        v=r[key]
        r["sm_total_cost_r"+suf]=(v+ct+sw+sl) if v is not None else None
        r["sm_total_cost_usd"+suf]=((v+ct+sw+sl)*risk) if v is not None else None
    a=anch.get((r["candidate_id"],r["decision_time_utc"])); m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
    w.write(json.dumps(r)+"\n")
w.close()
def sd(v):
    n=len(v); mm=sum(v)/n
    return math.sqrt(sum((x-mm)**2 for x in v)/(n-1)) if n>1 else None
def S(pop,cost="sm_total_cost_r",label=""):
    if not pop: return {"label":label,"n":0}
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    nt=[r["gross_r"]-r[cost] for r in pop if r["gross_r"] is not None and r.get(cost) is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    fnt=[r["fill_honest_walk_r"]-r[cost] for r in pop if r.get("fill_honest_walk_r") is not None and r.get(cost) is not None]
    return {"label":label,"n":len(pop),"gross":round(sum(g)/len(g),5),
      "gross_se":round(sd(g)/math.sqrt(len(g)),5) if len(g)>1 else None,
      "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
      "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
      "net_sm":round(sum(nt)/len(nt),5) if nt else None,
      "net_sm_se":round(sd(nt)/math.sqrt(len(nt)),5) if len(nt)>1 else None,
      "fh_net_sm":round(sum(fnt)/len(fnt),5) if fnt else None,
      "fh_net_sm_se":round(sd(fnt)/math.sqrt(len(fnt)),5) if len(fnt)>1 else None,
      "mean_sm_cost_usd":round(sum((r.get("sm_total_cost_usd") or 0) for r in pop)/len(pop),2),
      "mean_frozen_cost_usd":round(sum((r["cost_usd"] or 0) for r in pop)/len(pop),2)}
EX=[r for r in rows if r["born"]!="born_past_stop"]
out={"errors":dict(errs),"n":len(rows),"n_ex":len(EX),
     "coverage":dict(collections.Counter(r["sm_coverage"] for r in rows)),
     "decidable":dict(collections.Counter(str(r["sm_decidable"]) for r in rows))}
per={}
bysym=collections.defaultdict(list)
for r in EX: bysym[r["symbol"]].append(r)
def q(v,p):
    v=sorted(v); i=(len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1); return v[lo]+(v[hi]-v[lo])*(i-lo)
for s,v in bysym.items():
    ov=[r["sm_overcharge_x"] for r in v if r["sm_overcharge_x"]]
    tc=[r["sm_total_cost_r"] for r in v if r["sm_total_cost_r"] is not None]
    per[s]={"n":len(v),"median_sm_spread_price":round(q([r["sm_spread_price"] for r in v if r["sm_spread_price"]],.5),6),
            "median_frozen_spread_price":round(q([r["frozen_spread_price"] for r in v if r["frozen_spread_price"]],.5),6),
            "median_overcharge_x":round(q(ov,.5),3) if ov else None,
            "sm_cost_per_1000_risk_usd":round(1000*sum(tc)/len(tc),2) if tc else None,
            "coverage":collections.Counter(r["sm_coverage"] for r in v).most_common(1)[0][0],
            "decidable_share_pct":round(100*sum(1 for r in v if r["sm_decidable"])/len(v),1)}
out["per_symbol"]=dict(sorted(per.items(),key=lambda x:-(x[1]["median_overcharge_x"] or 0)))
steps={}
steps["pool_EX"]=S(EX,label="pool ex past-stop")
steps["incumbent_gate_EX"]=S([r for r in EX if r["spread_r"]<=0.10 and r["cost_r"]<=0.15],label="incumbent")
for T in (0.020,0.025,0.030,0.040,0.050,0.075,0.100,0.150):
    steps[f"sm_ceiling_{int(T*1000)}usd_per_1000risk"]=S([r for r in EX if r.get("sm_total_cost_r") is not None and r["sm_total_cost_r"]<=T])
out["stack_sm"]=steps
band={}
for cost in ("sm_total_cost_r","sm_total_cost_r_low","sm_total_cost_r_high"):
    band[cost]=S([r for r in EX if r.get(cost) is not None and r[cost]<=0.05],cost=cost,label=cost)
out["band_sensitivity_at_50usd"]=band
json.dump(out,open(os.path.join(DISC,"l5_SMTRUTH_V1.json"),"w"),indent=1)
print("errors",dict(errs),"coverage",out["coverage"],"decidable",out["decidable"])
print("\n=== spread_model (Jan-2026, per-instant) vs FROZEN, per symbol ===")
print(f"{'sym':11s} {'n':>5s} {'sm_p50':>11s} {'frozen_p50':>11s} {'ovx':>8s} {'sm$/1k':>8s} {'cov':>9s} {'dec%':>5s}")
for s,v in out["per_symbol"].items():
    print(f"{s:11s} {v['n']:5d} {v['median_sm_spread_price']:11.6f} {v['median_frozen_spread_price']:11.6f} {str(v['median_overcharge_x']):>8s} {str(v['sm_cost_per_1000_risk_usd']):>8s} {v['coverage'][:9]:>9s} {v['decidable_share_pct']:5.1f}")
print("\n=== STACK at spread_model truth (ex past-stop) ===")
for k,s in steps.items():
    if not s["n"]: print(f"  {k:38s} EMPTY"); continue
    print(f"  {k:38s} n {s['n']:6d} gross {s['gross']:9.5f} fillhon {str(s['fill_honest']):>9s} netSM {str(s['net_sm']):>9s} +-{str(s['net_sm_se']):>7s} fhNetSM {str(s['fh_net_sm']):>9s} sm$ {s['mean_sm_cost_usd']:7.1f}")
print("\n=== BAND SENSITIVITY at <=$50/1k ===")
for k,s in band.items(): print(f"  {k:26s} n {s['n']:6d} netSM {str(s['net_sm']):>9s} fhNetSM {str(s['fh_net_sm']):>9s}")
