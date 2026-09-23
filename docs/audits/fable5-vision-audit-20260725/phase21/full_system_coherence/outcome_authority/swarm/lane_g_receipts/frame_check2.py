"""Per-row identity test. If fill = tape_open + entry_offset and the barriers are
compared on the exit side, then for an intrabar STOP touch
   gross = d*(S - F)/R = -1 - spread_r - drift ,  drift = d*(tape_entry - E)/R
so the residual gross + 1 + spread_r + drift must be EXACTLY 0 (up to gap rows)."""
import gzip, pickle, numpy as np
from collections import defaultdict
recs=[]
for mo in ["feb","apr","may","jun","jul"]:
    with gzip.open(f"/private/tmp/phase0-inversion/walk_{mo}.pkl.gz","rb") as fh:
        recs += pickle.load(fh)
res=defaultdict(list)
for r in recs:
    a,b=r["orig"]["fill_price"],r["inv"]["fill_price"]
    if a is None or b is None or r["orig"]["fill_time"]!=r["inv"]["fill_time"]: continue
    s=abs(float(a)-float(b)); R=r["risk_price"]; sr=s/R
    d=1 if r["side"]=="LONG" else -1
    tape=float(a)-(s if d>0 else 0.0)
    drift=d*(tape-r["entry_price"])/R
    g=r["orig"]["gross"]; st=r["orig"]["state"]
    if g is None: continue
    if st=="STOP":   res["STOP"].append(g+1.0+sr+drift)
    if st=="TARGET": res["TARGET"].append(g-2.0+sr+drift)
for k,v in res.items():
    v=np.array(v)
    print(f"{k:7s} n={len(v):6d}  residual: median {np.median(v):+.6f}  mean {v.mean():+.6f}  "
          f"|res|<1e-9 on {100*np.mean(np.abs(v)<1e-9):.2f}%  p5 {np.percentile(v,5):+.4f} p95 {np.percentile(v,95):+.4f}")
