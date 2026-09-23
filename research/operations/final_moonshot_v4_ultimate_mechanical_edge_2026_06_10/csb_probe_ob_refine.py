"""csb_probe_ob_refine.py — refine the most promising new trigger (OB) and re-test DISP/SWP
with stronger quality filters. Same ac60>=0.10 gate + vol gate + exit_state_d.
Probe variants on the deep symbols + full core. Report per-year + forward-holdout.
"""
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import csb_commodity_setups as csb

CORE = csb.CORE
DEEP = csb.DEEP

def run(sigfn, syms):
    rows = []
    for s in syms:
        T, B = w1.load(s)
        if len(B) < 200: continue
        A = csb._atrs(B); cost = w1.cost_for(s)
        for (t, d, sd, i, B2, c2) in sigfn(s):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.10: continue
            vr = cs.vol_ratio(A, i)
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sym=s, year=t.year, dir=d, R=ex['R'], deep=(s in DEEP)))
    return rows

def stat(rs):
    if not rs: return (0, 0.0, 0.0)
    n=len(rs); m=sum(r['R'] for r in rs)/n; w=sum(1 for r in rs if r['R']>0)/n*100
    return n, round(m,3), round(w,0)

def show(name, rows):
    tr=[r for r in rows if r['year']<=2024]; fw=[r for r in rows if r['year']>=2025]
    f25=[r for r in rows if r['year']==2025]; f26=[r for r in rows if r['year']==2026]
    fd=[r for r in fw if r['deep']]
    print(f"\n--- {name} ---")
    print(f"  TR<=24 n={stat(tr)[0]:3d} EV={stat(tr)[1]:+.3f} | FWD n={stat(fw)[0]:3d} EV={stat(fw)[1]:+.3f} w={stat(fw)[2]:.0f}%")
    print(f"  2025 n={stat(f25)[0]:3d} EV={stat(f25)[1]:+.3f} | 2026 n={stat(f26)[0]:3d} EV={stat(f26)[1]:+.3f} | fwd-deep n={stat(fd)[0]} EV={stat(fd)[1]:+.3f}")
    by=collections.defaultdict(list)
    for r in rows: by[r['year']].append(r)
    print("  per-yr:", " ".join(f"{y}:{stat(by[y])[1]:+.2f}(n{stat(by[y])[0]})" for y in sorted(by)))

# OB refinements: require strong impulse (next bar range/displacement), tighter retest depth
def ob_v(impulse_k=0.0, min_retest_close=0.0, ob_lookback=9, require_body=False):
    def f(sym):
        T,B=w1.load(sym)
        if len(B)<200: return []
        A=csb._atrs(B); cost=w1.cost_for(sym); out=[]
        for i in range(60,len(B)-1):
            a=A[i]
            if a<=0: continue
            if not csb.vol_gate_ok(A,i): continue
            tr=w1.htf_trend(B,i,30); b=B[i]
            if tr==1:
                for k in range(i-2,max(i-ob_lookback,60),-1):
                    if not (B[k].c<B[k].o): continue
                    if require_body and (B[k].o-B[k].c) < 0.3*(B[k].h-B[k].l): continue
                    # impulse after OB: bar k+1 must be a strong up displacement
                    imp=B[k+1].c-B[k+1].o
                    if not (B[k+1].c>B[k].h and imp>=impulse_k*a): continue
                    ob_top,ob_bot=B[k].h,B[k].l
                    if b.l<=ob_top and b.c>ob_bot and b.c>b.o and (b.c-ob_bot)>=min_retest_close*a:
                        sd=max((b.c-min(b.l,ob_bot))+0.10*a,0.25*a)
                        out.append((T[i],+1,sd,i,B,cost)); break
            elif tr==-1:
                for k in range(i-2,max(i-ob_lookback,60),-1):
                    if not (B[k].c>B[k].o): continue
                    if require_body and (B[k].c-B[k].o) < 0.3*(B[k].h-B[k].l): continue
                    imp=B[k+1].o-B[k+1].c
                    if not (B[k+1].c<B[k].l and imp>=impulse_k*a): continue
                    ob_top,ob_bot=B[k].h,B[k].l
                    if b.h>=ob_bot and b.c<ob_top and b.c<b.o and (ob_top-b.c)>=min_retest_close*a:
                        sd=max((max(b.h,ob_top)-b.c)+0.10*a,0.25*a)
                        out.append((T[i],-1,sd,i,B,cost)); break
        return out
    return f

if __name__=="__main__":
    print("="*70); print("OB REFINEMENT PROBE (core = metals+energy)"); print("="*70)
    show("OB base (vol+ac gate)", run(csb.sig_ob, CORE))
    show("OB impulse>=0.5atr", run(ob_v(impulse_k=0.5), CORE))
    show("OB impulse>=0.8atr", run(ob_v(impulse_k=0.8), CORE))
    show("OB impulse>=1.0atr", run(ob_v(impulse_k=1.0), CORE))
    show("OB imp>=0.8 + body>=30%", run(ob_v(impulse_k=0.8, require_body=True), CORE))
    show("OB imp>=0.8 + retest_depth>=0.2atr", run(ob_v(impulse_k=0.8, min_retest_close=0.2), CORE))
    show("OB imp>=0.8 lookback=6", run(ob_v(impulse_k=0.8, ob_lookback=6), CORE))
