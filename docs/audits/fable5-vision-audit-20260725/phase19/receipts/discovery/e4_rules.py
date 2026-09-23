import sys, json, math, random, collections
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
NB=lambda p:[r for r in p if r.get("origin_family")!="current_breaker_re_entry"]
def risk_dist(r):
    try: return abs(float(r["entry_price"])-float(r["stop_loss"]))/max(1e-12,abs(float(r["entry_price"])))
    except Exception: return None
RULES={
 "PROD_score":       lambda r: r.get("_ps"),
 "LOWEST_fill":      lambda r: -r["fillp"],
 "HIGHEST_fill":     lambda r:  r["fillp"],
 "LOWEST_cost":      lambda r: -(r.get("cost_r") if r.get("cost_r") is not None else 9e9),
 "LOWEST_spread":    lambda r: -(r.get("spread_r") if r.get("spread_r") is not None else 9e9),
 "WIDEST_riskdist":  lambda r: (risk_dist(r) if risk_dist(r) is not None else -9e9),
 "HIGHEST_ev":       lambda r: (r.get("candidate_ev_r") if r.get("candidate_ev_r") is not None else -9e9),
 "HIGHEST_prob":     lambda r: (r.get("candidate_probability") if r.get("candidate_probability") is not None else -9e9),
 "LOWEST_fill_then_cost": lambda r: (-r["fillp"], -(r.get("cost_r") or 9e9)),
 "RANDOM":           None,
}
def run(pop,Y,seed=1234,perm=4000):
    us=[]
    for r in pop:
        s=L.prod_score(r,"fillp")
        if s is None or r.get("fillp") is None: continue
        r["_ps"]=s; us.append(r)
    wins=collections.defaultdict(list)
    for r in us: wins[r["decision_time_utc"]].append(r)
    rng=random.Random(seed); picks={}
    for name,fn in RULES.items():
        picks[name]={w:(rng.choice(c) if fn is None else max(c,key=fn)) for w,c in wins.items()}
    res={"n_windows":len(wins)}
    for name in RULES:
        res[name]=L.summ([picks[name][w].get(Y) for w in wins if picks[name][w].get(Y) is not None])
    for base in ("PROD_score","RANDOM"):
        d=[picks["LOWEST_fill"][w].get(Y)-picks[base][w].get(Y) for w in wins
           if picks["LOWEST_fill"][w].get(Y) is not None and picks[base][w].get(Y) is not None]
        s=L.summ(d); s["frac_positive"]=round(sum(1 for x in d if x>0)/len(d),4)
        if perm:
            rng2=random.Random(4242); obs=sum(d)/len(d); c=0
            for _ in range(perm):
                if abs(sum(x if rng2.random()<.5 else -x for x in d)/len(d))>=abs(obs): c+=1
            s["perm_p"]=round((c+1)/(perm+1),5)
        res["PAIRED_vs_"+base]=s
    return res
CASES=[("JAN_nb","gross",NB(JAN)),("JAN_nb","honest",NB(JAN)),("FEB_nb","gross",NB(FEB)),("MAR_nb","gross",NB(MAR))]
out={}
for tag,Y,pop in CASES:
    out[tag+"|"+Y]=run(pop,Y)
json.dump(out,open("/tmp/e4/E4_RULES_V1.json","w"),indent=1)
names=list(RULES)
print("%-14s %5s "%("case","wins")+" ".join("%9s"%n[:9] for n in names))
for k,v in out.items():
    print("%-14s %5d "%(k,v["n_windows"])+" ".join(("%9.4f"%v[n]["mean"]) if v[n].get("mean") is not None else "%9s"%"-" for n in names))
print()
for k,v in out.items():
    a,b=v["PAIRED_vs_PROD_score"],v["PAIRED_vs_RANDOM"]
    print("%-14s d_prod %+.4f t=%.2f p=%s fpos=%.3f | d_rand %+.4f t=%.2f p=%s"%(
        k,a["mean"],a["t"],a["perm_p"],a["frac_positive"],b["mean"],b["t"],b["perm_p"]))
