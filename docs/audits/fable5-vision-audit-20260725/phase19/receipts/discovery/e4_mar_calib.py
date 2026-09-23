import gzip, json, sys, collections, math
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
POP={"MAR_ALL_LEDGER":[r for r in rows if r["fillp"] is not None and r["filled"] is not None],
     "MAR_POOL":[r for r in rows if r.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
                 and r["fillp"] is not None and r["filled"] is not None]}
out={}
for name,pop in POP.items():
    y=[r["filled"] for r in pop]; p=[r["fillp"] for r in pop]
    base=sum(y)/len(y)
    br=sum((a-b)**2 for a,b in zip(p,y))/len(y); b0=sum((base-b)**2 for b in y)/len(y)
    # decile of model P -> realized fill rate
    v=sorted(pop,key=lambda r:r["fillp"]); n=len(v); dec=[]
    for i in range(10):
        s=v[i*n//10:(i+1)*n//10]
        dec.append({"d":i+1,"n":len(s),"p_lo":round(s[0]["fillp"],4),"p_hi":round(s[-1]["fillp"],4),
                    "model_p":round(sum(x["fillp"] for x in s)/len(s),5),
                    "realized_fill":round(sum(x["filled"] for x in s)/len(s),5),
                    "gross":L.mean([x["gross"] for x in s if x["gross"] is not None]),
                    "n_gross":sum(1 for x in s if x["gross"] is not None)})
    out[name]={"n":len(pop),"model_mean":round(sum(p)/len(p),6),"realized_fill":round(base,6),
               "brier":round(br,6),"brier_base":round(b0,6),"brier_skill":(round(1-br/b0,4) if b0>0 else None),
               "spearman_modelP_vs_filled":L.spearman(pop,"fillp","filled"),
               "deciles":dec}
json.dump(out,open("/tmp/e4/E4_MAR_CALIB_V1.json","w"),indent=1)
for name,d in out.items():
    print("==",name,"n=%d modelP=%.4f realizedFill=%.4f brier=%.4f base=%.4f SKILL=%.4f rho=%s"%(
        d["n"],d["model_mean"],d["realized_fill"],d["brier"],d["brier_base"],d["brier_skill"],d["spearman_modelP_vs_filled"]))
    print("   %-3s %7s %8s %8s %9s %9s"%("d","n","p_lo","p_hi","modelP","fillRate"))
    for c in d["deciles"]:
        print("   %-3d %7d %8.4f %8.4f %9.4f %9.4f  gross=%s"%(c["d"],c["n"],c["p_lo"],c["p_hi"],c["model_p"],c["realized_fill"],c["gross"]))
