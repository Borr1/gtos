"""csb_final_metals.py — FINAL: the breadth that survives. OB retest on METALS, ac60+vol gate,
exit_state_d. Compare/combine with FVG baseline on metals. Full per-year + forward-holdout +
per-symbol. This is the deployable add.
"""
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import csb_commodity_setups as csb

METALS=csb.METALS; DEEP=csb.DEEP

def gen(name, syms):
    rows=[]
    for s in syms:
        T,B=w1.load(s)
        if len(B)<200: continue
        A=csb._atrs(B); cost=w1.cost_for(s)
        sigs=[(t,d,sd,i,B2,c2) for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s)] if name=="FVG" else csb.SETUPS[name](s)
        for (t,d,sd,i,B2,c2) in sigs:
            ac=cs.autocorr(B,i,60)
            if ac is None or ac<0.10: continue
            vr=cs.vol_ratio(A,i); ex=cs.exit_state_d(B,i,d,sd,vr,c2)
            rows.append(dict(sym=s,year=t.year,date=str(t)[:10],dir=d,R=round(ex['R'],4),
                             setup=name,deep=(s in DEEP),reason=ex['reason']))
    return rows

def stat(rs):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(r['R'] for r in rs)/n; w=sum(1 for r in rs if r['R']>0)/n*100
    return n,round(m,4),round(w,1)

def py(rows):
    by=collections.defaultdict(list)
    for r in rows: by[r['year']].append(r)
    return {y:stat(by[y]) for y in sorted(by)}

def block(name,rows):
    fw=[r for r in rows if r['year']>=2025]; f25=[r for r in rows if r['year']==2025]
    f26=[r for r in rows if r['year']==2026]; tr=[r for r in rows if r['year']<=2024]
    P=py(rows)
    print(f"\n##### {name} #####")
    print(f"  TRAIN<=24: n={stat(tr)[0]:3d} EV={stat(tr)[1]:+.3f} win={stat(tr)[2]:.0f}%")
    print(f"  FWD 25-26: n={stat(fw)[0]:3d} EV={stat(fw)[1]:+.3f} win={stat(fw)[2]:.0f}%  (~{stat(fw)[0]/1.5:.0f}/yr)")
    print(f"    2025: n={stat(f25)[0]:3d} EV={stat(f25)[1]:+.3f} | 2026: n={stat(f26)[0]:3d} EV={stat(f26)[1]:+.3f}")
    print("  per-year:", " ".join(f"{y}:{P[y][1]:+.2f}(n{P[y][0]})" for y in sorted(P)))
    # per-symbol forward
    bs=collections.defaultdict(list)
    for r in fw: bs[r['sym']].append(r)
    print("  fwd per-sym:", " ".join(f"{s}:{stat(bs[s])[1]:+.2f}(n{stat(bs[s])[0]})" for s in sorted(bs)))
    return dict(train=stat(tr),fwd=stat(fw),fwd2025=stat(f25),fwd2026=stat(f26),
                per_year={str(y):P[y] for y in P})

if __name__=="__main__":
    print("="*70); print("FINAL METALS BREADTH: FVG vs OB vs FVG+OB union (metals only)"); print("="*70)
    fvg=gen("FVG",METALS); ob=gen("OB",METALS)
    out={}
    out['FVG_metals']=block("FVG metals (BASELINE)",fvg)
    out['OB_metals']=block("OB metals (NEW)",ob)
    # union dedup sym+date+dir (FVG priority)
    seen=set(); union=[]
    for r in fvg:
        k=(r['sym'],r['date'],r['dir']); seen.add(k); union.append(r)
    added=0
    for r in ob:
        k=(r['sym'],r['date'],r['dir'])
        if k in seen: continue
        seen.add(k); union.append(r); added+=1
    out['FVG_plus_OB_metals']=block(f"FVG + OB metals UNION (+{added} new entries)",union)
    out['ob_added_unique']=added
    (HERE/'CSB_FINAL_METALS_RESULT.json').write_text(json.dumps(out,indent=1))
    print("\nwrote CSB_FINAL_METALS_RESULT.json")
