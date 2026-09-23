import json, collections
import l9_lib as L
rows=L.load(); tk=[r for r in rows if r["takeable"]]
OUT={}
def cell(v):
    s=L.stats([r.get("fill_honest_walk_r") for r in v])
    return {"n":len(v),"honest":s["mean"],"se":s["se"],"t":s["t"],
            "gross_r":L.mean([r["gross_r"] for r in v]),
            "mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
            "mean_fp":L.mean([r.get("execution_fill_probability") for r in v]),
            "share_past_stop":sum(1 for r in v if r["born_state"]=="past_stop")/len(v),
            "cost_r":L.mean([r["cost_r"] for r in v])}
def group_by(field,label,sub=None,bucket=None):
    sub = rows if sub is None else sub
    d=collections.defaultdict(list)
    for r in sub:
        k=r.get(field)
        d[bucket(k) if bucket else str(k)].append(r)
    OUT[label]={k:cell(v) for k,v in sorted(d.items(),key=str)}
group_by("effective_admission_count","admission_count_ALL")
group_by("effective_admission_count","admission_count_TAKEABLE",tk)
group_by("matched_sleeve_count","matched_sleeve_ALL")
group_by("matched_sleeve_count","matched_sleeve_TAKEABLE",tk)
group_by("scheduler_selection_disposition","disposition_ALL")
group_by("scheduler_selection_disposition","disposition_TAKEABLE",tk)
group_by("scheduler_materialization_status","materialization_TAKEABLE",tk)
group_by("candidate_lifecycle_action","lifecycle_ALL")
group_by("final_blocker_class","blocker_TAKEABLE",tk)
group_by("risk_finalizer_reason","finalizer_reason_ALL")
def qb(v,edges):
    if v is None: return "null"
    if v==0: return "0"
    for e in edges:
        if v<=e: return f"<= {e}"
    return f"> {edges[-1]}"
for f in ["same_symbol_exposure_risk_pct","same_side_pending_risk_pct","opposite_pending_risk_pct"]:
    group_by(f,f+"_TAKEABLE",tk,bucket=lambda v,f=f: qb(v,[0.25,0.5,1.0,2.0,4.0]))
json.dump(OUT,open("L9_ADMISSION_EXPOSURE_V1.json","w"),indent=1,default=str)
for lab in ["admission_count_TAKEABLE","matched_sleeve_TAKEABLE","disposition_TAKEABLE",
            "same_symbol_exposure_risk_pct_TAKEABLE","same_side_pending_risk_pct_TAKEABLE",
            "opposite_pending_risk_pct_TAKEABLE"]:
    print("==",lab)
    for k,v in OUT[lab].items():
        print(f"   {k:>58} n={v['n']:>6} honest={v['honest']:+.4f} t={(v['t'] or 0):+6.2f} gross={v['gross_r']:+.4f} rank={v['mean_rank']:>5.1f}")
print("== finalizer_reason (ALL, n>=40) ==")
for k,v in sorted(OUT["finalizer_reason_ALL"].items(),key=lambda kv:-kv[1]["honest"]):
    if v["n"]>=40:
        print(f"   {k[:62]:>62} n={v['n']:>6} honest={v['honest']:+.4f} t={(v['t'] or 0):+6.2f} past%={100*v['share_past_stop']:>5.1f}")
