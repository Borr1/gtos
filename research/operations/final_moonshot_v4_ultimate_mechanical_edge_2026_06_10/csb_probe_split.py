"""csb_probe_split.py — metals-only vs energy-only vs deep-only per setup; and FVG-union test.
Where does each new trigger ACTUALLY pay? Forward-holdout per slice.
"""
import sys, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import csb_commodity_setups as csb

METALS=csb.METALS; ENERGY=csb.ENERGY; DEEP=csb.DEEP

def run(name, syms):
    rows=[]
    for s in syms:
        T,B=w1.load(s)
        if len(B)<200: continue
        A=csb._atrs(B); cost=w1.cost_for(s)
        sigs = [(t,d,sd,i,B2,c2) for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s)] if name=="FVG" else csb.SETUPS[name](s)
        for (t,d,sd,i,B2,c2) in sigs:
            ac=cs.autocorr(B,i,60)
            if ac is None or ac<0.10: continue
            vr=cs.vol_ratio(A,i); ex=cs.exit_state_d(B,i,d,sd,vr,c2)
            rows.append((s,t.year,ex['R']))
    return rows

def stat(rs):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(r for _,_,r in rs)/n; w=sum(1 for _,_,r in rs if r>0)/n*100
    return n,round(m,3),round(w,0)

def fwd(rows): return [r for r in rows if r[1]>=2025]

for name in ["FVG","OB","BRK","DISP","SWP"]:
    print(f"\n===== {name} forward 2025-26 by slice =====")
    for lab,syms in [("metals",METALS),("energy",ENERGY),("XAUUSD",["XAUUSD"]),("XAGUSD",["XAGUSD"]),("USOIL",["USOIL_cash"])]:
        f=fwd(run(name,syms)); n,m,w=stat(f)
        print(f"  {lab:8s} n={n:3d} EV={m:+.3f} win={w:.0f}%")
