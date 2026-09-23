import gzip, json, sys, os
sys.path.insert(0,"/tmp/e4")
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
def jan():
    sys.path.insert(0,DISC); import w0_ws
    rows=w0_ws.load()
    by={(r["candidate_id"],r["decision_time_utc"]):r for r in rows}
    with gzip.open(os.path.join(DISC,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
        for line in fh:
            if line.strip():
                a=json.loads(line); t=by.get((a["candidate_id"],a["decision_time_utc"]))
                if t is not None: t["_mkt_r"]=a.get("mkt_r_prev_close")
    for r in rows:
        r["fillp"]=r.get("execution_fill_probability"); r["gross"]=r.get("gross_r")
        r["honest"]=r.get("fill_honest_walk_r")
    return rows
def feb():
    P=("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
       "fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz")
    out=[]
    with gzip.open(P,"rt") as fh:
        for line in fh:
            if line.strip():
                r=json.loads(line); r["fillp"]=r.get("execution_fill_probability")
                r["gross"]=r.get("opportunity_gross_r"); out.append(r)
    return out
def mar(pool_only=True):
    out=[]
    with gzip.open("/tmp/e4/MAR_R0_slim.jsonl.gz","rt") as fh:
        for line in fh:
            if line.strip():
                r=json.loads(line)
                if pool_only and r.get("missed_opportunity_non_executable_diagnostic_scoreable") is not True:
                    continue
                r["fillp"]=r.get("cdq_execution_fill_probability")
                r["gross"]=r.get("opportunity_gross_r")
                fs=str(r.get("counterfactual_order_fill_status") or "")
                r["filled"]=(1 if fs.startswith("filled") else (0 if fs.startswith("not_filled") else None))
                out.append(r)
    return out
