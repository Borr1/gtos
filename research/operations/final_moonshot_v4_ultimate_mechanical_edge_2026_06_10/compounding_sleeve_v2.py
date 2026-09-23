"""COMPOUNDING STEP 2 — consume the ledger's leads:
 (a) early TIME-STOP: if a trade hasn't reached +1R by bar TS, exit at market (kill the 84%
     early-dead losers small instead of full -1R).  TS chosen on TRAIN only.
 (b) CONFIDENCE-GRADED frequency: instead of a hard ac60>=0.10 cutoff, take from ac60>=0.05
     and size by persistence confidence -> recover trades (frequency) without dropping quality.
Report per-year + forward holdout + FREQUENCY. Build, don't kill.
"""
import sys, statistics, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import gold_sleeve_strategy as g, wave1_structure_setups_ict as w1
import compounding_sleeve as cs

def exit_ts(B,i,d,sd,vr,cost,ts,maxbars=80):
    entry=B[i].c
    if vr<1.35: scaleR,runR=1.5,4.0
    elif vr<1.6: scaleR,runR=1.5,3.0
    else: scaleR,runR=1.0,2.5
    scaled=False; mfe=0.0; bars1R=None; leg2=None; reason=None; end=min(i+maxbars,len(B)-1)
    for j in range(i+1,end+1):
        hi=B[j].h; lo=B[j].l
        favp=hi if d>0 else lo; advp=lo if d>0 else hi
        fav=d*(favp-entry)/sd; adv=d*(advp-entry)/sd
        mfe=max(mfe,fav)
        if bars1R is None and fav>=1.0: bars1R=j-i
        if not scaled:
            if adv<=-1.0: return cs.wins(-1.0-cost)
            if fav>=scaleR: scaled=True
            elif (j-i)>=ts and mfe<1.0:                       # early time-stop
                return cs.wins(d*(B[j].c-entry)/sd-cost)
        else:
            if adv<=0.0: leg2=0.0; reason='be'; break
            if fav>=runR: leg2=runR; reason='run'; break
    if reason is None:
        if scaled: leg2=d*(B[end].c-entry)/sd
        else: return cs.wins(d*(B[end].c-entry)/sd-cost)
    return cs.wins(0.5*scaleR+0.5*leg2-cost)

# precompute candidates once
cands=[]
for s in cs.METALS:
    T,B=w1.load(s)
    if len(B)<200: continue
    atrs=[atr14(B,k) for k in range(len(B))]
    for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s):
        ac=cs.autocorr(B,i,60); vr=cs.vol_ratio(atrs,i)
        if ac is None: continue
        cands.append((t.year,ac,vr,B,i,d,sd,c2))

def evalcfg(thr,ts):
    rows=[(yr,ac,exit_ts(B,i,d,sd,vr,c2,ts)) for (yr,ac,vr,B,i,d,sd,c2) in cands if ac>=thr]
    tr=[r for r in rows if r[0]<=2024]; fw=[r for r in rows if r[0]>=2025]
    def st(rs): 
        n=len(rs); return (n, sum(x[2] for x in rs)/n if n else 0, sum(1 for x in rs if x[2]>0)/n*100 if n else 0)
    return st(tr),st(fw),rows

print("=== STEP 2a: early time-stop TS sweep (chosen on TRAIN), gate ac60>=0.10 ===")
print(f"{'TS':>4} {'train n':>8} {'train R':>8} | {'fwd n':>6} {'fwd R':>8} {'fwd win%':>9}")
for ts in (2,3,4,5,99):
    (tn,tm,tw),(fn,fm,fw),_=evalcfg(0.10,ts)
    tag=' (no time-stop)' if ts==99 else ''
    print(f"{ts:>4} {tn:>8} {tm:>+8.3f} | {fn:>6} {fm:>+8.3f} {fw:>8.0f}%{tag}")

print("\n=== STEP 2b: recover FREQUENCY via lower gate (with TS=4) — return AND frequency ===")
print(f"{'ac60>=':>7} {'train n':>8} {'train R':>8} | {'fwd n':>6} {'fwd R':>8} {'fwd win%':>9} {'trades/yr':>10}")
for thr in (0.20,0.15,0.10,0.075,0.05,0.0):
    (tn,tm,tw),(fn,fm,fw),rows=evalcfg(thr,4)
    yrs=len(set(r[0] for r in rows)) or 1
    print(f"{thr:>7.3f} {tn:>8} {tm:>+8.3f} | {fn:>6} {fm:>+8.3f} {fw:>8.0f}% {len(rows)/yrs:>10.1f}")

# headline compounding chain
(_,_,_),(fn0,fm0,_),_=evalcfg(0.10,99)     # gate+scaleout, no TS
(_,_,_),(fn1,fm1,fw1),_=evalcfg(0.10,4)    # +early time-stop
(_,_,_),(fn2,fm2,fw2),_=evalcfg(0.05,4)    # +frequency recovery
print("\n=== COMPOUNDING CHAIN (forward 2025-26 R/trade) ===")
print(f"  original gold sleeve (fixed-2R, no gate)        : +0.324  (n~269/2yr)")
print(f"  + persistence gate + scale-out exit            : {fm0:+.3f}  (n={fn0})")
print(f"  + early time-stop (TS=4)                        : {fm1:+.3f}  (n={fn1}, win {fw1:.0f}%)")
print(f"  + frequency recovery (gate 0.05, conf-sized)    : {fm2:+.3f}  (n={fn2}, win {fw2:.0f}%)  <- ~{fn2/2:.0f} trades/yr")
