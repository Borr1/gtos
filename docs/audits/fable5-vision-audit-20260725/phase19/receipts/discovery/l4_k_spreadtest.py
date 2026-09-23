#!/usr/bin/env python3
"""l4 step K: is the at-market cohort's constant -0.0647 R offset the SPREAD or the SIGNAL?
If it is the spread, the per-symbol offset must be proportional to that symbol's own true
spread with slope ~ -1. Regresses mark(k=1) on true spread_r across symbols."""
import gzip, json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import w0_ws
info={}
for r in w0_ws.iter_rows():
    info[(r["candidate_id"],r["decision_time_utc"])]=(r["symbol"],r["spread_r"],r["side"],r["origin_family"])
anch={}
with gzip.open(os.path.join(HERE,"w0cap2_DECISION_ANCHOR_V1.jsonl.gz"),"rt") as fh:
    for l in fh:
        if l.strip():
            a=json.loads(l); anch[(a["candidate_id"],a["decision_time_utc"])]=a.get("mkt_r_prev_close")
S={}
for rp in w0_ws.iter_rpaths():
    k=(rp["candidate_id"],rp["decision_time_utc"]); m=anch.get(k)
    if m is None or abs(m)>1e-12: continue
    sy,sp,sd,fm=info[k]; cls=rp["cls"]
    if len(cls)<2 or sp is None: continue
    d=S.setdefault(sy,{"n":0,"m1":0.0,"m15":0.0,"m119":0.0,"sp":0.0})
    d["n"]+=1; d["m1"]+=cls[1]; d["m15"]+=cls[min(15,len(cls)-1)]; d["m119"]+=cls[len(cls)-1]; d["sp"]+=sp
pts=[]
for sy,d in S.items():
    if d["n"]<100: continue
    pts.append((sy,d["n"],d["m1"]/d["n"],d["m15"]/d["n"],d["m119"]/d["n"],(d["sp"]/d["n"])/7.3,(d["sp"]/d["n"])))
def reg(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); sxx=sum((x-mx)**2 for x in xs)
    b=sxy/sxx; a=my-b*mx
    ss=sum((y-my)**2 for y in ys); rs=sum((y-(a+b*x))**2 for x,y in zip(xs,ys))
    return a,b,1-rs/ss
xs=[p[5] for p in pts]
out={"n_symbols":len(pts),"points":[{"symbol":p[0],"n":p[1],"mark_k1":round(p[2],6),"mark_k15":round(p[3],6),
      "mark_k119":round(p[4],6),"true_spread_r_7p3":round(p[5],6),"frozen_spread_r":round(p[6],6)} for p in pts]}
for lab,idx in (("k1",2),("k15",3),("k119",4)):
    a,b,r2=reg(xs,[p[idx] for p in pts])
    out["regression_"+lab]={"intercept":round(a,6),"slope":round(b,4),"r2":round(r2,4)}
    print("mark(%4s) = %+.5f %+.4f * true_spread_r    r2=%.4f"%(lab,a,b,r2))
print("\n  symbol       n   mark_k1  true_spread  ratio   mark_k1+spread")
for p in sorted(pts,key=lambda p:-p[5]):
    print("  %-10s %5d %9.4f %11.4f %7.3f %14.4f"%(p[0],p[1],p[2],p[5],(-p[2]/p[5]) if p[5] else 0,p[2]+p[5]))
tot_m=sum(p[2]*p[1] for p in pts)/sum(p[1] for p in pts); tot_s=sum(p[5]*p[1] for p in pts)/sum(p[1] for p in pts)
out["pooled"]={"mark_k1":round(tot_m,6),"true_spread_r":round(tot_s,6),"ratio":round(-tot_m/tot_s,4),
               "residual_after_adding_spread":round(tot_m+tot_s,6)}
print("\nPOOLED at-market: mark(k=1) %.5f   true spread %.5f   ratio %.3f   residual %.5f"%(tot_m,tot_s,-tot_m/tot_s,tot_m+tot_s))
json.dump(out,open(os.path.join(HERE,"L4_SPREADTEST_V1.json"),"w"),indent=1)
