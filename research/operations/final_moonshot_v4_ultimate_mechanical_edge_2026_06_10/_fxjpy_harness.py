import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
from geometry_lib import simulate, atr14, Bar
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
import statistics, json

FX = [s for s in w1.SYMBOLS if ASSET_CLASS_BY_SYMBOL.get(s) in ('fx','jpy_fx')]
JPY = [s for s in FX if ASSET_CLASS_BY_SYMBOL.get(s)=='jpy_fx']
PURE_FX = [s for s in FX if ASSET_CLASS_BY_SYMBOL.get(s)=='fx']

def wins(r): return max(-1.3, min(5.0, r))

def atr_series(B):
    out=[0.0]*len(B)
    for i in range(len(B)): out[i]=atr14(B,i)
    return out

# Cache loads
CACHE={}
def get(sym):
    if sym not in CACHE:
        T,B=w1.load(sym)
        CACHE[sym]=(T,B,atr_series(B))
    return CACHE[sym]

def ac60(B,i,n=60): return cs.autocorr(B,i,n)

def report_by_year(trades):
    # trades: list of (year, netR, dir)
    from collections import defaultdict
    yr=defaultdict(list)
    for y,r,d in trades: yr[y].append(r)
    out={}
    for y in sorted(yr):
        rs=yr[y]
        out[y]=dict(n=len(rs), R=round(statistics.mean(rs),4), win=round(100*sum(1 for x in rs if x>0)/len(rs),1), tot=round(sum(rs),1))
    return out

if __name__=='__main__':
    print('FX',FX)
    print('JPY',JPY)
    print('PURE_FX',PURE_FX)
