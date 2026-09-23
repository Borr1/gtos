#!/usr/bin/env python3
"""l4 step F: score the exit grid under the owner's fill-honest contract."""
import gzip, json, os
HERE=os.path.dirname(os.path.abspath(__file__))
TGT=[0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0,4.0,5.0]
STP=[-0.5,-0.75,-1.0,-1.5,-2.0]
MB =[15,30,60,120]
lad=[json.loads(l) for l in gzip.open(os.path.join(HERE,"l4_EXITLADDER_V1.jsonl.gz"),"rt") if l.strip()]
print("ladder rows",len(lad))
def cellbook(pop,ti,sj,mi):
    T=TGT[ti]; S=STP[sj]; M=MB[mi]
    n=0; s=0.0; w=0; tg=0; st=0; mk=0
    for r in pop:
        if r["fb"] is None: continue
        tb=r["tb"][ti]; sb=r["sb"][sj]
        tb_ok = tb is not None and tb<=M
        sb_ok = sb is not None and sb<=M
        if sb_ok and (not tb_ok or sb<=tb): x=S; st+=1
        elif tb_ok: x=T; tg+=1
        else:
            x=r["cl"][mi]
            if x is None: continue
            mk+=1
        n+=1; s+=x
        if x>0: w+=1
    if not n: return None
    return {"T":T,"S":S,"M":M,"n":n,"gross_same":round(s/n,6),"gross_rn":round(s/n/abs(S),6),
            "total":round(s,1),"win":round(w/n,5),"tgt":tg,"stop":st,"mark":mk}
sane=[r for r in lad if r["born"]!="past_stop"]
rest=[r for r in lad if r["born"]=="resting"]
res={"pop_sane_n":len(sane),"pop_resting_n":len(rest),"TGT":TGT,"STP":STP,"MB":MB}
for pname,pop in (("SANE",sane),("RESTING",rest)):
    g=[]
    for ti in range(len(TGT)):
        for sj in range(len(STP)):
            for mi in range(len(MB)):
                c=cellbook(pop,ti,sj,mi)
                if c: g.append(c)
    res["grid_"+pname]=g
    best=sorted(g,key=lambda c:-c["gross_rn"])[:12]
    print("\nTOP CELLS %s  (risk-normalised R/trade)"%pname)
    print("   T     S    M     n    grossRN  grossSAME   win%   tgt/stop/mark")
    for c in best:
        print("  %4.2f %5.2f %4d %6d %9.4f %9.4f %6.2f %5d/%5d/%5d"%(c["T"],c["S"],c["M"],c["n"],c["gross_rn"],c["gross_same"],100*c["win"],c["tgt"],c["stop"],c["mark"]))
# baseline row: T=2 S=-1 M=120
for pname,pop in (("SANE",sane),("RESTING",rest)):
    b=[c for c in res["grid_"+pname] if c["T"]==2.0 and c["S"]==-1.0 and c["M"]==120][0]
    print("\nBASELINE %s T=2 S=-1 M=120: %s"%(pname,json.dumps(b)))
# target sweep at S=-1,M=120
print("\nTARGET SWEEP (SANE, S=-1, M=120)")
print("   T      n   grossR    win%   tgt/stop/mark")
for c in sorted([c for c in res["grid_SANE"] if c["S"]==-1.0 and c["M"]==120],key=lambda c:c["T"]):
    print("  %4.2f %6d %8.4f %6.2f %5d/%5d/%5d"%(c["T"],c["n"],c["gross_same"],100*c["win"],c["tgt"],c["stop"],c["mark"]))
print("\nSTOP SWEEP (SANE, T=2, M=120)  risk-normalised")
for c in sorted([c for c in res["grid_SANE"] if c["T"]==2.0 and c["M"]==120],key=lambda c:c["S"]):
    print("  S=%5.2f n=%6d grossRN %8.4f grossSAME %8.4f win %5.2f%%"%(c["S"],c["n"],c["gross_rn"],c["gross_same"],100*c["win"]))
json.dump(res,open(os.path.join(HERE,"L4_EXITGRID_V1.json"),"w"),indent=1)
print("\nwrote L4_EXITGRID_V1.json")
