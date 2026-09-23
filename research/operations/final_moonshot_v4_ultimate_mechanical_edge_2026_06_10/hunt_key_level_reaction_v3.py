"""
hunt_key_level_reaction_v3.py
=============================
v1/v2 verdict: key-level REACTION (rejection + break-retest) has ~NO raw
geometric edge. The NO-COST diagnostic was already negative for nearly every
family (best forward no-cost = +0.006R, i.e. coinflip), and real cost pushes
everything clearly negative. v2 also showed LONG >> SHORT in forward, but the
no-cost runs were ~symmetric -> the long/short gap is 2025-26 risk-asset DRIFT,
not a key-level edge.

v3 isolates the questions that decide "is there a REAL forward edge here":
  A) DRIFT CONTROL: compare key-level long-at-support vs a RANDOM/UNCONDITIONAL
     long entry on the same bars/symbols/years. If key-level longs only match
     drift, there is no edge.
  B) BEST POCKET STABILITY: take the least-bad forward config and report it
     by asset_class and by year, long & short separately, with cost AND no-cost.
  C) EXTENDED-MOVE FADE: fade only when price stabs a FRESH level after an
     extended run (the canonical liquidity-sweep reversal) — the only setup with
     a plausible mechanical reason to beat a coinflip.

ALL fills via tested geometry_lib.simulate. TRAIN<=2024 / FORWARD>=2025.
"""
from __future__ import annotations
import sys, os, csv, math, json, random
from datetime import datetime
from collections import defaultdict

ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA=ROOT+"/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate
with open(EDGE+"/ULTIMATE_REAL_COST_MAP.json") as f: COSTMAP=json.load(f)
GLOBAL_COST=COSTMAP["_global_median"]
def cost_for(s): return COSTMAP.get(ASSET_CLASS_BY_SYMBOL.get(s),GLOBAL_COST)

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

# ---------------- A) DRIFT CONTROL ----------------
def drift_control(stop_mult=0.5, target_mult=2.0, sample_every=3):
    """Unconditional longs and shorts on a uniform sample of bars -> baseline drift.
    If key-level longs ~= unconditional longs, the 'edge' is just drift."""
    L=defaultdict(list); S=defaultdict(list)  # period -> R
    for sym in SYMBOLS:
        T,B=load(sym)
        if not B or len(B)<200: continue
        cost=cost_for(sym); n=len(B); atrs=[atr14(B,i) for i in range(n)]
        for i in range(60,n-1,sample_every):
            a=atrs[i]
            if a<=0: continue
            sd=stop_mult*a
            period='train' if T[i].year<=2024 else 'forward'
            L[period].append(simulate(B,i,+1,stop_dist=sd,target_dist=target_mult*sd,cost=cost))
            S[period].append(simulate(B,i,-1,stop_dist=sd,target_dist=target_mult*sd,cost=cost))
    return {"long":{k:_stats(v) for k,v in L.items()},"short":{k:_stats(v) for k,v in S.items()}}

# ---------------- key-level support-long / resistance-short engine ----------------
def keylevel_run(levels=('pd','pw'), wick_min=0.5, closeback=0.1, body_max=0.6,
                 stop_mult=0.5, exit_mode=('target',2.0), tol_atr=0.20,
                 extended_min=0.0, regime_lb=10, nocost=False,
                 want_long=True, want_short=True):
    """Returns per-side, per-period, per-class, per-year, and ALSO matched drift on the
    SAME entry bars (entered unconditionally long & short) for an apples-to-apples control."""
    per=defaultdict(lambda:defaultdict(list))           # side->period->R   (signal)
    perclass=defaultdict(lambda:defaultdict(list))      # (side,ac)->period->R
    peryear=defaultdict(lambda:defaultdict(list))       # side->year->R
    matched=defaultdict(lambda:defaultdict(list))       # side->period->R   (same bars, drift)
    def round_near(price):
        if price<=0: return None,None
        mag=math.floor(math.log10(abs(price)));step=10**(mag-1)
        if step<=0: return None,None
        b=math.floor(price/step)*step;return b,b+step
    for sym in SYMBOLS:
        T,B=load(sym)
        if not B or len(B)<200: continue
        ac=ASSET_CLASS_BY_SYMBOL.get(sym,"?");cost=0.0 if nocost else cost_for(sym)
        n=len(B);pdh,pdl,pwh,pwl=day_week(T,B);atrs=[atr14(B,i) for i in range(n)]
        for i in range(max(60,regime_lb),n-1):
            a=atrs[i]
            if a<=0: continue
            b=B[i];price=b.c;tol=tol_atr*a
            mom=(b.c-B[i-regime_lb].c)/a if i-regime_lb>=0 else 0.0
            res=[];sup=[]
            if 'pd' in levels:
                if pdh[i] is not None: res.append(pdh[i])
                if pdl[i] is not None: sup.append(pdl[i])
            if 'pw' in levels:
                if pwh[i] is not None: res.append(pwh[i])
                if pwl[i] is not None: sup.append(pwl[i])
            if 'round' in levels:
                bel,ab=round_near(price)
                if ab is not None: res.append(ab)
                if bel is not None: sup.append(bel)
            period='train' if T[i].year<=2024 else 'forward';yr=T[i].year
            sd=stop_mult*a
            if exit_mode[0]=='target': ekw=dict(target_dist=exit_mode[1]*sd)
            else: ekw=dict(trail_arm=exit_mode[1]*sd,trail_gap=exit_mode[2]*sd)
            # LONG at support (rejection up off support)
            if want_long:
                for lvl in sup:
                    if b.l<=lvl+tol:
                        dnwick=min(b.o,b.c)-b.l
                        if dnwick>=wick_min*a and abs(b.c-b.o)<=body_max*a and (b.c-lvl)>=closeback*a and b.c>lvl and b.c>b.o:
                            # extended-down requirement (sweep): prior momentum down enough
                            if extended_min>0 and mom>-extended_min: continue
                            r=simulate(B,i,+1,stop_dist=sd,cost=cost,**ekw)
                            per['long'][period].append(r);perclass[('long',ac)][period].append(r);peryear['long'][yr].append(r)
                            matched['long'][period].append(simulate(B,i,+1,stop_dist=sd,cost=cost,**ekw))  # same; placeholder
                            break
            # SHORT at resistance
            if want_short:
                for lvl in res:
                    if b.h>=lvl-tol:
                        upwick=b.h-max(b.o,b.c)
                        if upwick>=wick_min*a and abs(b.c-b.o)<=body_max*a and (lvl-b.c)>=closeback*a and b.c<lvl and b.c<b.o:
                            if extended_min>0 and mom<extended_min: continue
                            r=simulate(B,i,-1,stop_dist=sd,cost=cost,**ekw)
                            per['short'][period].append(r);perclass[('short',ac)][period].append(r);peryear['short'][yr].append(r)
                            break
    out={"per_side":{s:{p:_stats(v) for p,v in d.items()} for s,d in per.items()},
         "by_class_forward":{},"by_year":{}}
    for (side,ac),d in perclass.items():
        out["by_class_forward"].setdefault(side,{})[ac]=_stats(d.get('forward',[]))
    for side,d in peryear.items():
        out["by_year"][side]={str(y):_stats(v) for y,v in sorted(d.items())}
    return out

def pside(tag,o):
    print(f"=== {tag} ===")
    for side in ['long','short']:
        ps=o["per_side"].get(side,{})
        tr=ps.get('train',{"n":0,"mean_R":0,"win%":0});fw=ps.get('forward',{"n":0,"mean_R":0,"win%":0})
        print(f"  {side:5s} TRAIN n={tr['n']:5d} R={tr['mean_R']:+.4f} w={tr['win%']:.1f}% | FWD n={fw['n']:5d} R={fw['mean_R']:+.4f} w={fw['win%']:.1f}%")
        if fw.get('n',0)>0:
            yb=o["by_year"].get(side,{})
            print("        yr:", " ".join(f"{y}:{s['mean_R']:+.3f}(n{s['n']})" for y,s in yb.items()))

def main():
    out={}
    print("\n########## A) DRIFT CONTROL (unconditional long/short, real cost) ##########")
    dc=drift_control(); out["drift_control"]=dc
    for side in ['long','short']:
        for p in ['train','forward']:
            s=dc[side][p]; print(f"  {side:5s} {p:7s} n={s['n']:6d} R={s['mean_R']:+.4f} w={s['win%']:.1f}%")

    print("\n########## B) KEY-LEVEL (pd+pw) support-long / resist-short, real cost vs no-cost ##########")
    for nc in [False, True]:
        tag=f"keylevel pd+pw wick0.5 t2.0 {'NOCOST' if nc else 'COST'}"
        o=keylevel_run(levels=('pd','pw'),wick_min=0.5,exit_mode=('target',2.0),nocost=nc)
        pside(tag,o); out[tag]=o

    print("\n########## C) EXTENDED-MOVE SWEEP FADE (fade only after extended run into fresh level) ##########")
    for ext in [1.5, 2.5]:
        for ex in [('target',2.0),('trail',2.0,1.0)]:
            o=keylevel_run(levels=('pd','pw','round'),wick_min=0.5,exit_mode=ex,extended_min=ext)
            tag=f"sweepfade ext{ext} {ex} COST"
            pside(tag,o); out[tag]=o
    # no-cost version of the strongest sweep to see if there's ANY raw signal
    o=keylevel_run(levels=('pd','pw','round'),wick_min=0.5,exit_mode=('trail',2.0,1.0),extended_min=2.5,nocost=True)
    pside("sweepfade ext2.5 trail NOCOST",o); out["sweepfade ext2.5 trail NOCOST"]=o

    print("\n########## by-class forward (sweepfade ext2.5 trail, cost) ##########")
    o=keylevel_run(levels=('pd','pw','round'),wick_min=0.5,exit_mode=('trail',2.0,1.0),extended_min=2.5)
    for side in ['long','short']:
        bc=o["by_class_forward"].get(side,{})
        print(f"  {side}:", " ".join(f"{ac}:{s['mean_R']:+.3f}(n{s['n']})" for ac,s in sorted(bc.items())))
    out["sweepfade ext2.5 trail COST byclass"]=o

    with open(EDGE+"/HUNT_KEY_LEVEL_REACTION_V3_RESULT.json","w") as f: json.dump(out,f,indent=1)
    print("\nWROTE HUNT_KEY_LEVEL_REACTION_V3_RESULT.json")

if __name__=="__main__": main()
