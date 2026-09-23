import sys, json, math, random, collections, gzip
sys.path.insert(0,"/tmp/e4"); import e4lib as L, load3
RETEST={"current_fvg_fill","current_ob_retest"}
# ---- A. ex-ante threshold filter WITHIN retest families, all 3 months (pool = filled set)
JAN,FEB,MAR=load3.jan(),load3.feb(),load3.mar()
def thr(pop,fams,Y="gross"):
    v=[r for r in pop if r.get("origin_family") in fams and r.get("fillp") is not None and r.get(Y) is not None]
    o={}
    for t in (0.25,0.35,0.45,0.70,0.80,0.90,0.9199):
        b=[r[Y] for r in v if r["fillp"]<t]; a=[r[Y] for r in v if r["fillp"]>=t]
        o[str(t)]={"n_below":len(b),"below":round(sum(b)/len(b),5) if b else None,
                   "n_above":len(a),"above":round(sum(a)/len(a),5) if a else None,
                   "delta":round((sum(b)/len(b))-(sum(a)/len(a)),5) if b and a else None}
    return o
A={"JAN":thr(JAN,RETEST),"FEB":thr(FEB,RETEST),"MAR":thr(MAR,RETEST),
   "JAN_honest":thr(JAN,RETEST,"honest")}
# ---- B. MARCH ex-ante window ranking over the FULL ledger (filled + never-filled)
full=[]
with gzip.open("/tmp/e4/MAR_R0_slim.jsonl.gz","rt") as fh:
    for line in fh:
        if line.strip():
            r=json.loads(line); r["fillp"]=r.get("cdq_execution_fill_probability")
            r["gross"]=r.get("opportunity_gross_r")
            fs=str(r.get("counterfactual_order_fill_status") or "")
            r["filled"]=1 if fs.startswith("filled") else (0 if fs.startswith("not_filled") else None)
            r["inpool"]=r.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
            if r["fillp"] is not None and r["filled"] is not None and r.get("decision_time_utc"): full.append(r)
def exante(pop,fams=None):
    v=[r for r in pop if fams is None or r.get("origin_family") in fams]
    wins=collections.defaultdict(list)
    for r in v: wins[r["decision_time_utc"]].append(r)
    wins={w:c for w,c in wins.items() if len(c)>=2}
    rng=random.Random(7)
    rules={"LOWEST_fill":lambda r:-r["fillp"],"HIGHEST_fill":lambda r:r["fillp"],"RANDOM":None,
           "PROD":lambda r:(L.prod_score(r,"fillp") if L.prod_score(r,"fillp") is not None else -9e9)}
    o={"n_windows":len(wins),"n_cand":len(v),
       "base_fill_rate":round(sum(r["filled"] for r in v)/len(v),5)}
    for n,f in rules.items():
        pk=[ (rng.choice(c) if f is None else max(c,key=f)) for c in wins.values()]
        fr=sum(p["filled"] for p in pk)/len(pk)
        gs=[p["gross"] for p in pk if p["filled"]==1 and p["gross"] is not None]
        o[n]={"fill_rate":round(fr,5),"n_scored":len(gs),
              "mean_gross_given_fill":round(sum(gs)/len(gs),5) if gs else None,
              "per_placed_R":round(fr*(sum(gs)/len(gs)),5) if gs else None}
    return o
B={"MAR_ALL_families":exante(full),"MAR_retest":exante(full,RETEST),
   "MAR_no_breaker":exante([r for r in full if r.get("origin_family")!="current_breaker_re_entry"])}
out={"A_exante_threshold_within_retest":A,"B_march_exante_window_rank_full_ledger":B}
json.dump(out,open("/tmp/e4/E4_EXANTE_V1.json","w"),indent=1)
print("A. EX-ANTE THRESHOLD within retest families (below vs above modelled fill prob)")
print("%-12s %8s %10s %8s %10s %9s"%("month/thr","n_below","below","n_above","above","delta"))
for m,d in A.items():
    for t in ("0.45","0.8","0.9199"):
        c=d.get(t) or d.get(t+"0")
        if c: print("%-12s %8d %10.4f %8d %10.4f %+9.4f"%(m+"/"+t,c["n_below"],c["below"],c["n_above"],c["above"],c["delta"]))
print()
print("B. MARCH EX-ANTE window rank over FULL ledger (never-filled included)")
for k,v in B.items():
    print(" ",k,"windows=%d cand=%d baseFill=%.4f"%(v["n_windows"],v["n_cand"],v["base_fill_rate"]))
    for n in ("PROD","LOWEST_fill","HIGHEST_fill","RANDOM"):
        c=v[n]; print("     %-13s fill=%.4f nScored=%5d E[R|fill]=%s perPlaced=%s"%(n,c["fill_rate"],c["n_scored"],c["mean_gross_given_fill"],c["per_placed_R"]))
