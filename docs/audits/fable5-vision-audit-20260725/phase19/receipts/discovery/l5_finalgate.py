"""l5 item 4/5: the concrete rebuilt gate, measured. Offline scorer only."""
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
    r["net_true_r"]=(r["gross_r"]-r["true_total_cost_r"]) if (r["gross_r"] is not None and r["true_total_cost_r"] is not None) else None
    r["fh_net_true_r"]=(r["fill_honest_walk_r"]-r["true_total_cost_r"]) if (r.get("fill_honest_walk_r") is not None and r["true_total_cost_r"] is not None) else None
def sd(v):
    n=len(v)
    if n<2: return None
    m=sum(v)/n; return math.sqrt(sum((x-m)**2 for x in v)/(n-1))
def S(pop,label=""):
    if not pop: return {"label":label,"n":0}
    g=[r["gross_r"] for r in pop if r["gross_r"] is not None]
    nt=[r["net_true_r"] for r in pop if r["net_true_r"] is not None]
    fh=[r["fill_honest_walk_r"] for r in pop if r.get("fill_honest_walk_r") is not None]
    fnt=[r["fh_net_true_r"] for r in pop if r["fh_net_true_r"] is not None]
    s_nt=sd(nt); s_g=sd(g); s_fnt=sd(fnt)
    return {"label":label,"n":len(pop),
      "gross":round(sum(g)/len(g),5),"gross_se":round(s_g/math.sqrt(len(g)),5) if s_g else None,
      "win_pct":round(100*sum(1 for x in g if x>0)/len(g),2),
      "fill_honest":round(sum(fh)/len(fh),5) if fh else None,
      "net_true":round(sum(nt)/len(nt),5) if nt else None,
      "net_true_se":round(s_nt/math.sqrt(len(nt)),5) if s_nt else None,
      "fh_net_true":round(sum(fnt)/len(fnt),5) if fnt else None,
      "fh_net_true_se":round(s_fnt/math.sqrt(len(fnt)),5) if s_fnt else None,
      "net_true_usd_total":round(sum((r["gross_r"] or 0)*r["risk_usd"]-(r["true_total_cost_usd"] or 0) for r in pop),0),
      "mean_cost_usd":round(sum((r["cost_usd"] or 0) for r in pop)/len(pop),2),
      "mean_true_cost_usd":round(sum((r["true_total_cost_usd"] or 0) for r in pop)/len(pop),2)}
G={
 "G0_incumbent_frozen_0.10spread_0.15total": lambda r: r["spread_r"] is not None and r["spread_r"]<=0.10 and r["cost_r"] is not None and r["cost_r"]<=0.15,
 "G1_frozen_total_only_0.15":                lambda r: r["cost_r"] is not None and r["cost_r"]<=0.15,
 "G2_brokertrue_0.10spread_0.15total":       lambda r: r["true_spread_r"] is not None and r["true_spread_r"]<=0.10 and r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.15,
 "G3_brokertrue_total_only_0.15":            lambda r: r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.15,
 "G4_brokertrue_flat_150usd":                lambda r: r["true_total_cost_usd"] is not None and r["true_total_cost_usd"]<=150.0,
 "G5_brokertrue_total_only_0.030":           lambda r: r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.030,
 "G6_brokertrue_total_only_0.050":           lambda r: r["true_total_cost_r"] is not None and r["true_total_cost_r"]<=0.050,
 "G7_frozen_flat_150usd":                    lambda r: r["cost_usd"] is not None and r["cost_usd"]<=150.0,
}
out={}
for nm,pop in (("ALL",rows),("EX_PAST_STOP",[r for r in rows if r["born"]!="born_past_stop"])):
    blk={"pool":S(pop,"pool")}
    for k,f in G.items(): blk[k]=S([r for r in pop if f(r)],k)
    out[nm]=blk
# where does the frozen model ADMIT expensive trades? per-symbol census of frozenPASS/trueREF
EX=[r for r in rows if r["born"]!="born_past_stop"]
bad=[r for r in EX if G["G0_incumbent_frozen_0.10spread_0.15total"](r) and not G["G2_brokertrue_0.10spread_0.15total"](r)]
good=[r for r in EX if (not G["G0_incumbent_frozen_0.10spread_0.15total"](r)) and G["G2_brokertrue_0.10spread_0.15total"](r)]
def bysym(pop):
    c=collections.Counter(r["symbol"] for r in pop); tot=len(pop)
    return {s:{"n":n,"pct":round(100*n/tot,2),
               "mean_frozen_cost_usd":round(sum(x["cost_usd"] for x in pop if x["symbol"]==s)/n,2),
               "mean_true_cost_usd":round(sum(x["true_total_cost_usd"] for x in pop if x["symbol"]==s)/n,2),
               "gross":round(sum(x["gross_r"] for x in pop if x["symbol"]==s)/n,5)} for s,n in c.most_common()}
out["harmful_admissions_frozenPASS_trueREF_by_symbol"]=bysym(bad)
out["missed_admissions_frozenREF_truePASS_by_symbol"]=bysym(good)
out["harmful_admissions_summary"]=S(bad,"frozenPASS_trueREF")
out["missed_admissions_summary"]=S(good,"frozenREF_truePASS")
json.dump(out,open(os.path.join(DISC,"l5_FINALGATE_V1.json"),"w"),indent=1)
hdr=f"{'gate':44s} {'n':>6s} {'gross':>9s} {'fillhon':>9s} {'netTRUE':>9s} {'+-se':>7s} {'fhNetTRUE':>9s} {'true$':>7s} {'netTrueUSD':>12s}"
for nm in ("ALL","EX_PAST_STOP"):
    print("### "+nm); print(hdr)
    for k in ["pool"]+list(G):
        s=out[nm][k]
        if not s["n"]: print(f"{k:44s} EMPTY"); continue
        print(f"{k:44s} {s['n']:6d} {s['gross']:9.5f} {str(s['fill_honest']):>9s} {str(s['net_true']):>9s} {str(s['net_true_se']):>7s} {str(s['fh_net_true']):>9s} {s['mean_true_cost_usd']:7.1f} {s['net_true_usd_total']:12,.0f}")
    print()
print("### harmful admissions (frozen PASS, broker-true REFUSE) top symbols")
for s,v in list(out["harmful_admissions_frozenPASS_trueREF_by_symbol"].items())[:10]:
    print(f"  {s:11s} n {v['n']:5d} ({v['pct']:5.2f}%) frozen$ {v['mean_frozen_cost_usd']:8.2f} true$ {v['mean_true_cost_usd']:8.2f} gross {v['gross']:8.5f}")
print("### missed admissions (frozen REFUSE, broker-true PASS) top symbols")
for s,v in list(out["missed_admissions_frozenREF_truePASS_by_symbol"].items())[:10]:
    print(f"  {s:11s} n {v['n']:5d} ({v['pct']:5.2f}%) frozen$ {v['mean_frozen_cost_usd']:8.2f} true$ {v['mean_true_cost_usd']:8.2f} gross {v['gross']:8.5f}")
