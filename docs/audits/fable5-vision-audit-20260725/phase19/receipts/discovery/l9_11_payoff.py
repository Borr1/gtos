import json, collections
import l9_lib as L
rows=L.load()
DIV=7.3
def netr(r, honest):
    sp=r["spread_r"]/DIV
    cost=r["cost_r"]-r["spread_r"]+sp
    return honest-cost
def hz(r):  # zero-neither convention
    w=r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0)
OUT={}
# (a) cost-release with n's, takeable only
def passes(r,div):
    sp=r["spread_r"]/div; tot=r["cost_r"]-r["spread_r"]+sp
    return sp<=0.10 and tot<=0.15
for div in [1.0,7.3,8.5]:
    tk=[r for r in rows if r["takeable"] and passes(r,div)]
    al=[r for r in rows if passes(r,div)]
    OUT.setdefault("cost_release",{})[f"div_{div}"]={
      "n_all":len(al),"n_takeable":len(tk),"n_past_stop":len(al)-len(tk),
      "honest_all":L.mean([r.get("fill_honest_walk_r") for r in al]),
      "honest_takeable":L.mean([r.get("fill_honest_walk_r") for r in tk]),
      "gross_takeable":L.mean([r["gross_r"] for r in tk])}
a=OUT["cost_release"]["div_1.0"]; b=OUT["cost_release"]["div_7.3"]
OUT["cost_release_attribution"]={
  "honest_all_delta":b["honest_all"]-a["honest_all"],
  "honest_takeable_delta":b["honest_takeable"]-a["honest_takeable"],
  "pct_of_degradation_from_past_stop":100*(1-(b["honest_takeable"]-a["honest_takeable"])/(b["honest_all"]-a["honest_all"]))}

# (b) day-level conviction: does breadth predict quality?
day=collections.defaultdict(list)
for r in rows:
    if r["takeable"]: day[r["decision_time_utc"][:10]].append(r)
pts=[(len(v),L.mean([r.get("fill_honest_walk_r") for r in v])) for v in day.values()]
sp,_=L.spearman(pts)
OUT["day_breadth_vs_quality"]={"n_days":len(pts),"spearman":sp,
  "table":[{"day":k,"n":len(v),"honest":L.mean([r.get("fill_honest_walk_r") for r in v])} for k,v in sorted(day.items())]}
# cycle-level breadth
cyc=collections.defaultdict(list)
for r in rows:
    if r["takeable"]: cyc[r["decision_time_utc"]].append(r)
cp=[(len(v),L.mean([r.get("fill_honest_walk_r") for r in v])) for v in cyc.values()]
sp2,_=L.spearman(cp)
OUT["cycle_breadth_vs_quality"]={"n_cycles":len(cp),"spearman":sp2}

# (d) implementable per-cycle rules, net of corrected cost
g={t:v for t,v in cyc.items() if len(v)>=5}
rules={}
def add(nm,pick):
    hs=[];zs=[];ns=[];nz=[]
    for t,v in g.items():
        r=pick(v)
        if r is None: continue
        h=r.get("fill_honest_walk_r") or 0.0
        hs.append(h); zs.append(hz(r)); ns.append(netr(r,h)); nz.append(netr(r,hz(r)))
    S=L.stats
    rules[nm]={"n":len(hs),"honest":S(hs)["mean"],"honest_t":S(hs)["t"],
               "honest_zeroneither":S(zs)["mean"],"zn_t":S(zs)["t"],
               "net_at_spread_div7.3":S(ns)["mean"],"net_t":S(ns)["t"],
               "net_zn":S(nz)["mean"],"net_zn_t":S(nz)["t"]}
fp=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9.0)
add("allocator_rank1",lambda v:sorted(v,key=lambda r:r["risk_finalizer_rank"])[0])
add("most_passive_pos1",lambda v:sorted(v,key=fp)[0])
add("most_passive_pos1_costgated",lambda v:(sorted([r for r in v if passes(r,DIV)],key=fp)[0] if any(passes(r,DIV) for r in v) else None))
add("widest_riskdist",lambda v:max(v,key=lambda r:(r["risk_distance"]/r["entry_price"]) if r.get("entry_price") else -1))
add("passive_AND_wide",lambda v:sorted(v,key=lambda r:(fp(r), -(r["risk_distance"]/r["entry_price"] if r.get("entry_price") else 0)))[0])
# group-mean baseline computed explicitly
hs=[];zs=[];ns=[];nz=[]
for t,v in g.items():
    hs.append(L.mean([r.get("fill_honest_walk_r") for r in v]))
    zs.append(sum(hz(r) for r in v)/len(v))
    ns.append(sum(netr(r,r.get("fill_honest_walk_r") or 0.0) for r in v)/len(v))
    nz.append(sum(netr(r,hz(r)) for r in v)/len(v))
S=L.stats
rules["random_proxy_groupmean"]={"n":len(hs),"honest":S(hs)["mean"],"honest_t":S(hs)["t"],
   "honest_zeroneither":S(zs)["mean"],"zn_t":S(zs)["t"],"net_at_spread_div7.3":S(ns)["mean"],
   "net_t":S(ns)["t"],"net_zn":S(nz)["mean"],"net_zn_t":S(nz)["t"]}
OUT["per_cycle_rules"]=rules
json.dump(OUT,open("L9_PAYOFF_V1.json","w"),indent=1,default=str)
print("cost_release:")
for k,v in OUT["cost_release"].items():
    print(f"   {k:>9} nAll={v['n_all']:>6} nTk={v['n_takeable']:>6} nPS={v['n_past_stop']:>5} honestAll={v['honest_all']:+.4f} honestTk={v['honest_takeable']:+.4f}")
print("attribution:",{k:round(v,4) for k,v in OUT["cost_release_attribution"].items()})
print("day breadth rho:",round(sp["rho"],4) if sp else None,"n_days",len(pts),
      "| cycle breadth rho:",round(sp2["rho"],4) if sp2 else None,"n_cycles",len(cp))
print("per-cycle rules (groups>=5, n=%d):"%len(g))
print(f"{'rule':>30} {'n':>5} {'honest':>8} {'t':>6} {'hZN':>8} {'t':>6} {'net7.3':>8} {'t':>6} {'netZN':>8} {'t':>6}")
for k,v in sorted(rules.items(),key=lambda kv:-kv[1]["honest"]):
    print(f"{k:>30} {v['n']:>5} {v['honest']:>8.4f} {(v['honest_t'] or 0):>6.2f} {v['honest_zeroneither']:>8.4f} {(v['zn_t'] or 0):>6.2f} {v['net_at_spread_div7.3']:>8.4f} {(v['net_t'] or 0):>6.2f} {v['net_zn']:>8.4f} {(v['net_zn_t'] or 0):>6.2f}")
