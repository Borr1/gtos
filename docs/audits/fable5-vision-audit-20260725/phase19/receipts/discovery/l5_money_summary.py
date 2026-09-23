import gzip, json, os, statistics as st
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
rows=[json.loads(l) for l in gzip.open(os.path.join(DISC,"l5_MONEY_TABLE.jsonl.gz"),"rt")]
def q(v,p):
    v=sorted(x for x in v if x is not None)
    if not v: return None
    i=(len(v)-1)*p
    lo=int(i); hi=min(lo+1,len(v)-1)
    return v[lo]+(v[hi]-v[lo])*(i-lo)
def dist(name,vals):
    v=[x for x in vals if x is not None]
    return {"n":len(v),"mean":sum(v)/len(v) if v else None,"p5":q(v,.05),"p25":q(v,.25),
            "p50":q(v,.5),"p75":q(v,.75),"p90":q(v,.90),"p95":q(v,.95),"p99":q(v,.99),
            "max":max(v) if v else None,"min":min(v) if v else None}
out={}
out["cost_usd"]=dist("cost_usd",[r["cost_usd"] for r in rows])
out["cost_r"]=dist("cost_r",[r["cost_r"] for r in rows])
out["spread_usd"]=dist("spread_usd",[r["spread_usd"] for r in rows])
out["commission_usd"]=dist("commission_usd",[r["commission_usd"] for r in rows])
out["swap_usd"]=dist("swap_usd",[r["swap_usd"] for r in rows])
out["slippage_usd"]=dist("slippage_usd",[r["slippage_usd"] for r in rows])
out["notional_usd"]=dist("notional_usd",[r["notional_usd"] for r in rows])
out["lots"]=dist("lots",[r["lots"] for r in rows])
out["cost_bp_of_notional"]=dist("cost_bp",[r["cost_bp_of_notional"] for r in rows])
out["risk_usd"]=dist("risk_usd",[r["risk_usd"] for r in rows])
out["true_total_cost_usd"]=dist("true_usd",[r["true_total_cost_usd"] for r in rows])
out["true_total_cost_r"]=dist("true_r",[r["true_total_cost_r"] for r in rows])
out["spread_overcharge_x"]=dist("ovx",[r["spread_overcharge_x"] for r in rows])
# per symbol overcharge
per={}
for r in rows:
    s=r["symbol"]; per.setdefault(s,{"n":0,"ov":[],"froz":[],"true":[],"cost_usd":[],"cost_r":[],"bp":[]})
    d=per[s]; d["n"]+=1
    if r["spread_overcharge_x"]: d["ov"].append(r["spread_overcharge_x"])
    if r["frozen_spread_price"]: d["froz"].append(r["frozen_spread_price"])
    if r["true_spread_price"]: d["true"].append(r["true_spread_price"])
    if r["cost_usd"] is not None: d["cost_usd"].append(r["cost_usd"])
    if r["cost_r"] is not None: d["cost_r"].append(r["cost_r"])
    if r["cost_bp_of_notional"] is not None: d["bp"].append(r["cost_bp_of_notional"])
sym={}
for s,d in per.items():
    sym[s]={"n":d["n"],
      "median_overcharge_x":q(d["ov"],.5),"mean_overcharge_x":(sum(d["ov"])/len(d["ov"]) if d["ov"] else None),
      "median_frozen_spread_price":q(d["froz"],.5),"true_spread_price_p50":q(d["true"],.5),
      "median_cost_usd":q(d["cost_usd"],.5),"mean_cost_usd":sum(d["cost_usd"])/len(d["cost_usd"]),
      "median_cost_r":q(d["cost_r"],.5),"mean_cost_r":sum(d["cost_r"])/len(d["cost_r"]),
      "median_cost_bp_notional":q(d["bp"],.5)}
out["per_symbol"]=sym
# per risk_pct bucket
rpb={}
for r in rows:
    k=str(r["risk_per_trade_pct"]); rpb.setdefault(k,{"n":0,"cu":[],"cr":[],"g":[]})
    rpb[k]["n"]+=1; rpb[k]["cu"].append(r["cost_usd"]); rpb[k]["cr"].append(r["cost_r"])
    if r["gross_r"] is not None: rpb[k]["g"].append(r["gross_r"])
out["per_risk_pct"]={k:{"n":v["n"],"mean_cost_usd":sum(v["cu"])/len(v["cu"]),"median_cost_usd":q(v["cu"],.5),
                        "mean_cost_r":sum(v["cr"])/len(v["cr"]),"median_cost_r":q(v["cr"],.5),
                        "mean_gross_r":sum(v["g"])/len(v["g"]) if v["g"] else None,
                        "risk_usd":100000.0*float(k)/100.0} for k,v in sorted(rpb.items(),key=lambda x:float(x[0]))}
json.dump(out,open(os.path.join(DISC,"l5_MONEY_SUMMARY_V1.json"),"w"),indent=1)
f=lambda x: "None" if x is None else (f"{x:,.4f}" if abs(x)<1000 else f"{x:,.0f}")
print("=== POOL-WIDE (n=%d) ==="%len(rows))
for k in ["cost_r","cost_usd","spread_usd","commission_usd","slippage_usd","swap_usd","true_total_cost_r","true_total_cost_usd","cost_bp_of_notional","notional_usd","lots","risk_usd"]:
    d=out[k]; print(f"{k:24s} mean {f(d['mean'])} p25 {f(d['p25'])} p50 {f(d['p50'])} p75 {f(d['p75'])} p95 {f(d['p95'])} max {f(d['max'])}")
print("\n=== PER SYMBOL: frozen vs measured spread (price units) ===")
print(f"{'sym':11s} {'n':>5s} {'froz_p50':>10s} {'true_p50':>10s} {'ovx_med':>8s} {'cost$_med':>10s} {'cost_r_med':>10s} {'bp_notl':>8s}")
for s,v in sorted(sym.items(),key=lambda x:-(x[1]['median_overcharge_x'] or 0)):
    print(f"{s:11s} {v['n']:5d} {f(v['median_frozen_spread_price']):>10s} {f(v['true_spread_price_p50']):>10s} {f(v['median_overcharge_x']):>8s} {f(v['median_cost_usd']):>10s} {f(v['median_cost_r']):>10s} {f(v['median_cost_bp_notional']):>8s}")
print("\n=== PER RISK BUCKET ===")
for k,v in out["per_risk_pct"].items():
    print(f"risk {k:>5s}% (${v['risk_usd']:,.0f}) n {v['n']:6d} mean cost_r {v['mean_cost_r']:.4f} mean cost$ {v['mean_cost_usd']:8.2f} med cost$ {v['median_cost_usd']:8.2f} mean gross_r {v['mean_gross_r']:.4f}")
