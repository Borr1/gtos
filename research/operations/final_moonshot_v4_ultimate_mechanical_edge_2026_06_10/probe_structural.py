"""
probe_structural.py
Two structural hypotheses on the dead classes:
  (1) SWEEP-RECLAIM FADE at prior-day/session level: price pokes beyond a prior extreme
      then closes back inside -> fade back toward range. (liquidity grab) Enter next bar.
      Target = opposite prior extreme OR fixed. Tested per class, train/forward.
  (2) SESSION-OPEN BREAKOUT continuation: first bar of London (h==8) or NY (h==16) that
      breaks the prior session's range -> continue in breakout direction.
"""
import sys, json
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import feats, session, stats, wins, CLASSES
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1m

def sp(recs):
    tr=[r for _,y,r in recs if y<=2024]; f25=[r for _,y,r in recs if y==2025]; f26=[r for _,y,r in recs if y==2026]
    return stats(tr),stats(f25),stats(f26)

def per_sym(recs):
    from collections import defaultdict
    by=defaultdict(list)
    for s,y,r in recs: by[s].append(r)
    return {s:stats(by[s]) for s in sorted(by)}

def sweep_reclaim_fade(syms, level='pd', sweep_min=0.10, reclaim_min=0.10, stop_buf=0.30,
                       target_mult=1.0, stop_floor=0.5, maxbars=18, sess=None):
    """Sweep prior extreme + reclaim, fade toward range. stop beyond swept wick.
    target = target_mult * stop_dist (fixed R). Enter next bar open."""
    recs=[]
    for sym in syms:
        T,B,atrs,_,pdlv,pslv=feats(sym)
        n=len(B)
        if n<200: continue
        pdh,pdl=pdlv; psh,psl=pslv
        H=psh if level=='ps' else pdh; L=psl if level=='ps' else pdl
        cost=w1m.cost_for(sym)  # stop is structural ~ near 1 ATR; keep base
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if sess is not None and session(T[i].hour) not in sess: continue
            b=B[i]; nb=B[i+1]; lo=L[i]; hi=H[i]; entry=nb.o
            # sweep LOW + reclaim -> FADE = go LONG (revert up)
            if lo is not None and (lo-b.l)>=sweep_min*a and b.c>lo and (b.c-lo)>=reclaim_min*a:
                sd=max((entry-b.l)+stop_buf*a, stop_floor*a)
                td=target_mult*sd
                c=cost*(1.0/(sd/a)) if sd>0 else cost
                r=simulate(B,i+1,1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=c)
                recs.append((sym,T[i+1].year,wins(r)))
            # sweep HIGH + reclaim -> FADE = go SHORT
            if hi is not None and (b.h-hi)>=sweep_min*a and b.c<hi and (hi-b.c)>=reclaim_min*a:
                sd=max((b.h-entry)+stop_buf*a, stop_floor*a)
                td=target_mult*sd
                c=cost*(1.0/(sd/a)) if sd>0 else cost
                r=simulate(B,i+1,-1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=c)
                recs.append((sym,T[i+1].year,wins(r)))
    return recs

def session_open_breakout(syms, open_hours=(8,), break_min=0.0, stop_mult=1.0, target_mult=1.5, maxbars=20):
    """First bar of a session (bar hour in open_hours) that breaks prior-session range ->
    continue. Enter next bar open in breakout direction."""
    recs=[]
    for sym in syms:
        T,B,atrs,_,_,pslv=feats(sym)
        n=len(B)
        if n<200: continue
        psh,psl=pslv
        cost=w1m.cost_for(sym)*(1.0/stop_mult)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if T[i].hour not in open_hours: continue
            b=B[i]; hi=psh[i]; lo=psl[i]
            if hi is None or lo is None: continue
            sd=stop_mult*a; td=target_mult*sd
            if (b.c-hi)>=break_min*a and b.c>b.o:  # broke prior-session high up
                r=simulate(B,i+1,1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=cost)
                recs.append((sym,T[i+1].year,wins(r)))
            elif (lo-b.c)>=break_min*a and b.c<b.o:  # broke prior-session low down
                r=simulate(B,i+1,-1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=cost)
                recs.append((sym,T[i+1].year,wins(r)))
    return recs

if __name__=="__main__":
    out={}
    print("############ (1) SWEEP-RECLAIM FADE (structural liquidity grab) ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### {cls} #####")
        for level in ['pd','ps']:
            for tm in [0.75,1.0,1.5]:
                recs=sweep_reclaim_fade(CLASSES[cls],level=level,target_mult=tm)
                tr,f25,f26=sp(recs)
                if tr['n']<100: continue
                flag="  <<<" if (tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
                print(f"  {level} tgt{tm} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
                out[f"{cls}_sweepfade_{level}_t{tm}"]={"train":tr,"f25":f25,"f26":f26}
    print("\n############ (2) SESSION-OPEN BREAKOUT continuation ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### {cls} #####")
        for oh,ohn in [((8,),"London08"),((12,),"London12"),((16,),"NY16"),((20,),"NY20"),((0,),"Asia00")]:
            for tm in [1.0,1.5,2.5]:
                recs=session_open_breakout(CLASSES[cls],open_hours=oh,break_min=0.05,stop_mult=1.0,target_mult=tm)
                tr,f25,f26=sp(recs)
                if tr['n']<80: continue
                flag="  <<<" if (tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
                print(f"  {ohn} tgt{tm} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
                out[f"{cls}_sessbreak_{ohn}_t{tm}"]={"train":tr,"f25":f25,"f26":f26}
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_STRUCTURAL.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE PROBE_STRUCTURAL.json")
