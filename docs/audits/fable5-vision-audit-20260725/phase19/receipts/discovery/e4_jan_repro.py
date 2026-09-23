import gzip, json, os, sys, math, random
from collections import defaultdict
HERE="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0,HERE)
import w0_ws
ANCHOR=os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
rows=w0_ws.load()
by={(r["candidate_id"],r["decision_time_utc"]):r for r in rows}
with gzip.open(ANCHOR,"rt") as fh:
    for line in fh:
        if line.strip():
            a=json.loads(line); t=by.get((a["candidate_id"],a["decision_time_utc"]))
            if t is not None: t["_mkt_r"]=a.get("mkt_r_prev_close")
def bucket(m):
    if m is None: return "unanchored"
    if m<=-1.0: return "past_stop"
    if m<0: return "marketable"
    if m==0: return "at_limit"
    for lo,hi,name in [(0,.25,"rest_0-0.25R"),(.25,.5,"rest_0.25-0.5R"),(.5,1,"rest_0.5-1R"),
                       (1,2,"rest_1-2R"),(2,5,"rest_2-5R")]:
        if lo<m<=hi: return name
    return "rest_gt5R"
def agg(v,keys):
    o={"n":len(v)}
    for k in keys:
        x=[r.get(k) for r in v if r.get(k) is not None]
        o[k]=round(sum(x)/len(x),6) if x else None
    o["win_gross"]=round(sum(1 for r in v if (r.get("gross_r") or 0)>0)/len(v),5) if v else None
    tt=[r for r in v if r.get("entry_touched") is not None]
    o["entry_touch_rate"]=round(sum(1 for r in tt if r["entry_touched"])/len(tt),5) if tt else None
    return o
KEYS=["execution_fill_probability","gross_r","fill_honest_walk_r","cost_r"]
buckets=defaultdict(list)
for r in rows: buckets[bucket(r.get("_mkt_r"))].append(r)
ORDER=["past_stop","marketable","at_limit","rest_0-0.25R","rest_0.25-0.5R","rest_0.5-1R","rest_1-2R","rest_2-5R","rest_gt5R","unanchored"]
btab={b:agg(buckets[b],KEYS) for b in ORDER if buckets[b]}

# decile table on the model probability itself
def deciles(pop,field="execution_fill_probability"):
    v=[r for r in pop if r.get(field) is not None]
    v.sort(key=lambda r:r[field])
    out=[]; n=len(v)
    for i in range(10):
        s=v[i*n//10:(i+1)*n//10]
        out.append({"d":i+1,"n":len(s),"p_lo":round(s[0][field],4),"p_hi":round(s[-1][field],4),
                    **{k:v2 for k,v2 in agg(s,KEYS).items() if k!="n"}})
    return out
POP={"ALL":rows,"CLEAN":[r for r in rows if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0]}
dtab={k:deciles(v) for k,v in POP.items()}

# calibration: model P vs realised entry touch
def calib(pop):
    v=[r for r in pop if r.get("execution_fill_probability") is not None and r.get("entry_touched") is not None]
    y=[1.0 if r["entry_touched"] else 0.0 for r in v]
    p=[r["execution_fill_probability"] for r in v]
    base=sum(y)/len(y)
    br=sum((pi-yi)**2 for pi,yi in zip(p,y))/len(y)
    b0=sum((base-yi)**2 for yi in y)/len(y)
    return {"n":len(v),"model_mean":round(sum(p)/len(p),6),"realised_touch":round(base,6),
            "brier":round(br,6),"brier_base":round(b0,6),"brier_skill":round(1-br/b0,4)}
cal={k:calib(v) for k,v in POP.items()}

# selection rule: production score vs lowest-fill, per decision window
W_EV,W_P,W_CONF,W_COMP,W_FILL,W_XFER,W_COST=0.55,1.20,0.20,0.15,0.10,6.00,0.80
def prod_score(r):
    ev,p,c=r.get("candidate_ev_r"),r.get("candidate_probability"),r.get("cost_r")
    f,k,conf=r.get("execution_fill_probability"),r.get("source_completeness"),r.get("candidate_confidence")
    if None in (ev,p,c,k,conf): return None
    f=0.0 if f is None else f; k=max(0.,min(1.,float(k)))
    pm,fm=max(0.,min(1.,p)),max(0.,min(1.,f)); net=ev-c
    return (W_EV*ev+W_P*(p-.5)+W_CONF*conf+W_COMP*k+W_FILL*f
            +W_XFER*max(0.,net)*pm*fm*k-W_COST*c)
def summ(v):
    n=len(v); m=sum(v)/n
    sd=(sum((x-m)**2 for x in v)/max(1,n-1))**.5
    return {"n":n,"mean":round(m,6),"t":round(m/(sd/math.sqrt(n)),3) if sd else None}
def selection(pop,label):
    us=[]
    for r in pop:
        s=prod_score(r)
        if s is None or r.get("execution_fill_probability") is None: continue
        r["_ps"]=s; us.append(r)
    wins=defaultdict(list)
    for r in us: wins[r["decision_time_utc"]].append(r)
    rules={"PROD_score":lambda r:r["_ps"],
           "LOWEST_fill":lambda r:-r["execution_fill_probability"],
           "HIGHEST_fill":lambda r:r["execution_fill_probability"],
           "RANDOM":None}
    rng=random.Random(1234)
    out={"n_windows":len(wins),"rules":{}}
    picks={}
    for name,fn in rules.items():
        picks[name]={}
        for w,c in wins.items():
            picks[name][w]=rng.choice(c) if fn is None else max(c,key=fn)
    for y in ("gross_r","fill_honest_walk_r","plain_walk_r"):
        out["rules"][y]={}
        for name in rules:
            v=[picks[name][w].get(y) for w in wins if picks[name][w].get(y) is not None]
            out["rules"][y][name]=summ(v)
        d=[]
        for w in wins:
            a=picks["PROD_score"][w].get(y); b=picks["LOWEST_fill"][w].get(y)
            if a is not None and b is not None: d.append(b-a)
        s=summ(d); s["frac_positive"]=round(sum(1 for x in d if x>0)/len(d),5)
        out["rules"][y]["PAIRED_lowest_minus_prod"]=s
    # permutation on honest
    d=[]
    for w in wins:
        a=picks["PROD_score"][w].get("fill_honest_walk_r"); b=picks["LOWEST_fill"][w].get("fill_honest_walk_r")
        if a is not None and b is not None: d.append(b-a)
    obs=sum(d)/len(d); rng2=random.Random(4242); cnt=0
    for _ in range(4000):
        s=sum(x if rng2.random()<.5 else -x for x in d)/len(d)
        if abs(s)>=abs(obs): cnt+=1
    out["perm_honest"]={"n":len(d),"observed":round(obs,6),"p":round((cnt+1)/4001,5)}
    return out
sel={k:selection(v,k) for k,v in POP.items()}
res={"month":"JANUARY_2026","source":"CJ_RECLOCKED_S0R0 + w0 working set + w0cap2 anchor",
     "n_rows":len(rows),"distance_buckets":btab,"model_p_deciles":dtab,"calibration":cal,"selection":sel}
json.dump(res,open("/tmp/e4/E4_JAN_REPRO_V1.json","w"),indent=1)
print("== DISTANCE BUCKETS (Jan)")
print("%-16s %6s %8s %8s %9s %9s %8s"%("bucket","n","modelP","touch","gross","honest","win"))
for b in ORDER:
    if b not in btab: continue
    t=btab[b]
    print("%-16s %6d %8.4f %8s %9.4f %9.4f %8.4f"%(b,t["n"],t["execution_fill_probability"] or 0,
      ("%.4f"%t["entry_touch_rate"]) if t["entry_touch_rate"] is not None else "-",
      t["gross_r"],t["fill_honest_walk_r"],t["win_gross"]))
print("== CALIBRATION",json.dumps(cal))
for k in ("ALL","CLEAN"):
    s=sel[k]
    print("== SELECTION",k,"windows",s["n_windows"])
    for y in ("gross_r","fill_honest_walk_r"):
        rr=s["rules"][y]
        print("  ",y,{n:rr[n]["mean"] for n in rr})
    print("   perm",s["perm_honest"])
