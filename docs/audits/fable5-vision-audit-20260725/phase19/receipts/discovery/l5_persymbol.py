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
EX=[r for r in rows if r["born"]!="born_past_stop" and r["gross_r"] is not None]
def sd(v):
    n=len(v); m=sum(v)/n
    return math.sqrt(sum((x-m)**2 for x in v)/(n-1)) if n>1 else None
out={}
# 1) commission fidelity check: pool commission_r vs recomputed broker-true
d=[(r["commission_r"],r["commission_r_true"]) for r in rows if r["commission_r"] is not None and r["commission_r_true"] is not None]
rel=[abs(a-b)/max(1e-12,abs(b)) for a,b in d if b>0]
out["commission_fidelity"]={"n":len(d),"n_rel":len(rel),
  "max_rel_diff":round(max(rel),6) if rel else None,
  "median_rel_diff":round(sorted(rel)[len(rel)//2],6) if rel else None,
  "mean_pool_commission_r":round(sum(a for a,_ in d)/len(d),6),
  "mean_recomputed_commission_r":round(sum(b for _,b in d)/len(d),6),
  "n_pool_zero_but_true_nonzero":sum(1 for a,b in d if a==0 and b>0),
  "n_true_zero":sum(1 for a,b in d if b==0)}
# 2) slippage
sl=[r["expected_slippage_r"] for r in rows if r["expected_slippage_r"] is not None]
out["slippage"]={"n":len(sl),"distinct":len(set(sl)),"mean_charged_r":round(sum(sl)/len(sl),6),
  "modal":collections.Counter(sl).most_common(3),
  "broker_measured_r":0.003,"overcharge_x":round((sum(sl)/len(sl))/0.003,3),
  "source":"BROKER_TRUE_COSTS_V1_1.json accounts.FTMO.instruments.<sym>.slippage.value_r = 0.003 (MEASURED)"}
# 3) per-symbol affordability at BROKER TRUTH
per={}
bysym=collections.defaultdict(list)
for r in EX: bysym[r["symbol"]].append(r)
for s,v in bysym.items():
    g=[r["gross_r"] for r in v]
    tc=[r["true_total_cost_r"] for r in v if r["true_total_cost_r"] is not None]
    fc=[r["cost_r"] for r in v]
    nt=[r["gross_r"]-r["true_total_cost_r"] for r in v if r["true_total_cost_r"] is not None]
    nf=[r["gross_r"]-r["cost_r"] for r in v]
    per[s]={"n":len(v),"gross":round(sum(g)/len(g),5),"gross_se":round(sd(g)/math.sqrt(len(g)),5),
      "true_cost_per_1000_risk_usd":round(1000*sum(tc)/len(tc),2),
      "frozen_cost_per_1000_risk_usd":round(1000*sum(fc)/len(fc),2),
      "true_median_cost_per_1000":round(1000*sorted(tc)[len(tc)//2],2),
      "net_true":round(sum(nt)/len(nt),5),"net_true_se":round(sd(nt)/math.sqrt(len(nt)),5),
      "net_frozen":round(sum(nf)/len(nf),5),
      "charge_error_x":round((sum(fc)/len(fc))/(sum(tc)/len(tc)),3)}
out["per_symbol_affordability_EX_PAST_STOP"]=dict(sorted(per.items(),key=lambda x:x[1]["true_cost_per_1000_risk_usd"]))
# 4) the 374 spread-limb-only refusals, fully characterised
sl_only=[r for r in rows if r["spread_r"] is not None and r["spread_r"]>0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15]
sl_only_ex=[r for r in sl_only if r["born"]!="born_past_stop"]
def desc(pop):
    g=[r["gross_r"] for r in pop]
    nt=[r["gross_r"]-r["true_total_cost_r"] for r in pop if r["true_total_cost_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    return {"n":len(pop),"gross":round(sum(g)/len(g),5),"gross_se":round(sd(g)/math.sqrt(len(g)),5),
            "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
            "net_true":round(sum(nt)/len(nt),5),"net_true_se":round(sd(nt)/math.sqrt(len(nt)),5),
            "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
            "mean_spread_r":round(sum(r["spread_r"] for r in pop)/len(pop),5),
            "mean_cost_r":round(sum(r["cost_r"] for r in pop)/len(pop),5),
            "mean_true_cost_usd":round(sum((r["true_total_cost_usd"] or 0) for r in pop)/len(pop),2),
            "by_symbol":dict(collections.Counter(r["symbol"] for r in pop).most_common()),
            "by_family":dict(collections.Counter(r["origin_family"] for r in pop).most_common()),
            "by_risk_pct":dict(collections.Counter(r["risk_per_trade_pct"] for r in pop).most_common()),
            "by_born":dict(collections.Counter(r["born"] for r in pop).most_common()),
            "example_candidate_ids":[r["candidate_id"] for r in pop[:8]]}
out["spread_limb_only_refusals_ALL"]=desc(sl_only)
out["spread_limb_only_refusals_EX_PAST_STOP"]=desc(sl_only_ex)
json.dump(out,open(os.path.join(DISC,"l5_PERSYMBOL_V1.json"),"w"),indent=1)
print("commission fidelity:",json.dumps(out["commission_fidelity"]))
print("slippage:",json.dumps({k:v for k,v in out["slippage"].items() if k!="source"}))
print("\n=== PER SYMBOL AFFORDABILITY (ex past-stop) -- cost is $ per $1,000 of risk ===")
print(f"{'sym':11s} {'n':>5s} {'true$/1k':>9s} {'froz$/1k':>9s} {'err_x':>7s} {'gross':>9s} {'netTRUE':>9s} {'+-se':>7s} {'netFROZ':>9s}")
for s,v in out["per_symbol_affordability_EX_PAST_STOP"].items():
    print(f"{s:11s} {v['n']:5d} {v['true_cost_per_1000_risk_usd']:9.2f} {v['frozen_cost_per_1000_risk_usd']:9.2f} {v['charge_error_x']:7.3f} {v['gross']:9.5f} {v['net_true']:9.5f} {v['net_true_se']:7.4f} {v['net_frozen']:9.5f}")
print("\n=== SPREAD-LIMB-ONLY REFUSALS (spread_r>0.10 but total<=0.15) ===")
for k in ("ALL","EX_PAST_STOP"):
    v=out["spread_limb_only_refusals_"+k]
    print(f" {k}: n {v['n']} gross {v['gross']}+-{v['gross_se']} win {v['win_pct']}% netTRUE {v['net_true']}+-{v['net_true_se']} fillhon {v['fill_honest']} mean_spread_r {v['mean_spread_r']} true$ {v['mean_true_cost_usd']}")
    print("   symbols:",json.dumps(v["by_symbol"]))
    print("   families:",json.dumps(v["by_family"]))
    print("   risk_pct:",json.dumps(v["by_risk_pct"]),"born:",json.dumps(v["by_born"]))
