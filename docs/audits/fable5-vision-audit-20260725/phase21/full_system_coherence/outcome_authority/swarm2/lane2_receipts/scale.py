#!/usr/bin/env python3
"""The joint stop-width x horizon surface.

Cost in R is a price quantity divided by the stop distance, so widening the stop by k
divides spread/swap/commission by k (expected_slippage_r is a flat 0.02 R constant on
all 632,934 rows and does NOT divide). Time-to-hit scales as distance^2, so a k-wide
stop needs a k^2 horizon. This measures both at once. Fill is unchanged by construction
(the limit fill depends on `entry` only), so every arm prices the SAME trades.
"""
import gzip, json, pickle, sys, time
import numpy as np
from walk import load_symbol_series, log

SCALES=[1.0,1.5,2.0,3.0,4.0]
SLIP=0.02

def run(month):
    ser=load_symbol_series(month)
    recs=pickle.load(gzip.open(f"walk_{month}.pkl.gz","rb"))
    geom={}
    with gzip.open(f"geom_{month}.jsonl.gz","rt") as fh:
        for line in fh:
            r=json.loads(line); geom[r["k"]]=r
    out=[]
    for rec in recs:
        if rec.get("fi") is None or rec["H1"]<=0 or rec.get("err"): continue
        g=geom[rec["k"]]; S=ser[rec["sym"]]
        d=1 if str(g["side"]).upper()=="LONG" else -1
        entry=float(g["entry_price"]); stop0=float(g["stop_loss"]); target0=float(g["take_profit_1"])
        risk0=abs(entry-stop0); tR=d*(target0-entry)/risk0
        fp=rec["fp"]; fi=rec["fi"]; H1=rec["H1"]; sub=rec["sub"]
        n=len(S["t"]); end=min(n,fi+1+60*24*40); sl=slice(fi,end)
        off=(S["s"][sl] if d<0 else 0.0)
        O=S["o"][sl]+off; H=S["h"][sl]+off; L=S["l"][sl]+off; C=S["c"][sl]+off; TT=S["t"][sl]
        rr={"k":rec["k"],"month":month,"fam":rec["fam"],"ot":rec["ot"],"day":rec["day"],
            "ded":rec["ded"],"tR":float(tR),"fill_min":rec["fill_min"],"H1":H1,"arms":{}}
        for kk in SCALES:
            risk=kk*risk0; stop=entry-d*risk; target=entry+d*tR*risk
            if d>0: so=O<=stop; to=O>=target; hs=L<=stop; ht=H>=target
            else:   so=O>=stop; to=O<=target; hs=H>=stop; ht=L<=target
            ev=np.zeros(len(TT),dtype=np.int8); px=np.zeros(len(TT))
            ev[hs&ht]=3
            ev[hs&~ht]=1; px[hs&~ht]=stop
            ev[ht&~hs]=2; px[ht&~hs]=target
            ev[to]=2; px[to]=O[to]
            ev[so]=1; px[so]=O[so]
            ev[0]=0
            if hs[0] or ht[0]:
                ev[0]=3 if (not rec["fill_at_open"] or (hs[0] and ht[0])) else (1 if hs[0] else 2)
                px[0]=stop if ev[0]==1 else (target if ev[0]==2 else 0.0)
            nz=np.nonzero(ev)[0]
            ej=int(nz[0]) if len(nz) else None
            ekind=int(ev[ej]) if ej is not None else 0
            emin=(int(TT[ej])+(0 if (so[ej] or to[ej]) else 1)) if ej is not None else None
            epx=float(px[ej]) if ej is not None else None
            arm={}
            for hm,hz in (("hA",H1),("hB",int(round(H1*kk))),("hC",int(round(H1*kk*kk))),("hInf",None)):
                if hz is None:
                    if ej is not None and ekind in (1,2):
                        arm[hm]={"kind":{1:"STOP",2:"TARGET"}[ekind],"gross":float(d*(epx-fp)/risk),"end":emin}
                    elif ej is not None: arm[hm]={"kind":"CENSOR","gross":None,"end":emin}
                    else: arm[hm]={"kind":"RUNOUT","gross":float(d*(C[-1]-fp)/risk),"end":int(TT[-1])+1}
                    continue
                hlim=sub+hz
                jj=int(np.searchsorted(TT,hlim-1,side="right"))-1
                if jj<0: arm[hm]=None; continue
                if ej is not None and emin<=hlim and TT[ej]<hlim:
                    arm[hm]=({"kind":{1:"STOP",2:"TARGET"}[ekind],"gross":float(d*(epx-fp)/risk),"end":emin}
                             if ekind in (1,2) else {"kind":"CENSOR","gross":None,"end":emin})
                else:
                    arm[hm]={"kind":"TIME_STOP","gross":float(d*(C[jj]-fp)/risk),"end":int(TT[jj])+1}
            rr["arms"][str(kk)]=arm
        out.append(rr)
    with gzip.open(f"scale_{month}.pkl.gz","wb") as fh: pickle.dump(out,fh,protocol=5)
    log(stage="scale_done",month=month,n=len(out))

if __name__=="__main__":
    for m in sys.argv[1:]: run(m)
