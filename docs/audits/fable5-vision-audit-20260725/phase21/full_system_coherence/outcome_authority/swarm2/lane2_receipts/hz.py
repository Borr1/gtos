#!/usr/bin/env python3
"""Fill-anchored horizon ladder. The sealed horizon runs from SUBMISSION, so a limit that
rests 90 min gets 30 min of trade life; this arm anchors at the FILL so the exit clock is
measured independently of the fill clock."""
import gzip,json,pickle,sys
import numpy as np
from walk import load_symbol_series, log
LAD=[15,30,60,120,240,480,960,1920]
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
        entry=float(g["entry_price"]); stop=float(g["stop_loss"]); target=float(g["take_profit_1"])
        risk=abs(entry-stop); fp=rec["fp"]; fi=rec["fi"]
        n=len(S["t"]); end=min(n,fi+1+60*24*40); sl=slice(fi,end)
        off=(S["s"][sl] if d<0 else 0.0)
        O=S["o"][sl]+off;H=S["h"][sl]+off;L=S["l"][sl]+off;Cc=S["c"][sl]+off;TT=S["t"][sl]
        if d>0: so=O<=stop;to=O>=target;hs=L<=stop;ht=H>=target
        else:   so=O>=stop;to=O<=target;hs=H>=stop;ht=L<=target
        ev=np.zeros(len(TT),dtype=np.int8);px=np.zeros(len(TT))
        ev[hs&ht]=3; ev[hs&~ht]=1;px[hs&~ht]=stop; ev[ht&~hs]=2;px[ht&~hs]=target
        ev[to]=2;px[to]=O[to]; ev[so]=1;px[so]=O[so]; ev[0]=0
        if hs[0] or ht[0]:
            ev[0]=3 if (not rec["fill_at_open"] or (hs[0] and ht[0])) else (1 if hs[0] else 2)
            px[0]=stop if ev[0]==1 else (target if ev[0]==2 else 0.0)
        nz=np.nonzero(ev)[0]
        ej=int(nz[0]) if len(nz) else None
        ekind=int(ev[ej]) if ej is not None else 0
        emin=(int(TT[ej])+(0 if (so[ej] or to[ej]) else 1)) if ej is not None else None
        epx=float(px[ej]) if ej is not None else None
        fav=(H-fp)*d/risk if d>0 else (L-fp)*d/risk
        adv=(L-fp)*d/risk if d>0 else (H-fp)*d/risk
        cf=np.maximum.accumulate(fav); ca=np.minimum.accumulate(adv)
        f0=rec["fill_min"]
        rr={"k":rec["k"],"month":month,"fam":rec["fam"],"ot":rec["ot"],"day":rec["day"],
            "ded":rec["ded"],"tR":float(d*(target-entry)/risk),"rest":int(f0-rec["sub"]),
            "H1":rec["H1"],"remaining":int(rec["sub"]+rec["H1"]-f0),"arms":{}}
        for Hm in LAD:
            hlim=f0+Hm
            jj=int(np.searchsorted(TT,hlim-1,side="right"))-1
            if jj<0: rr["arms"][str(Hm)]=None; continue
            if ej is not None and emin<=hlim and TT[ej]<hlim:
                j=ej
                rr["arms"][str(Hm)]=({"kind":{1:"STOP",2:"TARGET"}[ekind],"gross":float(d*(epx-fp)/risk),
                    "end":emin,"mfe":float(cf[j]),"mae":float(ca[j])} if ekind in (1,2)
                    else {"kind":"CENSOR","gross":None,"end":emin,"mfe":float(cf[j]),"mae":float(ca[j])})
            else:
                rr["arms"][str(Hm)]={"kind":"TIME_STOP","gross":float(d*(Cc[jj]-fp)/risk),
                    "end":int(TT[jj])+1,"mfe":float(cf[jj]),"mae":float(ca[jj])}
        if ej is not None:
            rr["arms"]["inf"]=({"kind":{1:"STOP",2:"TARGET"}[ekind],"gross":float(d*(epx-fp)/risk),
                "end":emin,"mfe":float(cf[ej]),"mae":float(ca[ej])} if ekind in (1,2)
                else {"kind":"CENSOR","gross":None,"end":emin,"mfe":float(cf[ej]),"mae":float(ca[ej])})
        else:
            rr["arms"]["inf"]={"kind":"RUNOUT","gross":float(d*(Cc[-1]-fp)/risk),"end":int(TT[-1])+1,
                "mfe":float(cf[-1]),"mae":float(ca[-1])}
        out.append(rr)
    with gzip.open(f"hz_{month}.pkl.gz","wb") as fh: pickle.dump(out,fh,protocol=5)
    log(stage="hz_done",month=month,n=len(out))
if __name__=="__main__":
    for m in sys.argv[1:]: run(m)
