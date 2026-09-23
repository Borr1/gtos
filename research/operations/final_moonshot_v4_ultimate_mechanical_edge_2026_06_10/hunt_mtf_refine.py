"""Refine: trend-continuation may only work in (a) specific asset classes with
structural drift (index, crypto), (b) strong-trend regimes, (c) longer horizons.
Break results down by asset_class & direction, with a STRONG-trend gate
(slope normalized by ATR) and a wider stop to dilute cost. Also test a daily-MTF
gate + H4 pullback, asset-class-resolved. Honest forward reporting.
"""
from __future__ import annotations
import sys, os, csv, json
from datetime import datetime
from collections import defaultdict
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
SYMS=sorted(s[:-7] for s in os.listdir(DATA) if s.endswith("_H4.csv"))
def sma(v,i,n): return None if i+1<n else sum(v[i-n+1:i+1])/n
def agg(rs):
    if not rs: return dict(n=0,mean=0.0,win=0.0)
    return dict(n=len(rs),mean=sum(rs)/len(rs),win=sum(1 for r in rs if r>0)/len(rs))

def collect(cfg):
    """Return list of (year, ac, dir, R). cfg: htf_n, fast_n, stop_mult, strong (slope/atr min),
    exit ('trail'/'t2'), trail mults, pullback (bool touch_fast)."""
    out=[]
    for sym in SYMS:
        bars,times=load(sym); cost=cost_for(sym); ac=AC.get(sym,"?")
        cl=[b.c for b in bars]; hi=[b.h for b in bars]; lo=[b.l for b in bars]
        htf_n=cfg["htf_n"]; fast_n=cfg["fast_n"]; lag=cfg.get("lag",6)
        last=-10**9
        for i in range(120,len(bars)-2):
            if i-last<cfg.get("cooldown",3): continue
            a=atr14(bars,i)
            if a<=0: continue
            s=sma(cl,i,htf_n); sp=sma(cl,i-lag,htf_n)
            if s is None or sp is None: continue
            slope=(s-sp)/lag
            strong=abs(slope)/a
            if strong < cfg.get("strong",0.0): continue
            d=0
            if cl[i]>s and slope>0: d=1
            elif cl[i]<s and slope<0: d=-1
            if d==0: continue
            if cfg.get("long_only") and d!=1: continue
            if cfg.get("pullback"):
                f=sma(cl,i,fast_n)
                if f is None: continue
                if d==1 and not (lo[i]<=f and cl[i]>f): continue
                if d==-1 and not (hi[i]>=f and cl[i]<f): continue
            sm=cfg["stop_mult"]; sd=sm*a
            if cfg["exit"]=="trail":
                R=simulate(bars,i,d,stop_dist=sd,trail_arm=cfg.get("arm",2)*sd,trail_gap=cfg.get("gap",1)*sd,maxbars=cfg.get("maxbars",80),cost=cost)
            else:
                R=simulate(bars,i,d,stop_dist=sd,target_dist=cfg["tmult"]*a,maxbars=cfg.get("maxbars",80),cost=cost)
            out.append((times[i].year,ac,d,R))
            last=i
    return out

def report(out,label):
    tr=[t for t in out if t[0]<=2024]; fw=[t for t in out if t[0]>=2025]
    print(f"\n### {label}  (train n={len(tr)} fwd n={len(fw)})")
    a_tr=agg([t[3] for t in tr]); a_fw=agg([t[3] for t in fw])
    print(f"  ALL  TR {a_tr['mean']:+.4f} {a_tr['win']*100:4.1f}% (n{a_tr['n']}) | FW {a_fw['mean']:+.4f} {a_fw['win']*100:4.1f}% (n{a_fw['n']})")
    # forward by asset class
    accs=sorted(set(t[1] for t in fw))
    for ac in accs:
        f=agg([t[3] for t in fw if t[1]==ac]); tt=agg([t[3] for t in tr if t[1]==ac])
        flag=" <==+FW" if (f['mean']>0 and f['n']>=60) else ""
        print(f"    {ac:8s} TR {tt['mean']:+.4f}(n{tt['n']:4d}) | FW {f['mean']:+.4f} {f['win']*100:4.1f}% (n{f['n']:4d}){flag}")
    # forward by year
    for y in sorted(set(t[0] for t in fw)):
        yy=agg([t[3] for t in fw if t[0]==y]); print(f"    yr{y} FW {yy['mean']:+.4f} (n{yy['n']})")
    return a_fw

base=dict(htf_n=50,fast_n=20,stop_mult=0.5,exit="trail",arm=2,gap=1,cooldown=3)
report(collect(dict(base)),"baseline align trail (no strong gate)")
report(collect(dict(base,strong=0.15)),"strong>=0.15 align trail")
report(collect(dict(base,strong=0.30)),"strong>=0.30 align trail")
report(collect(dict(base,strong=0.15,stop_mult=1.0,arm=2,gap=1)),"strong>=0.15 stop1.0 trail")
report(collect(dict(base,strong=0.15,exit="t2",tmult=2.0)),"strong>=0.15 target2 ")
report(collect(dict(base,strong=0.15,pullback=True)),"strong>=0.15 + pullback trail")
report(collect(dict(base,strong=0.15,long_only=True)),"strong>=0.15 LONG-ONLY trail")
report(collect(dict(base,htf_n=100,strong=0.20,stop_mult=1.0,maxbars=120)),"htf100 strong.20 stop1 maxbars120")
