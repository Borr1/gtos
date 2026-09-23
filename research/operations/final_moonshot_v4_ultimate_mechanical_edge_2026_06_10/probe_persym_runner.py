"""
probe_persym_runner.py
Two final angles:
 (A) PER-SYMBOL heterogeneity: maybe one symbol carries a class. Decompose continuation
     (momentum) and fade per symbol with a TRAILING RUNNER (let winners run = real trend edge).
 (B) Trailing runner on stretched-bar continuation, per symbol, train/forward.
Only symbols with real train history (train n>=400 bars) are eligible for a train-verdict.
"""
import sys, json
from collections import defaultdict
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import feats, session, stats, wins, CLASSES
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1m

def htf(B,i,lb=30):
    a=atr14(B,i)
    if i<lb or a<=0: return 0
    diff=B[i].c-B[i-lb].c
    if diff>1.0*a: return 1
    if diff<-1.0*a: return -1
    return 0

def run_one(sym, mode, stretch_k, stop_mult, trail_arm, trail_gap, maxbars, trend_align=False):
    T,B,atrs,volpct,_,_=feats(sym)
    n=len(B)
    out=[]
    if n<200: return out
    cost=w1m.cost_for(sym)*(1.0/stop_mult)
    for i in range(120,n-2):
        a=atrs[i]
        if a<=0: continue
        b=B[i]; body=b.c-b.o
        if abs(body)<stretch_k*a: continue
        up=body>0
        d=(1 if up else -1) if mode=='cont' else (-1 if up else 1)
        if trend_align:
            tr=htf(B,i,30)
            if d!=tr: continue
        sd=stop_mult*a
        r=simulate(B,i+1,d,stop_dist=sd,trail_arm=trail_arm*a,trail_gap=trail_gap*a,maxbars=maxbars,cost=cost)
        out.append((T[i+1].year,wins(r)))
    return out

def sp(yr_r):
    tr=[r for y,r in yr_r if y<=2024]; f25=[r for y,r in yr_r if y==2025]; f26=[r for y,r in yr_r if y==2026]
    return stats(tr),stats(f25),stats(f26)

if __name__=="__main__":
    out={}
    print("############ PER-SYMBOL momentum-continuation w/ TRAILING RUNNER ############")
    print("(trend_align: only take stretch bars in direction of 30-bar HTF trend)")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### CLASS {cls} #####")
        for sym in CLASSES[cls]:
            recs=run_one(sym,'cont',stretch_k=1.0,stop_mult=1.0,trail_arm=1.0,trail_gap=1.0,maxbars=40,trend_align=True)
            tr,f25,f26=sp(recs)
            if tr['n']<60:
                tag="(thin train)"
            else:
                tag=""
            flag=""
            if tr['n']>=60 and tr['R']>0.02 and f25['n']>=10 and f25['R']>0 and f26['n']>=10 and f26['R']>0:
                flag="  <<< HOLDS"
            print(f"  {sym:12s} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}) {tag}{flag}")
            out[f"{cls}_{sym}_contrun"]={"train":tr,"f25":f25,"f26":f26}
    print("\n############ PER-SYMBOL FADE w/ trailing runner (mean-revert then ride) ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n##### CLASS {cls} #####")
        for sym in CLASSES[cls]:
            recs=run_one(sym,'fade',stretch_k=1.0,stop_mult=1.5,trail_arm=0.5,trail_gap=0.75,maxbars=18,trend_align=False)
            tr,f25,f26=sp(recs)
            flag=""
            if tr['n']>=60 and tr['R']>0.02 and f25['n']>=10 and f25['R']>0 and f26['n']>=10 and f26['R']>0:
                flag="  <<< HOLDS"
            print(f"  {sym:12s} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
            out[f"{cls}_{sym}_faderun"]={"train":tr,"f25":f25,"f26":f26}
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_PERSYM_RUNNER.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE PROBE_PERSYM_RUNNER.json")
