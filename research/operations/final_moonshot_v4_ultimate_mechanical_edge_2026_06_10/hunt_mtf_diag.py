"""Diagnostic: is there ANY directional trend-continuation edge in the geometry,
before we layer pullback logic? Compare:
  - trend-aligned entry (enter EVERY bar in HTF trend direction)
  - counter-trend entry (enter against HTF trend)
  - breakout continuation (enter when price makes new N-bar high in uptrend)
across exit geometries. If trend-aligned >> counter-trend, continuation has signal
and we tune the entry. If not, the family is dead.
"""
from __future__ import annotations
import sys, os, csv, json
from datetime import datetime
REPO="/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR=os.path.join(REPO,"research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
DATA=os.path.join(REPO,"data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
sys.path.insert(0,REPO); sys.path.insert(0,OPDIR)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate
COSTS=json.load(open(os.path.join(OPDIR,"ULTIMATE_REAL_COST_MAP.json"))); GC=COSTS["_global_median"]
def cost_for(s): return COSTS.get(ASSET_CLASS_BY_SYMBOL.get(s),GC)
def load(sym):
    bars,times=[],[]
    with open(os.path.join(DATA,f"{sym}_H4.csv")) as f:
        for r in csv.DictReader(f):
            bars.append(Bar(float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])))
            times.append(datetime.strptime(r["time"],"%Y-%m-%d %H:%M:%S"))
    return bars,times
SYMS=sorted(s[:-7] for s in os.listdir(DATA) if s.endswith("_H4.csv"))
def sma(v,i,n): return None if i+1<n else sum(v[i-n+1:i+1])/n
def agg(rs):
    if not rs: return (0,0.0,0.0)
    return (len(rs),sum(rs)/len(rs),sum(1 for r in rs if r>0)/len(rs))

def run(entry_fn, exit_kind, every=8):
    """entry_fn(closes,highs,lows,i,htf_n)-> +1/-1/0 desired direction.
       sample every `every` bars to keep counts comparable & reduce overlap."""
    tr_aligned=[]; fw_aligned=[]
    for sym in SYMS:
        bars,times=load(sym); c=cost_for(sym)
        cl=[b.c for b in bars]; hi=[b.h for b in bars]; lo=[b.l for b in bars]
        for i in range(120,len(bars)-2,every):
            a=atr14(bars,i)
            if a<=0: continue
            d=entry_fn(cl,hi,lo,i)
            if d==0: continue
            sd=0.5*a
            if exit_kind=="trail":
                R=simulate(bars,i,d,stop_dist=sd,trail_arm=2*sd,trail_gap=1*sd,maxbars=80,cost=c)
            elif exit_kind=="t1":
                R=simulate(bars,i,d,stop_dist=sd,target_dist=1.0*a,maxbars=80,cost=c)
            elif exit_kind=="t2":
                R=simulate(bars,i,d,stop_dist=sd,target_dist=2.0*a,maxbars=80,cost=c)
            (tr_aligned if times[i].year<=2024 else fw_aligned).append(R)
    return agg(tr_aligned),agg(fw_aligned)

def sma_trend(n,lag=6):
    def f(cl,hi,lo,i):
        s=sma(cl,i,n); sp=sma(cl,i-lag,n)
        if s is None or sp is None: return 0
        if cl[i]>s and s>sp: return 1
        if cl[i]<s and s<sp: return -1
        return 0
    return f
def sma_trend_counter(n,lag=6):
    base=sma_trend(n,lag)
    return lambda cl,hi,lo,i: -base(cl,hi,lo,i)
def breakout(n):
    def f(cl,hi,lo,i):
        if i<n: return 0
        if hi[i]>=max(hi[i-n:i]): return 1
        if lo[i]<=min(lo[i-n:i]): return -1
        return 0
    return f
def breakout_counter(n):
    base=breakout(n); return lambda cl,hi,lo,i:-base(cl,hi,lo,i)

print("entry x exit : TRAIN(n,mean,win) | FWD(n,mean,win)")
def show(name,fn,exits=("trail","t1","t2")):
    for ek in exits:
        tr,fw=run(fn,ek)
        print(f"{name:28s} {ek:5s} TR n={tr[0]:5d} {tr[1]:+.4f} {tr[2]*100:4.1f}%  | FW n={fw[0]:5d} {fw[1]:+.4f} {fw[2]*100:4.1f}%")

show("ALIGN sma50", sma_trend(50))
show("COUNTER sma50", sma_trend_counter(50))
show("ALIGN sma100", sma_trend(100))
show("COUNTER sma100", sma_trend_counter(100))
show("BREAKOUT 20 (cont)", breakout(20))
show("BRKOUT-CTR 20 (fade)", breakout_counter(20))
show("BREAKOUT 40 (cont)", breakout(40))
show("BRKOUT-CTR 40 (fade)", breakout_counter(40))
