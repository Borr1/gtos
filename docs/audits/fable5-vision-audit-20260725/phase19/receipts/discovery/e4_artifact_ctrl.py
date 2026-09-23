import sys, json, collections
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
def cs(v,Y="gross"):
    g=[r[Y] for r in v if r.get(Y) is not None]
    if not g: return None
    m=sum(g)/len(g); sd=(sum((x-m)**2 for x in g)/max(1,len(g)-1))**.5
    return {"n":len(g),"gross":round(m,5),"win":round(sum(1 for x in g if x>0)/len(g),4),
            "se":round(sd/len(g)**.5,5)}
def rm(pop,Y="gross"):
    rest=[r for r in pop if r.get("fillp") is not None and r["fillp"]<0.92-1e-9]
    mkt =[r for r in pop if r.get("fillp") is not None and r["fillp"]>=0.92-1e-9]
    a,b=cs(rest,Y),cs(mkt,Y)
    if not a or not b: return None
    return {"resting":a,"marketable":b,"delta":round(a["gross"]-b["gross"],5),
            "z":round((a["gross"]-b["gross"])/((a["se"]**2+b["se"]**2)**.5),3)}
NB=lambda p:[r for r in p if r.get("origin_family")!="current_breaker_re_entry"]
POPS={
 "JAN_ALL":JAN, "JAN_CLEAN_mkt_gt_-1":[r for r in JAN if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0],
 "JAN_no_breaker":NB(JAN),
 "JAN_CLEAN_no_breaker":NB([r for r in JAN if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0]),
 "FEB_ALL":FEB,"FEB_no_breaker":NB(FEB),
 "MAR_ALL":MAR,"MAR_no_breaker":NB(MAR)}
out={k:rm(v) for k,v in POPS.items()}
out["JAN_ALL_honest"]=rm(JAN,"honest"); out["JAN_CLEAN_honest"]=rm([r for r in JAN if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0],"honest")
out["JAN_CLEAN_no_breaker_honest"]=rm(NB([r for r in JAN if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0]),"honest")
# selection rule with breaker removed
sel={}
for tag,pop,wk in (("JAN_no_breaker",NB(JAN),"decision_time_utc"),
                   ("FEB_no_breaker",NB(FEB),"decision_time_utc"),
                   ("MAR_no_breaker",NB(MAR),"decision_time_utc"),
                   ("JAN_CLEAN_no_breaker",NB([r for r in JAN if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0]),"decision_time_utc")):
    s=L.selection(pop,Ys=("gross",),wkey=wk)
    g=s["gross"]
    sel[tag]={"n_windows":s["n_windows"],"PROD":g["PROD_score"]["mean"],"LOWEST":g["LOWEST_fill"]["mean"],
              "HIGHEST":g["HIGHEST_fill"]["mean"],"RANDOM":g["RANDOM"]["mean"],
              "paired_vs_prod":g["PAIRED_lowest_minus_prod"]["mean"],"t":g["PAIRED_lowest_minus_prod"]["t"],
              "paired_vs_random":g["PAIRED_lowest_minus_random"]["mean"],"perm_p":g.get("perm_p")}
out["selection_no_breaker"]=sel
json.dump(out,open("/tmp/e4/E4_ARTIFACT_CTRL_V1.json","w"),indent=1)
print("%-30s %7s %9s %6s | %7s %9s %6s | %8s %7s"%("population","nRest","restG","winR","nMkt","mktG","winM","delta","z"))
for k in ["JAN_ALL","JAN_CLEAN_mkt_gt_-1","JAN_no_breaker","JAN_CLEAN_no_breaker","FEB_ALL","FEB_no_breaker","MAR_ALL","MAR_no_breaker",
          "JAN_ALL_honest","JAN_CLEAN_honest","JAN_CLEAN_no_breaker_honest"]:
    d=out[k]
    print("%-30s %7d %9.4f %6.3f | %7d %9.4f %6.3f | %+8.4f %7.2f"%(k,d["resting"]["n"],d["resting"]["gross"],
      d["resting"]["win"],d["marketable"]["n"],d["marketable"]["gross"],d["marketable"]["win"],d["delta"],d["z"]))
print()
print("%-24s %6s %8s %8s %8s %8s %8s %6s %8s"%("selection(no breaker)","wins","PROD","LOWEST","HIGH","RANDOM","d_prod","t","d_rand"))
for k,v in sel.items():
    print("%-24s %6d %8.4f %8.4f %8.4f %8.4f %8.4f %6.2f %8.4f"%(k,v["n_windows"],v["PROD"],v["LOWEST"],
      v["HIGHEST"],v["RANDOM"],v["paired_vs_prod"],v["t"],v["paired_vs_random"]))
