import gzip,json,os,collections
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
anch={}
for l in gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt"):
    a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a
def bo(m): return "born_past_stop" if m<=-1.0 else ("born_marketable" if m<0.0 else ("born_at_limit" if m==0.0 else "born_resting"))
for r in rows:
    a=anch.get((r["candidate_id"],r["decision_time_utc"])); m=a.get("mkt_r_prev_close") if a else None
    r["born"]=bo(m) if m is not None else "unanchored"
    r["gate_R"]=(r["spread_r"] is not None and r["spread_r"]<=0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15)
    r["spread_limb_fail"]=(r["spread_r"] is not None and r["spread_r"]>0.10)
    r["total_limb_fail"]=(r["cost_r"] is not None and r["cost_r"]>0.15)
    r["gate_R_true"]=(r["true_spread_r"] is not None and r["true_spread_r"]<=0.10 and r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.15)
    r["net_true_r"]=(r["gross_r"]-r["true_total_cost_r"]) if (r["gross_r"] is not None and r["true_total_cost_r"] is not None) else None
    r["fh_net_true_r"]=(r["fill_honest_walk_r"]-r["true_total_cost_r"]) if (r.get("fill_honest_walk_r") is not None and r["true_total_cost_r"] is not None) else None
def S(pop):
    if not pop: return {"n":0}
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    nt=[r["net_true_r"] for r in pop if r["net_true_r"] is not None]
    fnt=[r["fh_net_true_r"] for r in pop if r["fh_net_true_r"] is not None]
    return {"n":len(pop),"gross":round(sum(g)/len(g),5) if g else None,
            "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2) if g else None,
            "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
            "net_true":round(sum(nt)/len(nt),5) if nt else None,
            "fill_honest_net_true":round(sum(fnt)/len(fnt),5) if fnt else None,
            "mean_cost_usd":round(sum(r["cost_usd"] for r in pop if r["cost_usd"] is not None)/len(pop),2),
            "mean_true_cost_usd":round(sum((r["true_total_cost_usd"] or 0) for r in pop)/len(pop),2),
            "mean_risk_usd":round(sum(r["risk_usd"] for r in pop)/len(pop),2)}
out={}
ALL=rows; EX=[r for r in rows if r["born"]!="born_past_stop"]
# --- refusal anatomy ---
for nm,pop in (("ALL",ALL),("EX_PAST_STOP",EX)):
    ref=[r for r in pop if not r["gate_R"]]
    blk={"refusals_total":S(ref)}
    blk["limb_spread_only"]=S([r for r in ref if r["spread_limb_fail"] and not r["total_limb_fail"]])
    blk["limb_total_only"]=S([r for r in ref if r["total_limb_fail"] and not r["spread_limb_fail"]])
    blk["limb_both"]=S([r for r in ref if r["spread_limb_fail"] and r["total_limb_fail"]])
    blk["refused_and_TRUE_also_refuses"]=S([r for r in ref if not r["gate_R_true"]])
    blk["refused_but_TRUE_passes__MODEL_ERROR"]=S([r for r in ref if r["gate_R_true"]])
    blk["admitted_but_TRUE_refuses__MODEL_ERROR"]=S([r for r in pop if r["gate_R"] and not r["gate_R_true"]])
    for T in (50,100,150,200,300,500):
        blk[f"refused_but_cost_usd_le_{T}"]=S([r for r in ref if r["cost_usd"] is not None and r["cost_usd"]<=T])
        blk[f"refused_but_TRUE_cost_usd_le_{T}"]=S([r for r in ref if r["true_total_cost_usd"] is not None and r["true_total_cost_usd"]<=T])
    # denominator artifact: refused rows whose dollar cost is below the gate's own $ equivalent at $1000 risk
    blk["refused_with_cost_usd_le_150_DENOM_ARTIFACT"]=S([r for r in ref if r["cost_usd"] is not None and r["cost_usd"]<=150])
    blk["refused_with_cost_usd_gt_150_GENUINELY_EXPENSIVE"]=S([r for r in ref if r["cost_usd"] is not None and r["cost_usd"]>150])
    # by risk bucket
    blk["refusals_by_risk_pct"]={str(k):S([r for r in ref if r["risk_per_trade_pct"]==k]) for k in (0.25,0.5,1.0,2.0)}
    blk["admits_by_risk_pct"]={str(k):S([r for r in pop if r["gate_R"] and r["risk_per_trade_pct"]==k]) for k in (0.25,0.5,1.0,2.0)}
    blk["pool_by_risk_pct"]={str(k):S([r for r in pop if r["risk_per_trade_pct"]==k]) for k in (0.25,0.5,1.0,2.0)}
    out[nm]=blk
# --- fine breakeven sweep on broker-true cost per $1000 risk ---
fine=[]
for T in (5,10,15,20,25,30,35,40,45,50,60,70,80,90,100,125,150,175,200,250):
    a=[r for r in EX if r["true_total_cost_r"] is not None and r["true_total_cost_r"]*1000<=T]
    s=S(a); s["usd_per_1000_risk"]=T; fine.append(s)
out["fine_true_cost_ceiling_sweep_EX"]=fine
fine2=[]
for T in (25,50,75,100,125,150,175,200,250,300,400,500):
    a=[r for r in EX if r["cost_r"] is not None and r["cost_r"]*1000<=T]
    s=S(a); s["usd_per_1000_risk"]=T; fine2.append(s)
out["fine_frozen_cost_ceiling_sweep_EX"]=fine2
# --- swap set composition: dollar gate vs R gate, count matched ---
pop=[r for r in EX if r["gross_r"] is not None]
TARGET=sum(1 for r in pop if r["gate_R"])
v=sorted([r for r in pop if r["cost_usd"] is not None],key=lambda r:r["cost_usd"])
adm=set(id(r) for r in v[:TARGET]); inc=set(id(r) for r in pop if r["gate_R"])
swin=[r for r in v[:TARGET] if id(r) not in inc]
swout=[r for r in pop if r["gate_R"] and id(r) not in adm]
def comp(pop,field):
    c=collections.Counter(r[field] for r in pop)
    tot=len(pop)
    return {str(k):{"n":n,"pct":round(100*n/tot,2),"gross":round(sum(x["gross_r"] for x in pop if x[field]==k)/n,5)} for k,n in c.most_common()}
out["dollar_gate_swap"]={"threshold_usd":v[TARGET-1]["cost_usd"],"target_n":TARGET,
    "swap_in":S(swin),"swap_out":S(swout),
    "swap_in_by_risk_pct":comp(swin,"risk_per_trade_pct"),"swap_out_by_risk_pct":comp(swout,"risk_per_trade_pct"),
    "swap_in_by_symbol":comp(swin,"symbol"),"swap_out_by_symbol":comp(swout,"symbol"),
    "swap_in_by_family":comp(swin,"origin_family"),"swap_out_by_family":comp(swout,"origin_family")}
json.dump(out,open(os.path.join(DISC,"l5_DECOMPOSE_V1.json"),"w"),indent=1)
def p(k,s): print(f"  {k:46s} n {s.get('n',0):6d} gross {str(s.get('gross')):>9s} fillhon {str(s.get('fill_honest')):>9s} netTRUE {str(s.get('net_true')):>9s} cost$ {str(s.get('mean_cost_usd')):>8s} true$ {str(s.get('mean_true_cost_usd')):>8s}")
for nm in ("ALL","EX_PAST_STOP"):
    print("### "+nm)
    for k in ("refusals_total","limb_spread_only","limb_total_only","limb_both",
              "refused_and_TRUE_also_refuses","refused_but_TRUE_passes__MODEL_ERROR",
              "admitted_but_TRUE_refuses__MODEL_ERROR",
              "refused_with_cost_usd_le_150_DENOM_ARTIFACT","refused_with_cost_usd_gt_150_GENUINELY_EXPENSIVE"):
        p(k,out[nm][k])
print("\n### FINE TRUE-COST CEILING SWEEP (ex past-stop) -- $ per $1,000 of risk")
for s in out["fine_true_cost_ceiling_sweep_EX"]:
    print(f"  <=${s['usd_per_1000_risk']:>4}  n {s['n']:6d} gross {str(s.get('gross')):>9s} fillhon {str(s.get('fill_honest')):>9s} netTRUE {str(s.get('net_true')):>9s} fhNetTRUE {str(s.get('fill_honest_net_true')):>9s}")
