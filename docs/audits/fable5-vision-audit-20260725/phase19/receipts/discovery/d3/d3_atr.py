"""d3 B2 — the VOL-MATCHED transplant.

A flat bps stop is the wrong transplant: it hands EURUSD a 400 bps stop and BTCUSD a 25
bps one.  The live sleeves size their stop off the instrument's own H4 structure (their
realised risk distances run 44 bps on sub_mid_dn_revert to 436 bps on mx_btcusd -- one
scale in ATR terms, five scales in bps terms).  This pass therefore sets

        stop = k * ATR14(H4, last CLOSED H4 bar before the decision)

which is the live sleeves' own sizing convention, and sweeps k.  Everything else --
horizon ladder, target ladder, toll, PLACEBO-SIDE -- is identical to the flat-bps pass.
"""
from __future__ import annotations
import json, sys, time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2

KS = [0.25, 0.5, 1.0, 2.0, 4.0]
HORIZ = W.HORIZ_BARS
TARGETS = [2.0, 3.0, 4.0]

def h4_atr(tape, sym, period=14):
    """ATR14 on H4 bars built from the printed M15 series.  Returns (bar_start_min, atr)
    where atr[i] is computable from bars <= i, i.e. usable at the CLOSE of H4 bar i."""
    tm = tape.tmin[sym]; h=tape.h[sym]; l=tape.l[sym]; c=tape.c[sym]
    if len(tm)==0: return np.array([]), np.array([])
    g = tm//240
    ug, start = np.unique(g, return_index=True)
    end = np.r_[start[1:], len(tm)]
    hi = np.maximum.reduceat(h, start); lo = np.minimum.reduceat(l, start)
    cl = c[end-1]
    pc = np.r_[cl[0], cl[:-1]]
    tr = np.maximum(hi-lo, np.maximum(np.abs(hi-pc), np.abs(lo-pc)))
    atr = np.full(len(tr), np.nan)
    if len(tr) >= period:
        cs = np.cumsum(tr)
        atr[period-1:] = (cs[period-1:] - np.r_[0.0, cs[:-period]])/period
    return ug*240, atr     # H4 bar START minute, atr valid at its CLOSE (start+240)

def build_atr_lookup(tape, symbols):
    out={}
    for s in symbols:
        st, a = h4_atr(tape, s)
        out[s] = (st+240, a)     # the instant the value becomes usable
    return out

def atr_at(lookup, sym, minute):
    st, a = lookup[sym]
    if len(st)==0: return np.nan
    i = int(np.searchsorted(st, minute, side="right"))-1
    if i < 0: return np.nan
    return float(a[i])

def run_window(win, indir, tape, C, lookup, out_path, chunk=6000):
    rows = W.load_window(win, D.WINDOWS[win] if indir is None else indir)
    n=len(rows)
    rng=np.random.default_rng(W.SEED+int(win.replace("-",""))+7)
    entry=np.array([float(r["e"]) for r in rows]); slp=np.array([float(r["sl"]) for r in rows])
    dnat=np.abs(entry-slp); long=np.array([r["d"]=="L" for r in rows]); plong=rng.random(n)<0.5
    sym=[r["s"] for r in rows]; inst=[r["t"] for r in rows]
    day=np.array([r["t"][:10] for r in rows]); fam=np.array([r["f"] for r in rows])
    base=np.zeros(n); pn_L=np.zeros(n); pn_S=np.zeros(n); atr=np.zeros(n); bd0=[]
    for a in range(n):
        b,_,_,_=C.base_px(sym[a],inst[a],entry[a]); base[a]=b
        pn_L[a]=C.per_night_px(sym[a],True,entry[a]); pn_S[a]=C.per_night_px(sym[a],False,entry[a])
        bd0.append(C.cm._to_broker(datetime.fromisoformat(inst[a]), C.cm.server))
        atr[a]=atr_at(lookup, sym[a], tape.minutes(inst[a]))
    acc=defaultdict(lambda: defaultdict(float)); daily=defaultdict(lambda: defaultdict(float))
    dailyg=defaultdict(lambda: defaultdict(float)); dailyn=defaultdict(lambda: defaultdict(int))
    famacc=defaultdict(lambda: defaultdict(float))
    for c0 in range(0,n,chunk):
        ix=list(range(c0,min(c0+chunk,n)))
        pos,W_h,W_l,W_c,W_t,t_dec=W.build_frames(tape,rows,ix)
        sl_=np.array(ix); e=entry[sl_][:,None]
        for arm,side in (("REAL",long[sl_]),("PLACEBO",plong[sl_])):
            sgn=np.where(side,1.0,-1.0)[:,None]
            pn=np.where(side,pn_L[sl_],pn_S[sl_])
            for k in KS:
                d=k*atr[sl_]
                bad=~np.isfinite(d)|(d<=0)
                d=np.where(bad,np.nan,d)
                dd=d[:,None]
                with np.errstate(invalid="ignore"):
                    rc=(W_c-e)/dd*sgn; rh_=(W_h-e)/dd*sgn; rl_=(W_l-e)/dd*sgn
                rhi=np.maximum(rh_,rl_); rlo=np.minimum(rh_,rl_)
                for tr in TARGETS:
                    res=W.cell_walk(rc,rhi,rlo,tr,HORIZ)
                    for Hh,(r,xb,code) in res.items():
                        W._accum(acc,daily,dailyg,dailyn,famacc,arm,"atr%g"%k,tr,Hh,"fixed",
                                 r,xb,code,base[sl_],pn,d,day[sl_],fam[sl_],
                                 [bd0[i] for i in ix],W_t,t_dec)
                # record the realised stop width in bps for this k
                key="ATRBPS|%g"%k
                v=(d/entry[sl_]*1e4)
                v=v[np.isfinite(v)]
                acc[key]["n"]+=len(v); acc[key]["sum_gross"]+=float(v.sum())
        del W_h,W_l,W_c,W_t
    out={"window":win,"n_rows":n,"cells":{}}
    for kk,v in acc.items():
        out["cells"][kk]=dict(v)
        out["cells"][kk]["day_net"]={d:daily[kk][d] for d in sorted(daily[kk])}
        out["cells"][kk]["day_gross"]={d:dailyg[kk][d] for d in sorted(dailyg[kk])}
        out["cells"][kk]["day_n"]={d:dailyn[kk][d] for d in sorted(dailyn[kk])}
    json.dump(out,open(out_path,"w"))
    return out

if __name__=="__main__":
    syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
    tape=T2.CTape(syms); C=W.Cost(); lookup=build_atr_lookup(tape,syms)
    for win in D.WINDOWS:
        t0=time.time()
        o=run_window(win,None,tape,C,lookup,f"/tmp/d3/D3ATR_{win}.json")
        print(win,o["n_rows"],len(o["cells"]),round(time.time()-t0,1),flush=True)
    print("ATR DONE",flush=True)
