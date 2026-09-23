"""p1 step 6 — the candidate register on the CORRECTED CONTRACT (d1b §2: at-market
families are market orders, POI families are resting limits), and the persistence of
the wave's named survivors."""
from __future__ import annotations
import numpy as np, json, sys, itertools
sys.path.insert(0, "/tmp/p1")
import p1_lib as L
ws, SYMS = L.load_all()
SI = {s: i for i, s in enumerate(SYMS)}; FA = L.FAMS
NW = len(ws)

def stat(w, m):
    g = w.gc[m]; c = w.cc[m]
    if len(g) < 5: return dict(window=w.w, n=0)
    d = dict(window=w.w, n=int(len(g)), gross=float(g.mean()), cost=float(c.mean()),
             net=float((g - c).mean()), wr=float((g > 0).mean()))
    a = m & (w.atm == 1)
    if a.sum() > 30:
        # exact mirror control on the SAME contract (market fill both sides)
        d["signal"] = float((w.mg[a] - np.asarray(np.load(f"{L.ROWS}/D1_{w.w}.npz")["mf20"])[a]).mean())
        d["n_signal"] = int(a.sum())
    return d

def series(name, fn, note=""):
    rows = [stat(w, fn(w)) for w in ws]
    ok = [r for r in rows if r["n"] > 0]
    if len(ok) < 4: return None
    W = lambda rs, f: float(np.average([r[f] for r in rs], weights=[r["n"] for r in rs]))
    x = np.arange(len(ok), dtype=float)
    sl = lambda f: float(np.polyfit(x, [r[f] for r in ok], 1)[0])
    first, last = ok[:len(ok)//2], ok[len(ok)//2:]
    out = dict(name=name, note=note, per_window=ok,
               pooled=dict(n=sum(r["n"] for r in ok), gross=W(ok,"gross"), cost=W(ok,"cost"), net=W(ok,"net")),
               first_half=dict(gross=W(first,"gross"), cost=W(first,"cost"), net=W(first,"net")),
               last_half=dict(gross=W(last,"gross"), cost=W(last,"cost"), net=W(last,"net")),
               slope=dict(gross=sl("gross"), cost=sl("cost"), net=sl("net")),
               months_gross_pos=sum(1 for r in ok if r["gross"]>0),
               months_net_pos=sum(1 for r in ok if r["net"]>0))
    out["decay"] = dict(d_gross=out["last_half"]["gross"]-out["first_half"]["gross"],
                        d_cost=out["last_half"]["cost"]-out["first_half"]["cost"],
                        d_net=out["last_half"]["net"]-out["first_half"]["net"])
    sg = [r["signal"] for r in ok if "signal" in r]
    if len(sg) >= 4:
        out["signal"] = dict(per_window=sg, mean=float(np.mean(sg)),
                             months_pos=sum(1 for v in sg if v>0),
                             first_half=float(np.mean(sg[:len(sg)//2])), last_half=float(np.mean(sg[len(sg)//2:])))
    return out

OKF = lambda w: w.ok
CL  = lambda w: w.ok & (w.past == 0) & (w.fam != 1)
C = {}
def add(n, fn, note=""):
    r = series(n, fn, note)
    if r: C[n] = r
add("CORRECTED_all", OKF, "d1b corrected contract, all fills")
add("CORRECTED_clean", CL, "corrected contract, clean roster")
add("CORRECTED_at_market", lambda w: w.ok & (w.atm==1), "seven at-market families, market fill")
for fi, fn in enumerate(FA):
    if fn=="__other__": continue
    add(f"FAM_{fn}", lambda w, fi=fi: w.ok & (w.fam==fi) & (w.past==0), "family, clean, corrected contract")
add("d7_POI_level_already_at_market", lambda w: (w.fil==1)&(w.atm==0)&(w.touch==0), "POI limit that filled in the decision bar")
add("d7_POI_genuine_pullback",        lambda w: (w.fil==1)&(w.atm==0)&(w.touch>0),  "POI limit that filled later")
add("d7_REPAIR_clean_minus_poi_at_mkt", lambda w: CL(w) & ~((w.atm==0)&(w.touch==0)), "d7 repair applied to the clean roster")
json.dump(C, open("/tmp/p1/P1_CORRECTED_V1.json","w"))
for k,v in C.items():
    p=v["pooled"]; d=v["decay"]; s=v.get("signal",{})
    print(f"{k:40s} n{p['n']:>7d} gross {p['gross']:+.5f} cost {p['cost']:.5f} net {p['net']:+.5f} "
          f"| g+ {v['months_gross_pos']}/8 | dg {d['d_gross']:+.5f} dc {d['d_cost']:+.5f} slope_g {v['slope']['gross']:+.5f}"
          + (f" | sig {s['mean']:+.5f} ({s['months_pos']}/8) first {s['first_half']:+.5f} last {s['last_half']:+.5f}" if s else ""), flush=True)
