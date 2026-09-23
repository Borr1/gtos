"""Probe the only train+forward-positive cell: LONG-side trend continuation in METALS.
Is it a real per-symbol-stable signal, or just gold's 2024-25 bull drift on one symbol?
Tests:
 1. per-symbol breakdown (7 metals) train vs forward
 2. per-year forward
 3. compare ALIGN-long vs ALWAYS-long (every-bar long) — if align doesn't beat
    always-long, the 'signal' is just drift, not a continuation edge.
 4. compare long vs short in metals (drift asymmetry check)
"""
from __future__ import annotations
import sys, os, csv, json
from datetime import datetime
REPO="/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR=os.path.join(REPO,"research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
DATA=os.path.join(REPO,"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
sys.path.insert(0,REPO); sys.path.insert(0,OPDIR)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC
from geometry_lib import Bar, atr14, simulate
COSTS=json.load(open(os.path.join(OPDIR,"ULTIMATE_REAL_COST_MAP.json"))); GC=COSTS["_global_median"]
def cost_for(s): return COSTS.get(AC.get(s),GC)
def load(sym):
    bars,times=[],[]
    with open(os.path.join(DATA,f"{sym}_H4.csv")) as f:
        for r in csv.DictReader(f):
            bars.append(Bar(float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])))
            times.append(datetime.strptime(r["time"],"%Y-%m-%d %H:%M:%S"))
    return bars,times
METALS=sorted([s[:-7] for s in os.listdir(DATA) if s.endswith("_H4.csv") and AC.get(s[:-7])=="metals"])
def sma(v,i,n): return None if i+1<n else sum(v[i-n+1:i+1])/n
def agg(rs):
    if not rs: return dict(n=0,mean=0.0,win=0.0)
    return dict(n=len(rs),mean=sum(rs)/len(rs),win=sum(1 for r in rs if r>0)/len(rs))

def collect(mode, htf_n=50, strong=0.15, lag=6, stop_mult=0.5, cooldown=3):
    """mode: 'align_long','align_short','always_long','always_short'."""
    out={}
    for sym in METALS:
        bars,times=load(sym); cost=cost_for(sym)
        cl=[b.c for b in bars]
        rows=[]; last=-10**9
        for i in range(120,len(bars)-2):
            if i-last<cooldown: continue
            a=atr14(bars,i)
            if a<=0: continue
            d=0
            if mode.startswith("align"):
                s=sma(cl,i,htf_n); sp=sma(cl,i-lag,htf_n)
                if s is None or sp is None: continue
                slope=(s-sp)/lag
                if abs(slope)/a < strong: continue
                td = 1 if (cl[i]>s and slope>0) else (-1 if (cl[i]<s and slope<0) else 0)
                if td==0: continue
                want = 1 if mode=="align_long" else -1
                if td!=want: continue
                d=want
            else:
                d = 1 if mode=="always_long" else -1
                # sample at same cadence-ish: only every cooldown bars handled by last
            sd=stop_mult*a
            R=simulate(bars,i,d,stop_dist=sd,trail_arm=2*sd,trail_gap=1*sd,maxbars=80,cost=cost)
            rows.append((times[i].year,R)); last=i
        out[sym]=rows
    return out

def summ(out,label):
    allrows=[r for rows in out.values() for r in rows]
    tr=[r[1] for r in allrows if r[0]<=2024]; fw=[r[1] for r in allrows if r[0]>=2025]
    at=agg(tr); af=agg(fw)
    print(f"\n## {label}")
    print(f"  ALL  TR {at['mean']:+.4f} {at['win']*100:4.1f}% n{at['n']} | FW {af['mean']:+.4f} {af['win']*100:4.1f}% n{af['n']}")
    for y in (2025,2026):
        yy=agg([r[1] for r in allrows if r[0]==y]); print(f"     yr{y} FW {yy['mean']:+.4f} {yy['win']*100:4.1f}% n{yy['n']}")
    for sym in METALS:
        rows=out[sym]
        t=agg([r[1] for r in rows if r[0]<=2024]); f=agg([r[1] for r in rows if r[0]>=2025])
        print(f"     {sym:8s} TR {t['mean']:+.4f}(n{t['n']:4d}) | FW {f['mean']:+.4f}(n{f['n']:4d})")
    return af

summ(collect("align_long"),  "METALS ALIGN-LONG (strong.15 sma50 stop.5 trail)")
summ(collect("always_long"), "METALS ALWAYS-LONG (drift baseline)")
summ(collect("align_short"), "METALS ALIGN-SHORT")
summ(collect("always_short"),"METALS ALWAYS-SHORT (drift baseline)")
# tighter strong filter
summ(collect("align_long",strong=0.10), "METALS ALIGN-LONG strong.10")
summ(collect("align_long",htf_n=100,strong=0.15), "METALS ALIGN-LONG htf100")
