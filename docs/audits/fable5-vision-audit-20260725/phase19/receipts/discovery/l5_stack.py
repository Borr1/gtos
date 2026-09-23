"""The stacked repair, measured end to end. Offline scorer, no engine file touched."""
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
    r["gate_R"]=(r["spread_r"] is not None and r["spread_r"]<=0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15)
def sd(v):
    n=len(v); m=sum(v)/n
    return math.sqrt(sum((x-m)**2 for x in v)/(n-1)) if n>1 else None
def S(pop,label=""):
    if not pop: return {"label":label,"n":0}
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    nt=[r["gross_r"]-r["true_total_cost_r"] for r in pop if r["gross_r"] is not None and r["true_total_cost_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    fnt=[r["fill_honest_walk_r"]-r["true_total_cost_r"] for r in pop if r.get("fill_honest_walk_r") is not None and r["true_total_cost_r"] is not None]
    return {"label":label,"n":len(pop),
      "gross":round(sum(g)/len(g),5),"gross_se":round(sd(g)/math.sqrt(len(g)),5) if len(g)>1 else None,
      "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
      "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
      "net_true":round(sum(nt)/len(nt),5) if nt else None,
      "net_true_se":round(sd(nt)/math.sqrt(len(nt)),5) if len(nt)>1 else None,
      "fh_net_true":round(sum(fnt)/len(fnt),5) if fnt else None,
      "fh_net_true_se":round(sd(fnt)/math.sqrt(len(fnt)),5) if len(fnt)>1 else None,
      "total_net_true_usd":round(sum((r["gross_r"] or 0)*r["risk_usd"]-(r["true_total_cost_usd"] or 0) for r in pop),0),
      "mean_true_cost_usd":round(sum((r["true_total_cost_usd"] or 0) for r in pop)/len(pop),2),
      "trades_per_month":len(pop)}
out={}
S0=rows
S1=[r for r in rows if r["born"]!="born_past_stop"]
steps={}
steps["A_pool_as_shipped"]=S(S0)
steps["B_incumbent_gate"]=S([r for r in S0 if r["gate_R"]])
steps["C_incumbent_gate_ex_past_stop"]=S([r for r in S1 if r["gate_R"]])
steps["D_C_plus_brokertrue_cost_015"]=S([r for r in S1 if r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.15 and (r["true_spread_r"] is not None and r["true_spread_r"]<=0.10)])
steps["E_D_drop_spread_limb"]=S([r for r in S1 if r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.15])
for T in (0.020,0.025,0.030,0.040,0.050,0.075,0.100):
    steps[f"F_brokertrue_ceiling_{T:.3f}_({int(T*1000)}usd_per_1000risk)"]=S([r for r in S1 if r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=T])
out["stack"]=steps
# per-family on the best affordable cells
for T,name in ((0.05,"le_50usd_per_1000"),(0.15,"le_150usd_per_1000")):
    pop=[r for r in S1 if r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=T]
    fam=collections.defaultdict(list)
    for r in pop: fam[r["origin_family"]].append(r)
    out[f"per_family_{name}"]={k:S(v,k) for k,v in sorted(fam.items(),key=lambda x:-len(x[1]))}
    sym=collections.defaultdict(list)
    for r in pop: sym[r["symbol"]].append(r)
    out[f"per_symbol_{name}"]={k:S(v,k) for k,v in sorted(sym.items(),key=lambda x:-len(x[1]))}
json.dump(out,open(os.path.join(DISC,"l5_STACK_V1.json"),"w"),indent=1)
print(f"{'step':52s} {'n':>6s} {'gross':>9s} {'fillhon':>9s} {'netTRUE':>9s} {'+-se':>7s} {'fhNetTRUE':>9s} {'true$':>7s} {'netTrueUSD':>11s}")
for k,s in steps.items():
    if not s["n"]: print(f"{k:52s} EMPTY"); continue
    print(f"{k:52s} {s['n']:6d} {s['gross']:9.5f} {str(s['fill_honest']):>9s} {str(s['net_true']):>9s} {str(s['net_true_se']):>7s} {str(s['fh_net_true']):>9s} {s['mean_true_cost_usd']:7.1f} {s['total_net_true_usd']:11,.0f}")
print("\n=== PER FAMILY at broker-true cost <= $50 per $1,000 risk ===")
for k,s in out["per_family_le_50usd_per_1000"].items():
    if s["n"]<20: continue
    print(f"  {k:34s} n {s['n']:5d} gross {s['gross']:9.5f}+-{s['gross_se']:6.4f} netTRUE {s['net_true']:9.5f} fhNetTRUE {str(s['fh_net_true']):>9s} win {s['win_pct']:5.2f}%")
print("\n=== PER SYMBOL at broker-true cost <= $50 per $1,000 risk ===")
for k,s in out["per_symbol_le_50usd_per_1000"].items():
    if s["n"]<20: continue
    print(f"  {k:11s} n {s['n']:5d} gross {s['gross']:9.5f}+-{s['gross_se']:6.4f} netTRUE {s['net_true']:9.5f} fhNetTRUE {str(s['fh_net_true']):>9s} win {s['win_pct']:5.2f}%")
