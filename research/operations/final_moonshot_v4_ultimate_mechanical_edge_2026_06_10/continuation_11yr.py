"""11-year regime-robustness test of the vol-expansion continuation edge.
Concatenates H4 2015-2022 + 2022-2026 per symbol; vol-expansion Donchian-55
breakout (ATR/SMA100(ATR)>=1.45), trail exit, tested geometry_lib. Per-year
per-trade R + by asset class + long/short. Decisive: does continuation hold
across 11 years/many regimes, or only 2025-2026?"""
import csv,sys,glob,collections,statistics
from pathlib import Path
R="research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0,R); sys.path.insert(0,".")
from geometry_lib import Bar, atr14, simulate
import json
COST=json.load(open(f"{R}/ULTIMATE_REAL_COST_MAP.json"))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC
OLD="data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022"
NEW="data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
def load(sym):
    rows=[]
    for d in (OLD,NEW):
        f=f"{d}/{sym}_H4.csv"
        if Path(f).exists():
            rows+=[(str(r["time"])[:19],float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),float(r["volume"])) for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
    # dedupe by time, sort
    seen={};[seen.setdefault(t,(t,o,h,l,c,v)) for (t,o,h,l,c,v) in rows]
    return [seen[k] for k in sorted(seen)]
yr=collections.defaultdict(lambda:[0,0.0]); ac_agg=collections.defaultdict(lambda:[0,0.0]); side=collections.defaultdict(lambda:[0,0.0])
syms=sorted(set(Path(f).name[:-7] for f in glob.glob(NEW+"/*_H4.csv")))
for sym in syms:
    ac=AC.get(sym)
    if ac is None or ac in {"index","jpy_fx","agri"}: continue
    rows=load(sym)
    if len(rows)<300: continue
    c=float(COST.get(ac,0.095))
    bars=[Bar(r[1],r[2],r[3],r[4],r[5]) for r in rows];T=[r[0] for r in rows]
    A=[atr14(bars,i) for i in range(len(bars))]
    for i in range(160,len(bars)-1):
        if A[i]<=0: continue
        sma100=sum(A[i-99:i+1])/100
        if sma100<=0 or A[i]/sma100<1.45: continue
        ph=max(b.h for b in bars[i-55:i]);pl=min(b.l for b in bars[i-55:i])
        d=1 if bars[i].c>ph else (-1 if bars[i].c<pl else 0)
        if d==0: continue
        sd=0.5*A[i];r=simulate(bars,i,d,stop_dist=sd,trail_arm=2*sd,trail_gap=1*sd,cost=c)
        y=T[i][:4];yr[y][0]+=1;yr[y][1]+=r;ac_agg[ac][0]+=1;ac_agg[ac][1]+=r
        side["long" if d>0 else "short"][0]+=1;side["long" if d>0 else "short"][1]+=r
out={"by_year":{y:{"n":v[0],"per_trade":round(v[1]/v[0],4)} for y,v in sorted(yr.items()) if v[0]},
     "by_asset":{a:{"n":v[0],"per_trade":round(v[1]/v[0],4)} for a,v in sorted(ac_agg.items()) if v[0]},
     "by_side":{k:{"n":v[0],"per_trade":round(v[1]/v[0],4)} for k,v in side.items()},
     "pos_years":sum(1 for v in yr.values() if v[0] and v[1]>0),"total_years":len([v for v in yr.values() if v[0]])}
json.dump(out,open(f"{R}/ULTIMATE_CONTINUATION_11YR.json","w"),indent=1,sort_keys=True)
print(json.dumps(out["by_year"],sort_keys=True));print("pos_years",out["pos_years"],"/",out["total_years"])
print("by_asset",json.dumps(out["by_asset"]));print("by_side",json.dumps(out["by_side"]))
