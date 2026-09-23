"""
dead_class_harness.py
=====================
Hunt hidden conditional edges in the "dead-on-average" classes:
  fx, jpy_fx, index, crypto.

Doctrine:
  - No lookahead: features at bar i use only bars index<=i; entry at i+1 open (or i close
    via simulate which only looks forward for fills).
  - Forward holdout: pick on TRAIN (entry year<=2024); report SAME rule on 2025 & 2026
    separately, per-year, per-symbol.
  - Real cost w1.cost_for(sym), scaled by stop tightness in ATR units.
  - Winsorize net R to [-1.3, +5].
"""
from __future__ import annotations
import sys, math, json
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
import wave1_structure_setups_ict as w1
from geometry_lib import atr14, simulate
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

WIN_LO, WIN_HI = -1.3, 5.0
def wins(r): return WIN_LO if r < WIN_LO else (WIN_HI if r > WIN_HI else r)

CLASSES = {
    "fx":     ["AUDUSD","EURGBP","EURUSD","GBPUSD","NZDUSD","USDCAD","USDCHF","USDCNH","USDSGD"],
    "jpy_fx": ["AUDJPY","CHFJPY","EURJPY","GBPJPY","USDJPY"],
    "index":  ["AUS200_cash","DXY_cash","EU50_cash","FRA40_cash","GER40","JP225","N25_cash",
               "NAS100","SPX500","UK100","US2000_cash","US30_cash"],
    "crypto": ["ADAUSD","BTCUSD","DASHUSD","DOTUSD","ETHUSD","LTCUSD","XTZUSD"],
}

# ---- cached load + features ----
_CACHE = {}
def feats(sym):
    if sym in _CACHE: return _CACHE[sym]
    T, B = w1.load(sym)
    n = len(B)
    if n < 60:
        _CACHE[sym] = (T, B, [], [], [], [])
        return _CACHE[sym]
    atrs = [atr14(B, i) for i in range(n)]
    # vol regime: atr percentile vs trailing 100-bar window (no lookahead)
    volpct = [None]*n
    for i in range(n):
        if i < 120 or atrs[i] <= 0:
            continue
        window = [atrs[j] for j in range(i-100, i) if atrs[j] > 0]
        if len(window) < 50: continue
        below = sum(1 for x in window if x < atrs[i])
        volpct[i] = below/len(window)
    pdh, pdl, psh, psl = w1.levels(T, B)
    _CACHE[sym] = (T, B, atrs, volpct, (pdh, pdl), (psh, psl))
    return _CACHE[sym]

def session(h):
    if h < 8: return 0   # Asia (00,04)
    if h < 16: return 1  # London (08,12)
    return 2             # NY (16,20)

# ---- stats / reporting ----
def stats(rs):
    if not rs: return {"n":0,"R":0.0,"win":0.0,"sum":0.0}
    n=len(rs); s=sum(rs); w=sum(1 for r in rs if r>0)
    return {"n":n,"R":round(s/n,4),"win":round(100*w/n,1),"sum":round(s,1)}

def split(records):
    """records: list of (sym, year, R)."""
    tr=[r for _,y,r in records if y<=2024]
    f25=[r for _,y,r in records if y==2025]
    f26=[r for _,y,r in records if y==2026]
    return stats(tr), stats(f25), stats(f26)

def per_year(records):
    by=defaultdict(list)
    for _,y,r in records: by[y].append(r)
    return {y:stats(by[y]) for y in sorted(by)}

def per_sym(records, yfilter=None):
    by=defaultdict(list)
    for s,y,r in records:
        if yfilter is None or yfilter(y): by[s].append(r)
    return {s:stats(by[s]) for s in sorted(by)}

def show(name, records, syms_with_train=None):
    tr,f25,f26=split(records)
    py=per_year(records)
    print(f"\n=== {name} ===")
    print(f"  TRAIN<=24 n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | "
          f"2025 n={f25['n']:5d} R={f25['R']:+.4f} w={f25['win']:.0f}% | "
          f"2026 n={f26['n']:5d} R={f26['R']:+.4f} w={f26['win']:.0f}%")
    line="  yr: "
    for y in sorted(py):
        line+=f"{y}:{py[y]['R']:+.3f}(n{py[y]['n']}) "
    print(line)
    return {"name":name,"train":tr,"f25":f25,"f26":f26,
            "per_year":{str(y):py[y] for y in py}}
