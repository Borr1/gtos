import json, collections, math
import l9_lib as L
rows=L.load()
tk=[r for r in rows if r["takeable"]]
for r in rows:
    ep=r.get("entry_price"); r["risk_distance_pct"]=100.0*r["risk_distance"]/ep if ep else None
g={t:v for t,v in L.groups(tk).items() if len(v)>=5}
OUT={"n_groups_ge5":len(g),"n_rows":sum(len(v) for v in g.values())}

# ladder by within-cycle passivity position (1 = most passive = lowest fill prob)
lad=collections.defaultdict(list); ladq=collections.defaultdict(list)
allo=collections.defaultdict(list)
for t,v in g.items():
    order=sorted(v,key=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9.0))
    n=len(order)
    for i,r in enumerate(order):
        lad[min(i+1,8)].append(r)
        ladq[min(4,int(5.0*i/n))].append(r)
    ro=sorted(v,key=lambda r:r["risk_finalizer_rank"])
    for i,r in enumerate(ro): allo[min(4,int(5.0*i/n))].append(r)
def blk(d,keyfmt):
    t={}
    for k in sorted(d):
        v=d[k]; s=L.stats([r.get("fill_honest_walk_r") for r in v])
        t[keyfmt(k)]={"n":len(v),"honest_mean":s["mean"],"honest_se":s["se"],"t":s["t"],
            "gross_r":L.mean([r["gross_r"] for r in v]),
            "mean_fp":L.mean([r.get("execution_fill_probability") for r in v]),
            "mean_rank":L.mean([r["risk_finalizer_rank"] for r in v]),
            "risk_dist_pct":L.mean([r["risk_distance_pct"] for r in v]),
            "pct_neither":100*sum(1 for r in v if r.get("fill_honest_which_came_first")=="neither")/len(v)}
    return t
OUT["passivity_position"]=blk(lad,lambda k:f"pos{k}")
OUT["passivity_quintile"]=blk(ladq,lambda k:f"P{k+1}")
OUT["allocator_quintile"]=blk(allo,lambda k:f"A{k+1}")

# 2-way: passivity quintile x risk_distance_pct quartile (within-cycle, both)
two=collections.defaultdict(list)
for t,v in g.items():
    n=len(v)
    op=sorted(v,key=lambda r:(r.get("execution_fill_probability") or 9.0))
    pq={id(r):min(4,int(5.0*i/n)) for i,r in enumerate(op)}
    od=sorted(v,key=lambda r:(r["risk_distance_pct"] if r["risk_distance_pct"] is not None else -1))
    dq={id(r):min(3,int(4.0*i/n)) for i,r in enumerate(od)}
    for r in v: two[(pq[id(r)],dq[id(r)])].append(r)
OUT["two_way_passivity_x_riskdist"]={f"P{a+1}_D{b+1}":{"n":len(v),"honest":L.mean([r.get("fill_honest_walk_r") for r in v])} for (a,b),v in sorted(two.items())}
json.dump(OUT,open("L9_PASSIVITY_V1.json","w"),indent=1,default=str)
print("groups>=5:",OUT["n_groups_ge5"],"rows:",OUT["n_rows"])
for nm in ["passivity_position","passivity_quintile","allocator_quintile"]:
    print("==",nm)
    t=OUT[nm]
    print(f"{'k':>6} {'n':>6} {'honest':>8} {'se':>7} {'t':>6} {'gross':>8} {'fp':>6} {'rank':>6} {'rdpct':>7} {'nei%':>6}")
    for k in t:
        d=t[k]
        print(f"{k:>6} {d['n']:>6} {d['honest_mean']:>8.4f} {d['honest_se']:>7.4f} {(d['t'] or 0):>6.2f} {d['gross_r']:>8.4f} {(d['mean_fp'] or 0):>6.3f} {d['mean_rank']:>6.1f} {(d['risk_dist_pct'] or 0):>7.4f} {d['pct_neither']:>6.1f}")
print("== 2-way P(passivity) x D(risk dist) honest ==")
for k,v in OUT["two_way_passivity_x_riskdist"].items():
    print(f"   {k} n={v['n']:>5} {v['honest']:+.4f}")
