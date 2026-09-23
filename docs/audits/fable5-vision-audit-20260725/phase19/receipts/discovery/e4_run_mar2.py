import gzip, json, sys, collections
sys.path.insert(0,"/tmp/e4"); import e4lib as L
rows=[]
with gzip.open("/tmp/e4/MAR_R0_slim.jsonl.gz","rt") as fh:
    for line in fh:
        if line.strip():
            r=json.loads(line); r["fillp"]=r.get("cdq_execution_fill_probability")
            g=r.get("opportunity_gross_r")
            if g is None and r.get("opportunity_net_proxy_r") is not None and r.get("cost_r") is not None:
                g=r["opportunity_net_proxy_r"]+r["cost_r"]
            r["gross"]=g
            rows.append(r)
pool=[r for r in rows if r.get("missed_opportunity_non_executable_diagnostic_scoreable") is True]
wk="decision_time_utc" if pool[0].get("decision_time_utc") else "decision_window_id"
res={"month":"MARCH_2026","route":"FA2_M_R0","n_ledger":len(rows),"n":len(pool),
     "pool_gross_mean":L.mean([r["gross"] for r in pool if r["gross"] is not None]),
     "pool_win":round(sum(1 for r in pool if (r["gross"] or 0)>0)/len(pool),5),
     "mean_cost_r":L.mean([r["cost_r"] for r in pool if r.get("cost_r") is not None]),
     "model_p_mean":L.mean([r["fillp"] for r in pool if r["fillp"] is not None]),
     "model_p_eq_092":sum(1 for r in pool if r["fillp"] is not None and abs(r["fillp"]-0.92)<1e-9),
     "deciles":L.deciles(pool),"spearman_fillp_vs_gross":L.spearman(pool),
     "floors":L.floors(pool),"selection":L.selection(pool,wkey=wk)}
json.dump(res,open("/tmp/e4/E4_MAR_V1.json","w"),indent=1)
print("MAR pool n=%d gross=%.5f win=%.4f cost=%.4f modelP=%.4f p092=%d"%(
 res["n"],res["pool_gross_mean"],res["pool_win"],res["mean_cost_r"],res["model_p_mean"],res["model_p_eq_092"]))
print("%-3s %6s %8s %8s %9s %8s %8s"%("d","n","p_lo","p_hi","gross","win","cost"))
for c in res["deciles"]:
    print("%-3d %6d %8.4f %8.4f %9.4f %8.4f %8.4f"%(c["d"],c["n"],c["p_lo"],c["p_hi"],c["gross"],c["win"],c["cost_r"]))
print("spearman(fillp,gross)=",res["spearman_fillp_vs_gross"])
s=res["selection"]; print("windows",s["n_windows"],"usable",s["n_usable"],"wkey",wk)
g=s["gross"]; print({k:(g[k]["mean"] if isinstance(g[k],dict) else g[k]) for k in g if k!="perm_p"})
print("perm_p",g.get("perm_p"),"t_paired",g["PAIRED_lowest_minus_prod"]["t"],"fracpos",g["PAIRED_lowest_minus_prod"]["frac_positive"])
print("FLOORS: thr  n_below gross_below | n_above gross_above")
for t,d in res["floors"].items():
    print("  %-5s %7d %9.4f | %7d %9.4f"%(t,d["below"]["n"],d["below"]["gross"] or 0,d["above"]["n"],d["above"]["gross"] or 0))
