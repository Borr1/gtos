import gzip, json, sys
sys.path.insert(0,"/tmp/e4"); import e4lib as L
P="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
rows=[]
with gzip.open(P,"rt") as fh:
    for line in fh:
        if line.strip():
            r=json.loads(line)
            r["fillp"]=r.get("execution_fill_probability")
            g=r.get("opportunity_gross_r")
            if g is None and r.get("opportunity_net_proxy_r") is not None and r.get("cost_r") is not None:
                g=r["opportunity_net_proxy_r"]+r["cost_r"]
            r["gross"]=g
            rows.append(r)
# sanity: does opportunity_gross_r == net + cost?
d=[abs(r["opportunity_gross_r"]-(r["opportunity_net_proxy_r"]+r["cost_r"])) for r in rows
   if r.get("opportunity_gross_r") is not None]
print("gross identity max abs dev", max(d) if d else None, "n", len(d))
res={"month":"FEBRUARY_2026","n":len(rows),
     "pool_gross_mean":L.mean([r["gross"] for r in rows if r["gross"] is not None]),
     "pool_win":round(sum(1 for r in rows if (r["gross"] or 0)>0)/len(rows),5),
     "mean_cost_r":L.mean([r["cost_r"] for r in rows]),
     "model_p_mean":L.mean([r["fillp"] for r in rows if r["fillp"] is not None]),
     "model_p_eq_092":sum(1 for r in rows if r["fillp"] is not None and abs(r["fillp"]-0.92)<1e-9),
     "deciles":L.deciles(rows),"spearman_fillp_vs_gross":L.spearman(rows),
     "floors":L.floors(rows),"selection":L.selection(rows)}
json.dump(res,open("/tmp/e4/E4_FEB_V1.json","w"),indent=1)
print("FEB n=%d gross=%.5f win=%.4f cost=%.4f modelP=%.4f p092=%d"%(
 res["n"],res["pool_gross_mean"],res["pool_win"],res["mean_cost_r"],res["model_p_mean"],res["model_p_eq_092"]))
print("%-3s %6s %8s %8s %9s %8s %8s"%("d","n","p_lo","p_hi","gross","win","cost"))
for c in res["deciles"]:
    print("%-3d %6d %8.4f %8.4f %9.4f %8.4f %8.4f"%(c["d"],c["n"],c["p_lo"],c["p_hi"],c["gross"],c["win"],c["cost_r"]))
print("spearman(fillp,gross)=",res["spearman_fillp_vs_gross"])
s=res["selection"]; print("windows",s["n_windows"],"usable",s["n_usable"])
g=s["gross"]; print({k:(g[k]["mean"] if isinstance(g[k],dict) else g[k]) for k in g if k!="perm_p"})
print("perm_p",g.get("perm_p"))
