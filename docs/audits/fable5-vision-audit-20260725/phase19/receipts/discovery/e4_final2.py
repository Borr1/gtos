import sys, json, math, collections, gzip
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
RETEST={"current_fvg_fill","current_ob_retest"}
JAN=load3.jan()
# ---- 1. JANUARY CLEAN control inside retest families
def cs(v,Y):
    g=[r[Y] for r in v if r.get(Y) is not None]
    if not g: return None
    m=sum(g)/len(g); sd=(sum((x-m)**2 for x in g)/max(1,len(g)-1))**.5
    return {"n":len(g),"mean":round(m,5),"win":round(sum(1 for x in g if x>0)/len(g),4),"se":round(sd/len(g)**.5,5)}
ret=[r for r in JAN if r.get("origin_family") in RETEST and r.get("fillp") is not None]
out1={}
for pname,pop in (("ALL",ret),("CLEAN_mkt_gt_-1",[r for r in ret if r.get("_mkt_r") is not None and r["_mkt_r"]>-1.0])):
    for Y in ("gross","honest"):
        b=cs([r for r in pop if r["fillp"]<0.92-1e-9],Y); a=cs([r for r in pop if r["fillp"]>=0.92-1e-9],Y)
        out1["%s|%s"%(pname,Y)]={"passive":b,"marketable":a,
            "delta":round(b["mean"]-a["mean"],5),
            "z":round((b["mean"]-a["mean"])/math.sqrt(b["se"]**2+a["se"]**2),3)}
# how many retest marketable rows are past-stop
mk=[r for r in ret if r["fillp"]>=0.92-1e-9]
out1["retest_marketable_pastsstop_share"]={"n":len(mk),
  "past_stop":sum(1 for r in mk if r.get("_mkt_r") is not None and r["_mkt_r"]<=-1.0),
  "at_or_through":sum(1 for r in mk if r.get("_mkt_r") is not None and -1.0<r["_mkt_r"]<=0.0)}
# ---- 2. MARCH per-placed-order curve by fillp band, full ledger
full=[]
with gzip.open("/tmp/e4/MAR_R0_slim.jsonl.gz","rt") as fh:
    for line in fh:
        if line.strip():
            r=json.loads(line); p=r.get("cdq_execution_fill_probability")
            fs=str(r.get("counterfactual_order_fill_status") or "")
            f=1 if fs.startswith("filled") else (0 if fs.startswith("not_filled") else None)
            if p is None or f is None: continue
            full.append({"p":p,"f":f,"g":r.get("opportunity_gross_r"),"fam":r.get("origin_family")})
def curve(v):
    v=sorted(v,key=lambda r:r["p"]); n=len(v); out=[]
    for i in range(10):
        s=v[i*n//10:(i+1)*n//10]
        gs=[x["g"] for x in s if x["f"]==1 and x["g"] is not None]
        fr=sum(x["f"] for x in s)/len(s)
        eg=(sum(gs)/len(gs)) if gs else None
        out.append({"d":i+1,"n":len(s),"p_lo":round(s[0]["p"],4),"p_hi":round(s[-1]["p"],4),
                    "model_p":round(sum(x["p"] for x in s)/len(s),5),"fill_rate":round(fr,5),
                    "n_scored":len(gs),"E_R_given_fill":round(eg,5) if eg is not None else None,
                    "per_placed_R":round(fr*eg,5) if eg is not None else None})
    return out
out2={"ALL":curve(full),"RETEST":curve([r for r in full if r["fam"] in RETEST]),
      "NO_BREAKER":curve([r for r in full if r["fam"]!="current_breaker_re_entry"])}
json.dump({"jan_clean_retest_control":out1,"march_per_placed_curve":out2},
          open("/tmp/e4/E4_FINAL2_V1.json","w"),indent=1)
print("1. JANUARY retest families: passive (fillp<0.92) vs marketable (>=0.92)")
for k,v in out1.items():
    if k.startswith("retest_marketable"): print("  ",k,v); continue
    print("   %-22s passive n=%5d %+.4f (win %.3f) | marketable n=%5d %+.4f (win %.3f) | delta %+.4f z %+.2f"%(
      k,v["passive"]["n"],v["passive"]["mean"],v["passive"]["win"],v["marketable"]["n"],v["marketable"]["mean"],
      v["marketable"]["win"],v["delta"],v["z"]))
print("\n2. MARCH per-PLACED-ORDER curve (full ledger incl. never-filled)")
for tag,c in out2.items():
    print("  ==",tag)
    print("   %-3s %7s %8s %8s %8s %8s %9s %10s"%("d","n","p_lo","p_hi","modelP","fillR","E[R|fill]","perPlaced"))
    for x in c:
        print("   %-3d %7d %8.4f %8.4f %8.4f %8.4f %9s %10s"%(x["d"],x["n"],x["p_lo"],x["p_hi"],
          x["model_p"],x["fill_rate"],x["E_R_given_fill"],x["per_placed_R"]))
