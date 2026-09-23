import sys, json, math, random, collections
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
RETEST={"current_fvg_fill","current_ob_retest"}
def run(pop,Y,fams=None,seed=1234,perm=4000,minn=2):
    us=[]
    for r in pop:
        if fams is not None and r.get("origin_family") not in fams: continue
        s=L.prod_score(r,"fillp")
        if s is None or r.get("fillp") is None or r.get(Y) is None: continue
        r["_ps"]=s; us.append(r)
    wins=collections.defaultdict(list)
    for r in us: wins[r["decision_time_utc"]].append(r)
    wins={w:c for w,c in wins.items() if len(c)>=minn}
    rng=random.Random(seed)
    R={"PROD":lambda r:r["_ps"],"LOWEST_fill":lambda r:-r["fillp"],
       "HIGHEST_fill":lambda r:r["fillp"],"RANDOM":None}
    picks={n:{w:(rng.choice(c) if f is None else max(c,key=f)) for w,c in wins.items()} for n,f in R.items()}
    o={"n_windows":len(wins),"n_cand":len(us),
       "mean_window_size":round(sum(len(c) for c in wins.values())/max(1,len(wins)),2)}
    for n in R: o[n]=L.summ([picks[n][w][Y] for w in wins])
    for base in ("PROD","RANDOM"):
        d=[picks["LOWEST_fill"][w][Y]-picks[base][w][Y] for w in wins]
        s=L.summ(d); s["frac_positive"]=round(sum(1 for x in d if x>0)/len(d),4) if d else None
        if perm and d:
            rng2=random.Random(4242); obs=sum(d)/len(d); c=0
            for _ in range(perm):
                if abs(sum(x if rng2.random()<.5 else -x for x in d)/len(d))>=abs(obs): c+=1
            s["perm_p"]=round((c+1)/(perm+1),5)
        o["vs_"+base]=s
    return o
out={}
CASES=[("JAN_retest","gross",JAN,RETEST),("JAN_retest_honest","honest",JAN,RETEST),
       ("FEB_retest","gross",FEB,RETEST),("MAR_retest","gross",MAR,RETEST),
       ("JAN_displacement","gross",JAN,{"displacement_continuation"}),
       ("FEB_displacement","gross",FEB,{"displacement_continuation"}),
       ("MAR_displacement","gross",MAR,{"displacement_continuation"})]
for tag,Y,pop,f in CASES: out[tag]=run(pop,Y,f)
# pooled three-month retest slope
def prep(pop,Y="gross",fams=None,minn=3):
    wins=collections.defaultdict(list)
    for r in pop:
        if fams and r.get("origin_family") not in fams: continue
        if r.get("fillp") is not None and r.get(Y) is not None: wins[r["decision_time_utc"]].append(r)
    pts=[]
    for w,c in wins.items():
        n=len(c)
        if n<minn or len(set(round(x["fillp"],9) for x in c))<2: continue
        order=sorted(range(n),key=lambda i:c[i]["fillp"]); rk=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and c[order[j+1]]["fillp"]==c[order[i]]["fillp"]: j+=1
            for t in range(i,j+1): rk[order[t]]=(i+j)/2.0
            i=j+1
        mg=sum(x[Y] for x in c)/n
        for i,x in enumerate(c): pts.append((rk[i]/(n-1)-0.5, x[Y]-mg))
    return pts
def slope(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; n=len(pts)
    mx=sum(xs)/n; my=sum(ys)/n; sxx=sum((x-mx)**2 for x in xs)
    b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sxx; a=my-b*mx
    s2=sum((y-(a+b*x))**2 for x,y in zip(xs,ys))/(n-2); se=math.sqrt(s2/sxx)
    return {"n":n,"slope":round(b,5),"se":round(se,5),"t":round(b/se,3)}
pooled=slope(prep(JAN,"gross",RETEST)+prep(FEB,"gross",RETEST)+prep(MAR,"gross",RETEST))
pooled_d=slope(prep(JAN,"gross",{"displacement_continuation"})+prep(FEB,"gross",{"displacement_continuation"})+prep(MAR,"gross",{"displacement_continuation"}))
out["POOLED_3MO_retest_slope"]=pooled
out["POOLED_3MO_displacement_slope"]=pooled_d
json.dump(out,open("/tmp/e4/E4_CONDITIONED_V1.json","w"),indent=1)
print("%-20s %5s %6s %6s %9s %9s %9s %9s %9s %7s"%("case","wins","ncand","wsize","PROD","LOWEST","HIGH","RANDOM","d_prod","p"))
for k in [c[0] for c in CASES]:
    v=out[k]
    print("%-20s %5d %6d %6.2f %9.4f %9.4f %9.4f %9.4f %+9.4f %7s"%(k,v["n_windows"],v["n_cand"],v["mean_window_size"],
      v["PROD"]["mean"],v["LOWEST_fill"]["mean"],v["HIGHEST_fill"]["mean"],v["RANDOM"]["mean"],
      v["vs_PROD"]["mean"],v["vs_PROD"]["perm_p"]))
print()
print("POOLED 3-month within-window slope, retest families:",pooled)
print("POOLED 3-month within-window slope, displacement    :",pooled_d)
