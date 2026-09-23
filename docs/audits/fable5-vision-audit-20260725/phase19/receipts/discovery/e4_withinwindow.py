import sys, json, math, collections, random
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
NB=lambda p:[r for r in p if r.get("origin_family")!="current_breaker_re_entry"]
def wwrho(pop,Y="gross",minn=3):
    wins=collections.defaultdict(list)
    for r in pop:
        if r.get("fillp") is not None and r.get(Y) is not None: wins[r["decision_time_utc"]].append(r)
    rhos=[]; ns=[]
    for w,c in wins.items():
        if len(c)<minn: continue
        if len(set(round(x["fillp"],9) for x in c))<2: continue
        sub=[{"fillp":x["fillp"],"gross":x[Y]} for x in c]
        rho=L.spearman(sub,"fillp","gross")
        if rho is not None: rhos.append(rho); ns.append(len(c))
    if not rhos: return None
    m=sum(rhos)/len(rhos); sd=(sum((x-m)**2 for x in rhos)/max(1,len(rhos)-1))**.5
    return {"n_windows":len(rhos),"mean_rho":round(m,5),"t":round(m/(sd/math.sqrt(len(rhos))),3),
            "frac_negative":round(sum(1 for x in rhos if x<0)/len(rhos),4),
            "median_window_size":sorted(ns)[len(ns)//2],"mean_window_size":round(sum(ns)/len(ns),2)}
def pooledrho(pop,Y="gross"):
    return L.spearman([r for r in pop if r.get("fillp") is not None and r.get(Y) is not None],"fillp",Y)
out={}
for tag,pop,Y in (("JAN_all",JAN,"gross"),("JAN_nb",NB(JAN),"gross"),("JAN_nb_honest",NB(JAN),"honest"),
                  ("FEB_all",FEB,"gross"),("FEB_nb",NB(FEB),"gross"),
                  ("MAR_all",MAR,"gross"),("MAR_nb",NB(MAR),"gross")):
    out[tag]={"within_window":wwrho(pop,Y),"pooled_rho":pooledrho(pop,Y),"n":len(pop)}
# window size census
for tag,pop in (("JAN_nb",NB(JAN)),("FEB_nb",NB(FEB)),("MAR_nb",NB(MAR))):
    wins=collections.Counter(r["decision_time_utc"] for r in pop)
    sizes=sorted(wins.values())
    out[tag]["window_sizes"]={"n_windows":len(sizes),"median":sizes[len(sizes)//2],
        "p90":sizes[int(.9*len(sizes))],"max":sizes[-1],"mean":round(sum(sizes)/len(sizes),2)}
json.dump(out,open("/tmp/e4/E4_WITHINWINDOW_V1.json","w"),indent=1)
print("%-14s %6s %10s %8s %8s %7s %8s %8s"%("case","n","pooledRho","wwRho","t","fracNeg","medWin","nWin"))
for k,v in out.items():
    w=v["within_window"]
    print("%-14s %6d %10s %8.4f %8.2f %7.3f %8d %8d"%(k,v["n"],v["pooled_rho"],w["mean_rho"],w["t"],w["frac_negative"],w["median_window_size"],w["n_windows"]))
print()
for k in ("JAN_nb","FEB_nb","MAR_nb"): print(k,out[k]["window_sizes"])
