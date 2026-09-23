"""COMPOUNDING SLEEVE v1 — integrate the two forward-validated improvements onto the
commodity continuation setup, and consume EVERY trade as intelligence.
  ENTRY  : FVG-retest continuation + momentum-persistence gate (ac60>=0.10).
  EXIT   : vol-tiered scale-out (STATE_D): 50% leg + BE runner + deep fixed target, no trail.
Builds a PER-TRADE intelligence ledger (state + why-selected + outcome + diagnosis) for every
candidate incl. rejected ones, then mines the ledger for the NEXT incremental improvement.
Never reports a single bulk average as a verdict — per-year and per-regime always.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1

METALS=g.METALS                                   # ex-copper carrier
ENERGY=['USOIL_cash','UKOIL_cash','NATGAS_cash','HEATOIL_c']
AGRI=['CORN_c','COTTON_c']
AC_THR=0.10
def wins(r): return max(-1.3,min(5.0,r))

def autocorr(B,i,n=60):
    if i<n+1: return None
    rets=[B[k].c-B[k-1].c for k in range(i-n+1,i+1)]
    m=statistics.mean(rets)
    num=sum((rets[k]-m)*(rets[k-1]-m) for k in range(1,len(rets)))
    den=sum((x-m)**2 for x in rets)
    return num/den if den>0 else 0.0

def vol_ratio(atrs,i):
    if i<100: return 1.0
    s=sum(atrs[i-99:i+1])/100
    return atrs[i]/s if s>0 else 1.0

def exit_state_d(B,i,d,sd,vr,cost,maxbars=80):
    entry=B[i].c
    if vr<1.35: scaleR,runR=1.5,4.0
    elif vr<1.6: scaleR,runR=1.5,3.0
    else: scaleR,runR=1.0,2.5
    scaled=False; mfe=0.0; mae=0.0; bars1R=None; leg2=None; reason=None; end=min(i+maxbars,len(B)-1)
    for j in range(i+1,end+1):
        hi=B[j].h; lo=B[j].l
        favp=hi if d>0 else lo; advp=lo if d>0 else hi
        fav=d*(favp-entry)/sd; adv=d*(advp-entry)/sd
        mfe=max(mfe,fav); mae=min(mae,adv)
        if bars1R is None and fav>=1.0: bars1R=j-i
        if not scaled:
            if adv<=-1.0: return dict(R=-1.0-cost,mfe=mfe,mae=mae,bars1R=bars1R,reason='full_stop',vr=vr)
            if fav>=scaleR: scaled=True   # book 0.5 @ scaleR, runner stop -> BE
        else:
            if adv<=0.0: leg2=0.0; reason='scratch_be'; break
            if fav>=runR: leg2=runR; reason='win_runner'; break
    if reason is None:
        if scaled:
            leg2=d*(B[end].c-entry)/sd; reason='win_partial' if leg2>0 else 'partial_flat'
        else:
            R=d*(B[end].c-entry)/sd; return dict(R=wins(R-cost),mfe=mfe,mae=mae,bars1R=bars1R,reason='market_close',vr=vr)
    R=0.5*scaleR+0.5*leg2
    return dict(R=wins(R-cost),mfe=mfe,mae=mae,bars1R=bars1R,reason=reason,vr=vr)

def build():
    ledger=[]
    for grp,syms in (('metals',METALS),('energy',ENERGY),('agri',AGRI)):
        for s in syms:
            try: T,B=w1.load(s)
            except Exception: continue
            if len(B)<200: continue
            atrs=[atr14(B,k) for k in range(len(B))]; cost=w1.cost_for(s)
            for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s):
                ac=autocorr(B,i,60); vr=vol_ratio(atrs,i)
                sel=ac is not None and ac>=AC_THR
                ex=exit_state_d(B,i,d,sd,vr,c2)
                base2R=wins(simulate(B,i,d,stop_dist=sd,target_dist=2*sd,cost=c2))
                # per-trade diagnosis (the intelligence)
                if not sel:
                    diag='rejected_low_persistence'+('|missed_winner' if base2R>0 else '|correctly_avoided')
                elif ex['reason']=='full_stop':
                    diag='loss_full'+('|early_dead' if (ex['bars1R'] is None) else '')+('|stop_vs_mfe' if ex['mfe']>0.9 else '')
                elif ex['reason']=='scratch_be': diag='scratch_be'
                elif ex['reason']=='win_runner': diag='win_runner'
                else: diag='win_partial' if ex['R']>0 else 'partial_flat'
                ledger.append(dict(sym=s,grp=grp,year=t.year,date=str(t)[:10],dir=d,ac60=round(ac,4) if ac is not None else None,
                                   vr=round(vr,3),sel=sel,R=round(ex['R'],4),base2R=round(base2R,4),
                                   mfe=round(ex['mfe'],3),bars1R=ex['bars1R'],reason=ex['reason'],diag=diag))
    return ledger

def pstat(rows):
    if not rows: return (0,0.0,0.0)
    n=len(rows); m=sum(x['R'] for x in rows)/n; w=sum(1 for x in rows if x['R']>0)/n*100
    return n,m,w

def main():
    L=build()
    (HERE/'COMPOUNDING_TRADE_LEDGER.jsonl').write_text('\n'.join(json.dumps(r) for r in L))
    metals=[r for r in L if r['grp']=='metals']
    # BASELINE = original gold sleeve (all metals, fixed 2R, NO gate)
    base=[(r,r['base2R']) for r in metals]
    bn=len(base); bm=sum(x for _,x in base)/bn
    # IMPROVED = selected metals (ac60 gate) + STATE_D exit
    imp=[r for r in metals if r['sel']]
    print("=== COMPOUNDING LIFT (metals core) — per-year, never a bulk verdict ===")
    print(f"{'year':>5} {'BASE n':>7} {'BASE R/t':>9} | {'IMP n':>6} {'IMP R/t':>9} {'IMP win%':>9}")
    yrs=sorted(set(r['year'] for r in metals))
    for y in yrs:
        b=[x for x in base if x[0]['year']==y]; im=[r for r in imp if r['year']==y]
        bmy=sum(v for _,v in b)/len(b) if b else 0
        n,m,wn=pstat(im)
        print(f"{y:>5} {len(b):>7} {bmy:>+9.3f} | {n:>6} {m:>+9.3f} {wn:>8.0f}%")
    n,m,wn=pstat(imp)
    print(f"\nORIGINAL gold sleeve (metals, fixed-2R, no gate): n={bn} {bm:+.4f}R/trade")
    print(f"IMPROVED (ac60>=0.10 gate + STATE_D exit)        : n={n} {m:+.4f}R/trade win {wn:.0f}%")
    print(f"  -> per-trade EV lift: {bm:+.3f} -> {m:+.3f}  ({(m-bm):+.3f}R, {((m/bm-1)*100 if bm else 0):+.0f}%)")
    # forward only
    impf=[r for r in imp if r['year']>=2025]; nf,mf,wf=pstat(impf)
    basef=[x for x in base if x[0]['year']>=2025]; bmf=sum(v for _,v in basef)/len(basef) if basef else 0
    print(f"  FORWARD 2025-26: original {bmf:+.3f} -> improved {mf:+.3f}R/trade (n={nf}, win {wf:.0f}%)")
    print("\n=== per REGIME (vol tier) — improved metals, forward 2025-26 ===")
    for lab,lo,hi in (('LOW <1.35',0,1.35),('MID 1.35-1.6',1.35,1.6),('HI >=1.6',1.6,99)):
        rr=[r for r in impf if lo<=r['vr']<hi]; n,m,wn=pstat(rr)
        if n: print(f"  {lab:>14}: n={n:>3} {m:+.3f}R win {wn:.0f}%")
    # ---- PER-TRADE INTELLIGENCE -> next improvement ----
    print("\n=== PER-TRADE INTELLIGENCE (the compounding signal) ===")
    sel_losers=[r for r in imp if r['R']<0]
    early=[r for r in sel_losers if r['bars1R'] is None]
    print(f"  selected losers: {len(sel_losers)} | of those, {len(early)} ({100*len(early)/max(1,len(sel_losers)):.0f}%) NEVER reached +1R (early-dead)")
    if early:
        e_if_timestop=len(early)  # these would be cut earlier -> smaller losses
        print(f"    -> IMPROVEMENT LEAD: early time-stop on no-progress trades cuts {len(early)} losers' size")
    rej=[r for r in metals if not r['sel']]
    missed=[r for r in rej if r['base2R']>0]
    print(f"  rejected (ac60<0.10): {len(rej)} | missed winners among them: {len(missed)} (mean base2R {sum(x['base2R'] for x in missed)/max(1,len(missed)):+.3f})")
    print(f"    -> FREQUENCY LEAD: {sum(x['base2R'] for x in missed):+.1f}R of winners sit just below the gate; test ac60>=0.05 / pool sweep+breakout under same gate")
    wins_r=[r for r in imp if r['reason']=='win_runner']; part=[r for r in imp if r['reason'] in('win_partial','scratch_be','partial_flat')]
    print(f"  winners: {len(wins_r)} full-runner, {len([r for r in imp if r['R']>0])-len(wins_r)} partial — runner-capture rate {100*len(wins_r)/max(1,len([r for r in imp if r['R']>0])):.0f}%")
    # a few individual trades (detail, not bulk)
    print("\n  sample individual trade dissections:")
    for r in [x for x in imp if x['year']>=2025][:6]:
        print(f"    {r['date']} {r['sym']:>7} dir{r['dir']:+d} ac60={r['ac60']} vr={r['vr']} -> {r['reason']:>11} R={r['R']:+.2f} mfe={r['mfe']:.1f} ({r['diag']})")
    print(f"\nwrote COMPOUNDING_TRADE_LEDGER.jsonl ({len(L)} candidates incl. rejected)")

if __name__=='__main__':
    main()
