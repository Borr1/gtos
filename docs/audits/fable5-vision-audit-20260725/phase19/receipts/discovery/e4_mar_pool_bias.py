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
            fs=str(r.get("counterfactual_order_fill_status") or "")
            r["filled"]=(1 if fs.startswith("filled") else (0 if fs.startswith("not_filled") else None))
            rows.append(r)
pool=[r for r in rows if r.get("missed_opportunity_non_executable_diagnostic_scoreable") is True]
non =[r for r in rows if r.get("missed_opportunity_non_executable_diagnostic_scoreable") is not True]
out={"n_ledger":len(rows),"n_pool":len(pool),"n_nonpool":len(non)}
out["pool_fill_census"]=dict(collections.Counter(r["filled"] for r in pool))
out["nonpool_fill_census"]=dict(collections.Counter(r["filled"] for r in non))
out["pool_fill_status"]=dict(collections.Counter(r.get("counterfactual_order_fill_status") for r in pool).most_common(8))
out["nonpool_fill_status"]=dict(collections.Counter(r.get("counterfactual_order_fill_status") for r in non).most_common(8))
def q(v,ps=(0.05,0.25,0.5,0.75,0.95)):
    v=sorted(x for x in v if x is not None)
    return {str(p):round(v[min(len(v)-1,int(p*len(v)))],4) for p in ps} if v else None
out["pool_modelP_quantiles"]=q([r["fillp"] for r in pool])
out["nonpool_modelP_quantiles"]=q([r["fillp"] for r in non])
out["pool_modelP_mean"]=L.mean([r["fillp"] for r in pool if r["fillp"] is not None])
out["nonpool_modelP_mean"]=L.mean([r["fillp"] for r in non if r["fillp"] is not None])
out["pool_modelP_eq092"]=sum(1 for r in pool if r["fillp"] is not None and abs(r["fillp"]-0.92)<1e-9)
out["nonpool_modelP_eq092"]=sum(1 for r in non if r["fillp"] is not None and abs(r["fillp"]-0.92)<1e-9)
out["pool_gross_mean"]=L.mean([r["gross"] for r in pool if r["gross"] is not None])
out["pool_gross_n"]=sum(1 for r in pool if r["gross"] is not None)
# fill rate by model-P bucket for filled-vs-not within the NON-pool (the invisible population)
json.dump(out,open("/tmp/e4/E4_MAR_POOLBIAS_V1.json","w"),indent=1,default=str)
for k,v in out.items(): print(k,"=",v)
