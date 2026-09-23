"""Is the cost gate a LEVERAGE cap in disguise? And the over/under-charge in dollars."""
import gzip,json,os,collections,math
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
for r in rows:
    a=anch.get((r["candidate_id"],r["decision_time_utc"])); m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
    r["leverage"]=r["notional_usd"]/100000.0 if r["notional_usd"] else None
    r["gate_R"]=(r["spread_r"] is not None and r["spread_r"]<=0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15)
def sd(v):
    n=len(v); m=sum(v)/n
    return math.sqrt(sum((x-m)**2 for x in v)/(n-1)) if n>1 else None
def S(pop):
    if not pop: return {"n":0}
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    nt=[r["gross_r"]-r["true_total_cost_r"] for r in pop if r["gross_r"] is not None and r["true_total_cost_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    return {"n":len(pop),"gross":round(sum(g)/len(g),5),"gross_se":round(sd(g)/math.sqrt(len(g)),5) if len(g)>1 else None,
            "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
            "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
            "net_true":round(sum(nt)/len(nt),5) if nt else None,
            "net_true_se":round(sd(nt)/math.sqrt(len(nt)),5) if len(nt)>1 else None,
            "mean_leverage_x":round(sum(r["leverage"] for r in pop if r["leverage"])/len(pop),1),
            "median_leverage_x":round(sorted(r["leverage"] for r in pop if r["leverage"])[len(pop)//2],1)}
EX=[r for r in rows if r["born"]!="born_past_stop" and r["gross_r"] is not None]
out={}
# over/under charge in dollars
over=sum(max(0.0,(r["cost_usd"] or 0)-(r["true_total_cost_usd"] or 0)) for r in rows)
under=sum(max(0.0,(r["true_total_cost_usd"] or 0)-(r["cost_usd"] or 0)) for r in rows)
out["charge_error_usd"]={"n":len(rows),
  "frozen_total_usd":round(sum(r["cost_usd"] or 0 for r in rows),0),
  "broker_true_total_usd":round(sum(r["true_total_cost_usd"] or 0 for r in rows),0),
  "gross_overcharge_usd":round(over,0),"gross_undercharge_usd":round(under,0),
  "net_overcharge_usd":round(over-under,0),
  "n_overcharged":sum(1 for r in rows if (r["cost_usd"] or 0)>(r["true_total_cost_usd"] or 0)),
  "n_undercharged":sum(1 for r in rows if (r["cost_usd"] or 0)<(r["true_total_cost_usd"] or 0))}
# leverage census
lev=sorted(r["leverage"] for r in EX if r["leverage"])
def q(v,p):
    i=(len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1); return v[lo]+(v[hi]-v[lo])*(i-lo)
out["leverage_distribution_EX"]={"n":len(lev),"p5":round(q(lev,.05),2),"p25":round(q(lev,.25),2),
  "p50":round(q(lev,.5),2),"p75":round(q(lev,.75),2),"p90":round(q(lev,.90),2),"p95":round(q(lev,.95),2),
  "p99":round(q(lev,.99),2),"max":round(max(lev),2),"mean":round(sum(lev)/len(lev),2),
  "share_over_30x":round(100*sum(1 for x in lev if x>30)/len(lev),2),
  "share_over_100x":round(100*sum(1 for x in lev if x>100)/len(lev),2),
  "share_over_500x":round(100*sum(1 for x in lev if x>500)/len(lev),2)}
# leverage-capped gate, count matched to incumbent
TARGET=sum(1 for r in EX if r["gate_R"])
v=sorted([r for r in EX if r["leverage"]],key=lambda r:r["leverage"])
out["G8_leverage_cap_count_matched"]={"threshold_leverage_x":round(v[TARGET-1]["leverage"],2),"admit":S(v[:TARGET]),"refuse":S(v[TARGET:])}
inc=set(id(r) for r in EX if r["gate_R"]); adm=set(id(r) for r in v[:TARGET])
out["G8_swap_in"]=S([r for r in v[:TARGET] if id(r) not in inc])
out["G8_swap_out"]=S([r for r in EX if r["gate_R"] and id(r) not in adm])
# leverage bands
bands=[(0,5),(5,10),(10,20),(20,50),(50,100),(100,300),(300,1000),(1000,10**12)]
out["leverage_bands_EX"]={f"{a}-{b}x":S([r for r in EX if r["leverage"] and a<=r["leverage"]<b]) for a,b in bands}
# agreement between cost gate and leverage cap
out["cost_gate_vs_leverage_agreement"]={"jaccard":round(len(inc&adm)/len(inc|adm),4),"n_incumbent":len(inc),"n_leverage":len(adm),"n_both":len(inc&adm)}
# fixed leverage ceilings
fx=[]
for T in (2,5,10,20,30,50,100,200,500,1000):
    a=[r for r in EX if r["leverage"] and r["leverage"]<=T]
    s=S(a); s["cap_x"]=T; fx.append(s)
out["fixed_leverage_ceilings_EX"]=fx
json.dump(out,open(os.path.join(DISC,"l5_LEVERAGE_V1.json"),"w"),indent=1)
print("charge error $:",json.dumps(out["charge_error_usd"]))
print("leverage dist:",json.dumps(out["leverage_distribution_EX"]))
print("\n=== LEVERAGE BANDS (ex past-stop) ===")
for k,s in out["leverage_bands_EX"].items():
    if not s["n"]: continue
    print(f"  {k:12s} n {s['n']:6d} gross {s['gross']:9.5f} +-{s['gross_se']:6.4f} win {s['win_pct']:5.2f}% netTRUE {str(s['net_true']):>9s}")
print("\n=== FIXED LEVERAGE CEILINGS ===")
for s in out["fixed_leverage_ceilings_EX"]:
    print(f"  <= {s['cap_x']:5d}x  n {s['n']:6d} gross {s['gross']:9.5f} win {s['win_pct']:5.2f}% netTRUE {str(s['net_true']):>9s} fillhon {str(s['fill_honest']):>9s}")
print("\nG8 count-matched leverage cap:",json.dumps({k:out["G8_leverage_cap_count_matched"][k] for k in ("threshold_leverage_x",)}),
      "\n  admit",json.dumps(out["G8_leverage_cap_count_matched"]["admit"]),
      "\n  swap_in",json.dumps(out["G8_swap_in"]),
      "\n  swap_out",json.dumps(out["G8_swap_out"]))
print("agreement:",json.dumps(out["cost_gate_vs_leverage_agreement"]))
