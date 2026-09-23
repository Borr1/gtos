#!/usr/bin/env python3
"""First-passage-time ladder: measures the exponent in E[T_hit] ~ d^alpha.

One-sided first passage avoids the selection bias of conditioning on which of two
competing barriers won. Measured from the FILL price, in observed M1 bars.
"""
import gzip, json, pickle, sys, time
import numpy as np
from walk import load_symbol_series, log, MONTH_SRC

LAD = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]

def run(month):
    ser = load_symbol_series(month)
    recs = pickle.load(gzip.open(f"walk_{month}.pkl.gz","rb"))
    geom = {}
    with gzip.open(f"geom_{month}.jsonl.gz","rt") as fh:
        for line in fh:
            r = json.loads(line); geom[r["k"]] = r
    out = []
    for rec in recs:
        if rec.get("fi") is None: continue
        g = geom[rec["k"]]; S = ser[rec["sym"]]
        d = 1 if str(g["side"]).upper()=="LONG" else -1
        entry=float(g["entry_price"]); stop=float(g["stop_loss"]); target=float(g["take_profit_1"])
        risk=abs(entry-stop); fp=rec["fp"]; fi=rec["fi"]
        n=len(S["t"]); end=min(n, fi+1+60*24*40); sl=slice(fi,end)
        off = (S["s"][sl] if d<0 else 0.0)
        H=S["h"][sl]+off; L=S["l"][sl]+off; TT=S["t"][sl]
        fav = (H-fp)*d/risk if d>0 else (L-fp)*d/risk
        adv = (L-fp)*d/risk if d>0 else (H-fp)*d/risk
        cf = np.maximum.accumulate(fav); ca = np.minimum.accumulate(adv)
        rel = TT - rec["fill_min"]            # wall-clock minutes since fill
        bar = np.arange(len(TT))              # observed bars since fill
        rr = {"k":rec["k"],"month":month,"fam":rec["fam"],"ot":rec["ot"],"sym":rec["sym"],
              "day":rec["day"],"tR":float(d*(target-entry)/risk),
              "stop_atr":None,"nobs":int(len(TT))}
        for x in LAD:
            j = int(np.argmax(cf >= x)) if (cf >= x).any() else -1
            rr[f"fu{x}"] = [int(rel[j]), int(bar[j])] if j >= 0 else None
            j = int(np.argmax(ca <= -x)) if (ca <= -x).any() else -1
            rr[f"fd{x}"] = [int(rel[j]), int(bar[j])] if j >= 0 else None
        out.append(rr)
    with gzip.open(f"fpt_{month}.pkl.gz","wb") as fh: pickle.dump(out, fh, protocol=5)
    log(stage="fpt_done", month=month, n=len(out))

if __name__ == "__main__":
    for m in sys.argv[1:]: run(m)
