"""
probe_conditional_slices.py
Slice fade/cont of stretched bar by SESSION x VOL-REGIME x DOW. Also test a
"failed-breakout fade" and "London-open continuation" hypothesis explicitly.
Pick condition on TRAIN, report 2025/2026 separately + per-symbol.
"""
import sys, json
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from dead_class_harness import feats, session, stats, split, per_year, per_sym, wins, CLASSES
from geometry_lib import simulate
import wave1_structure_setups_ict as w1m

SESS_NAME={0:"Asia",1:"London",2:"NY"}

def run_setup(syms, mode, stretch_k, stop_mult, target_R):
    """Returns list of (sym, year, sess, vp, dow, R)."""
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
            d=(1 if up else -1) if mode=='cont' else (-1 if up else 1)
            stop_dist=stop_mult*a; target_dist=target_R*stop_dist
            r=simulate(B,i+1,d,stop_dist=stop_dist,target_dist=target_dist,cost=cost)
            recs.append((sym,T[i+1].year,session(T[i].hour),volpct[i],T[i].weekday(),wins(r)))
    return recs

def split3(rows):
    tr=[r for *_,r in [(x[5],) and x for x in rows] if x[1]<=2024]
    return tr  # unused helper

def agg(rows, predicate):
    sel=[(s,y,r) for (s,y,se,vp,dw,r) in rows if predicate(se,vp,dw)]
    tr=[r for _,y,r in sel if y<=2024]
    f25=[r for _,y,r in sel if y==2025]
    f26=[r for _,y,r in sel if y==2026]
    return stats(tr),stats(f25),stats(f26),sel

def scan_slices(class_name, mode, stretch_k, stop_mult, target_R):
    rows=run_setup(CLASSES[class_name],mode,stretch_k,stop_mult,target_R)
    print(f"\n##### {class_name} {mode} k={stretch_k} stop={stop_mult} tgt={target_R}R #####")
    results=[]
    # by session
    for se in [0,1,2]:
        tr,f25,f26,sel=agg(rows,lambda s,v,d,se=se: s==se)
        print(f"  sess={SESS_NAME[se]:6s} TR n={tr['n']:5d} R={tr['R']:+.4f} | 25 n={f25['n']:4d} R={f25['R']:+.4f} | 26 n={f26['n']:4d} R={f26['R']:+.4f}")
        results.append((f"{class_name}_{mode}_sess{SESS_NAME[se]}",tr,f25,f26,sel))
    # by vol regime band (low<0.33, mid, high>=0.66)
    for lo,hi,nm in [(0.0,0.33,"loVol"),(0.33,0.66,"midVol"),(0.66,1.01,"hiVol")]:
        tr,f25,f26,sel=agg(rows,lambda s,v,d,lo=lo,hi=hi: v is not None and lo<=v<hi)
        print(f"  vol={nm:7s} TR n={tr['n']:5d} R={tr['R']:+.4f} | 25 n={f25['n']:4d} R={f25['R']:+.4f} | 26 n={f26['n']:4d} R={f26['R']:+.4f}")
        results.append((f"{class_name}_{mode}_{nm}",tr,f25,f26,sel))
    # by day of week
    for dw in range(5):
        tr,f25,f26,sel=agg(rows,lambda s,v,d,dw=dw: d==dw)
        nm=["Mon","Tue","Wed","Thu","Fri"][dw]
        print(f"  dow={nm:6s} TR n={tr['n']:5d} R={tr['R']:+.4f} | 25 n={f25['n']:4d} R={f25['R']:+.4f} | 26 n={f26['n']:4d} R={f26['R']:+.4f}")
        results.append((f"{class_name}_{mode}_{nm}",tr,f25,f26,sel))
    return results, rows

if __name__=="__main__":
    allres={}
    for cls in ["fx","jpy_fx","index","crypto"]:
        for mode in ["fade","cont"]:
            res,rows=scan_slices(cls,mode,stretch_k=1.0,stop_mult=1.0,target_R=1.0)
            for nm,tr,f25,f26,sel in res:
                allres[nm]={"train":tr,"f25":f25,"f26":f26}
    with open("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PROBE_CONDITIONAL_SLICES.json","w") as f:
        json.dump(allres,f,indent=1)
    print("\nWROTE PROBE_CONDITIONAL_SLICES.json")
