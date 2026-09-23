"""
probe_final_selective.py
Most-selective reversion triggers on the least-dead class (index) + retest on fx/jpy/crypto:
 (A) EXHAUSTION FADE: after >=2 consecutive same-direction bars whose cumulative move
     >= K*ATR (stretched run), fade next bar. Scalp target.
 (B) LOW-VOL RANGE FADE: fade prior-day extreme rejection ONLY when vol regime is low
     (range regime) -> revert to mid.
 (C) RSI-style: 3-bar momentum extreme fade.
Pick on TRAIN, report 2025/2026 + per-symbol for any holder.
"""
import sys, json
from collections import defaultdict
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import feats, session, stats, wins, CLASSES
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1m

def sp(recs):
    tr=[r for _,y,r in recs if y<=2024]; f25=[r for _,y,r in recs if y==2025]; f26=[r for _,y,r in recs if y==2026]
    return stats(tr),stats(f25),stats(f26)
def per_sym(recs):
    by=defaultdict(list)
    for s,y,r in recs: by[s].append(r)
    return {s:stats(by[s]) for s in sorted(by)}

def exhaustion_fade(syms, run_bars=2, cum_k=2.0, stop_mult=1.5, target_mult=1.0, maxbars=12, lowvol_only=False):
    recs=[]
    for sym in syms:
        T,B,atrs,vp,_,_=feats(sym); n=len(B)
        if n<200: continue
        cost=w1m.cost_for(sym)*(1.0/stop_mult)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if lowvol_only and (vp[i] is None or vp[i]>=0.5): continue
            # last run_bars all same direction?
            dirs=[1 if B[j].c>B[j].o else (-1 if B[j].c<B[j].o else 0) for j in range(i-run_bars+1,i+1)]
            if 0 in dirs or len(set(dirs))!=1: continue
            sgn=dirs[0]
            cum=B[i].c-B[i-run_bars].c   # cumulative move over run
            if abs(cum)<cum_k*a: continue
            d=-sgn  # fade
            r=simulate(B,i+1,d,stop_dist=stop_mult*a,target_dist=target_mult*stop_mult*a,maxbars=maxbars,cost=cost)
            recs.append((sym,T[i+1].year,wins(r)))
    return recs

def lowvol_pd_fade(syms, sweep_min=0.05, target_mult=0.75, stop_buf=0.4, stop_floor=0.6, maxbars=12):
    recs=[]
    for sym in syms:
        T,B,atrs,vp,pdlv,_=feats(sym); n=len(B)
        if n<200: continue
        pdh,pdl=pdlv
        cost=w1m.cost_for(sym)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if vp[i] is None or vp[i]>=0.5: continue   # low vol only
            b=B[i]; nb=B[i+1]; lo=pdl[i]; hi=pdh[i]; entry=nb.o
            if lo is not None and (lo-b.l)>=sweep_min*a and b.c>lo:
                sd=max((entry-b.l)+stop_buf*a, stop_floor*a); td=target_mult*sd
                c=cost*(1.0/(sd/a))
                r=simulate(B,i+1,1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=c)
                recs.append((sym,T[i+1].year,wins(r)))
            if hi is not None and (b.h-hi)>=sweep_min*a and b.c<hi:
                sd=max((b.h-entry)+stop_buf*a, stop_floor*a); td=target_mult*sd
                c=cost*(1.0/(sd/a))
                r=simulate(B,i+1,-1,stop_dist=sd,target_dist=td,maxbars=maxbars,cost=c)
                recs.append((sym,T[i+1].year,wins(r)))
    return recs

if __name__=="__main__":
    out={}
    print("############ (A) EXHAUSTION FADE (>=2-3 consec bars, cumulative stretch) ############")
    for cls in ["index","fx","jpy_fx","crypto"]:
        print(f"\n##### {cls} #####")
        for rb in [2,3]:
            for ck in [1.5,2.0,2.5]:
                for lv in [False,True]:
                    recs=exhaustion_fade(CLASSES[cls],run_bars=rb,cum_k=ck,stop_mult=1.5,target_mult=1.0,maxbars=12,lowvol_only=lv)
                    tr,f25,f26=sp(recs)
                    if tr['n']<80: continue
                    flag="  <<<" if (tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
                    print(f"  rb{rb} ck{ck} lowvol={lv} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
                    out[f"{cls}_exh_rb{rb}_ck{ck}_lv{int(lv)}"]={"train":tr,"f25":f25,"f26":f26}
    print("\n############ (B) LOW-VOL PRIOR-DAY EXTREME FADE (range-day revert) ############")
    for cls in ["index","fx","jpy_fx","crypto"]:
        recs=lowvol_pd_fade(CLASSES[cls])
        tr,f25,f26=sp(recs)
        flag="  <<<" if (tr['n']>=80 and tr['R']>0.01 and f25['R']>0 and f26['R']>0) else ""
        print(f"  {cls:7s} TR n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | 25 R={f25['R']:+.4f}(n{f25['n']}) | 26 R={f26['R']:+.4f}(n{f26['n']}){flag}")
        out[f"{cls}_lowvol_pdfade"]={"train":tr,"f25":f25,"f26":f26}
        if flag or (cls=="index"):
            ps=per_sym(recs)
            for s,st in ps.items():
                if st['n']>=20: print(f"        {s:12s} n={st['n']:4d} R={st['R']:+.4f} w={st['win']:.0f}%")
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_FINAL_SELECTIVE.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE PROBE_FINAL_SELECTIVE.json")
