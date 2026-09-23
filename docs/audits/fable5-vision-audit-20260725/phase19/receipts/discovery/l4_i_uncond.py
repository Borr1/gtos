#!/usr/bin/env python3
"""l4 step I: the decisive split. Is the fill-instant penalty SELECTION (only the filled
rows are bad) or DRIFT (the whole cohort is bad and the fill is incidental)?
Compares, per born class, the UNCONDITIONAL mean mark at bar k with the fill-conditioned
one, and prices the penalty against the true (over-charge-corrected) spread."""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws
info={}
for r in w0_ws.iter_rows():
    info[(r["candidate_id"],r["decision_time_utc"])]=(r["spread_r"],r["risk_distance"],r["entry_price"])
anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")
def born(m):
    if m is None: return "unknown"
    if m<=-1+1e-12: return "past_stop"
    if m<-1e-12: return "marketable"
    if m<=1e-12: return "at_limit"
    return "resting"
KS=[0,1,5,15,30,60,119]
U={}; C={}; SP={}; MK={}
def add(d,k,x):
    a=d.setdefault(k,[0.0,0]); a[0]+=x; a[1]+=1
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]; nb=len(fav)
    m=anch.get(k); b=born(m)
    sp,rd,ep=info.get(k,(None,None,None))
    if sp is not None: add(SP,b,sp)
    if m is not None: add(MK,b,m)
    for kk in KS:
        if kk<nb: add(U,(b,kk),cls[kk])           # UNCONDITIONAL, absolute bar index
    fb=next((i for i in range(nb) if adv[i]<=1e-12),None)
    if fb is not None:
        for kk in KS:
            if fb+kk<nb: add(C,(b,kk),cls[fb+kk]) # fill-conditioned, bars AFTER the fill
out={"KS":KS,"by_born":{}}
print("  born        n   mkt_r_at_decision |  UNCONDITIONAL mean mark at absolute bar k")
print("                                    "+"".join("%9d"%k for k in KS))
for b in ("at_limit","resting","marketable","past_stop"):
    u=[U.get((b,kk)) for kk in KS]
    mk=MK.get(b); spm=SP.get(b)
    print("  %-11s %6d %8.4f          "%(b,u[0][1],mk[0]/mk[1] if mk else 0)+"".join("%9.4f"%(x[0]/x[1]) for x in u))
    c=[C.get((b,kk)) for kk in KS]
    print("  %-11s        FILL-CONDITIONED           "%""+"".join("%9.4f"%(x[0]/x[1]) for x in c))
    d0=(c[0][0]/c[0][1])-(u[0][0]/u[0][1])
    tsp=(spm[0]/spm[1])/7.3
    print("  %-11s        selection effect at k=0 = %+.4f R ; true spread(7.3x corr) = %.4f R ; penalty/spread = %.2f"%(
          "",d0,tsp,(c[0][0]/c[0][1])/tsp))
    out["by_born"][b]={"n":u[0][1],"mkt_r_mean":round(mk[0]/mk[1],6) if mk else None,
        "uncond":{str(KS[i]):round(u[i][0]/u[i][1],6) for i in range(len(KS))},
        "fillcond":{str(KS[i]):round(c[i][0]/c[i][1],6) for i in range(len(KS))},
        "selection_effect_k0":round(d0,6),
        "mean_spread_r_frozen":round(spm[0]/spm[1],6),"true_spread_r_7p3x":round(tsp,6),
        "fill_penalty_over_true_spread":round((c[0][0]/c[0][1])/tsp,4)}
json.dump(out,open(os.path.join(HERE,"L4_UNCOND_V1.json"),"w"),indent=1)
