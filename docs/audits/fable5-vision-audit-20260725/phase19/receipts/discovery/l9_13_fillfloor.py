import json, collections
import l9_lib as L
rows=L.load(); tk=[r for r in rows if r["takeable"]]
fp=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else None)
def hz(r):
    w=r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0)
def cell(v):
    s=L.stats([r.get("fill_honest_walk_r") for r in v]); z=L.stats([hz(r) for r in v])
    return {"n":len(v),"honest":s["mean"],"se":s["se"],"t":s["t"],"honest_zn":z["mean"],"zn_t":z["t"],
            "gross_r":L.mean([r["gross_r"] for r in v]),
            "pct_scheduler_materialized":100*sum(1 for r in v if r.get("scheduler_materialization_status")=="scheduler_option_materialized")/len(v),
            "mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
            "cost_r":L.mean([r["cost_r"] for r in v]),
            "pct_neither":100*sum(1 for r in v if r.get("fill_honest_which_came_first")=="neither")/len(v)}
OUT={}
bands=[("fp<0.25",lambda x:x is not None and x<0.25),
       ("0.25<=fp<0.35",lambda x:x is not None and 0.25<=x<0.35),
       ("0.35<=fp<0.45",lambda x:x is not None and 0.35<=x<0.45),
       ("0.45<=fp<0.70",lambda x:x is not None and 0.45<=x<0.70),
       ("0.70<=fp<0.80",lambda x:x is not None and 0.70<=x<0.80),
       ("fp>=0.80",lambda x:x is not None and x>=0.80),
       ("fp_null",lambda x:x is None)]
for lab,f in bands:
    v=[r for r in tk if f(fp(r))]
    if v: OUT.setdefault("bands_TAKEABLE",{})[lab]=cell(v)
    v2=[r for r in tk if f(fp(r)) and r["born_state"]=="resting"]
    if v2: OUT.setdefault("bands_RESTING",{})[lab]=cell(v2)
# what the floors exclude, in aggregate
for floor in [0.25,0.35,0.45,0.80]:
    below=[r for r in tk if fp(r) is not None and fp(r)<floor]
    above=[r for r in tk if fp(r) is not None and fp(r)>=floor]
    OUT.setdefault("floor_impact_TAKEABLE",{})[f"floor_{floor}"]={
        "n_excluded":len(below),"pct_excluded":100*len(below)/len(tk),
        "excluded_honest":L.mean([r.get("fill_honest_walk_r") for r in below]),
        "excluded_honest_zn":L.mean([hz(r) for r in below]),
        "kept_honest":L.mean([r.get("fill_honest_walk_r") for r in above]),
        "kept_honest_zn":L.mean([hz(r) for r in above]),
        "delta_excluded_minus_kept":L.mean([r.get("fill_honest_walk_r") for r in below])-L.mean([r.get("fill_honest_walk_r") for r in above])}
# does the floor actually bite: materialized rows' fp distribution
mat=[r for r in rows if r.get("scheduler_materialization_status")=="scheduler_option_materialized"]
OUT["materialized_fp"]={"n":len(mat),"mean_fp":L.mean([fp(r) for r in mat]),
  "pct_fp_ge_0.80":100*sum(1 for r in mat if (fp(r) or 0)>=0.80)/len(mat),
  "pct_fp_ge_0.45":100*sum(1 for r in mat if (fp(r) or 0)>=0.45)/len(mat),
  "pct_fp_lt_0.45":100*sum(1 for r in mat if (fp(r) or 1)<0.45)/len(mat),
  "honest":L.mean([r.get("fill_honest_walk_r") for r in mat])}
notmat=[r for r in rows if r.get("scheduler_materialization_status")!="scheduler_option_materialized"]
OUT["not_materialized_fp"]={"n":len(notmat),"mean_fp":L.mean([fp(r) for r in notmat]),
  "pct_fp_ge_0.80":100*sum(1 for r in notmat if (fp(r) or 0)>=0.80)/len(notmat),
  "pct_fp_lt_0.45":100*sum(1 for r in notmat if (fp(r) or 1)<0.45)/len(notmat)}
# the fill-floor veto cohort
vet=[r for r in rows if str(r.get("miss_reason") or "").startswith("scheduler_vetoed_candidate_package_fill_floor")]
OUT["fill_floor_veto_cohort"]=cell(vet) if vet else None
OUT["fill_floor_veto_cohort_takeable"]=cell([r for r in vet if r["takeable"]]) if vet else None
json.dump(OUT,open("L9_FILLFLOOR_V1.json","w"),indent=1,default=str)
for nm in ["bands_TAKEABLE","bands_RESTING"]:
    print("==",nm)
    print(f"{'band':>16} {'n':>6} {'honest':>8} {'t':>6} {'honestZN':>9} {'t':>6} {'gross':>8} {'mat%':>6} {'rank':>6} {'nei%':>6}")
    for k,v in OUT[nm].items():
        print(f"{k:>16} {v['n']:>6} {v['honest']:>8.4f} {(v['t'] or 0):>6.2f} {v['honest_zn']:>9.4f} {(v['zn_t'] or 0):>6.2f} {v['gross_r']:>8.4f} {v['pct_scheduler_materialized']:>6.1f} {v['mean_rank']:>6.1f} {v['pct_neither']:>6.1f}")
print("== floor impact (TAKEABLE) ==")
for k,v in OUT["floor_impact_TAKEABLE"].items():
    print(f"   {k:>12} excl n={v['n_excluded']:>5} ({v['pct_excluded']:>4.1f}%) exclHonest={v['excluded_honest']:+.4f} ZN={v['excluded_honest_zn']:+.4f} keptHonest={v['kept_honest']:+.4f} ZN={v['kept_honest_zn']:+.4f} delta={v['delta_excluded_minus_kept']:+.4f}")
print("materialized:",{k:(round(v,4) if isinstance(v,float) else v) for k,v in OUT["materialized_fp"].items()})
print("not materialized:",{k:(round(v,4) if isinstance(v,float) else v) for k,v in OUT["not_materialized_fp"].items()})
print("fill_floor_veto cohort:",{k:(round(v,4) if isinstance(v,float) else v) for k,v in (OUT["fill_floor_veto_cohort"] or {}).items()})
