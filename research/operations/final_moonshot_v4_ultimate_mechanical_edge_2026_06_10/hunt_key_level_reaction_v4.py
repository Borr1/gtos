"""
hunt_key_level_reaction_v4.py
=============================
Final confirmation for KEY_LEVEL_REACTION.

Prior verdict (v1-v3):
  - Raw geometry has ~no edge (no-cost runs ~coinflip; best forward no-cost ~+0.09R
    for long-at-support, but that tracks 2025 risk-asset drift).
  - After real cost the BEST pocket (pd/pw support-long, 0.5atr stop, 2R target)
    is ~ -0.003R forward = breakeven-negative, and is 2025-positive / 2026-negative.
  - Short-at-resistance is firmly negative forward.
  - The good-looking sweep-fade SHORT is TRAIN-only and INVERTS in forward (overfit).

v4 answers two clean questions:
  (1) MATCHED CONTROL (fixed): on the EXACT signal bars, what does an
      unconditional long (same stop/target/cost) earn? Edge = signal - matched.
  (2) STABILITY: split forward into 2025-H1, 2025-H2, 2026 and report per-period
      so we can see if the tiny long pocket is stable or just one good half.

ALL fills via tested geometry_lib.simulate.
"""
from __future__ import annotations
import sys, os, csv, math, json
from datetime import datetime
from collections import defaultdict
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA=ROOT+"/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate
with open(EDGE+"/ULTIMATE_REAL_COST_MAP.json") as f: COSTMAP=json.load(f)
GC=COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s),GC)
def load(sym):
    p=f"{DATA}/{sym}_H4.csv"
    if not os.path.exists(p): return None,None
    T=[];B=[]
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                T.append(datetime.strptime(row["time"],"%Y-%m-%d %H:%M:%S"))
                B.append(Bar(float(row["open"]),float(row["high"]),float(row["low"]),float(row["close"]),float(row.get("volume",0) or 0)))
            except Exception: continue
    return T,B
SYMBOLS=[fn[:-7] for fn in sorted(os.listdir(DATA)) if fn.endswith("_H4.csv")]
def day_week(times,bars):
    n=len(bars);dk=[t.date() for t in times];wk=[t.isocalendar()[:2] for t in times]
    pdh=[None]*n;pdl=[None]*n;pwh=[None]*n;pwl=[None]*n
    cd=None;cdh=cdl=None;ldh=ldl=None;cw=None;cwh=cwl=None;lwh=lwl=None
    for i in range(n):
        if dk[i]!=cd:
            if cd is not None: ldh=cdh;ldl=cdl
            cd=dk[i];cdh=bars[i].h;cdl=bars[i].l
        else: cdh=max(cdh,bars[i].h);cdl=min(cdl,bars[i].l)
        if wk[i]!=cw:
            if cw is not None: lwh=cwh;lwl=cwl
            cw=wk[i];cwh=bars[i].h;cwl=bars[i].l
        else: cwh=max(cwh,bars[i].h);cwl=min(cwl,bars[i].l)
        pdh[i]=ldh;pdl[i]=ldl;pwh[i]=lwh;pwl[i]=lwl
    return pdh,pdl,pwh,pwl
def _stats(rs):
    if not rs: return {"n":0,"mean_R":0.0,"win%":0.0}
    n=len(rs);s=sum(rs);w=sum(1 for r in rs if r>0)
    return {"n":n,"mean_R":round(s/n,4),"win%":round(100*w/n,1)}
def seg(t):
    if t.year<=2024: return 'train'
    if t.year==2025: return '2025H1' if t.month<=6 else '2025H2'
    return '2026'

def run(levels=('pd','pw'), wick_min=0.5, closeback=0.1, body_max=0.6,
        stop_mult=0.5, exit_mode=('target',2.0), tol_atr=0.20):
    sig=defaultdict(lambda:defaultdict(list))   # side->seg->R
    ctl=defaultdict(lambda:defaultdict(list))   # side->seg->R (same bars, unconditional same-direction)
    def rn(price):
        if price<=0: return None,None
        mag=math.floor(math.log10(abs(price)));step=10**(mag-1)
        if step<=0: return None,None
        b=math.floor(price/step)*step;return b,b+step
    for sym in SYMBOLS:
        T,B=load(sym)
        if not B or len(B)<200: continue
        cost=cost_for(sym);n=len(B);pdh,pdl,pwh,pwl=day_week(T,B);atrs=[atr14(B,i) for i in range(n)]
        for i in range(60,n-1):
            a=atrs[i]
            if a<=0: continue
            b=B[i];price=b.c;tol=tol_atr*a;sd=stop_mult*a
            if exit_mode[0]=='target': ekw=dict(target_dist=exit_mode[1]*sd)
            else: ekw=dict(trail_arm=exit_mode[1]*sd,trail_gap=exit_mode[2]*sd)
            res=[];sup=[]
            if 'pd' in levels:
                if pdh[i] is not None: res.append(pdh[i])
                if pdl[i] is not None: sup.append(pdl[i])
            if 'pw' in levels:
                if pwh[i] is not None: res.append(pwh[i])
                if pwl[i] is not None: sup.append(pwl[i])
            if 'round' in levels:
                bel,ab=rn(price)
                if ab is not None: res.append(ab)
                if bel is not None: sup.append(bel)
            s=seg(T[i])
            for lvl in sup:
                if b.l<=lvl+tol:
                    dnwick=min(b.o,b.c)-b.l
                    if dnwick>=wick_min*a and abs(b.c-b.o)<=body_max*a and (b.c-lvl)>=closeback*a and b.c>lvl and b.c>b.o:
                        sig['long'][s].append(simulate(B,i,+1,stop_dist=sd,cost=cost,**ekw))
                        ctl['long'][s].append(simulate(B,i,+1,stop_dist=sd,cost=cost,**ekw))  # identical => control is "long this bar regardless of level test"
                        break
            for lvl in res:
                if b.h>=lvl-tol:
                    upwick=b.h-max(b.o,b.c)
                    if upwick>=wick_min*a and abs(b.c-b.o)<=body_max*a and (lvl-b.c)>=closeback*a and b.c<lvl and b.c<b.o:
                        sig['short'][s].append(simulate(B,i,-1,stop_dist=sd,cost=cost,**ekw))
                        break
    return sig

def matched_control(stop_mult=0.5, exit_mode=('target',2.0)):
    """Unconditional long & short on EVERY qualifying bar (atr>0), segmented,
    to compare the signal's per-seg mean against the universe drift per seg."""
    L=defaultdict(list);S=defaultdict(list)
    for sym in SYMBOLS:
        T,B=load(sym)
        if not B or len(B)<200: continue
        cost=cost_for(sym);n=len(B);atrs=[atr14(B,i) for i in range(n)]
        for i in range(60,n-1,2):
            a=atrs[i]
            if a<=0: continue
            sd=stop_mult*a
            if exit_mode[0]=='target': ekw=dict(target_dist=exit_mode[1]*sd)
            else: ekw=dict(trail_arm=exit_mode[1]*sd,trail_gap=exit_mode[2]*sd)
            s=seg(T[i])
            L[s].append(simulate(B,i,+1,stop_dist=sd,cost=cost,**ekw))
            S[s].append(simulate(B,i,-1,stop_dist=sd,cost=cost,**ekw))
    return L,S

def main():
    out={}
    SEGS=['train','2025H1','2025H2','2026']
    print("########## STABILITY: pd+pw support-long / resist-short (real cost, t2.0) ##########")
    sig=run(levels=('pd','pw'),exit_mode=('target',2.0))
    for side in ['long','short']:
        print(f"  {side}:")
        for s in SEGS:
            st=_stats(sig[side].get(s,[]))
            print(f"     {s:7s} n={st['n']:5d} R={st['mean_R']:+.4f} w={st['win%']:.1f}%")
        out[f"sig_{side}"]={s:_stats(sig[side].get(s,[])) for s in SEGS}

    print("\n########## MATCHED DRIFT CONTROL (unconditional long/short per seg) ##########")
    L,S=matched_control(exit_mode=('target',2.0))
    for nm,D in [('long',L),('short',S)]:
        print(f"  {nm}:")
        for s in SEGS:
            st=_stats(D.get(s,[])); print(f"     {s:7s} n={st['n']:6d} R={st['mean_R']:+.4f}")
        out[f"drift_{nm}"]={s:_stats(D.get(s,[])) for s in SEGS}

    print("\n########## EDGE = signal - drift, per seg ##########")
    for side,D in [('long',L),('short',S)]:
        print(f"  {side}:")
        for s in SEGS:
            sg=_stats(sig[side].get(s,[]))['mean_R']; dr=_stats(D.get(s,[]))['mean_R']
            print(f"     {s:7s} signal={sg:+.4f}  drift={dr:+.4f}  EDGE={sg-dr:+.4f}")

    with open(EDGE+"/HUNT_KEY_LEVEL_REACTION_V4_RESULT.json","w") as f: json.dump(out,f,indent=1)
    print("\nWROTE HUNT_KEY_LEVEL_REACTION_V4_RESULT.json")

if __name__=="__main__": main()
