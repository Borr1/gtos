"""
probe_geometry_sweep.py
The 1R symmetric target is structurally a loser at ~50% win. Sweep geometry to find
where reversion / pullback-continuation actually pays. Key ideas:
  REVERSION (fade stretch): tight target (mean-revert quickly), tolerant stop, short hold.
  PULLBACK-CONT: only WITH HTF trend, enter on a pullback bar (counter-trend bar) in trend.
Pick on TRAIN, report 2025/2026.
"""
import sys, json
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import feats, session, stats, wins, CLASSES
from geometry_lib import simulate
import wave1_structure_setups_ict as w1m
from geometry_lib import atr14

def htf(B,i,lb=30):
    a=atr14(B,i)
    if i<lb or a<=0: return 0
    diff=B[i].c-B[i-lb].c
    if diff>1.0*a: return 1
    if diff<-1.0*a: return -1
    return 0

def fade_sweep(syms, stretch_k, stop_mult, target_mult, maxbars):
    recs=[]
    for sym in syms:
        T,B,atrs,volpct,_,_=feats(sym)
        n=len(B)
        if n<200: continue
        cost=w1m.cost_for(sym)*(1.0/stop_mult)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            b=B[i]; body=b.c-b.o
            if abs(body)<stretch_k*a: continue
            up=body>0
            d=-1 if up else 1   # fade
            sd=stop_mult*a; td=target_mult*a
            r=simulate(B,i+1,d,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=cost)
            recs.append((sym,T[i+1].year,wins(r)))
    return recs

def pullback_cont_sweep(syms, trend_lb, pull_k, stop_mult, target_mult, maxbars, hi_vol_only=False):
    """In HTF up-trend, after a DOWN (pullback) bar of >= pull_k*ATR, enter long next bar.
    Symmetric for down-trend."""
    recs=[]
    for sym in syms:
        T,B,atrs,volpct,_,_=feats(sym)
        n=len(B)
        if n<200: continue
        cost=w1m.cost_for(sym)*(1.0/stop_mult)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if hi_vol_only and (volpct[i] is None or volpct[i]<0.66): continue
            tr=htf(B,i,trend_lb); b=B[i]; body=b.c-b.o
            sd=stop_mult*a; td=target_mult*a
            if tr==1 and body < -pull_k*a:   # pullback down in uptrend
                r=simulate(B,i+1,1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=cost)
                recs.append((sym,T[i+1].year,wins(r)))
            elif tr==-1 and body > pull_k*a:  # pullback up in downtrend
                r=simulate(B,i+1,-1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=cost)
                recs.append((sym,T[i+1].year,wins(r)))
    return recs

def sp(recs):
    tr=[r for _,y,r in recs if y<=2024]; f25=[r for _,y,r in recs if y==2025]; f26=[r for _,y,r in recs if y==2026]
    return stats(tr),stats(f25),stats(f26)

if __name__=="__main__":
    out={}
    print("############ FADE geometry sweep (reversion) ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### {cls} FADE #####")
        for k in [0.8,1.2]:
            for sm in [1.0,1.5,2.0]:
                for tm in [0.5,0.75,1.0]:
                    recs=fade_sweep(CLASSES[cls],k,sm,tm,maxbars=12)
                    tr,f25,f26=sp(recs)
                    if tr['n']<150: continue
                    flag="  <<<" if (tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
                    print(f"  k{k} stop{sm} tgt{tm} TR n={tr['n']:5d} R={tr['R']:+.4f} | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
                    out[f"{cls}_fade_k{k}_s{sm}_t{tm}"]={"train":tr,"f25":f25,"f26":f26}
    print("\n############ PULLBACK-CONTINUATION (with HTF trend) ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### {cls} PULLBACK-CONT #####")
        for lb in [20,40]:
            for pk in [0.5,0.8]:
                for sm in [1.0,1.5]:
                    for tm in [1.5,2.5]:
                        recs=pullback_cont_sweep(CLASSES[cls],lb,pk,sm,tm,maxbars=40)
                        tr,f25,f26=sp(recs)
                        if tr['n']<150: continue
                        flag="  <<<" if (tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
                        print(f"  lb{lb} pk{pk} stop{sm} tgt{tm} TR n={tr['n']:5d} R={tr['R']:+.4f} | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
                        out[f"{cls}_pull_lb{lb}_pk{pk}_s{sm}_t{tm}"]={"train":tr,"f25":f25,"f26":f26}
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_GEOMETRY_SWEEP.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE PROBE_GEOMETRY_SWEEP.json")
