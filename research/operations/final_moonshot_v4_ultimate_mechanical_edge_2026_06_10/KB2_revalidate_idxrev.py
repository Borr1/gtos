"""KB2 re-validation: index failed-breakout fade on DEEP H4 history.

Reproduces the EXACT locked rule from KB_index_reversion.md but now with real pre-2024
TRAIN per index (SPX500 2021+, GER40 2018+, UK100 2017+, US30 2019+, EU50 2021+),
sourced via the deep H4 backfill merged into w1.load's D2 dir.

LOCKED RULE: failed-breakout fade, lb_range=16, stop=1.5*ATR, target=0.75R, maxbars=60, NO gate.
Cost = w1.cost_for (index 0.0638) scaled by 1/stop_atr. Winsorize [-1.3,+5].
TRAIN=entries year<=2024 ; FORWARD=2025 & 2026 reported separately + per-year + per-symbol.
"""
import sys
from pathlib import Path
HERE=Path('/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
sys.path.insert(0,str(HERE)); sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent')
import idxrev_sleeve as idx

POCKET=['SPX500','UK100','FRA40_cash','EU50_cash','US2000_cash','JP225','GER40','US30_cash']
DEEP_TRAIN=['SPX500','GER40','UK100','US30_cash','EU50_cash']  # have real pre-2024 bars now

def agg(rows):
    if not rows: return (0,0.0,0.0)
    n=len(rows); m=sum(r['R'] for r in rows)/n; w=100*sum(1 for r in rows if r['R']>0)/n
    return (n,round(m,4),round(w,1))

def split(rows,label):
    print(f"\n===== {label} =====")
    yrs=sorted(set(r['year'] for r in rows))
    for y in yrs:
        ry=[r for r in rows if r['year']==y]; n,m,w=agg(ry)
        tag='FWD' if y>=2025 else 'train'
        print(f"  {y}: n={n:>4} R/t={m:+.3f} win={w:.0f}% {tag}")
    tr=[r for r in rows if r['year']<=2024]; f25=[r for r in rows if r['year']==2025]
    f26=[r for r in rows if r['year']==2026]; fwd=[r for r in rows if r['year']>=2025]
    print("  TRAIN<=2024:",agg(tr),"| FWD2025:",agg(f25),"| FWD2026:",agg(f26),"| FWD25-26:",agg(fwd))

if __name__=='__main__':
    # LOCKED RULE on the full kept pocket
    rows=idx.run(lb_range=16, ac_max=99.0, stop_atr=1.5, tgt_R=0.75, maxbars=60, symbols=POCKET)
    split(rows,"LOCKED RULE (lb16 stop1.5 tgt0.75 no-gate) FULL POCKET, DEEP H4")

    print("\n----- PER-SYMBOL TRAIN vs FWD (deep-train indices) -----")
    for s in DEEP_TRAIN:
        rs=idx.run(lb_range=16, ac_max=99.0, stop_atr=1.5, tgt_R=0.75, maxbars=60, symbols=[s])
        tr=[r for r in rs if r['year']<=2024]; fwd=[r for r in rs if r['year']>=2025]
        print(f"  {s:12s} TRAIN {agg(tr)}  FWD {agg(fwd)}")

    print("\n----- DEEP-TRAIN-ONLY pocket (the honest convertible set) -----")
    rows2=idx.run(lb_range=16, ac_max=99.0, stop_atr=1.5, tgt_R=0.75, maxbars=60, symbols=DEEP_TRAIN)
    split(rows2,"DEEP-TRAIN indices pocket (SPX500,GER40,UK100,US30,EU50)")

    print("\n----- geometry robustness on DEEP-TRAIN pocket (train-chosen?) -----")
    for st,tg in [(1.5,0.5),(1.5,0.75),(2.0,0.5),(1.0,1.0),(0.75,2.0)]:
        rs=idx.run(lb_range=16, ac_max=99.0, stop_atr=st, tgt_R=tg, maxbars=60, symbols=DEEP_TRAIN)
        tr=[r for r in rs if r['year']<=2024]; fwd=[r for r in rs if r['year']>=2025]
        print(f"  stop{st}/tgt{tg}: TRAIN {agg(tr)}  FWD {agg(fwd)}")

    print("\n----- lb robustness on DEEP-TRAIN pocket -----")
    for lb in [8,12,16,20]:
        rs=idx.run(lb_range=lb, ac_max=99.0, stop_atr=1.5, tgt_R=0.75, maxbars=60, symbols=DEEP_TRAIN)
        tr=[r for r in rs if r['year']<=2024]; fwd=[r for r in rs if r['year']>=2025]
        print(f"  lb{lb}: TRAIN {agg(tr)}  FWD {agg(fwd)}")
