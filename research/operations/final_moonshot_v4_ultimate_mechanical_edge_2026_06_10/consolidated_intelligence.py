"""FULL-PICTURE INTELLIGENCE + CONDITIONAL-POCKET PROBE.
Dissect EVERY FVG trade across EVERY asset class: per-year, per-symbol, inverted null,
AND conditional EV by market-state buckets with a TRAIN(<=2024)->FORWARD(2025+) holdout.
Question: do the 'dead' classes (fx/index/jpy/crypto) hide +EV conditions we discarded by averaging?
Reuses the trusted FVG engine; features computed from closed price history only (no lookahead).
"""
import sys, json, statistics, collections, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

def atrs_of(B): return [atr14(B,i) for i in range(len(B))]

# collect every trade with features
rows=[]  # dict per trade
for sym in w1.SYMBOLS:
    ac=AC.get(sym)
    if not ac: continue
    try: sig=g.fvg_signals(sym)
    except Exception: continue
    if not sig: continue
    B=sig[0][5]; A=atrs_of(B)
    for (t,d,sd,td,i,Bb,cost) in sig:
        a=A[i] if A[i]>0 else 1e-9
        sma100=sum(A[max(0,i-99):i+1])/min(100,i+1)
        gate=a/sma100 if sma100>0 else 1.0
        # trend strength: how many of last 30 closes below current (up) / above (down)
        win=Bb[max(0,i-30):i+1]
        slope=(Bb[i].c-Bb[max(0,i-30)].c)/a
        r=simulate(Bb,i,d,stop_dist=sd,target_dist=td,cost=cost)
        ri=simulate(Bb,i,-d,stop_dist=sd,target_dist=td,cost=cost)
        rows.append(dict(ac=ac,sym=sym,year=t.year,dt=t,d=d,r=r,ri=ri,
                         gate=gate,hour=t.hour,slope=slope,stop_atr=sd/a))
print(f"total trades: {len(rows)}")

def ev(rs): return statistics.fmean(rs) if rs else float('nan')

# ---- conditional pocket search within EACH class: find a feature condition that is
# +EV in TRAIN(<=2024) and CHECK it FORWARD(2025+). Features bucketed into terciles. ----
FEATS=["gate","slope","hour","stop_atr"]
print("\nCONDITIONAL POCKETS (train<=2024 pick best tercile per feature, then forward 2025+):")
print(f"{'class':>8} {'feat':>9} {'condition':>22} {'train_EV(n)':>16} {'FWD_EV(n)':>14} {'holds?':>7}")
book_pockets=[]
for ac in sorted(set(r['ac'] for r in rows)):
    crows=[r for r in rows if r['ac']==ac]
    tr=[r for r in crows if r['year']<=2024]; fw=[r for r in crows if r['year']>=2025]
    base_tr=ev([r['r'] for r in tr]); base_fw=ev([r['r'] for r in fw])
    print(f"{ac:>8} {'(all)':>9} {'baseline':>22} {base_tr:>+9.3f}({len(tr):>4}) {base_fw:>+8.3f}({len(fw):>4})")
    for f in FEATS:
        vals=sorted(r[f] for r in tr)
        if len(vals)<30: continue
        q1=vals[len(vals)//3]; q2=vals[2*len(vals)//3]
        buckets={"lo":lambda x:x<=q1,"mid":lambda x:q1<x<=q2,"hi":lambda x:x>q2}
        best=None
        for bn,fn in buckets.items():
            sub=[r['r'] for r in tr if fn(r[f])]
            if len(sub)>=25:
                e=ev(sub)
                if best is None or e>best[1]: best=(bn,e,len(sub))
        if not best: continue
        bn,te,tn=best; fn=buckets[bn]
        fsub=[r['r'] for r in fw if fn(r[f])]
        fe=ev(fsub) if len(fsub)>=10 else float('nan')
        holds = (not math.isnan(fe)) and fe>0 and te>0
        cond=f"{f}_{bn}({q1:.2f},{q2:.2f})"
        if te>base_tr+0.05:  # only show conditions that improve on baseline in train
            print(f"{ac:>8} {f:>9} {cond:>22} {te:>+9.3f}({tn:>4}) {fe:>+8.3f}({len(fsub):>4}) {str(holds):>7}")
            if holds and fe>0.05: book_pockets.append((ac,cond,round(te,3),round(fe,3),len(fsub)))

print("\nCONDITIONS THAT HOLD FORWARD (+EV train AND +EV forward, fwd>0.05R):")
for p in sorted(book_pockets,key=lambda x:-x[3]):
    print(f"  {p[0]:>8} {p[1]:>24} train {p[2]:+.3f} fwd {p[3]:+.3f} (fwd n={p[4]})")
