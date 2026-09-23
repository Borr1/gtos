#!/usr/bin/env python3
"""l4 step G: WHERE THE MONEY GOES.

The exit grid is flat in T and in S, which is the signature of a stopped martingale plus a
constant. This measures the constant directly: the mean close-based R at k bars AFTER the
fill, against the same curve from the decision bar (the fill-blind convention), and the
same-bar tie sensitivity that could otherwise manufacture it.
"""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws
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
KS=[0,1,2,3,5,10,15,20,30,45,60,90,119]
acc={}   # (pop,latbucket) -> [ [sum,n] per k ]
def A(p):
    return acc.setdefault(p,[[0.0,0] for _ in KS])
ties=0; tie_tgt_first=0; both=0; nres=0
lat_edges=[(1,1),(2,5),(6,15),(16,60),(61,120)]
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"])
    fav,adv,cls=rp["fav"],rp["adv"],rp["cls"]; nb=len(fav)
    b=born(anch.get(k))
    fb=next((i for i in range(nb) if adv[i]<=1e-12),None)
    # blind curve from bar 0
    for j,kk in enumerate(KS):
        if kk<nb:
            a=A(("BLIND_"+("SANE" if b!="past_stop" else "PAST"),)); a[j][0]+=cls[kk]; a[j][1]+=1
    if fb is None: continue
    pops=[("FILL_SANE",)] if b!="past_stop" else [("FILL_PAST",)]
    if b=="resting": pops.append(("FILL_RESTING",))
    if b=="at_limit": pops.append(("FILL_ATLIMIT",))
    for lo,hi in lat_edges:
        if lo<=fb+1<=hi and b!="past_stop": pops.append(("FILL_SANE_lat%d_%d"%(lo,hi),))
    for j,kk in enumerate(KS):
        idx=fb+kk
        if idx<nb:
            for p in pops:
                a=A(p); a[j][0]+=cls[idx]; a[j][1]+=1
    # tie sensitivity at T=2 S=-1 from the fill
    for i in range(fb,nb):
        f,a_=fav[i],adv[i]
        s=a_<=-1.0+1e-12; t=f>=2.0-1e-12
        if s or t:
            nres+=1
            if s and t: ties+=1
            break
out={"KS":KS,"curves":{},"tie":{"resolved":nres,"same_bar_both":ties,
     "share_of_resolved":round(ties/nres,5) if nres else None}}
for p,a in acc.items():
    out["curves"][p[0]]=[{"k":KS[j],"n":a[j][1],"mean_r":round(a[j][0]/a[j][1],6) if a[j][1] else None} for j in range(len(KS))]
json.dump(out,open(os.path.join(HERE,"L4_DRIFT_V1.json"),"w"),indent=1)
print("MEAN CLOSE-BASED R AT k BARS AFTER THE ANCHOR BAR")
print("  curve                 "+"".join("%8d"%k for k in KS))
for name in ("BLIND_SANE","FILL_SANE","FILL_RESTING","FILL_ATLIMIT","BLIND_PAST","FILL_PAST"):
    c=out["curves"].get(name)
    if not c: continue
    print("  %-20s"%name+"".join("%8.4f"%(x["mean_r"] if x["mean_r"] is not None else 0) for x in c))
print("\n  by fill latency (SANE, k measured FROM THE FILL):")
for lo,hi in lat_edges:
    c=out["curves"].get("FILL_SANE_lat%d_%d"%(lo,hi))
    if c: print("  %-20s"%("lat %d-%d n=%d"%(lo,hi,c[0]["n"]))+"".join("%8.4f"%(x["mean_r"] or 0) for x in c))
print("\nTIE at T=2/S=-1 from fill: resolved %d, same-bar both %d (%.3f%%)"%(nres,ties,100*ties/nres))
