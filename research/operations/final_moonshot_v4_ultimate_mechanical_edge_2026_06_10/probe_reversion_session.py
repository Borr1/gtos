"""
probe_reversion_session.py
Broad scan: for each class, test FADE (reversion) vs CONTINUATION of a stretched H4 bar,
sliced by session and vol regime. Pick on TRAIN, report forward.

Setup primitive:
  At bar i (features only <=i): measure body move = (c-o). A "stretched up" bar = c-o >= k*ATR.
  CONTINUATION up: enter long next bar open. REVERSION: enter short (fade) next bar open.
  Stop = stop_mult*ATR. Target = target_R * stop. Cost scaled by (1 / stop_mult) since
  base cost map is per fixed ATR? -> base cost is in R for ~ default stop; we scale cost
  by (REF_STOP/stop_mult) where REF_STOP ~ derived. Simpler & honest: cost in price terms.

We treat w1.cost_for(sym) as R-cost at a 1.0*ATR stop (its design basis is ATR-scaled
geometry in this route). To be conservative we scale: cost_R = base * (1.0/stop_mult).
"""
import sys, json
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import (feats, session, stats, split, per_year, per_sym,
                                show, wins, CLASSES, AC)
from geometry_lib import simulate

def scan(class_name, mode, stretch_k, stop_mult, target_R, sess=None, vollo=None, volhi=None):
    """mode: 'cont' or 'fade'. sess: None or set of session ids. vollo/volhi: vol pct band."""
    recs=[]
    for sym in CLASSES[class_name]:
        T,B,atrs,volpct,_,_=feats(sym)
        n=len(B)
        if n<200: continue
        base=w1.cost_for(sym) if False else None
        import wave1_structure_setups_ict as w1m
        cost=w1m.cost_for(sym)*(1.0/stop_mult)
        for i in range(120,n-2):
            a=atrs[i]
            if a<=0: continue
            if sess is not None and session(T[i].hour) not in sess: continue
            if vollo is not None:
                vp=volpct[i]
                if vp is None or vp<vollo or vp>=volhi: continue
            b=B[i]; body=b.c-b.o
            if abs(body) < stretch_k*a: continue
            up = body>0
            entry_dir = (1 if up else -1) if mode=='cont' else (-1 if up else 1)
            stop_dist=stop_mult*a
            target_dist=target_R*stop_dist
            r=simulate(B,i+1,entry_dir,stop_dist=stop_dist,target_dist=target_dist,cost=cost)
            recs.append((sym,T[i+1].year,wins(r)))
    return recs

if __name__=="__main__":
    import wave1_structure_setups_ict as w1m
    out={}
    print("############ REVERSION vs CONTINUATION of stretched H4 bar ############")
    for cls in ["fx","jpy_fx","index","crypto"]:
        print(f"\n################## CLASS={cls} ##################")
        for mode in ["fade","cont"]:
            for k in [1.0, 1.5]:
                recs=scan(cls,mode,k,stop_mult=1.0,target_R=1.0)
                r=show(f"{cls} {mode} stretch>={k}ATR stop1.0 tgt1R allsess",recs)
                out[r["name"]]=r
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_REVERSION_SESSION.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE PROBE_REVERSION_SESSION.json")
