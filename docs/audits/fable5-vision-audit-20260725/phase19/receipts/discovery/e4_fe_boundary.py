import sys, json, math, collections
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
NB=lambda p:[r for r in p if r.get("origin_family")!="current_breaker_re_entry"]
def prep(pop,Y="gross",minn=3):
    """within-window demean: returns list of (subgroup-dict, x=fill-rank centered, y=gross centered)"""
    wins=collections.defaultdict(list)
    for r in pop:
        if r.get("fillp") is not None and r.get(Y) is not None: wins[r["decision_time_utc"]].append(r)
    out=[]
    for w,c in wins.items():
        n=len(c)
        if n<minn: continue
        if len(set(round(x["fillp"],9) for x in c))<2: continue
        order=sorted(range(n),key=lambda i:c[i]["fillp"])
        rk=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and c[order[j+1]]["fillp"]==c[order[i]]["fillp"]: j+=1
            avg=(i+j)/2.0
            for t in range(i,j+1): rk[order[t]]=avg
            i=j+1
        mg=sum(x[Y] for x in c)/n
        for i,x in enumerate(c):
            out.append((x, rk[i]/(n-1)-0.5, x[Y]-mg))
    return out
def slope(pts):
    if len(pts)<30: return None
    xs=[p[1] for p in pts]; ys=[p[2] for p in pts]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    sxx=sum((x-mx)**2 for x in xs)
    if sxx<=0: return None
    b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sxx
    a=my-b*mx
    resid=[y-(a+b*x) for x,y in zip(xs,ys)]
    s2=sum(e*e for e in resid)/max(1,len(pts)-2)
    se=math.sqrt(s2/sxx)
    return {"n":len(pts),"slope":round(b,5),"se":round(se,5),"t":round(b/se,3)}
CASES=[("JAN_nb",NB(JAN),"gross"),("JAN_nb_honest",NB(JAN),"honest"),
       ("FEB_nb",NB(FEB),"gross"),("MAR_nb",NB(MAR),"gross"),
       ("JAN_all",JAN,"gross"),("FEB_all",FEB,"gross"),("MAR_all",MAR,"gross")]
out={}
for tag,pop,Y in CASES:
    pts=prep(pop,Y)
    d={"OVERALL":slope(pts)}
    for axis in ("origin_family","symbol","session_bucket","utc_hour_bucket"):
        g=collections.defaultdict(list)
        for p in pts: g[str(p[0].get(axis))].append(p)
        tab={k:slope(v) for k,v in g.items()}
        d[axis]={k:v for k,v in sorted(((k,v) for k,v in tab.items() if v),key=lambda kv:kv[1]["slope"])}
    out[tag]=d
json.dump(out,open("/tmp/e4/E4_FE_BOUNDARY_V1.json","w"),indent=1)
print("OVERALL within-window slope (R per full low->high fill-rank sweep; NEGATIVE = low-fill better)")
for k,v in out.items():
    o=v["OVERALL"]; print("  %-16s n=%6d slope=%+.5f se=%.5f t=%+.2f"%(k,o["n"],o["slope"],o["se"],o["t"]))
print("\nFAMILY slope (no-breaker pops):")
fams=sorted(set(out["JAN_nb"]["origin_family"])|set(out["FEB_nb"]["origin_family"])|set(out["MAR_nb"]["origin_family"]))
print("%-32s %18s %18s %18s"%("family","JAN","FEB","MAR"))
for f in fams:
    cs=[]
    for m in ("JAN_nb","FEB_nb","MAR_nb"):
        c=out[m]["origin_family"].get(f)
        cs.append("%+7.4f t%+5.2f"%(c["slope"],c["t"]) if c else "%18s"%"-")
    print("%-32s %18s %18s %18s"%(f,cs[0],cs[1],cs[2]))
