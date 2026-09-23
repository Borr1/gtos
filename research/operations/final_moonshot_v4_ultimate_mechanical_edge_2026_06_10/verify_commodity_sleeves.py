"""VERIFY the commodity-book candidates before trusting them. Per-YEAR and per-SYMBOL
breakdown for energy/agri/metals (catch 2025-26 trend-confound + single-symbol drivers),
and an inverted-signal null. Reuses the trusted FVG engine."""
import sys, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

def sym_trades(sym):
    out=[]
    try:
        for (t,d,sd,td,i,B,cost) in g.fvg_signals(sym):
            out.append((t,d,sd,td,i,B,cost))
    except Exception: return []
    return out

for cls in ("metals","energy","agri"):
    syms=sorted(s for s in w1.SYMBOLS if AC.get(s)==cls)
    print(f"\n==== {cls.upper()} : {syms}")
    peryear=collections.defaultdict(lambda:[0,0.0]); persym=collections.defaultdict(lambda:[0,0.0])
    inv_year=collections.defaultdict(lambda:[0,0.0])
    for sym in syms:
        for (t,d,sd,td,i,B,cost) in sym_trades(sym):
            r=simulate(B,i,d,stop_dist=sd,target_dist=td,cost=cost)
            ri=simulate(B,i,-d,stop_dist=sd,target_dist=td,cost=cost)  # inverted null
            peryear[t.year][0]+=1; peryear[t.year][1]+=r
            persym[sym][0]+=1; persym[sym][1]+=r
            inv_year[t.year][0]+=1; inv_year[t.year][1]+=ri
    print("  per-year EV/trade (n):")
    for y in sorted(peryear):
        c,s=peryear[y]; ic,isum=inv_year[y]
        print(f"    {y}: {s/c:+.3f} (n={c:>3})   inverted {isum/ic:+.3f}")
    print("  per-symbol EV/trade (n):")
    for sym in sorted(persym, key=lambda k:-persym[k][1]/max(1,persym[k][0])):
        c,s=persym[sym]
        print(f"    {sym:>12}: {s/c:+.3f} (n={c:>3})")
