"""Rigorous mirror test: adjust for the geometry asymmetry the mirror inherits.

Under the sealed labeler a LONG's tape-frame barriers are (R, 2R) but a SHORT's are
(R-s, 2R+s) -- the spread lands in the barrier geometry for a SHORT and in the P&L
for a LONG. So flipping the side moves the driftless benchmark by +-spread_r/3 and a
naive mirror comparison inherits that bias. Remove it by differencing each arm
against its OWN corrected driftless benchmark."""
import gzip, pickle, math, json
import numpy as np
from collections import Counter, defaultdict
from scipy.stats import binomtest

MONTHS=["feb","apr","may","jun","jul"]
recs=[]
for mo in MONTHS:
    with gzip.open(f"/private/tmp/laneG-walk/lg_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh): r["month"]=mo; recs.append(r)

def geom(r, arm):
    """Tape-frame (exit-side-frame) barrier distances and the corrected driftless P."""
    E,S,T,R,W = r["entry_price"],r["stop_price"],r["target_price"],r["risk_price"],r["reward_price"]
    d = 1 if r["side"]=="LONG" else -1
    if arm=="orig":       dd, stop, tgt = d, S, T
    elif arm=="mirror":   dd, stop, tgt = -d, E+d*R, E-d*W
    else:                 dd, stop, tgt = -d, T, S          # phase0 inverted contract
    F=r[arm]["fill_price"]; s=r["spread_at_fill_price"]
    if F is None or s is None: return None
    down = dd*(float(F)-stop) - s        # entry moved into the exit-side quote frame
    up   = dd*(tgt-float(F))   + s
    if down<=0 or up<=0: return None
    return down/(down+up)

rowsf=defaultdict(list)
for r in recs: rowsf[r["family"]].append(r)

def block(rows):
    """Observed-minus-expected for each arm, and the difference-in-differences."""
    o_hit=o_exp=o_var=o_n=0.0
    m_hit=m_exp=m_var=m_n=0.0
    dd_obs=0.0; dd_var=0.0; n_pair=0
    a=b=0
    for r in rows:
        po, pm = geom(r,"orig"), geom(r,"mirror")
        so, sm = r["orig"]["state"], r["mirror"]["state"]
        if so in ("TARGET","STOP") and po is not None:
            o_hit += (so=="TARGET"); o_exp += po; o_var += po*(1-po); o_n += 1
        if sm in ("TARGET","STOP") and pm is not None:
            m_hit += (sm=="TARGET"); m_exp += pm; m_var += pm*(1-pm); m_n += 1
        if so in ("TARGET","STOP") and sm in ("TARGET","STOP") and po is not None and pm is not None:
            dd_obs += (so=="TARGET") - (sm=="TARGET") - (po-pm)
            dd_var += po*(1-po) + pm*(1-pm); n_pair += 1
            if (so=="TARGET") and (sm!="TARGET"): a+=1
            elif (sm=="TARGET") and (so!="TARGET"): b+=1
    return dict(
        o_n=int(o_n), o_hit=o_hit/o_n if o_n else None, o_bench=o_exp/o_n if o_n else None,
        o_z=(o_hit-o_exp)/math.sqrt(o_var) if o_var>0 else None,
        m_n=int(m_n), m_hit=m_hit/m_n if m_n else None, m_bench=m_exp/m_n if m_n else None,
        m_z=(m_hit-m_exp)/math.sqrt(m_var) if m_var>0 else None,
        n_pair=n_pair, dd=dd_obs/n_pair if n_pair else None,
        dd_z=dd_obs/math.sqrt(dd_var) if dd_var>0 else None,
        raw_a=a, raw_b=b,
        raw_z=(a-(a+b)/2)/math.sqrt((a+b)/4) if (a+b)>0 else None,
        long_share=float(np.mean([r["side"]=="LONG" for r in rows])),
        med_spread_r=float(np.median([r["spread_at_fill_price"]/r["risk_price"] for r in rows
                                      if r["spread_at_fill_price"] is not None])),
    )

print(f"{'family':34s} {'LONG%':>6s} {'sprd_r':>7s} | {'ORIG hit':>8s} {'bench':>6s} {'z':>7s} | "
      f"{'MIRR hit':>8s} {'bench':>6s} {'z':>7s} | {'DiD':>8s} {'DiD z':>7s}")
res={}
for fam,rows in sorted(rowsf.items(), key=lambda kv:-len(kv[1])):
    d=block(rows); res[fam]=d
    print(f"{fam:34s} {100*d['long_share']:6.1f} {d['med_spread_r']:7.4f} | "
          f"{d['o_hit']:8.4f} {d['o_bench']:6.4f} {d['o_z']:7.2f} | "
          f"{d['m_hit']:8.4f} {d['m_bench']:6.4f} {d['m_z']:7.2f} | {d['dd']:+8.4f} {d['dd_z']:7.2f}")
d=block(recs); res["_POOLED"]=d
print(f"{'POOLED':34s} {100*d['long_share']:6.1f} {d['med_spread_r']:7.4f} | "
      f"{d['o_hit']:8.4f} {d['o_bench']:6.4f} {d['o_z']:7.2f} | "
      f"{d['m_hit']:8.4f} {d['m_bench']:6.4f} {d['m_z']:7.2f} | {d['dd']:+8.4f} {d['dd_z']:7.2f}")
json.dump(res, open("/tmp/laneG/mirror_adjusted.json","w"), indent=1)
