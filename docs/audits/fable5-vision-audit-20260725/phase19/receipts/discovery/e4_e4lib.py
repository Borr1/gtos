import math, random, json
from collections import defaultdict
W_EV,W_P,W_CONF,W_COMP,W_FILL,W_XFER,W_COST=0.55,1.20,0.20,0.15,0.10,6.00,0.80
FLOORS=[0.25,0.35,0.45,0.70,0.80,0.90]
def prod_score(r,F="fillp"):
    ev,p,c=r.get("candidate_ev_r"),r.get("candidate_probability"),r.get("cost_r")
    f,k,conf=r.get(F),r.get("source_completeness"),r.get("candidate_confidence")
    if None in (ev,p,c,k,conf,f): return None
    k=max(0.,min(1.,float(k))); pm,fm=max(0.,min(1.,p)),max(0.,min(1.,f)); net=ev-c
    return (W_EV*ev+W_P*(p-.5)+W_CONF*conf+W_COMP*k+W_FILL*f+W_XFER*max(0.,net)*pm*fm*k-W_COST*c)
def mean(v): return round(sum(v)/len(v),6) if v else None
def summ(v):
    if not v: return {"n":0}
    n=len(v); m=sum(v)/n; sd=(sum((x-m)**2 for x in v)/max(1,n-1))**.5
    return {"n":n,"mean":round(m,6),"t":round(m/(sd/math.sqrt(n)),3) if sd else None}
def cell(v,Y="gross",F="fillp",extra=()):
    o={"n":len(v),"model_p":mean([r[F] for r in v if r.get(F) is not None]),
       "gross":mean([r[Y] for r in v if r.get(Y) is not None]),
       "win":round(sum(1 for r in v if (r.get(Y) or 0)>0)/len(v),5) if v else None,
       "cost_r":mean([r["cost_r"] for r in v if r.get("cost_r") is not None])}
    for e in extra:
        vals=[r[e] for r in v if r.get(e) is not None]
        o[e]=mean(vals)
    return o
def deciles(pop,F="fillp",Y="gross",extra=()):
    v=sorted([r for r in pop if r.get(F) is not None],key=lambda r:r[F]); n=len(v); out=[]
    for i in range(10):
        s=v[i*n//10:(i+1)*n//10]
        if not s: continue
        c=cell(s,Y,F,extra); c["d"]=i+1; c["p_lo"]=round(s[0][F],4); c["p_hi"]=round(s[-1][F],4)
        out.append(c)
    return out
def spearman(pop,F="fillp",Y="gross"):
    v=[r for r in pop if r.get(F) is not None and r.get(Y) is not None]
    n=len(v)
    if n<3: return None
    def ranks(key):
        idx=sorted(range(n),key=lambda i:v[i][key]); rk=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and v[idx[j+1]][key]==v[idx[i]][key]: j+=1
            avg=(i+j)/2.0+1
            for t in range(i,j+1): rk[idx[t]]=avg
            i=j+1
        return rk
    a,b=ranks(F),ranks(Y)
    ma,mb=sum(a)/n,sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return round(num/den,5) if den else None
def floors(pop,F="fillp",Y="gross"):
    out={}
    for t in FLOORS:
        below=[r for r in pop if r.get(F) is not None and r[F]<t]
        above=[r for r in pop if r.get(F) is not None and r[F]>=t]
        out[str(t)]={"below":cell(below,Y,F),"above":cell(above,Y,F)}
    return out
def selection(pop,F="fillp",Ys=("gross",),wkey="decision_time_utc",perm=4000,seed=1234):
    us=[]
    for r in pop:
        s=prod_score(r,F)
        if s is None: continue
        r["_ps"]=s; us.append(r)
    wins=defaultdict(list)
    for r in us: wins[r[wkey]].append(r)
    rng=random.Random(seed)
    rules={"PROD_score":lambda r:r["_ps"],"LOWEST_fill":lambda r:-r[F],
           "HIGHEST_fill":lambda r:r[F],"RANDOM":None,
           "LOWEST_cost":lambda r:-(r.get("cost_r") or 9e9),
           "HIGHEST_ev":lambda r:(r.get("candidate_ev_r") or -9e9)}
    picks={}
    for name,fn in rules.items():
        picks[name]={w:(rng.choice(c) if fn is None else max(c,key=fn)) for w,c in wins.items()}
    out={"n_windows":len(wins),"n_usable":len(us)}
    for y in Ys:
        o={}
        for name in rules:
            o[name]=summ([picks[name][w].get(y) for w in wins if picks[name][w].get(y) is not None])
        d=[picks["LOWEST_fill"][w].get(y)-picks["PROD_score"][w].get(y) for w in wins
           if picks["LOWEST_fill"][w].get(y) is not None and picks["PROD_score"][w].get(y) is not None]
        s=summ(d); s["frac_positive"]=round(sum(1 for x in d if x>0)/len(d),5) if d else None
        o["PAIRED_lowest_minus_prod"]=s
        d2=[picks["LOWEST_fill"][w].get(y)-picks["RANDOM"][w].get(y) for w in wins
            if picks["LOWEST_fill"][w].get(y) is not None and picks["RANDOM"][w].get(y) is not None]
        o["PAIRED_lowest_minus_random"]=summ(d2)
        if perm and d:
            rng2=random.Random(4242); obs=sum(d)/len(d); cnt=0
            for _ in range(perm):
                ss=sum(x if rng2.random()<.5 else -x for x in d)/len(d)
                if abs(ss)>=abs(obs): cnt+=1
            o["perm_p"]=round((cnt+1)/(perm+1),5)
        out[y]=o
    return out
