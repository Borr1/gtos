#!/usr/bin/env python3
"""l4 step A: fill-window sweep and the owner-contract headline."""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
F=os.path.join(HERE,"l4_FILL_V1.jsonl.gz")
def load():
    out=[]
    with gzip.open(F,"rt") as fh:
        for line in fh:
            if line.strip(): out.append(json.loads(line))
    return out
def st(v):
    v=[x for x in v if x is not None]
    if not v: return {"n":0}
    n=len(v); m=sum(v)/n
    s=sorted(v)
    return {"n":n,"mean":round(m,6),"median":round(s[n//2],6),"sum":round(sum(v),3)}
rows=load()
N=len(rows)
res={"n_rows":N}
# born census
born={}
for r in rows:
    b=r["born"]; d=born.setdefault(b,{"n":0,"filled":0,"fb":[],"gross":[]})
    d["n"]+=1
    if r["fill_bar0"] is not None:
        d["filled"]+=1; d["fb"].append(r["fill_bar0"]+1)
    d["gross"].append(r["gross_r"])
res["born_census"]={b:{"n":d["n"],"share":round(d["n"]/N,5),"ever_fills":d["filled"],
                       "ever_fill_rate":round(d["filled"]/d["n"],5),
                       "fill_bar_mean":round(sum(d["fb"])/len(d["fb"]),3) if d["fb"] else None,
                       "fill_bar_median":sorted(d["fb"])[len(d["fb"])//2] if d["fb"] else None,
                       "fill_bar_p90":sorted(d["fb"])[int(0.9*len(d["fb"]))] if d["fb"] else None,
                       "pool_gross_mean":round(sum(d["gross"])/d["n"],6)}
                    for b,d in sorted(born.items())}
WINDOWS=[1,3,5,10,15,30,45,60,90,120]
def sweep(pop,label):
    out=[]
    n=len(pop)
    for W in WINDOWS:
        f=[r for r in pop if r["fill_bar0"] is not None and (r["fill_bar0"]+1)<=W]
        rs=[r["fill_r"] for r in f]
        ex={}; life=[]
        for r in f:
            ex[r["fill_reason"]]=ex.get(r["fill_reason"],0)+1; life.append(r["fill_life"])
        tot=sum(rs) if rs else 0.0
        out.append({"window_bars":W,"window_min":W,"n_pop":n,"n_filled":len(f),
                    "fill_rate":round(len(f)/n,5),
                    "r_per_filled_trade":round(tot/len(f),6) if f else None,
                    "total_book_r":round(tot,3),
                    "r_per_candidate_offered":round(tot/n,6),
                    "exit_target":ex.get("target",0),"exit_stop":ex.get("stop",0),"exit_mark":ex.get("mark",0),
                    "win_rate":round(sum(1 for x in rs if x>0)/len(rs),5) if rs else None,
                    "mean_life_bars":round(sum(life)/len(life),2) if life else None,
                    "share_marked":round(ex.get("mark",0)/len(f),5) if f else None})
    return {"label":label,"sweep":out}
allpop=rows
sane=[r for r in rows if r["born"]!="past_stop"]
resting=[r for r in rows if r["born"]=="resting"]
res["sweep_ALL"]=sweep(allpop,"ALL candidates")
res["sweep_SANE"]=sweep(sane,"drop born_past_stop (stop already breached at decision)")
res["sweep_RESTING_ONLY"]=sweep(resting,"genuine passive limits only (mkt above entry)")
out=os.path.join(HERE,"L4_WINDOW_V1.json")
json.dump(res,open(out,"w"),indent=1)
print("BORN CENSUS  n  share  everfill%  fillbar med/p90  poolgross")
for b,d in res["born_census"].items():
    print("  %-11s %6d %6.2f%% %7.2f%% %5s/%-5s %8.4f"%(b,d["n"],100*d["share"],100*d["ever_fill_rate"],d["fill_bar_median"],d["fill_bar_p90"],d["pool_gross_mean"]))
for kk in ("sweep_ALL","sweep_SANE","sweep_RESTING_ONLY"):
    print("\n%s (n=%d)"%(res[kk]["label"],res[kk]["sweep"][0]["n_pop"]))
    print("  W(min) nfill  fill%  R/filled  totalR   win%  tgt/stop/mark   life  mark%")
    for s in res[kk]["sweep"]:
        print("  %5d %6d %6.2f %9.4f %8.1f %6.2f %5d/%5d/%5d %6.1f %5.1f"%(
            s["window_bars"],s["n_filled"],100*s["fill_rate"],s["r_per_filled_trade"] or 0,s["total_book_r"],
            100*(s["win_rate"] or 0),s["exit_target"],s["exit_stop"],s["exit_mark"],s["mean_life_bars"] or 0,100*(s["share_marked"] or 0)))
print("\nwrote",out)
