"""
LM_independence.py — is the liquidity stop-hunt layer a NEW edge or a relabel of
the existing continuation sleeves?

The strict-gate survivors are HTF-ALIGNED continuation longs on metals/energy/index.
The book already has metals_core + energy_agri continuation sleeves. This script:
  1) Rebuilds daily-R streams for the best liquidity cells (H4, train-evidenced).
  2) Compares them to the existing FVG-retest continuation mechanic (gold_sleeve
     fvg_signals, the canonical continuation entry) on the SAME symbols.
  3) Reports day-overlap %, same-day-direction agreement, and daily-R correlation.
A LOW correlation => the layer is additive; HIGH => it is a relabel (no new alpha).

Also isolates the ONE structurally-distinct liquidity mechanic — the COUNTER-trend
(reversal) reclaim, which the continuation sleeves do NOT trade — and grades it.
"""
import sys, os, json, collections, statistics, math
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import liquidity_map as L
import wave1_structure_setups_ict as w1
from geometry_lib import simulate, atr14
import gold_sleeve_strategy as g

def htf_dir(B,i,lb=30): return w1.htf_trend(B,i,lb)

def liquidity_daily_stream(symbols, htf_filter='ALN'):
    """Daily summed-R for liquidity aligned-continuation longs on given symbols (H4)."""
    daily=collections.defaultdict(float); days=collections.defaultdict(list)
    gk=dict(target_mode='fixedR', target_R=2.0, activity_min=0.0)
    for sym in symbols:
        lm=L.get_map(sym,'H4')
        if lm is None: continue
        for sig in L.sweep_signals(lm, **gk):
            i_sweep=sig['i']-1; tr=htf_dir(lm.B,i_sweep)
            d=1 if sig['side']=='long' else -1
            tag='ALN' if tr==d else 'CTR' if tr==-d else 'NEU'
            if tag!=htf_filter: continue
            dk=lm.T[sig['i']].date()
            daily[dk]+=sig['R']; days[dk].append((sym,sig['side'],sig['R']))
    return daily, days

def fvg_daily_stream(symbols):
    """Daily summed-R for the canonical FVG continuation mechanic on given symbols."""
    daily=collections.defaultdict(float)
    for sym in symbols:
        try: T,B=w1.load(sym)
        except Exception: continue
        if len(B)<200: continue
        cost=w1.cost_for(sym)
        try:
            sigs=list(g.fvg_signals(sym))
        except Exception:
            continue
        for (t,d,sd,td,i,B2,c2) in sigs:
            r=simulate(B,i,d,stop_dist=sd,target_dist=2*sd,cost=c2)
            daily[t.date()]+=r
    return daily

def corr(a,b):
    keys=sorted(set(a)|set(b))
    xa=[a.get(k,0.0) for k in keys]; xb=[b.get(k,0.0) for k in keys]
    if len(keys)<3: return None
    ma=statistics.mean(xa); mb=statistics.mean(xb)
    num=sum((x-ma)*(y-mb) for x,y in zip(xa,xb))
    da=math.sqrt(sum((x-ma)**2 for x in xa)); db=math.sqrt(sum((y-mb)**2 for y in xb))
    return num/(da*db) if da>0 and db>0 else None

def overlap(a,b):
    sa=set(a); sb=set(b)
    inter=sa&sb
    return dict(liq_days=len(sa), fvg_days=len(sb), shared_days=len(inter),
                liq_overlap_pct=round(100*len(inter)/max(1,len(sa)),1),
                fvg_overlap_pct=round(100*len(inter)/max(1,len(sb)),1))

def main():
    out={}
    # the metals+energy continuation overlap test (where the strongest aligned cells live)
    METALS=g.METALS; ENERGY=['USOIL_cash','UKOIL_cash','NATGAS_cash','HEATOIL_c']
    for grp,syms in (('metals',METALS),('energy',ENERGY)):
        liq,_=liquidity_daily_stream(syms, 'ALN')
        fvg=fvg_daily_stream(syms)
        c=corr(liq,fvg); ov=overlap(liq,fvg)
        liq_sum=sum(liq.values()); fvg_sum=sum(fvg.values())
        print(f"\n=== {grp}: liquidity ALIGNED-continuation vs FVG continuation ===")
        print(f"  daily-R corr = {c}")
        print(f"  overlap: {ov}")
        print(f"  liq total R {liq_sum:+.1f} over {len(liq)} days; fvg total R {fvg_sum:+.1f} over {len(fvg)} days")
        out[grp]=dict(corr=c, overlap=ov, liq_total_R=round(liq_sum,1), fvg_total_R=round(fvg_sum,1))

    # the structurally DISTINCT mechanic: COUNTER-trend reclaim (reversal) — sleeves don't trade this
    print("\n=== COUNTER-trend (reversal) reclaim — the genuinely new mechanic ===")
    for grp,syms in (('metals',METALS),('energy',ENERGY),('jpy_fx',['GBPJPY','USDJPY','EURJPY','CHFJPY']),
                     ('index',['SPX500','GER40','NAS100','UK100','JP225'])):
        recs=[]
        for sym in syms:
            lm=L.get_map(sym,'H4')
            if lm is None: continue
            for sig in L.sweep_signals(lm, target_mode='fixedR', target_R=2.0):
                i_sweep=sig['i']-1; tr=htf_dir(lm.B,i_sweep)
                d=1 if sig['side']=='long' else -1
                if tr==-d:  # counter-trend reclaim = reversal
                    recs.append(sig)
        if not recs: continue
        trn,fw=L.split_tf(recs); py=L.per_year(recs)
        fy=" ".join(f"{y}:{py[y]['mean_R']:+.2f}(n{py[y]['n']})" for y in sorted(py) if y>=2025)
        print(f"  {grp:7s} CTR: TRAIN {trn['mean_R']:+.3f}(n{trn['n']}) FWD {fw['mean_R']:+.3f}(n{fw['n']}) w{fw['win']:.0f}% [{fy}]")
        out[f"counter_{grp}"]=dict(train=trn, fwd=fw)

    with open(EDGE+"/LM_INDEPENDENCE_RESULT.json","w") as f: json.dump(out,f,indent=1,default=str)
    print("\nWROTE LM_INDEPENDENCE_RESULT.json")

if __name__=="__main__":
    main()
