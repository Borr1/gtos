import json, collections, random
import l9_lib as L
rows=L.load()
fp=lambda r:(r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9.0)
def hz(r):
    w=r.get("fill_honest_which_came_first")
    return 0.0 if w in ("neither","no_fill") else (r.get("fill_honest_walk_r") or 0.0)
OUT={}
def run(sub,minsize,label,dedup=False):
    s=[r for r in sub if (not dedup or r.get("is_first_emission"))]
    g={t:v for t,v in L.groups(s).items() if len(v)>=minsize}
    if not g: return
    p1=[sorted(v,key=fp)[0] for v in g.values()]
    gm=[L.mean([r.get("fill_honest_walk_r") for r in v]) for v in g.values()]
    a1=[sorted(v,key=lambda r:r["risk_finalizer_rank"])[0] for v in g.values()]
    S=L.stats
    OUT.setdefault("robustness",{})[label]={
      "n_cycles":len(g),"pos1_honest":S([r.get("fill_honest_walk_r") for r in p1])["mean"],
      "pos1_t":S([r.get("fill_honest_walk_r") for r in p1])["t"],
      "pos1_zn":S([hz(r) for r in p1])["mean"],
      "random_honest":S(gm)["mean"],
      "alloc1_honest":S([r.get("fill_honest_walk_r") for r in a1])["mean"],
      "alloc1_zn":S([hz(r) for r in a1])["mean"],
      "delta_pos1_minus_alloc1":S([r.get("fill_honest_walk_r") for r in p1])["mean"]-S([r.get("fill_honest_walk_r") for r in a1])["mean"]}
tk=[r for r in rows if r["takeable"]]
for ms in [2,3,5,8,12]: run(tk,ms,f"takeable_minsize{ms}")
run(tk,5,"takeable_minsize5_DEDUP_first_emission",dedup=True)
run(rows,5,"ALL_incl_past_stop_minsize5")
run([r for r in tk if r["born_state"]=="resting"],3,"RESTING_only_minsize3")
# permutation test: pos1 vs random pick, within-cycle
g={t:v for t,v in L.groups(tk).items() if len(v)>=5}
obs=L.mean([sorted(v,key=fp)[0].get("fill_honest_walk_r") for v in g.values()])
rnd=random.Random(99); null=[]
for it in range(2000):
    null.append(L.mean([rnd.choice(v).get("fill_honest_walk_r") or 0.0 for v in g.values()]))
ge=sum(1 for x in null if x>=obs)
OUT["permutation"]={"n_cycles":len(g),"observed_pos1":obs,"iters":2000,"n_null_ge_obs":ge,
   "p_one_sided":(ge+1)/2001,"null_mean":sum(null)/len(null),
   "null_p95":sorted(null)[int(0.95*len(null))],"null_max":max(null)}
# weekly stability
wk=collections.defaultdict(list)
for v in g.values():
    r=sorted(v,key=fp)[0]; wk[r["decision_time_utc"][:10]].append(r)
weeks=collections.defaultdict(list)
for d,v in wk.items():
    import datetime
    w=datetime.date.fromisoformat(d).isocalendar()[1]
    weeks[w].extend(v)
OUT["pos1_by_week"]={str(k):{"n":len(v),"honest":L.mean([r.get("fill_honest_walk_r") for r in v]),
    "zn":L.mean([hz(r) for r in v])} for k,v in sorted(weeks.items())}
json.dump(OUT,open("L9_ROBUST_V1.json","w"),indent=1,default=str)
print(f"{'variant':>44} {'cyc':>5} {'pos1':>8} {'t':>6} {'pos1ZN':>8} {'rand':>8} {'alloc1':>8} {'delta':>8}")
for k,v in OUT["robustness"].items():
    print(f"{k:>44} {v['n_cycles']:>5} {v['pos1_honest']:>8.4f} {(v['pos1_t'] or 0):>6.2f} {v['pos1_zn']:>8.4f} {v['random_honest']:>8.4f} {v['alloc1_honest']:>8.4f} {v['delta_pos1_minus_alloc1']:>8.4f}")
print("permutation:",{k:(round(v,5) if isinstance(v,float) else v) for k,v in OUT["permutation"].items()})
print("by week:",{k:(v['n'],round(v['honest'],4),round(v['zn'],4)) for k,v in OUT["pos1_by_week"].items()})
