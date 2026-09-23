"""KB2 re-validation: fx_jpy London-open momentum continuation on DEEP M15 history.

Reproduces the EXACT locked rule from KB_fx_jpy.md R1 but on the new TRAIN->FORWARD split
made possible by the 2014-2025 M15 backfill unioned with the 2025-06..2026-06 forward dir.

Locked rule (KB_fx_jpy R1):
  symbols GBPJPY,USDJPY ; M15 ; at first London bar at/after server-hour 8:
  impulse = close(4th London M15 bar) - open(1st London M15 bar) ; d=sign(impulse)
  entry = close of 4th bar ; stop=1.0*ATR14 ; target=2.5*ATR14 ; maxbars=48 ; 1 trade/sym/day.
  cost = w1.cost_for ; winsorize net R to [-1.3,+5].

TRAIN = entries year<=2024 ; FORWARD = 2025 & 2026, reported separately + per-year + per-symbol.
"""
import sys, os, csv, statistics
from datetime import datetime
from collections import defaultdict
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1

DIR_DEEP = ROOT+'/data/mt5_research_exports/bridge_ftmo_fx_m15_backfill_2014_2025'
DIR_FWD  = ROOT+'/data/mt5_research_exports/bridge_ftmo_m15_20250601_20260610'
def wins(r): return max(-1.3, min(5.0, r))

_C={}
def load_m15(sym):
    if sym in _C: return _C[sym]
    merged={}
    for d in (DIR_DEEP, DIR_FWD):
        p=os.path.join(d, f'{sym}_M15.csv')
        if not os.path.exists(p): continue
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t=datetime.strptime(row['time'],'%Y-%m-%d %H:%M:%S')
                    merged[t]=Bar(float(row['open']),float(row['high']),float(row['low']),float(row['close']),float(row.get('volume',0) or 0))
                except: continue
    T=sorted(merged); B=[merged[t] for t in T]
    A=[atr14(B,i) for i in range(len(B))]
    _C[sym]=(T,B,A); return _C[sym]

def london_open_rule(symbols, london_start_h=8, lookwin=4, stop_m=1.0, tgt_m=2.5, maxbars=48):
    """KB R1 exact: impulse over first `lookwin` London bars, enter at close of bar lookwin-1."""
    trades=[]   # (year, sym, R, date)
    for sym in symbols:
        T,B,A=load_m15(sym); cost=w1.cost_for(sym)
        byday=defaultdict(list)
        for i,t in enumerate(T): byday[t.date()].append(i)
        for day,idxs in sorted(byday.items()):
            lon=[i for i in idxs if T[i].hour>=london_start_h]
            if len(lon)<lookwin+1: continue
            i0=lon[0]
            if i0<20: continue
            iw=lon[lookwin-1]
            a=A[iw]
            if a<=0: continue
            d=1 if B[iw].c>B[i0].o else -1
            r=simulate(B,iw,d,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=maxbars,cost=cost)
            trades.append((T[iw].year, sym, wins(r), str(T[iw].date())))
    return trades

def agg(rows):
    if not rows: return (0,0.0,0.0)
    n=len(rows); m=statistics.mean(r[2] for r in rows); w=100*sum(1 for r in rows if r[2]>0)/n
    return (n, round(m,4), round(w,1))

def report(rows, title):
    print(f"\n===== {title} =====")
    yrs=sorted(set(r[0] for r in rows))
    print(f"{'year':>6}{'n':>7}{'R/t':>9}{'win%':>7}")
    for y in yrs:
        ry=[r for r in rows if r[0]==y]; n,m,wn=agg(ry)
        tag=' FWD' if y>=2025 else ' train'
        print(f"{y:>6}{n:>7}{m:>+9.3f}{wn:>6.1f}%{tag}")
    tr=[r for r in rows if r[0]<=2024]; fwd=[r for r in rows if r[0]>=2025]
    f25=[r for r in rows if r[0]==2025]; f26=[r for r in rows if r[0]==2026]
    print("  TRAIN<=2024:", agg(tr))
    print("  FWD2025    :", agg(f25))
    print("  FWD2026    :", agg(f26))
    print("  FWD25-26   :", agg(fwd))
    for s in sorted(set(r[1] for r in rows)):
        rs_tr=[r for r in tr if r[1]==s]; rs_fwd=[r for r in fwd if r[1]==s]
        print(f"  {s}: TRAIN {agg(rs_tr)}  FWD {agg(rs_fwd)}")

if __name__=='__main__':
    JPY2=['GBPJPY','USDJPY']
    rows=london_open_rule(JPY2)
    report(rows, "LOCKED RULE R1 (GBPJPY+USDJPY, lw4, stop1.0/tgt2.5, maxbars48) DEEP M15")
    # robustness: per-symbol full sets, and the pure-FX falsification control on deep data
    print("\n----- falsification control: SAME rule on PURE FX (EURUSD,GBPUSD,AUDUSD) -----")
    report(london_open_rule(['EURUSD','GBPUSD','AUDUSD']), "PURE FX control")
    # geometry robustness on TRAIN: does t2.5 still beat t1.5/t2.0/t3.0 in-train?
    print("\n----- target robustness on JPY2 (train vs fwd) -----")
    for tg in [1.5,2.0,2.5,3.0]:
        rws=london_open_rule(JPY2, tgt_m=tg)
        tr=[r for r in rws if r[0]<=2024]; fwd=[r for r in rws if r[0]>=2025]
        print(f"  tgt{tg}: TRAIN {agg(tr)}  FWD {agg(fwd)}")
